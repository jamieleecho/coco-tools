from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from coco import b09
from coco.b09.configs import StringConfigs
from coco.b09.elements import (
    AbstractBasicConstruct,
    AbstractBasicExpression,
    AbstractBasicStatement,
    Basic09CodeStatement,
    BasicArrayRef,
    BasicAssignment,
    BasicBinaryExp,
    BasicCls,
    BasicDataStatement,
    BasicDimStatement,
    BasicExpressionList,
    BasicForStatement,
    BasicFunctionalExpression,
    BasicFunctionCall,
    BasicGoStatements,
    BasicHbuffStatement,
    BasicInputStatement,
    BasicJoystkExpression,
    BasicLine,
    BasicLiteral,
    BasicNextStatement,
    BasicOnGoStatement,
    BasicOpExp,
    BasicParenExp,
    BasicPrintArgs,
    BasicPrintStatement,
    BasicReadStatement,
    BasicRunCall,
    BasicSound,
    BasicStatements,
    BasicVar,
    BasicWidthStatement,
    HexLiteral,
)

if TYPE_CHECKING:
    from coco.b09.procbank import ProcedureSignature
    from coco.b09.prog import BasicProg


# Extracts the procedure name from a ``run <name>`` invocation
# string stored on ``BasicRunCall._run_invocation`` or
# ``BasicFunctionalExpression._func``.
_RUN_INVOCATION_REGEX = re.compile(r"(?i)^\s*run\s+(\w+)")


class BasicConstructVisitor:
    def visit_array_ref(self, array_ref: BasicArrayRef) -> None:
        """
        Invoked when an array reference is encountered.
        """
        pass

    def visit_data_statement(self, statement: BasicDataStatement) -> None:
        """
        Invoked when a DATA statement is encountered.
        """
        pass

    def visit_exp(self, exp: AbstractBasicExpression) -> None:
        """
        Invoked when an expression is encountered.
        """
        pass

    def visit_for_statement(self, for_statement: BasicForStatement) -> None:
        """
        Invoked when a FOR statement is encountered.
        """
        pass

    def visit_go_statement(self, go_statement: BasicGoStatements) -> None:
        """
        Invoked when a [ON] GOTO/GOSUB statement is encountered.
        """
        pass

    def visit_input_statement(
        self, statement: BasicInputStatement
    ) -> AbstractBasicStatement:
        """
        Args:
            statement (BasicInputStatement): input statement to transform.

        Returns:
            BasicStatement: BasicStatement to replace statement.
        """
        return statement

    def visit_joystk(self, joystk_exp: BasicJoystkExpression) -> None:
        """
        Invoked when a JOYSTK function is encountered.
        """
        pass

    def visit_line(self, line: BasicLine) -> None:
        """
        Invoked when a new line is encountered.
        """
        pass

    def visit_next_statement(self, next_statement: BasicNextStatement) -> None:
        """
        Invoked when a NEXT statement is encountered.
        """
        pass

    def visit_print_statement(
        self, statement: BasicPrintStatement
    ) -> AbstractBasicStatement:
        """
        Args:
            statement (BasicPrintStatement): input statement to transform.

        Returns:
            BasicStatement: BasicStatement to replace statement.
        """
        return statement

    def visit_program(self, prog: "BasicProg") -> None:
        """
        Invoked when a program is encountered.
        """
        pass

    def visit_read_statement(
        self, statement: BasicReadStatement
    ) -> AbstractBasicStatement:
        """
        Args:
            statement (BasicReadStatement): input statement to transform.

        Returns:
            BasicStatement: BasicStatement to replace statement.
        """
        return statement

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        """
        Invoked when a statement is encountered.
        """
        pass

    def visit_var(self, var: BasicVar) -> None:
        """
        Invoked when a variable is encountered.
        """
        pass


class ForNextVisitor(BasicConstructVisitor):
    def __init__(self):
        self._count = 0

    @property
    def count(self):
        return self._count

    def visit_for_statement(self, for_statement: BasicForStatement) -> None:
        self._count = self._count + 1

    def visit_next_statement(self, next_statement: BasicNextStatement) -> None:
        self._count = self._count - len(next_statement.var_list.exp_list)


class LineReferenceVisitor(BasicConstructVisitor):
    def __init__(self):
        self._references: set = set()

    @property
    def references(self) -> set:
        return self._references

    def visit_go_statement(self, go_statement: BasicGoStatements):
        if isinstance(go_statement, BasicOnGoStatement):
            for linenum in go_statement.linenums:
                self.references.add(linenum)
        else:
            self.references.add(go_statement.linenum)


class LineNumberFilterVisitor(BasicConstructVisitor):
    def __init__(self, references: set):
        self._references: set = references

    def visit_line(self, line: BasicLine):
        line.set_is_referenced(line.num in self._references)


class LineNumberTooLargeException(Exception):
    pass


class LineNumberCheckerVisitor(BasicConstructVisitor):
    def __init__(self, references: set):
        self._references = references.copy()

    def visit_line(self, line: BasicLine):
        if line.num is not None and line.num > 32699:
            raise LineNumberTooLargeException(f"{line.num} exceeds 32699.")
        self._references.discard(line.num)

    @property
    def undefined_lines(self) -> set:
        return self._references


class LineZeroFilterVisitor(BasicConstructVisitor):
    def __init__(self, references):
        self._references = references

    def visit_line(self, line: BasicLine):
        if line.num == 0:
            line.set_is_referenced(line.num in self._references)


class StatementCollectorVisitor(BasicConstructVisitor):
    _statement_type: type
    _statements: List[AbstractBasicConstruct]

    @property
    def statements(self) -> List[AbstractBasicConstruct]:
        return self._statements

    def __init__(self, statement_type: type):
        self._statements = []
        self._statement_type = statement_type

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if type(statement) is self._statement_type:
            self._statements.append(statement)
        super().visit_statement(statement)


class VarInitializerVisitor(BasicConstructVisitor):
    _vars: Set[str]
    _dimmed_var_names: Set[str]
    _integer_var_names: Set[str]

    def __init__(self, *, integer_var_names: Optional[Set[str]] = None):
        self._vars = set()
        self._dimmed_var_names = set()
        self._integer_var_names = set(integer_var_names) if integer_var_names else set()

    def _init_literal(self, var: str) -> BasicLiteral:
        if var.endswith("$"):
            return BasicLiteral("", is_str_expr=True)
        if var in self._integer_var_names:
            return BasicLiteral(0)
        return BasicLiteral(0.0)

    @property
    def assignment_lines(self) -> List[BasicLine]:
        vars_to_assign = self._vars - self._dimmed_var_names
        return (
            [
                BasicLine(
                    None,
                    BasicStatements(
                        [
                            BasicAssignment(
                                BasicVar(var, is_str_expr=var.endswith("$")),
                                self._init_literal(var),
                            )
                            for var in sorted(vars_to_assign)
                            if ((var.endswith("$") and len(var) <= 3) or len(var) <= 2)
                        ]
                    ),
                )
            ]
            if vars_to_assign
            else []
        )

    def visit_var(self, var) -> None:
        self._vars.add(var.name())

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicDimStatement):
            self._dimmed_var_names.update(
                [
                    var.var.name() if isinstance(var, BasicArrayRef) else var.name()
                    for var in statement.dim_vars
                ]
            )


class StrVarAllocatorVisitor(BasicConstructVisitor):
    _vars: Set[str]
    _default_str_storage: int
    _dimmed_var_names: Set[str]

    def __init__(
        self,
        *,
        default_str_storage: int,
        dimmed_var_names: Set[str],
    ):
        self._vars = set()
        self._default_str_storage = default_str_storage
        self._dimmed_var_names = dimmed_var_names

    @property
    def allocation_lines(self) -> List[BasicLine]:
        return (
            [
                BasicLine(
                    None,
                    Basic09CodeStatement(
                        f"DIM {var}:STRING[{self._default_str_storage}]"
                    ),
                )
                for var in sorted(self._vars)
            ]
            if self._default_str_storage != b09.DEFAULT_STR_STORAGE
            else []
        )

    def visit_var(self, var) -> None:
        if var.name().endswith("$") and var.name() not in self._dimmed_var_names:
            self._vars.add(var.name())


class SetDimStringStorageVisitor(BasicConstructVisitor):
    _default_str_storage: int
    _dimmed_var_names: Set[str]
    _string_configs: StringConfigs
    _strname_to_size: Dict[str, int]

    def __init__(self, *, default_str_storage: int, string_configs: StringConfigs):
        self._default_str_storage = default_str_storage
        self._dimmed_var_names = set()
        self.string_configs = string_configs
        self._strname_to_size = {
            var if var.endswith("$") else f"arr_{var[:-3]}$": size
            for var, size in string_configs.strname_to_size.items()
        }

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicDimStatement):
            statement.default_str_storage = self._default_str_storage
            statement.strname_to_size = self._strname_to_size
            self._dimmed_var_names.update(
                [
                    var.name() if isinstance(var, BasicVar) else var.var.name()
                    for var in statement.dim_vars
                ]
            )

    @property
    def dimmed_var_names(self) -> Set[str]:
        return self._dimmed_var_names


class GetDimmedArraysVisitor(BasicConstructVisitor):
    _dimmed_var_names: Set[str]

    def __init__(self):
        self._dimmed_var_names = set()

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicDimStatement):
            self._dimmed_var_names.update(
                [
                    var.var.name()
                    for var in statement.dim_vars
                    if isinstance(var, BasicArrayRef)
                ]
            )

    @property
    def dimmed_var_names(self) -> Set[str]:
        return self._dimmed_var_names


class DeclareImplicitArraysVisitor(BasicConstructVisitor):
    _dimmed_var_names: Set[str]
    _initialize_vars: bool
    _referenced_var_names: Set[str]

    def __init__(self, *, dimmed_var_names: Set[str], initialize_vars: bool = False):
        self._dimmed_var_names = dimmed_var_names
        self._initialize_vars = initialize_vars
        self._referenced_var_names = set()

    def visit_array_ref(self, array_ref: BasicArrayRef) -> None:
        self._referenced_var_names.add(array_ref.var.name())

    @property
    def implicitly_declared_arrays(self) -> Set[str]:
        return self._referenced_var_names - self._dimmed_var_names

    @property
    def dim_statements(self) -> List[BasicDimStatement]:
        return [
            BasicDimStatement(
                [
                    BasicArrayRef(
                        BasicVar(var[4:], is_str_expr=var.endswith("$")),
                        BasicExpressionList([BasicLiteral(10)]),
                        is_str_expr=var.endswith("$"),
                    ),
                ],
                initialize_vars=self._initialize_vars,
            )
            for var in self.implicitly_declared_arrays
        ]


class JoystickVisitor(BasicConstructVisitor):
    def __init__(self):
        self._uses_joystk = False

    @property
    def joystk_var_statements(self):
        return (
            [
                Basic09CodeStatement("dim joy0x, joy0y, joy1x, joy0y: integer"),
            ]
            if self._uses_joystk
            else []
        )

    def visit_joystk(self, joystk_exp):
        self._uses_joystk = True


class BasicEmptyDataElementVisitor(BasicConstructVisitor):
    def __init__(self):
        self._has_empty_data_elements = False

    @property
    def has_empty_data_elements(self):
        return self._has_empty_data_elements

    def visit_data_statement(self, statement: BasicDataStatement) -> None:
        for exp in statement.exp_list.exp_list:
            self._has_empty_data_elements = (
                self._has_empty_data_elements or exp.literal == ""
            )


class BasicReadStatementPatcherVisitor(BasicConstructVisitor):
    def visit_data_statement(self, statement: BasicDataStatement) -> None:
        exp: AbstractBasicExpression
        for exp in statement.exp_list.exp_list:
            if not isinstance(exp.literal, str):
                exp.literal = str(exp.literal)

    def visit_read_statement(
        self, statement: BasicReadStatement
    ) -> AbstractBasicStatement:
        """
        Transform the READ statement so that READ statements that read into
        REAL vars properly handle empty strings. This means:
        1. Changing the statement into a BasicStatements
        2. Changing the READ statement to read into temp strings
        3. Calling functions to convert the string temps into the REAL
        """

        # Map REAL vars to temp string vars
        rhs_to_temp = {
            rhs: statement.get_new_temp(True)
            for rhs in statement.rhs_list
            if not rhs.is_str_expr
        }

        # Transform the READ REAL vars to the temp string vars
        for idx, rhs in enumerate(statement.rhs_list):
            statement.rhs_list[idx] = rhs_to_temp.get(rhs, rhs)

        # Create statements for reading into the REAL vars
        filter_statements = [
            BasicRunCall("RUN ecb_read_filter", BasicExpressionList((inval, outval)))
            for outval, inval in rhs_to_temp.items()
        ]

        return BasicStatements([statement] + filter_statements, multi_line=False)


class BasicInputStatementPatcherVisitor(BasicConstructVisitor):
    def visit_input_statement(
        self, statement: BasicInputStatement
    ) -> AbstractBasicStatement:
        """
        Transform the INPUT statement so that the cursor and full duplex are
        enabled before the statement and disabled after the statement.
        """

        # Create statements for reading into the REAL vars
        filter_statements = [
            BasicRunCall("RUN _ecb_input_prefix", BasicExpressionList([])),
            statement,
            BasicRunCall("RUN _ecb_input_suffix", BasicExpressionList([])),
        ]

        return BasicStatements(filter_statements, multi_line=False)


class BasicPrintStatementPatcherVisitor(BasicConstructVisitor):
    def visit_print_statement(
        self, statement: BasicPrintStatement
    ) -> AbstractBasicStatement:
        """
        Transform the PRINT statement so that non string expressions are
        converted to strings via STR.
        """

        # Create statements for reading into the REAL vars
        print_args = [
            arg
            if not isinstance(arg, AbstractBasicExpression) or arg.is_str_expr
            else BasicFunctionalExpression(
                "run ecb_str", BasicExpressionList([arg]), is_str_expr=True
            )
            for arg in statement.print_args.args
        ]

        return BasicPrintStatement(BasicPrintArgs(print_args))


class BasicNextPatcherVisitor(BasicConstructVisitor):
    def __init__(self):
        self.for_stack = []

    def visit_for_statement(self, for_statement: BasicForStatement):
        self.for_stack.append(for_statement.var)

    def visit_next_statement(self, next_statement):
        if self.for_stack and len(next_statement.var_list.exp_list) == 0:
            next_statement.var_list.exp_list.append(self.for_stack.pop())


class BasicFunctionalExpressionPatcherVisitor(BasicConstructVisitor):
    def __init__(self):
        self._statement = None

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        self._statement = statement
        if isinstance(statement, BasicAssignment) and isinstance(
            statement.exp, BasicFunctionalExpression
        ):
            statement.exp.set_var(statement.var)

    def visit_exp(self, exp) -> None:
        if not isinstance(exp, BasicFunctionalExpression) or exp.var:
            return
        if isinstance(self._statement, AbstractBasicStatement):
            self._statement.transform_function_to_call(exp)


class BasicHbuffPresenceVisitor(BasicConstructVisitor):
    _hasHbuff: bool

    def __init__(self):
        self._hasHbuff = False

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicHbuffStatement):
            self._hasHbuff = True

    @property
    def has_hbuff(self) -> bool:
        return self._hasHbuff


class SetInitializeVisitor(BasicConstructVisitor):
    def __init__(self, initialize_vars: bool):
        self._initialize_vars = initialize_vars

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicDimStatement):
            statement.initialize_vars = self._initialize_vars


class SetIntegerDimVisitor(BasicConstructVisitor):
    """Tags ``BasicDimStatement`` nodes with the set of integer
    variable names so their :meth:`basic09_text` emits a separate
    ``DIM ... : INTEGER`` line for those vars.

    Also records which integer variables were already covered by a
    ``DIM`` (as opposed to needing a fresh prefix declaration).
    """

    _integer_var_names: Set[str]
    _dimmed_integer_var_names: Set[str]

    def __init__(self, integer_var_names: Set[str]):
        self._integer_var_names = integer_var_names
        self._dimmed_integer_var_names = set()

    @property
    def dimmed_integer_var_names(self) -> Set[str]:
        return self._dimmed_integer_var_names

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if not isinstance(statement, BasicDimStatement):
            return
        statement.integer_var_names = self._integer_var_names
        for var in statement.dim_vars:
            name = var.name() if isinstance(var, BasicVar) else var.var.name()
            if name in self._integer_var_names:
                self._dimmed_integer_var_names.add(name)


class RewriteIntegerLiteralsVisitor(BasicConstructVisitor):
    """Rewrites integer-valued ``BasicLiteral`` floats (e.g.,
    ``1.0``, ``-5.0``) into genuine integer literals whenever they
    appear on the RHS of an assignment to an integer-optimized
    variable, on the bounds/step of an integer ``FOR`` loop, or as
    subscripts of an integer array reference. Basic09 is strict
    about mixing REAL and INTEGER at assignment time, so this
    rewrite keeps the generated code type-clean.
    """

    _integer_var_names: Set[str]

    def __init__(self, integer_var_names: Set[str]):
        self._integer_var_names = integer_var_names

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicAssignment):
            target = statement.var
            target_is_integer = (
                isinstance(target, BasicVar)
                and target.name() in self._integer_var_names
            ) or (
                isinstance(target, BasicArrayRef)
                and target.var.name() in self._integer_var_names
            )
            if target_is_integer:
                new_exp = self._rewrite(statement.exp)
                if new_exp is not statement.exp:
                    statement._exp = new_exp

    def visit_for_statement(self, for_statement: BasicForStatement) -> None:
        var = for_statement.var
        if not isinstance(var, BasicVar):
            return
        if var.name() not in self._integer_var_names:
            return
        for_statement._start_exp = self._rewrite(for_statement._start_exp)
        for_statement._end_exp = self._rewrite(for_statement._end_exp)
        if for_statement._step_exp is not None:
            for_statement._step_exp = self._rewrite(for_statement._step_exp)

    def visit_array_ref(self, array_ref: BasicArrayRef) -> None:
        if array_ref.var.name() not in self._integer_var_names:
            return
        array_ref._indices._exp_list = [
            self._rewrite(idx) for idx in array_ref.indices.exp_list
        ]

    def _rewrite(self, exp: AbstractBasicExpression) -> AbstractBasicExpression:
        """Return ``exp`` with any integer-valued float literals
        recursively converted to int literals. Other expression
        shapes are passed through unchanged.
        """
        if isinstance(exp, BasicLiteral):
            if (
                not exp.is_str_expr
                and isinstance(exp.literal, float)
                and exp.literal.is_integer()
            ):
                return BasicLiteral(int(exp.literal))
            return exp
        if isinstance(exp, BasicParenExp):
            exp._exp = self._rewrite(exp._exp)
            return exp
        if isinstance(exp, BasicOpExp):
            exp._exp = self._rewrite(exp._exp)
            return exp
        if isinstance(exp, BasicBinaryExp):
            exp._exp1 = self._rewrite(exp._exp1)
            exp._exp2 = self._rewrite(exp._exp2)
            return exp
        return exp


class CoerceIntegerArgsVisitor(BasicConstructVisitor):
    """Wraps integer-optimized variables with ``float(...)`` when
    they appear as arguments to ``REAL`` parameters of a known
    procedure.

    BASIC09 is strict about parameter types at call sites: an
    ``INTEGER`` variable cannot be passed where a ``REAL`` is
    expected. Input parameters can be safely coerced with
    ``float(...)``; this visitor walks ``BasicRunCall`` statements
    and assignment-like ``BasicFunctionalExpression`` nodes and
    rewrites their arguments accordingly.

    Variables passed as output parameters are never wrapped —
    the :class:`IntegerVarVisitor` has already excluded them from
    the integer set when the output parameter is ``REAL``, so by
    the time this visitor runs there are no such conflicts.
    """

    _integer_var_names: Set[str]
    _signatures: Dict[str, "ProcedureSignature"]

    def __init__(
        self,
        *,
        integer_var_names: Set[str],
        signatures: Dict[str, "ProcedureSignature"],
    ):
        self._integer_var_names = integer_var_names
        self._signatures = signatures

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicRunCall):
            self._rewrite_args(statement._run_invocation, statement._arguments.exp_list)
            return
        if isinstance(statement, BasicSound):
            # BasicSound hand-emits ``RUN ecb_sound(f, d, 31.0, ...)``
            # without using a ``BasicRunCall``. f and d are the two
            # REAL input parameters; coerce them directly.
            statement._exp1 = self._wrap_if_integer(statement._exp1)
            statement._exp2 = self._wrap_if_integer(statement._exp2)
            return
        if isinstance(statement, BasicCls):
            # BasicCls hand-emits ``RUN ecb_cls(color, display)``
            # — color is a REAL input.
            if statement._exp is not None:
                statement._exp = self._wrap_if_integer(statement._exp)
            return
        if isinstance(statement, BasicWidthStatement):
            # BasicWidthStatement hand-emits ``run _ecb_width(w,
            # display)``. _ecb_width's width parameter is REAL.
            statement._expr = self._wrap_if_integer(statement._expr)
            return
        if isinstance(statement, BasicAssignment) and isinstance(
            statement.exp, BasicFunctionalExpression
        ):
            exp = statement.exp
            # Functional expressions that have been patched carry
            # their full ``run <proc>(...args..., target)`` form in
            # ``exp._statement``. We rewrite the arguments in place
            # on ``exp._args.exp_list`` because
            # :meth:`BasicFunctionalExpression.set_var` passes that
            # same list through to the synthesized function call,
            # so mutating it keeps the two representations in
            # sync.
            self._rewrite_args(exp._func, exp._args.exp_list)

    def _rewrite_args(
        self, invocation: str, args: "list[AbstractBasicExpression]"
    ) -> None:
        match = _RUN_INVOCATION_REGEX.match(invocation or "")
        if not match:
            return
        signature = self._signatures.get(match.group(1))
        if signature is None:
            return
        for idx in range(min(len(args), len(signature.params))):
            param = signature.params[idx]
            if param.is_output or not param.is_real:
                continue
            args[idx] = self._wrap_if_integer(args[idx])

    def _wrap_if_integer(self, arg: AbstractBasicExpression) -> AbstractBasicExpression:
        if self._is_integer_arg(arg):
            return BasicFunctionCall("float", BasicExpressionList([arg]))
        return arg

    def _is_integer_arg(self, arg: AbstractBasicExpression) -> bool:
        if isinstance(arg, BasicVar) and not arg.is_str_expr:
            return arg.name() in self._integer_var_names
        if isinstance(arg, BasicArrayRef) and not arg.is_str_expr:
            return arg.var.name() in self._integer_var_names
        return False


class IntegerVarVisitor(BasicConstructVisitor):
    """Collects numeric variables and arrays that can be represented as
    Basic09 ``INTEGER`` storage.

    A variable is an integer candidate only if every value ever assigned
    to it is statically provable to be an integer in the 16-bit signed
    range ``[-32768, 32767]``. A variable is disqualified if any of the
    following appears on the RHS of one of its assignments (directly or
    transitively through another non-integer variable):

    - a transcendental or otherwise non-integer function
      (``SIN``, ``COS``, ``TAN``, ``ATN``, ``LOG``, ``EXP``, ``SQR``,
      ``SQRT``, ``RND``, ``VAL``, ...),
    - the division ``/`` or power ``^`` operator,
    - a fractional literal, or a numeric literal outside
      ``[-32768, 32767]``,
    - a value read from ``INPUT`` or ``READ`` (since the data can be
      fractional or out of range),
    - being passed as a ``REAL`` output parameter to a known BASIC09
      procedure — because output parameters write back through the
      caller's variable and therefore pin the variable's declared
      type. (An ``INTEGER`` output parameter imposes no constraint:
      an integer write is compatible with an integer variable.)

    The walk records every assignment site (regular assignments,
    ``FOR`` loop bounds/step, and procedure output arguments) and
    defers classification to :attr:`integer_vars`, which runs a
    fixpoint to propagate non-integer-ness through
    variable-to-variable assignments.

    Array variable names follow the convention used elsewhere in this
    module: the array ``X`` is tracked as ``arr_X`` (matching
    :attr:`BasicArrayRef.var`), which keeps it distinct from a scalar
    ``X``.

    Signatures for known procedures (typically loaded from
    ``ecb.b09``) can be supplied via the ``signatures`` constructor
    argument; call sites are then analyzed against them to find
    variables passed into output parameters.
    """

    # Functions that always yield an integer result in Basic09.
    _INTEGER_FUNCS: frozenset = frozenset(
        {
            "INT",
            "FIX",
            "PEEK",
            "LEN",
            "ASC",
            "SGN",
            "RUN ecb_int",
            "RUN ecb_button",
        }
    )

    # Functions whose result is never guaranteed to be an integer.
    # These include transcendentals, RND (may return a float), and
    # VAL (parses arbitrary user data).
    _NON_INTEGER_FUNCS: frozenset = frozenset(
        {
            "ATN",
            "COS",
            "EXP",
            "LOG",
            "SIN",
            "SQR",
            "SQRT",
            "TAN",
            "RND",
            "RUN ecb_val",
        }
    )

    # Functions that pass through integer-ness of their single
    # argument.
    _PASSTHROUGH_FUNCS: frozenset = frozenset({"ABS"})

    def __init__(
        self,
        *,
        signatures: Optional[Dict[str, "ProcedureSignature"]] = None,
    ) -> None:
        # Map of variable name -> list of RHS expressions ever
        # assigned to it. Scalar names are the plain var name;
        # array names are ``arr_X`` to match ``BasicArrayRef.var``.
        self._assignments: Dict[str, List[AbstractBasicExpression]] = defaultdict(list)
        # Every numeric scalar/array name observed in the program.
        self._numeric_vars: Set[str] = set()
        # Variables known to be non-integer independent of their
        # assignments (e.g., targets of INPUT / READ, or passed to
        # a REAL output parameter of a known procedure).
        self._tainted: Set[str] = set()
        # Signatures of known procedures, used at call sites to
        # decide whether to taint caller variables.
        self._signatures: Dict[str, "ProcedureSignature"] = signatures or {}

    @property
    def integer_vars(self) -> Set[str]:
        """Return the set of numeric variable/array names that can
        be represented as Basic09 integers.

        Scalar names appear as-is (e.g., ``"A"``, ``"X1"``); array
        names appear with the ``arr_`` prefix used throughout the
        transpiler (e.g., the Basic array ``X`` appears as
        ``"arr_X"``).
        """
        candidates: Set[str] = set(self._numeric_vars) - self._tainted

        # Fixpoint: drop any variable whose assignments can't be
        # shown to be integer given the current candidate set.
        changed = True
        while changed:
            changed = False
            for var in list(candidates):
                exps = self._assignments.get(var, ())
                if not all(self._is_integer_exp(exp, candidates) for exp in exps):
                    candidates.discard(var)
                    changed = True
        return candidates

    def visit_var(self, var: BasicVar) -> None:
        if not var.is_str_expr:
            self._numeric_vars.add(var.name())

    def visit_array_ref(self, array_ref: BasicArrayRef) -> None:
        if not array_ref.is_str_expr:
            self._numeric_vars.add(array_ref.var.name())

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicRunCall):
            self._analyze_call_site(
                statement._run_invocation,
                list(statement._arguments.exp_list),
            )
            return

        if not isinstance(statement, BasicAssignment):
            return

        target = statement.var
        exp = statement.exp

        # An assignment whose RHS is a BasicFunctionalExpression
        # emits ``run <proc>(<args...>, <target>)`` in Basic09. The
        # target variable is passed as the last (output) parameter
        # of the procedure, so if that parameter is REAL the target
        # variable is tainted.
        if isinstance(exp, BasicFunctionalExpression):
            args = list(exp._args.exp_list) + [target]
            self._analyze_call_site(exp._func, args)

        if isinstance(target, BasicVar) and not target.is_str_expr:
            name = target.name()
            self._numeric_vars.add(name)
            self._assignments[name].append(exp)
        elif isinstance(target, BasicArrayRef) and not target.is_str_expr:
            name = target.var.name()
            self._numeric_vars.add(name)
            self._assignments[name].append(exp)

    def visit_for_statement(self, for_statement: BasicForStatement) -> None:
        # The loop variable receives the start value and is
        # incremented by the step (default 1, which is integer).
        var = for_statement.var
        if not isinstance(var, BasicVar) or var.is_str_expr:
            return
        name = var.name()
        self._numeric_vars.add(name)
        self._assignments[name].append(for_statement._start_exp)
        if for_statement._step_exp is not None:
            self._assignments[name].append(for_statement._step_exp)

    def visit_read_statement(
        self, statement: BasicReadStatement
    ) -> AbstractBasicStatement:
        for rhs in statement.rhs_list:
            self._taint_target(rhs)
        return statement

    def visit_input_statement(
        self, statement: BasicInputStatement
    ) -> AbstractBasicStatement:
        for rhs in statement._rhs_list:
            self._taint_target(rhs)
        return statement

    def _taint_target(self, target: AbstractBasicExpression) -> None:
        if isinstance(target, BasicVar) and not target.is_str_expr:
            self._tainted.add(target.name())
            self._numeric_vars.add(target.name())
        elif isinstance(target, BasicArrayRef) and not target.is_str_expr:
            self._tainted.add(target.var.name())
            self._numeric_vars.add(target.var.name())

    def _analyze_call_site(
        self,
        invocation: str,
        args: List[AbstractBasicExpression],
    ) -> None:
        """Taint caller variables whose call-site usage constrains
        them to a non-integer type.

        Two cases taint a variable:

        1. It is passed to a ``REAL`` output parameter. Output
           parameters write back through the caller's storage, so
           the caller's variable must already be declared as the
           callee's type.
        2. It is passed to a parameter whose type isn't numeric
           at all (e.g., ``display_t``, ``play_t``, ``string``,
           ``rregisters``). Such a variable is not a numeric
           scalar and has no business appearing in the integer
           candidate set even though the visitor sees it at call
           sites as a ``BasicVar``.

        Numeric input parameters impose no constraint because the
        transpiler can coerce values at the call site with
        ``float(...)`` or ``fix(...)``.
        """
        match = _RUN_INVOCATION_REGEX.match(invocation or "")
        if not match:
            return
        signature = self._signatures.get(match.group(1))
        if signature is None:
            return
        for arg, param in zip(args, signature.params):
            if param.is_output and param.is_real:
                # Passing a variable to a REAL output parameter
                # pins that variable's type to REAL in the
                # generated code, so it cannot become INTEGER.
                self._taint_target(arg)
            elif not (param.is_real or param.is_integer):
                # Non-numeric typed parameter (record, string,
                # array of bytes, etc.) — the passed variable has
                # that same compound type, not a numeric scalar.
                self._taint_target(arg)

    def _is_integer_exp(
        self,
        exp: AbstractBasicExpression,
        candidates: Set[str],
    ) -> bool:
        """Return True iff ``exp`` is statically known to evaluate
        to an integer in ``[-32768, 32767]`` under the assumption
        that every variable in ``candidates`` is an integer.
        """
        if isinstance(exp, BasicLiteral):
            return (not exp.is_str_expr) and self._is_int16_value(exp.literal)

        if isinstance(exp, HexLiteral):
            # The integer value is what matters here; the transpiler's
            # ``is_float`` flag only controls how the literal is
            # currently *emitted*, not its underlying value.
            return self._is_int16_value(exp.literal)

        if isinstance(exp, BasicVar):
            if exp.is_str_expr:
                return False
            return exp.name() in candidates

        if isinstance(exp, BasicArrayRef):
            if exp.is_str_expr:
                return False
            return exp.var.name() in candidates

        if isinstance(exp, BasicParenExp):
            return self._is_integer_exp(exp._exp, candidates)

        if isinstance(exp, BasicBinaryExp):
            op = exp._op if isinstance(exp._op, str) else exp._op.operator
            # Division and exponentiation can always produce a
            # non-integer / out-of-range result.
            if op in {"/", "^"}:
                return False
            # Sum, product, bitwise-and-logical ops: integer iff
            # both operands are integers. Note: we're taking a
            # best-effort static approximation — overflow of the
            # 16-bit range is not detected here because the inputs
            # themselves are already bounded to 16 bits.
            if op in {"+", "-", "*", "AND", "OR"}:
                return self._is_integer_exp(
                    exp._exp1, candidates
                ) and self._is_integer_exp(exp._exp2, candidates)
            # Comparison operators evaluate to 0 or -1 in Basic09:
            # always integer regardless of operand types.
            if op in {"=", "<>", "<", ">", "<=", ">=", "=<", "=>"}:
                return True
            return False

        if isinstance(exp, BasicOpExp):
            inner = exp.exp
            if exp.operator == "-":
                # Handle "-<literal>" so that -32768 is recognized
                # as a valid 16-bit integer even though 32768 on
                # its own would fall outside the range.
                if isinstance(inner, BasicLiteral) and self._is_numeric_literal(
                    inner.literal
                ):
                    return self._is_int16_value(-inner.literal)
                if isinstance(inner, HexLiteral):
                    return self._is_int16_value(-inner.literal)
                return self._is_integer_exp(inner, candidates)
            if exp.operator == "+":
                return self._is_integer_exp(inner, candidates)
            if exp.operator == "NOT":
                # Bitwise/logical NOT of an integer is an integer.
                return self._is_integer_exp(inner, candidates)
            return False

        if isinstance(exp, (BasicFunctionCall, BasicFunctionalExpression)):
            func = exp._func
            if func in self._NON_INTEGER_FUNCS:
                return False
            if func in self._INTEGER_FUNCS:
                return True
            if func in self._PASSTHROUGH_FUNCS:
                args = exp._args.exp_list
                return len(args) == 1 and self._is_integer_exp(args[0], candidates)
            return False

        # Anything we don't understand is assumed non-integer for
        # safety.
        return False

    @staticmethod
    def _is_numeric_literal(value: object) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    @staticmethod
    def _is_int16_value(value: object) -> bool:
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return -32768 <= value <= 32767
        if isinstance(value, float):
            if not value.is_integer():
                return False
            return -32768 <= int(value) <= 32767
        return False
