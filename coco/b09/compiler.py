from typing import List

from coco import b09
from coco.b09 import error_handler
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
from coco.b09.grammar import grammar, PROCNAME_REGEX
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
    DeclareImplicitArraysVisitor,
    GetDimmedArraysVisitor,
    JoystickVisitor,
    LineNumberFilterVisitor,
    LineNumberCheckerVisitor,
    LineReferenceVisitor,
    LineZeroFilterVisitor,
    SetDimStringStorageVisitor,
    StatementCollectorVisitor,
    StrVarAllocatorVisitor,
    VarInitializerVisitor,
)


class ParseError(Exception):
    pass


def convert(
    progin: str,
    *,
    add_standard_prefix: bool = True,
    add_suffix: bool = True,
    default_str_storage: int = b09.DEFAULT_STR_STORAGE,
    default_width32: bool = True,
    filter_unused_linenum: bool = False,
    initialize_vars: bool = False,
    output_dependencies: bool = False,
    procname: str = "",
    skip_procedure_headers: bool = False,
) -> str:
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
        default_str_storage=default_str_storage
    )
    basic_prog.visit(set_string_storage_vistor)

    # Declare implicitly declared arrays
    dimmed_array_visitor = GetDimmedArraysVisitor()
    basic_prog.visit(dimmed_array_visitor)
    declare_array_visitor = DeclareImplicitArraysVisitor(
        dimmed_var_names=dimmed_array_visitor.dimmed_var_names,
    )
    basic_prog.visit(declare_array_visitor)
    basic_prog.extend_prefix_lines(declare_array_visitor.dim_statements)

    # allocate sufficient string storage
    str_var_allocator: StrVarAllocatorVisitor = StrVarAllocatorVisitor(
        default_str_storage=default_str_storage,
        dimmed_var_names=set_string_storage_vistor.dimmed_var_names,
    )
    basic_prog.visit(str_var_allocator)
    basic_prog.extend_prefix_lines(str_var_allocator.allocation_lines)

    # initialize variables
    if initialize_vars:
        var_initializer = VarInitializerVisitor()
        basic_prog.visit(var_initializer)
        basic_prog.extend_prefix_lines(var_initializer.assignment_lines)

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
    err_line: BasicOnErrGoStatement = (
        on_err_collector.statements[0].linenum if on_err_collector.statements else None
    )

    # make sure there are no more than 1 ON BRK statement
    on_brk_collector: StatementCollectorVisitor = StatementCollectorVisitor(
        BasicOnBrkGoStatement
    )
    basic_prog.visit(on_brk_collector)
    if len(on_brk_collector.statements) > 1:
        raise ParseError("At most 1 ON BRK GOTO statement is allowed.")
    brk_line: BasicOnBrkGoStatement = (
        on_brk_collector.statements[0].linenum if on_brk_collector.statements else None
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


def convert_file(
    input_program_file: str,
    output_program_file: str,
    *,
    add_standard_prefix: bool = True,
    default_width32: bool = True,
    default_str_storage: int = b09.DEFAULT_STR_STORAGE,
    filter_unused_linenum: bool = False,
    initialize_vars: bool = False,
    output_dependencies: bool = False,
    procname: str = "",
) -> None:
    progin = input_program_file.read()
    progout = convert(
        progin,
        add_standard_prefix=add_standard_prefix,
        default_str_storage=default_str_storage,
        default_width32=default_width32,
        filter_unused_linenum=filter_unused_linenum,
        initialize_vars=initialize_vars,
        output_dependencies=output_dependencies,
        procname=procname,
    )
    progout = progout.replace("\n", "\r")
    output_program_file.write(progout)
