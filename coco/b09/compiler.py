from __future__ import annotations

from pathlib import Path
from typing import IO, List

from coco import b09
from coco.b09 import error_handler
from coco.b09.configs import CompilerConfigs
from coco.b09.elements import (
    Basic09CodeStatement,
    BasicExpressionList,
    BasicLine,
    BasicLiteral,
    BasicOnBrkGoStatement,
    BasicOnErrGoStatement,
    BasicRunCall,
    BasicVar,
)
from coco.b09.grammar import PROCNAME_REGEX, grammar
from coco.b09.parser import BasicVisitor
from coco.b09.procbank import ProcedureBank
from coco.b09.prog import BasicProg
from coco.b09.visitors import (
    BasicEmptyDataElementVisitor,
    BasicFunctionalExpressionPatcherVisitor,
    BasicHbuffPresenceVisitor,
    BasicInputStatementPatcherVisitor,
    BasicNextPatcherVisitor,
    BasicPrintStatementPatcherVisitor,
    BasicReadStatementPatcherVisitor,
    CoerceIntegerArgsVisitor,
    DeclareImplicitArraysVisitor,
    GetDimmedArraysVisitor,
    IntegerVarVisitor,
    JoystickVisitor,
    LineNumberCheckerVisitor,
    LineNumberFilterVisitor,
    LineReferenceVisitor,
    LineZeroFilterVisitor,
    RewriteIntegerLiteralsVisitor,
    SetDimStringStorageVisitor,
    SetInitializeVisitor,
    SetIntegerDimVisitor,
    StatementCollectorVisitor,
    StrVarAllocatorVisitor,
    VarInitializerVisitor,
)


class ParseError(Exception):
    pass


def _normalized_no_optimize_vars(names: "set[str] | list[str]") -> "set[str]":
    """Normalize a user-supplied ``--no-optimize`` list to the
    internal naming convention used by :class:`IntegerVarVisitor`.

    Users provide uppercase BASIC names such as ``A``, ``X1``, or
    ``Y()`` (matching the ``--list-integer-candidates`` output).
    Arrays are stored internally with an ``arr_`` prefix, so
    ``Y()`` maps to ``arr_Y``. Names are uppercased before matching
    because BASIC is case-insensitive and the rest of the pipeline
    uppercases identifiers.
    """
    normalized: set[str] = set()
    for raw in names:
        name = raw.strip().upper()
        if not name:
            continue
        if name.endswith("()"):
            normalized.add(f"arr_{name[:-2]}")
        else:
            normalized.add(name)
    return normalized


def convert(
    progin: str,
    *,
    add_standard_prefix: bool = True,
    add_suffix: bool = True,
    compiler_configs: CompilerConfigs | None = None,
    default_str_storage: int = b09.DEFAULT_STR_STORAGE,
    default_width32: bool = True,
    filter_unused_linenum: bool = False,
    initialize_vars: bool = False,
    no_optimize_vars: "set[str] | None" = None,
    optimize: bool = False,
    output_dependencies: bool = False,
    procname: str = "",
    skip_procedure_headers: bool = False,
) -> str:
    compiler_configs = compiler_configs or CompilerConfigs()
    tree = grammar.parse(progin)
    bv = BasicVisitor()
    basic_prog: BasicProg = bv.visit(tree)

    if add_standard_prefix:
        prefix_lines = [
            BasicLine(None, Basic09CodeStatement("base 0")),
            BasicLine(
                None,
                Basic09CodeStatement(
                    "type display_t = tpth, vpth, wpth, hpth, pal(16), blnk, "
                    "undrln, bck, fore, brdr, hbck, hfore, hscl, hpy, hagl, hdsc: byte; hpx: integer"
                ),
            ),
            BasicLine(None, Basic09CodeStatement("dim display: display_t")),
            BasicLine(None, Basic09CodeStatement("dim erno: real")),
            BasicLine(None, Basic09CodeStatement("erno := -1")),
            BasicLine(
                None,
                BasicRunCall(
                    "RUN _ecb_start",
                    BasicExpressionList(
                        [
                            BasicVar("display"),
                            BasicLiteral(1 if default_width32 else 0),
                        ]
                    ),
                ),
            ),
            BasicLine(
                None, Basic09CodeStatement("TYPE play_t=oct,octo,lnt,tne,vol,dot:BYTE")
            ),
            BasicLine(None, Basic09CodeStatement("DIM play: play_t")),
            BasicLine(None, Basic09CodeStatement("play.oct := 3")),
            BasicLine(None, Basic09CodeStatement("play.octo := 0")),
            BasicLine(None, Basic09CodeStatement("play.lnt := 4")),
            BasicLine(None, Basic09CodeStatement("play.tne := 2")),
            BasicLine(None, Basic09CodeStatement("play.vol := 15")),
            BasicLine(None, Basic09CodeStatement("play.dot := 0")),
        ]
        basic_prog.insert_lines_at_beginning(prefix_lines)

    if skip_procedure_headers := skip_procedure_headers or not output_dependencies:
        procname = ""
    else:
        procname = procname if PROCNAME_REGEX.match(procname) else "program"
    basic_prog.set_procname(procname)

    # Patch INPUT statements
    basic_prog.visit(BasicInputStatementPatcherVisitor())

    # Patch up READ statements to handle empty DATA elements
    empty_data_elements_visitor = BasicEmptyDataElementVisitor()
    basic_prog.visit(empty_data_elements_visitor)
    if empty_data_elements_visitor.has_empty_data_elements:
        basic_prog.visit(BasicReadStatementPatcherVisitor())

    # Update joystk stuff
    joystk_initializer = JoystickVisitor()
    basic_prog.visit(joystk_initializer)
    basic_prog.extend_prefix_lines(joystk_initializer.joystk_var_statements)

    # Patch PRINT statements
    basic_prog.visit(BasicPrintStatementPatcherVisitor())

    # transform functions to proc calls
    basic_prog.visit(BasicFunctionalExpressionPatcherVisitor())

    set_string_storage_vistor: SetDimStringStorageVisitor = SetDimStringStorageVisitor(
        default_str_storage=default_str_storage,
        string_configs=compiler_configs.string_configs,
    )
    basic_prog.visit(set_string_storage_vistor)

    # Declare implicitly declared arrays
    dimmed_array_visitor = GetDimmedArraysVisitor()
    basic_prog.visit(dimmed_array_visitor)
    declare_array_visitor = DeclareImplicitArraysVisitor(
        dimmed_var_names=dimmed_array_visitor.dimmed_var_names,
        initialize_vars=initialize_vars,
    )
    basic_prog.visit(declare_array_visitor)
    basic_prog.insert_lines_at_beginning(declare_array_visitor.dim_statements)

    # allocate sufficient string storage
    str_var_allocator: StrVarAllocatorVisitor = StrVarAllocatorVisitor(
        default_str_storage=default_str_storage,
        dimmed_var_names=set_string_storage_vistor.dimmed_var_names,
    )
    basic_prog.visit(str_var_allocator)
    basic_prog.extend_prefix_lines(str_var_allocator.allocation_lines)

    # Signature-aware call-site coercion.
    #
    # Many ``ecb_*`` procedures take ``INTEGER`` parameters
    # (sound, locate, hcircle, ...). Real expressions emitted by
    # the transpiler must be coerced with ``fix(...)``, and — when
    # the real-to-integer optimization is enabled — integer
    # variables passed as arguments to ``REAL`` parameters must be
    # coerced with ``float(...)``. ``CoerceIntegerArgsVisitor``
    # handles both directions and runs unconditionally so that
    # even non-``-O`` builds produce well-typed call sites.
    signature_bank = ProcedureBank()
    signature_bank.add_from_resource("ecb.b09")

    integer_var_names: set[str] = set()
    if optimize:
        int_visitor = IntegerVarVisitor(signatures=signature_bank.signatures)
        basic_prog.visit(int_visitor)
        excluded: set[str] = _normalized_no_optimize_vars(no_optimize_vars or set())
        integer_var_names = int_visitor.integer_vars - excluded

    if integer_var_names:
        set_integer_dim = SetIntegerDimVisitor(integer_var_names)
        basic_prog.visit(set_integer_dim)

        # Any integer scalar not already covered by a DIM needs a
        # fresh ``DIM <names>: INTEGER`` line in the prefix.
        scalar_integer_names = sorted(
            name
            for name in integer_var_names
            if not name.startswith("arr_")
            and name not in set_integer_dim.dimmed_integer_var_names
        )
        if scalar_integer_names:
            basic_prog.extend_prefix_lines(
                [
                    BasicLine(
                        None,
                        Basic09CodeStatement(
                            f"DIM {', '.join(scalar_integer_names)}: INTEGER"
                        ),
                    )
                ]
            )

    basic_prog.visit(
        CoerceIntegerArgsVisitor(
            integer_var_names=integer_var_names,
            signatures=signature_bank.signatures,
        )
    )
    if integer_var_names:
        basic_prog.visit(RewriteIntegerLiteralsVisitor(integer_var_names))

    # initialize variables
    if initialize_vars:
        var_initializer = VarInitializerVisitor(integer_var_names=integer_var_names)
        basic_prog.visit(var_initializer)
        basic_prog.extend_prefix_lines(var_initializer.assignment_lines)
    set_init_visitor = SetInitializeVisitor(initialize_vars)
    basic_prog.visit(set_init_visitor)

    # remove unused line numbers
    line_ref_visitor = LineReferenceVisitor()
    basic_prog.visit(line_ref_visitor)
    line_num_filter = (
        LineNumberFilterVisitor(line_ref_visitor.references)
        if filter_unused_linenum
        else LineZeroFilterVisitor(line_ref_visitor.references)
    )
    basic_prog.visit(line_num_filter)

    # make sure line numbers exist and are not too big
    line_checker: LineNumberCheckerVisitor = LineNumberCheckerVisitor(
        line_ref_visitor.references
    )
    basic_prog.visit(line_checker)
    if len(line_checker.undefined_lines) > 0:
        raise ParseError(
            f"The following lines are undefined: {', '.join(str(linenum) for linenum in line_checker.undefined_lines)}"
        )

    # make sure there are no more than 1 ON ERR statement
    on_err_collector: StatementCollectorVisitor = StatementCollectorVisitor(
        BasicOnErrGoStatement
    )
    basic_prog.visit(on_err_collector)
    if len(on_err_collector.statements) > 1:
        raise ParseError("At most 1 ON ERR GOTO statement is allowed.")
    err_statement = (
        on_err_collector.statements[0] if on_err_collector.statements else None
    )
    err_line: int | None = (
        err_statement.linenum
        if isinstance(err_statement, BasicOnErrGoStatement)
        else None
    )

    # make sure there are no more than 1 ON BRK statement
    on_brk_collector: StatementCollectorVisitor = StatementCollectorVisitor(
        BasicOnBrkGoStatement
    )
    basic_prog.visit(on_brk_collector)
    if len(on_brk_collector.statements) > 1:
        raise ParseError("At most 1 ON BRK GOTO statement is allowed.")
    brk_statement = (
        on_brk_collector.statements[0] if on_brk_collector.statements else None
    )
    brk_line: int | None = (
        brk_statement.linenum
        if isinstance(brk_statement, BasicOnBrkGoStatement)
        else None
    )

    # try to patch up empty next statements
    basic_prog.visit(BasicNextPatcherVisitor())
    suffix_lines: List[BasicLine] = error_handler.generate(
        brk_line=brk_line,
        err_line=err_line,
    )
    if add_suffix:
        basic_prog.append_lines(suffix_lines)

    # detect hbuff
    if add_standard_prefix:
        hbuff_visitor = BasicHbuffPresenceVisitor()
        basic_prog.visit(hbuff_visitor)
        if hbuff_visitor.has_hbuff:
            basic_prog.insert_lines_at_beginning(
                [
                    BasicLine(None, Basic09CodeStatement("dim pid: integer")),
                    BasicLine(
                        None,
                        BasicRunCall(
                            "RUN _ecb_init_hbuff",
                            BasicExpressionList([BasicVar("pid")]),
                        ),
                    ),
                ]
            )

    # output the program
    program = basic_prog.basic09_text(0)
    if output_dependencies and procname:
        procedure_bank = ProcedureBank(
            default_str_storage=default_str_storage,
        )
        procedure_bank.add_from_resource("ecb.b09")
        procedure_bank.add_from_str(program)
        program = procedure_bank.get_procedure_and_dependencies(procname)

    return program + "\n"


def collect_integer_candidates(progin: str) -> List[str]:
    """Return the sorted list of scalar and array names in ``progin``
    that could legally be stored as Basic09 ``INTEGER`` values.

    Call sites of the procedures defined in ``ecb.b09`` are analyzed
    against their parsed signatures so that variables passed as
    ``REAL`` output parameters are excluded from the candidate set.

    Array names are emitted with a trailing ``()`` (e.g., ``X()``) to
    distinguish them from a scalar of the same name.
    """
    tree = grammar.parse(progin)
    basic_prog: BasicProg = BasicVisitor().visit(tree)
    basic_prog.visit(BasicFunctionalExpressionPatcherVisitor())

    procedure_bank = ProcedureBank()
    procedure_bank.add_from_resource("ecb.b09")
    visitor = IntegerVarVisitor(signatures=procedure_bank.signatures)
    basic_prog.visit(visitor)

    formatted: List[str] = []
    for name in visitor.integer_vars:
        if name.startswith("arr_"):
            formatted.append(f"{name[4:]}()")
        else:
            formatted.append(name)
    return sorted(formatted)


def convert_file(
    input_program_file: IO[str],
    output_program_file: IO[str],
    *,
    add_standard_prefix: bool = True,
    config_file: str | None = None,
    default_width32: bool = True,
    default_str_storage: int = b09.DEFAULT_STR_STORAGE,
    filter_unused_linenum: bool = False,
    initialize_vars: bool = False,
    list_integer_candidates: bool = False,
    no_optimize_vars: "set[str] | None" = None,
    optimize: bool = False,
    output_dependencies: bool = False,
    procname: str = "",
) -> None:
    progin = input_program_file.read()

    if list_integer_candidates:
        candidates = collect_integer_candidates(progin)
        output_program_file.write("\n".join(candidates))
        if candidates:
            output_program_file.write("\n")
        return

    compiler_configs = (
        CompilerConfigs.load(Path(config_file)) if config_file else CompilerConfigs()
    )
    progout = convert(
        progin,
        add_standard_prefix=add_standard_prefix,
        compiler_configs=compiler_configs,
        default_str_storage=default_str_storage,
        default_width32=default_width32,
        filter_unused_linenum=filter_unused_linenum,
        initialize_vars=initialize_vars,
        no_optimize_vars=no_optimize_vars,
        optimize=optimize,
        output_dependencies=output_dependencies,
        procname=procname,
    )
    progout = progout.replace("\n", "\r")
    output_program_file.write(progout)
