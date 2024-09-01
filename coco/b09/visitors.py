from coco import b09
from coco.b09.elements import (
    AbstractBasicExpression,
    AbstractBasicStatement,
    Basic09CodeStatement,
    BasicArrayRef,
    BasicAssignment,
    BasicDataStatement,
    BasicDimStatement,
    BasicExpressionList,
    BasicForStatement,
    BasicFunctionalExpression,
    BasicGoStatements,
    BasicHbuffStatement,
    BasicJoystkExpression,
    BasicInputStatement,
    BasicLine,
    BasicLiteral,
    BasicNextStatement,
    BasicOnGoStatement,
    BasicPrintArgs,
    BasicPrintStatement,
    BasicReadStatement,
    BasicRunCall,
    BasicStatement,
    BasicStatements,
    BasicVar,
)

from typing import List, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from coco.b09.prog import BasicProg


class BasicConstructVisitor:
    def visit_array_ref(self, array_ref: BasicArrayRef) -> None:
        """
        Invoked when an array reference is encountered.
        """
        pass

    def visit_data_statement(self, for_statement: BasicDataStatement) -> None:
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

    def visit_print_statement(self, statement: BasicPrintStatement) -> None:
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

    def visit_statement(self, statement: BasicStatement) -> None:
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

    def visit_for_statement(self, _: BasicForStatement):
        self._count = self._count + 1

    def visit_next_statement(self, next_statement: BasicNextStatement):
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
    _statements: List[BasicStatement]

    @property
    def statements(self) -> List[BasicStatement]:
        return self._statements

    def __init__(self, statement_type: type):
        self._statements = []
        self._statement_type = statement_type

    def visit_statement(self, statement: BasicStatement):
        if type(statement) is self._statement_type:
            self._statements.append(statement)
        super().visit_statement(statement)


class VarInitializerVisitor(BasicConstructVisitor):
    def __init__(self):
        self._vars = set()

    @property
    def assignment_lines(self) -> List[BasicLine]:
        return [
            BasicLine(
                None,
                BasicStatements(
                    [
                        BasicAssignment(
                            BasicVar(var, is_str_expr=var.endswith("$")),
                            BasicLiteral(
                                "" if var.endswith("$") else 0.0,
                                is_str_expr=var.endswith("$"),
                            ),
                        )
                        for var in sorted(self._vars)
                        if ((var.endswith("$") and len(var) <= 3) or len(var) <= 2)
                    ]
                ),
            )
        ]

    def visit_var(self, var) -> None:
        self._vars.add(var.name())


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

    def __init__(self, *, default_str_storage: int):
        self._default_str_storage = default_str_storage
        self._dimmed_var_names = set()

    def visit_statement(self, statement: BasicStatement) -> None:
        if isinstance(statement, BasicDimStatement):
            statement.default_str_storage = self._default_str_storage
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

    def visit_statement(self, statement: BasicStatement) -> None:
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
    _referenced_var_names: Set[str]

    def __init__(self, *, dimmed_var_names: Set[str]):
        self._dimmed_var_names = dimmed_var_names
        self._referenced_var_names = set()

    def visit_array_ref(self, array_ref: BasicArrayRef) -> None:
        self._referenced_var_names.add(array_ref.var.name())

    @property
    def implicitly_declared_arrays(self) -> Set[str]:
        return self._referenced_var_names - self._dimmed_var_names

    @property
    def dim_statements(self) -> List[BasicStatement]:
        return [
            BasicDimStatement(
                [
                    BasicArrayRef(
                        BasicVar(var[4:], is_str_expr=var.endswith("$")),
                        BasicExpressionList([BasicLiteral(10)]),
                        is_str_expr=var.endswith("$"),
                    )
                ]
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

    def visit_data_statement(self, statement: BasicDataStatement):
        for exp in statement.exp_list.exp_list:
            self._has_empty_data_elements = (
                self._has_empty_data_elements or exp.literal == ""
            )


class BasicReadStatementPatcherVisitor(BasicConstructVisitor):
    def visit_data_statement(self, statement: BasicDataStatement):
        exp: AbstractBasicExpression
        for exp in statement.exp_list.exp_list:
            if not isinstance(exp.literal, str):
                exp.literal = str(exp.literal)

    def visit_read_statement(self, statement: BasicReadStatement):
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
    def visit_input_statement(self, statement: BasicInputStatement):
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
    def visit_print_statement(self, statement: BasicPrintStatement):
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

    def visit_statement(self, statement: BasicStatement):
        self._statement = statement
        if isinstance(statement, BasicAssignment) and isinstance(
            statement.exp, BasicFunctionalExpression
        ):
            statement.exp.set_var(statement.var)

    def visit_exp(self, exp):
        if not isinstance(exp, BasicFunctionalExpression) or exp.var:
            return
        self._statement.transform_function_to_call(exp)


class BasicHbuffPresenceVisitor(BasicConstructVisitor):
    _hasHbuff: bool

    def __init__(self):
        self._hasHbuff = False

    def visit_statement(self, statement: BasicStatement) -> None:
        if isinstance(statement, BasicHbuffStatement):
            self._hasHbuff = True

    @property
    def has_hbuff(self) -> bool:
        return self._hasHbuff
