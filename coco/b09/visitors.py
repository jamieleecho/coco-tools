from __future__ import annotations

import copy
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import TYPE_CHECKING, Dict, List, Optional, Set

from coco import b09
from coco.b09.configs import StringConfigs
from coco.b09.elements import (
    RELATIONAL_OPERATORS,
    AbstractBasicConstruct,
    AbstractBasicExpression,
    AbstractBasicStatement,
    Basic09CodeStatement,
    BasicArrayRef,
    BasicAssignment,
    BasicBinaryExp,
    BasicBooleanBinaryExp,
    BasicBooleanOpExp,
    BasicCls,
    BasicComparisonValue,
    BasicComparisonValueAssignment,
    BasicComparisonValueStatement,
    BasicDataStatement,
    BasicDefFnStatement,
    BasicDimStatement,
    BasicExpressionList,
    BasicFnArgAssignment,
    BasicFnExpression,
    BasicForStatement,
    BasicFunctionalExpression,
    BasicFunctionCall,
    BasicGoStatements,
    BasicHbuffStatement,
    BasicIf,
    BasicInputStatement,
    BasicJoystkExpression,
    BasicLine,
    BasicLiteral,
    BasicNextStatement,
    BasicNumericCondition,
    BasicOnGoStatement,
    BasicOpExp,
    BasicParenExp,
    BasicPoke,
    BasicPrintArgs,
    BasicPrintStatement,
    BasicReadStatement,
    BasicRunCall,
    BasicSound,
    BasicStatements,
    BasicTabCall,
    BasicVar,
    BasicWidthStatement,
    HexLiteral,
    numeric_literal_value,
)
from coco.b09.errors import ParseError

if TYPE_CHECKING:
    from coco.b09.procbank import ProcedureParam, ProcedureSignature
    from coco.b09.prog import BasicProg


# Extracts the procedure name from a ``run <name>`` invocation
# string stored on ``BasicRunCall._run_invocation`` or
# ``BasicFunctionalExpression._func``.
_RUN_INVOCATION_REGEX = re.compile(r"(?i)^\s*run\s+(\w+)")

# Variables that the transpiler always declares as INTEGER in the
# generated prologue. These are referenced by name from built-in
# statements (HBUFF, HGET, HPUT, JOYSTK) rather than coming from the
# source program, so the optimization passes must leave them alone:
# they are never coerced with ``fix(...)`` and never turn up as
# integer candidates needing a DIM of their own.
BUILTIN_INTEGER_VAR_NAMES: frozenset = frozenset(
    {
        "pid",
        "joy0x",
        "joy0y",
        "joy1x",
        "joy1y",
    }
)


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

    def visit_inlined_fn(self, exp: BasicFnExpression) -> None:
        """
        Invoked when an inlined DEF FN call is encountered, after the
        assignment of its argument has been visited and before its body
        is.
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

    @property
    def default_str_storage(self) -> int:
        return self._default_str_storage

    @property
    def strname_to_size(self) -> Dict[str, int]:
        """Per-variable string sizes, keyed the way
        :class:`BasicDimStatement` names its variables (arrays carry
        the ``arr_`` prefix).
        """
        return self._strname_to_size


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
    _default_str_storage: int
    _dimmed_var_names: Set[str]
    _initialize_vars: bool
    _referenced_var_names: Set[str]
    _strname_to_size: Dict[str, int]

    def __init__(
        self,
        *,
        dimmed_var_names: Set[str],
        initialize_vars: bool = False,
        default_str_storage: int = b09.DEFAULT_STR_STORAGE,
        strname_to_size: Optional[Dict[str, int]] = None,
    ):
        self._dimmed_var_names = dimmed_var_names
        self._initialize_vars = initialize_vars
        self._referenced_var_names = set()
        self._default_str_storage = default_str_storage
        self._strname_to_size = strname_to_size or {}

    def visit_array_ref(self, array_ref: BasicArrayRef) -> None:
        self._referenced_var_names.add(array_ref.var.name())

    @property
    def implicitly_declared_arrays(self) -> Set[str]:
        return self._referenced_var_names - self._dimmed_var_names

    @property
    def dim_statements(self) -> List[BasicDimStatement]:
        """The ``DIM`` statements for arrays used without a ``DIM``.

        String arrays get the same storage treatment as explicitly
        dimensioned ones, so a ``--default-str-storage`` or a
        per-variable size from the config file is honored here too.
        The names are sorted so that a program always converts to the
        same text; iterating the set directly reorders the ``DIM``
        lines from run to run.
        """
        statements: List[BasicDimStatement] = []
        for var in sorted(self.implicitly_declared_arrays):
            statement = BasicDimStatement(
                [
                    BasicArrayRef(
                        BasicVar(var[4:], is_str_expr=var.endswith("$")),
                        BasicExpressionList([BasicLiteral(10)]),
                        is_str_expr=var.endswith("$"),
                    ),
                ],
                initialize_vars=self._initialize_vars,
            )
            statement.default_str_storage = self._default_str_storage
            statement.strname_to_size = self._strname_to_size
            statements.append(statement)
        return statements


class JoystickVisitor(BasicConstructVisitor):
    def __init__(self):
        self._uses_joystk = False

    @property
    def joystk_var_statements(self):
        return (
            [
                Basic09CodeStatement("dim joy0x, joy0y, joy1x, joy1y: integer"),
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


class HoistableExpressionVisitor(BasicConstructVisitor):
    """Reports whether an expression holds anything that
    :class:`BasicFunctionalExpressionPatcherVisitor` hoists in front of
    the statement that holds it: a call it turns into a procedure call,
    a comparison whose result is used as a number, or the argument
    assignment of an inlined DEF FN call.
    """

    def __init__(self) -> None:
        self._found: bool = False

    @property
    def found(self) -> bool:
        return self._found

    def visit_exp(self, exp: AbstractBasicExpression) -> None:
        if isinstance(exp, (BasicFunctionalExpression, BasicComparisonValue)):
            self._found = self._found or not exp.var
        elif isinstance(exp, BasicFnExpression):
            self._found = self._found or exp.assignment is not None


class BasicReadStatementSplitterVisitor(BasicConstructVisitor):
    """Gives every READ item that hoists something a READ of its own.

    Hoisted calls and comparisons run in front of the statement that
    holds them, so a subscript holding one is evaluated before the READ
    reads anything. Color BASIC evaluates a subscript when it reaches
    that item, after the items in front of it have been read:
    ``READ I, A(INT(I))`` indexes ``A`` with the ``I`` the same
    statement just read. Reading such an item with a READ of its own
    puts the hoisted statements after the reads in front of it, since
    each READ picks up where the one before it left off.
    """

    def visit_read_statement(
        self, statement: BasicReadStatement
    ) -> AbstractBasicStatement:
        groups: List[List[AbstractBasicExpression]] = [[]]
        for rhs in statement.rhs_list:
            hoistable = HoistableExpressionVisitor()
            rhs.visit(hoistable)
            # An item that hoists in front of the whole statement reads
            # nothing before itself, so the first group never splits.
            if hoistable.found and groups[-1]:
                groups.append([])
            groups[-1].append(rhs)

        if len(groups) < 2:
            return statement

        statement.rhs_list[:] = groups[0]
        return BasicStatements(
            [statement] + [BasicReadStatement(group) for group in groups[1:]],
            multi_line=False,
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
    """Wrap INPUT so the cursor and full duplex are set around it.

    In terminal mode the ``_t`` variants are used instead. Those
    drop the ``_ecb_cursor_color`` call, which writes the two raw
    bytes ``$05, $20 + v`` that set the CoCo cursor color. An
    ordinary terminal swallows the ``$05`` and prints the second
    byte, so every INPUT leaves a stray ``!`` (prefix) or space
    (suffix) on screen. Worse, those bytes go out through ``PUT
    #1``, which Basic09's PRINT column accounting does not see, so
    the first ``TAB`` after an INPUT lands one column too far right.
    """

    def __init__(self, terminal: bool = False):
        self._suffix = "_t" if terminal else ""

    def visit_input_statement(
        self, statement: BasicInputStatement
    ) -> AbstractBasicStatement:
        """
        Transform the INPUT statement so that the cursor and full duplex are
        enabled before the statement and disabled after the statement.
        """

        # Create statements for reading into the REAL vars
        filter_statements = [
            BasicRunCall(
                f"RUN _ecb_input_prefix{self._suffix}", BasicExpressionList([])
            ),
            statement,
            BasicRunCall(
                f"RUN _ecb_input_suffix{self._suffix}", BasicExpressionList([])
            ),
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


class VarReferenceVisitor(BasicConstructVisitor):
    """Records whether a scalar variable is read."""

    def __init__(self, name: str):
        self._name = name
        self._found = False

    @property
    def found(self) -> bool:
        return self._found

    def visit_var(self, var: BasicVar) -> None:
        self._found = self._found or var.name() == self._name


class HoistedStatementCollectorVisitor(BasicConstructVisitor):
    """Collects the statements hoisted out of an expression: the calls
    of functional expressions, the comparisons whose results are used as
    numbers and the argument assignments of inlined DEF FN calls.

    A call that is the whole argument of a DEF FN call is collected
    too, although it is not hoisted: it assigns the parameter itself.
    """

    def __init__(self):
        self._statements: List[AbstractBasicConstruct] = []

    @property
    def statements(self) -> List[AbstractBasicConstruct]:
        return self._statements

    def visit_exp(self, exp: AbstractBasicExpression) -> None:
        if (
            isinstance(exp, (BasicFunctionalExpression, BasicComparisonValue))
            and exp.statement is not None
        ):
            self._statements.append(exp.statement)
        elif isinstance(exp, BasicFnExpression) and exp.assignment is not None:
            self._statements.append(exp.assignment)


class ForLoopSemanticsVisitor(BasicConstructVisitor):
    """Chooses between Color BASIC's and Basic09's ``FOR`` semantics.

    See :class:`BasicForStatement`. With ``runs_at_least_once`` set,
    it also notes which loops compute their bounds from the loop
    variable, since those need the start assigned before the limit
    is evaluated.
    """

    def __init__(self, runs_at_least_once: bool = True):
        self._runs_at_least_once = runs_at_least_once

    def visit_for_statement(self, for_statement: BasicForStatement) -> None:
        for_statement.runs_at_least_once = self._runs_at_least_once
        reference_visitor = VarReferenceVisitor(for_statement.var.name())
        for exp in (
            for_statement.start_exp,
            for_statement.end_exp,
            for_statement.step_exp,
        ):
            if exp is not None:
                exp.visit(reference_visitor)
        for_statement.bounds_read_var = reference_visitor.found
        start_statements = HoistedStatementCollectorVisitor()
        for_statement.start_exp.visit(start_statements)
        for_statement.start_call_count = sum(
            any(statement is hoisted for hoisted in start_statements.statements)
            for statement in for_statement.pre_assignment_statements
        )


class TruncateRealArgsVisitor(BasicConstructVisitor):
    """Truncates the real values Basic09 would otherwise round.

    Wherever Color BASIC needs an integer -- an array subscript, the
    argument of ``CHR$``, ``LEFT$``, ``MID$``, ``PEEK``, ``RIGHT$`` or
    ``TAB``, the selector of ``ON ... GOTO``, the operands of ``AND``,
    ``OR``, ``NOT`` and ``POKE`` -- it drops the fraction, so ``A(1.9)``
    is ``A(1)``. Basic09 rounds instead and reads ``A(2)``. Expressions
    that cannot be shown to hold a whole number are wrapped in
    ``INT``, which truncates in Basic09.

    For negative values Color BASIC rounds down, while ``INT``
    rounds toward zero. The two differ only for a negative fraction,
    which is an error in every one of these places except ``AND``,
    ``OR`` and ``NOT``.
    """

    # The positions of the integer arguments of each function, or
    # ``None`` for all of them.
    _INTEGER_ARG_POSITIONS: Dict[str, Optional[tuple]] = {
        "CHR$": None,
        "LEFT$": (1,),
        "MID$": (1, 2),
        "PEEK": None,
        "RIGHT$": (1,),
    }

    def __init__(self, integral_var_names: Set[str]):
        self._integral_var_names = integral_var_names
        self._integral_checker = IntegralVarVisitor()

    def visit_array_ref(self, array_ref: BasicArrayRef) -> None:
        array_ref.indices._exp_list = [
            self._truncate(index) for index in array_ref.indices.exp_list
        ]

    def visit_exp(self, exp: AbstractBasicExpression) -> None:
        if isinstance(exp, BasicTabCall):
            exp.column = self._truncate(exp.column)
        elif isinstance(exp, BasicFunctionCall):
            if exp._func in self._INTEGER_ARG_POSITIONS:
                positions = self._INTEGER_ARG_POSITIONS[exp._func]
                exp._args._exp_list = [
                    self._truncate(arg)
                    if positions is None or position in positions
                    else arg
                    for position, arg in enumerate(exp._args.exp_list)
                ]
        elif isinstance(exp, BasicBinaryExp) and not isinstance(
            exp, BasicBooleanBinaryExp
        ):
            if exp.operator in {"AND", "OR"}:
                exp._exp1 = self._truncate(exp.exp1)
                exp._exp2 = self._truncate(exp.exp2)
        elif isinstance(exp, BasicOpExp) and not isinstance(exp, BasicBooleanOpExp):
            if exp.operator == "NOT":
                exp._exp = self._truncate(exp.exp)

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicOnGoStatement):
            statement._exp = self._truncate(statement._exp)
        elif isinstance(statement, BasicPoke):
            statement._exp1 = self._truncate(statement._exp1)
            statement._exp2 = self._truncate(statement._exp2)

    def _truncate(self, exp: AbstractBasicExpression) -> AbstractBasicExpression:
        if self._integral_checker.is_integral(exp, self._integral_var_names):
            return exp
        return BasicFunctionCall("INT", BasicExpressionList([exp]))


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
        # Calls in the argument of a DEF FN call are hoisted in front of
        # the enclosing statement too, which also gives them temporaries
        # distinct from the ones it already holds. So is everything in a
        # comparison whose result is used as a number.
        if not isinstance(
            statement,
            (
                BasicFnArgAssignment,
                BasicComparisonValueAssignment,
                BasicComparisonValueStatement,
            ),
        ):
            self._statement = statement
        if isinstance(statement, BasicAssignment) and isinstance(
            statement.exp, (BasicFunctionalExpression, BasicComparisonValue)
        ):
            statement.exp.set_var(statement.var)

    def visit_exp(self, exp) -> None:
        if (
            not isinstance(exp, (BasicFunctionalExpression, BasicComparisonValue))
            or exp.var
        ):
            return
        if isinstance(self._statement, AbstractBasicStatement):
            self._statement.transform_function_to_call(exp)

    def visit_inlined_fn(self, exp: BasicFnExpression) -> None:
        # After the calls in the argument and before the ones in the
        # body, which read the parameter.
        if isinstance(self._statement, AbstractBasicStatement):
            self._statement.pre_assignment_statements.append(exp.assignment)


class FixArraySizesVisitor(BasicConstructVisitor):
    """Gives arrays the bounds passed with ``--fix-array-size`` and
    rejects the ``DIM`` statements whose bounds are still not constants.

    Color BASIC sizes an array when its ``DIM`` runs, so a bound can be
    any expression. BASIC09 declares an array with a fixed size, so the
    user has to pick one that is large enough.

    ``fixed_array_sizes`` maps an array's Color BASIC name, such as
    ``A`` or ``B$``, to its bounds, where ``None`` keeps the program's
    bound for that dimension. Call :meth:`check` once the whole program
    has been visited.
    """

    def __init__(self, fixed_array_sizes: Mapping[str, Sequence[int | None]]):
        self._fixed_array_sizes = {
            name.upper(): bounds for name, bounds in fixed_array_sizes.items()
        }
        self._fixed_names: Set[str] = set()
        self._linenum: int | None = None
        self._unfixed_statements: List[tuple[int | None, BasicDimStatement]] = []
        self._unfixed_arrays: Dict[str, BasicArrayRef] = {}

    def visit_line(self, line: BasicLine) -> None:
        self._linenum = line.num

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if not isinstance(statement, BasicDimStatement):
            return
        is_fixed = True
        for index, dim_var in enumerate(statement.dim_vars):
            if not isinstance(dim_var, BasicArrayRef):
                continue
            name = dim_var.var.name()[4:]
            bounds = self._fixed_array_sizes.get(name)
            if bounds is not None:
                if len(bounds) != len(dim_var.indices.exp_list):
                    raise ParseError(
                        f"--fix-array-size gives {name} {len(bounds)} "
                        f"bound{'' if len(bounds) == 1 else 's'}, but "
                        f"{self._line_text()}DIMs it with "
                        f"{len(dim_var.indices.exp_list)}: {statement.source}"
                    )
                statement.fix_array_size(index, bounds)
                self._fixed_names.add(name)
                dim_var = statement.dim_vars[index]
                assert isinstance(dim_var, BasicArrayRef)
            if not BasicDimStatement.has_constant_sizes(dim_var):
                is_fixed = False
                self._unfixed_arrays.setdefault(name, dim_var)
        if not is_fixed:
            self._unfixed_statements.append((self._linenum, statement))

    def _line_text(self) -> str:
        return "" if self._linenum is None else f"line {self._linenum} "

    def _bound_text(self, name: str, index: int, size: AbstractBasicExpression) -> str:
        bounds = self._fixed_array_sizes.get(name)
        if bounds and bounds[index] is not None:
            return str(bounds[index])
        return "*" if BasicDimStatement.is_constant(size) else "n"

    def check(self) -> None:
        unused_names = sorted(set(self._fixed_array_sizes) - self._fixed_names)
        if unused_names:
            raise ParseError(
                "--fix-array-size names arrays that no DIM statement "
                f"declares: {', '.join(unused_names)}."
            )
        if not self._unfixed_statements:
            return

        statements = "\n".join(
            f"  {'' if linenum is None else f'{linenum} '}{statement.source}"
            for linenum, statement in self._unfixed_statements
        )
        options = " ".join(
            '--fix-array-size "{}({})"'.format(
                name,
                ",".join(
                    self._bound_text(name, index, size)
                    for index, size in enumerate(dim_var.indices.exp_list)
                ),
            )
            for name, dim_var in self._unfixed_arrays.items()
        )
        raise ParseError(
            "BASIC09 arrays have a fixed size, but these DIM statements "
            "size arrays as the program runs:\n"
            f"{statements}\n"
            "Replace each n below with the largest subscript the program "
            "needs in that dimension. A * keeps the program's own bound.\n"
            f"  {options}"
        )


class RenameVarVisitor(BasicConstructVisitor):
    """Renames a numeric scalar variable."""

    def __init__(self, name: str, new_name: str):
        self._name = name
        self._new_name = new_name

    def visit_var(self, var: BasicVar) -> None:
        if var.name() == self._name and not var.is_str_expr:
            var._name = self._new_name


class DefFnInlinerVisitor(BasicConstructVisitor):
    """Inlines every call to a ``DEF FN`` function; see
    :class:`BasicFnExpression`.

    Definitions are looked up by name wherever they are in the program,
    rather than by which ``DEF`` last ran, so a function defined twice
    is rejected.

    The variable a call assigns its argument to is named after the
    function and numbered within the line, since two calls in one
    statement must not share one. Each is read only by the statement it
    is assigned in front of, so the next line can reuse it.
    """

    def __init__(self, definitions: List[BasicDefFnStatement]):
        self._definitions: Dict[str, BasicDefFnStatement] = {}
        for definition in definitions:
            if definition.name in self._definitions:
                raise ParseError(f"FN{definition.name} is defined more than once.")
            self._definitions[definition.name] = definition
        self._call_counts: Dict[str, int] = defaultdict(int)
        self._expanding: List[str] = []

    def visit_line(self, line: BasicLine) -> None:
        self._call_counts.clear()

    def visit_exp(self, exp: AbstractBasicExpression) -> None:
        if not isinstance(exp, BasicFnExpression) or exp.body is not None:
            return
        definition = self._definitions.get(exp.name)
        if definition is None:
            raise ParseError(f"FN{exp.name} is called but never defined.")
        if exp.name in self._expanding:
            raise ParseError(f"FN{exp.name} calls itself.")

        self._call_counts[exp.name] += 1
        param = BasicVar(f"fn{exp.name}_{self._call_counts[exp.name]}")
        body = copy.deepcopy(definition.body)
        # Color BASIC does not give the parameter a variable of its own.
        # It saves the variable, assigns it the argument while the body
        # runs and then restores it, so the functions the body calls see
        # the parameter too. The calls are therefore inlined before the
        # parameter is renamed, and the renaming reaches into them. Their
        # own parameters are renamed by then, so they still shadow it.
        self._expanding.append(exp.name)
        body.visit(self)
        self._expanding.pop()
        body.visit(RenameVarVisitor(definition.param.name(), param.name()))
        exp.inline(param, body)


class ComparisonConditionVisitor(BasicConstructVisitor):
    """Uses a numeric ``IF`` condition that is a single comparison as the
    condition itself.

    Such a condition holds a :class:`BasicComparisonValue`, maybe in
    parentheses or as the body of an inlined DEF FN call, and comparing
    its -1 or 0 against zero amounts to making the comparison. DEF FN
    calls cannot be seen into until they are inlined, so this runs after
    they are.
    """

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if not isinstance(statement, BasicIf) or not isinstance(
            statement.exp, BasicNumericCondition
        ):
            return
        condition = self._comparison(statement.exp.exp1)
        if condition is not None:
            statement._exp = condition

    @classmethod
    def _comparison(
        cls, exp: AbstractBasicExpression
    ) -> AbstractBasicExpression | None:
        """Return ``exp`` with its comparison made directly, or ``None``
        if ``exp`` is not a single comparison."""
        if isinstance(exp, BasicComparisonValue):
            return exp.comparison
        if isinstance(exp, BasicParenExp):
            inner = cls._comparison(exp.exp)
            if inner is not None:
                exp._exp = inner
                return exp
        if isinstance(exp, BasicFnExpression) and exp.body is not None:
            body = cls._comparison(exp.body)
            if body is not None:
                exp._body = (
                    body if isinstance(body, BasicParenExp) else BasicParenExp(body)
                )
                return exp
        return None


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
        if isinstance(exp, BasicFnExpression) and exp.body is not None:
            exp._body = self._rewrite(exp.body)
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
    """Coerces ``REAL`` arguments to ``INTEGER`` parameters of
    known procedures.

    BASIC09 converts neither an ``INTEGER`` argument to a ``REAL``
    parameter nor a ``REAL`` argument to an ``INTEGER`` parameter.
    For ``INTEGER`` parameters this visitor performs the conversion
    by either
    rewriting integer-valued ``BasicLiteral`` floats to genuine
    integer literals in place, or wrapping the argument with
    ``fix(...)``. Because ``fix`` rounds, an argument that is not
    known to be a whole number (per ``integral_var_names``) is
    truncated with ``INT`` first: ``fix(INT(...))``. Integer-typed
    arguments to ``REAL`` parameters are wrapped with ``float(...)``.

    The visitor walks ``BasicRunCall``, the patched
    ``BasicFunctionalExpression`` form (for things like
    ``A = INT(X)``), and the hand-rolled emitters ``BasicSound``,
    ``BasicCls``, and ``BasicWidthStatement``.

    Variables passed as output parameters are never coerced — the
    :class:`IntegerVarVisitor` has already excluded them from the
    integer set when the output parameter is ``REAL``, and the
    visitor cannot insert a temporary write-back for the
    ``INTEGER`` direction.
    """

    _integer_var_names: Set[str]
    _integral_var_names: Set[str]
    _signatures: Dict[str, "ProcedureSignature"]

    # Basic09 functions whose result is an INTEGER.
    _INTEGER_FUNCS: frozenset = frozenset(
        {"asc", "fix", "land", "len", "lnot", "lor", "peek", "sgn"}
    )

    # Basic09 functions whose result has the type of their arguments.
    _INTEGER_PASSTHROUGH_FUNCS: frozenset = frozenset({"abs", "mod", "sq"})

    def __init__(
        self,
        *,
        integer_var_names: Set[str],
        signatures: Dict[str, "ProcedureSignature"],
        integral_var_names: Optional[Set[str]] = None,
    ):
        self._integer_var_names = integer_var_names
        self._integral_var_names = (
            integer_var_names if integral_var_names is None else integral_var_names
        )
        self._signatures = signatures
        self._integral_checker = IntegralVarVisitor()

    def visit_statement(self, statement: AbstractBasicConstruct) -> None:
        if isinstance(statement, BasicRunCall):
            self._rewrite_args(statement._run_invocation, statement._arguments)
            return
        if isinstance(statement, BasicSound):
            # BasicSound hand-emits ``RUN ecb_sound(f, d, 31.0, ...)``
            # without using a ``BasicRunCall``. f and d are the two
            # leading parameters of ecb_sound — coerce them per the
            # signature so the conversion direction tracks ecb.b09.
            sig = self._signatures.get("ecb_sound")
            if sig and len(sig.params) >= 2:
                statement._exp1 = self._coerce_for_param(statement._exp1, sig.params[0])
                statement._exp2 = self._coerce_for_param(statement._exp2, sig.params[1])
            return
        if isinstance(statement, BasicCls):
            # BasicCls hand-emits ``RUN ecb_cls(color, display)``.
            # ``color`` is the first parameter of ecb_cls.
            if statement._exp is not None:
                sig = self._signatures.get("ecb_cls")
                if sig and len(sig.params) >= 1:
                    statement._exp = self._coerce_for_param(
                        statement._exp, sig.params[0]
                    )
            return
        if isinstance(statement, BasicWidthStatement):
            # BasicWidthStatement hand-emits ``run _ecb_width(w,
            # display)``. ``w`` is the first parameter of
            # _ecb_width.
            sig = self._signatures.get("_ecb_width")
            if sig and len(sig.params) >= 1:
                statement._expr = self._coerce_for_param(statement._expr, sig.params[0])
            return
        if isinstance(statement, BasicAssignment) and isinstance(
            statement.exp, BasicFunctionalExpression
        ):
            exp = statement.exp
            # Functional expressions that have been patched carry
            # their full ``run <proc>(...args..., target)`` form in
            # ``exp._statement``. The patcher creates a *new*
            # argument list (``self._args.exp_list + [var]``), so
            # we have to rewrite the args on the synthesized
            # ``BasicFunctionCall`` for the change to actually
            # appear in the emitted source.
            if exp._statement is not None:
                self._rewrite_args(exp._func, exp._statement._args)

    def visit_exp(self, exp: AbstractBasicExpression) -> None:
        # Some functional expressions never appear as the RHS of
        # an explicit assignment — for instance,
        # ``PRINT JOYSTK(0)`` patches into a synthetic call whose
        # output goes to a transpiler-allocated temp. Coerce that
        # call's arguments here too so the input literals match
        # the procedure's declared parameter types.
        if isinstance(exp, BasicFunctionalExpression) and exp._statement is not None:
            self._rewrite_args(exp._func, exp._statement._args)

    def _rewrite_args(
        self,
        invocation: str,
        exp_list: "BasicExpressionList",
    ) -> None:
        match = _RUN_INVOCATION_REGEX.match(invocation or "")
        if not match:
            return
        signature = self._signatures.get(match.group(1))
        if signature is None:
            return
        # Always normalize to a list — parser-built expression
        # lists are tuples, which can't be mutated in place. Storing
        # the rewritten list back on the container ensures both
        # views (raw exp_list and the BasicExpressionList wrapper)
        # see the coercions.
        args = list(exp_list.exp_list)
        for idx in range(min(len(args), len(signature.params))):
            args[idx] = self._coerce_for_param(args[idx], signature.params[idx])
        exp_list._exp_list = args

    def _coerce_for_param(
        self, arg: AbstractBasicExpression, param: "ProcedureParam"
    ) -> AbstractBasicExpression:
        """Return ``arg`` adapted to match ``param``'s declared
        type. Output parameters are returned unchanged because the
        visitor cannot synthesize a temporary buffer.

        Basic09 does not widen an ``INTEGER`` argument to a ``REAL``
        parameter: the procedure reads the integer's bytes as a real
        and sees garbage (7 arrives as -.0288), so integer-typed
        arguments to ``REAL`` parameters are wrapped in ``float``.
        """
        if param.is_output:
            return arg
        if param.is_integer:
            return self._coerce_to_integer(arg)
        if param.is_real and self._is_integer_arg(arg):
            if isinstance(arg, BasicLiteral):
                return BasicLiteral(float(arg.literal))
            return BasicFunctionCall("float", BasicExpressionList([arg]))
        return arg

    def _coerce_to_integer(
        self, arg: AbstractBasicExpression
    ) -> AbstractBasicExpression:
        if self._is_integer_arg(arg):
            return arg
        # Unwrap a redundant ``float(x)``: we are about to coerce
        # back to integer, so the round-trip is silly. After
        # unwrapping, retry coercion on the inner expression — it
        # may already be integer-typed (a record byte field, for
        # example), in which case we end up with no wrapping at
        # all.
        unwrapped = self._unwrap_float(arg)
        if unwrapped is not arg:
            return self._coerce_to_integer(unwrapped)
        if (
            isinstance(arg, BasicLiteral)
            and not arg.is_str_expr
            and isinstance(arg.literal, float)
            and arg.literal.is_integer()
        ):
            return BasicLiteral(int(arg.literal))
        # ``fix`` rounds, where Color BASIC drops the fraction, so a
        # value that may have one is truncated with ``INT`` first.
        if not self._integral_checker.is_integral(arg, self._integral_var_names):
            arg = BasicFunctionCall("INT", BasicExpressionList([arg]))
        return BasicFunctionCall("fix", BasicExpressionList([arg]))

    def _is_integer_arg(self, arg: AbstractBasicExpression) -> bool:
        """True if ``arg`` is statically known to be of an integer
        family type (``INTEGER`` or ``BYTE``) in the emitted
        Basic09 source — meaning Basic09 will accept it in an
        ``INTEGER`` parameter slot without an explicit ``fix()``.

        We deliberately treat record-member accesses (anything
        with a dot in the name) as integer-compatible: every byte
        field of the ``display_t`` and ``play_t`` records auto-
        promotes to ``INTEGER`` in Basic09, and the rare ``REAL``
        field would already need an explicit conversion in the
        original source.
        """
        if isinstance(arg, BasicVar) and not arg.is_str_expr:
            name = arg.name()
            if "." in name:
                return True
            return name in self._integer_var_names or name in BUILTIN_INTEGER_VAR_NAMES
        if isinstance(arg, BasicArrayRef) and not arg.is_str_expr:
            return arg.var.name() in self._integer_var_names
        if isinstance(arg, BasicLiteral):
            return isinstance(arg.literal, int) and not isinstance(arg.literal, bool)
        if isinstance(arg, HexLiteral):
            return not arg._is_float
        if isinstance(arg, BasicParenExp):
            return self._is_integer_arg(arg.exp)
        if isinstance(arg, BasicOpExp):
            return arg.operator == "NOT" or self._is_integer_arg(arg.exp)
        if isinstance(arg, BasicBinaryExp):
            if arg.operator in {"AND", "OR"}:
                return True
            return arg.operator in {"+", "-", "*", "/"} and all(
                self._is_integer_arg(operand) for operand in (arg.exp1, arg.exp2)
            )
        if isinstance(arg, (BasicFunctionalExpression, BasicComparisonValue)):
            return arg.var is not None and self._is_integer_arg(arg.var)
        if isinstance(arg, BasicFnExpression):
            return arg.body is not None and self._is_integer_arg(arg.body)
        if isinstance(arg, BasicFunctionCall):
            func = arg._func.strip().lower()
            if func in self._INTEGER_FUNCS:
                return True
            if func in self._INTEGER_PASSTHROUGH_FUNCS:
                return all(self._is_integer_arg(a) for a in arg._args.exp_list)
        return False

    def _unwrap_float(self, arg: AbstractBasicExpression) -> AbstractBasicExpression:
        """If ``arg`` is a single-argument ``float(x)`` call,
        return ``x``. Otherwise return ``arg`` unchanged.

        Both :class:`BasicFunctionCall` and :class:`BasicRunCall`
        are recognized because the transpiler uses both forms in
        different emitters (e.g., :class:`BasicCircleStatement`
        builds ``BasicRunCall("float", ...)``).
        """
        if isinstance(arg, BasicFunctionCall):
            if arg._func.strip().lower() == "float" and len(arg._args.exp_list) == 1:
                return arg._args.exp_list[0]
        if isinstance(arg, BasicRunCall):
            if (
                arg._run_invocation.strip().lower() == "float"
                and len(arg._arguments.exp_list) == 1
            ):
                return arg._arguments.exp_list[0]
        return arg


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
        candidates: Set[str] = (
            set(self._numeric_vars) - self._tainted - BUILTIN_INTEGER_VAR_NAMES
        )

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
        if var.is_str_expr:
            return
        name = var.name()
        # Skip record-member accesses (e.g. ``display.hfore``,
        # ``play.octo``). These are typed by their containing
        # record definition, not by the optimization, so they
        # must never end up in the integer candidate set.
        if "." in name:
            return
        self._numeric_vars.add(name)

    def visit_array_ref(self, array_ref: BasicArrayRef) -> None:
        if array_ref.is_str_expr:
            return
        name = array_ref.var.name()
        if "." in name:
            return
        self._numeric_vars.add(name)

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

    def visit_exp(self, exp: AbstractBasicExpression) -> None:
        # When a BasicFunctionalExpression has been patched into
        # its synthetic ``run <proc>(args..., temp)`` form, the
        # temp does not appear as the LHS of any explicit
        # BasicAssignment in the tree — it is added by
        # ``transform_function_to_call``. We still need to taint
        # the temp if the underlying procedure's output parameter
        # is REAL, otherwise the optimizer would think the temp
        # is integer and DIM it as INTEGER.
        if isinstance(exp, BasicFunctionalExpression) and exp._var is not None:
            args = list(exp._args.exp_list) + [exp._var]
            self._analyze_call_site(exp._func, args)

    def visit_read_statement(
        self, statement: BasicReadStatement
    ) -> AbstractBasicStatement:
        for rhs in statement.rhs_list:
            self._taint_target(rhs)
        return statement

    def visit_input_statement(
        self, statement: BasicInputStatement
    ) -> AbstractBasicStatement:
        for rhs in statement.rhs_list:
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
            return self._is_integer_exp(exp.exp, candidates)

        if isinstance(exp, BasicFnExpression):
            return exp.body is not None and self._is_integer_exp(exp.body, candidates)

        if isinstance(exp, BasicComparisonValue):
            # -1 or 0.
            return True

        if isinstance(exp, BasicBinaryExp):
            op = exp.operator
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
                    exp.exp1, candidates
                ) and self._is_integer_exp(exp.exp2, candidates)
            # Comparison operators evaluate to 0 or -1 in Basic09:
            # always integer regardless of operand types.
            if op in RELATIONAL_OPERATORS:
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


class IntegralVarVisitor(IntegerVarVisitor):
    """Collects the numeric variables and arrays that only ever hold
    whole numbers, whatever their size.

    This is :class:`IntegerVarVisitor` without the 16-bit range limit:
    it answers whether a value can have a fraction, not whether it fits
    in a Basic09 ``INTEGER``.
    """

    @staticmethod
    def _is_int16_value(value: object) -> bool:
        # Any whole number will do, whatever its size.
        if isinstance(value, bool):
            return False
        if isinstance(value, int):
            return True
        if isinstance(value, float):
            return value.is_integer()
        return False

    def is_integral(
        self, exp: AbstractBasicExpression, integral_var_names: Set[str]
    ) -> bool:
        """Return True iff ``exp`` is statically known to evaluate to a
        whole number, given that every variable in
        ``integral_var_names`` holds one."""
        if isinstance(exp, BasicVar) and "." in exp.name():
            # Record fields (``display.hfore``) are all BYTEs.
            return True
        value = self._constant_value(exp)
        if value is not None:
            return value.denominator == 1
        return self._is_integer_exp(exp, integral_var_names)

    def _is_integer_exp(
        self,
        exp: AbstractBasicExpression,
        candidates: Set[str],
    ) -> bool:
        # ``LAND``, ``LOR`` and ``LNOT`` yield whole numbers whatever
        # their operands hold.
        if (
            isinstance(exp, BasicBinaryExp)
            and not isinstance(exp, BasicBooleanBinaryExp)
            and exp.operator in {"AND", "OR"}
        ) or (
            isinstance(exp, BasicOpExp)
            and not isinstance(exp, BasicBooleanOpExp)
            and exp.operator == "NOT"
        ):
            return True
        return super()._is_integer_exp(exp, candidates)

    @classmethod
    def _constant_value(cls, exp: AbstractBasicExpression) -> Optional[Fraction]:
        """Return the exact value of an arithmetic expression over
        numeric literals, or ``None`` if ``exp`` is anything else."""
        if isinstance(exp, (BasicLiteral, HexLiteral)):
            value = numeric_literal_value(exp)
            if value is not None:
                return Fraction(value)
        if isinstance(exp, BasicParenExp):
            return cls._constant_value(exp.exp)
        if isinstance(exp, BasicOpExp) and exp.operator in {"-", "+"}:
            inner = cls._constant_value(exp.exp)
            if inner is None:
                return None
            return -inner if exp.operator == "-" else inner
        if isinstance(exp, BasicBinaryExp) and exp.operator in {"+", "-", "*", "/"}:
            left = cls._constant_value(exp.exp1)
            right = cls._constant_value(exp.exp2)
            if left is None or right is None:
                return None
            if exp.operator == "+":
                return left + right
            if exp.operator == "-":
                return left - right
            if exp.operator == "*":
                return left * right
            return left / right if right else None
        return None
