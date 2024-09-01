from abc import ABC, abstractmethod
from itertools import chain
from typing import List, Literal, TYPE_CHECKING, Union

from coco.b09 import DEFAULT_STR_STORAGE

if TYPE_CHECKING:
    from visitors import BasicConstructVisitor


class AbstractBasicConstruct(ABC):
    def indent_spaces(self, indent_level):
        return "  " * indent_level

    @abstractmethod
    def basic09_text(self, indent_level: int) -> str:
        """Return the Basic09 text that represents this construct"""
        pass

    @property
    def is_expr(self):
        return False

    @property
    def is_str_expr(self):
        return False

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        pass


class AbstractBasicExpression(AbstractBasicConstruct):
    def __init__(self, is_str_expr=False):
        self._is_str_expr = is_str_expr

    @property
    def is_expr(self):
        return True

    @property
    def is_str_expr(self):
        return self._is_str_expr


class AbstractBasicStatement(AbstractBasicConstruct):
    def __init__(self):
        self._pre_assignment_statements = []
        self._temps = set()
        self._str_temps = set()

    def get_new_temp(self, is_str_exp):
        if is_str_exp:
            val = f"tmp_{len(self._str_temps) + 1}$"
            self._str_temps.add(val)
        else:
            val = f"tmp_{len(self._temps) + 1}"
            self._temps.add(val)

        return BasicVar(val, is_str_expr=is_str_exp)

    def transform_function_to_call(self, exp):
        exp.set_var(self.get_new_temp(exp.is_str_expr))
        self.pre_assignment_statements.append(exp.statement)

    @property
    def pre_assignment_statements(self):
        return self._pre_assignment_statements

    def basic09_text(self, indent_level: int) -> str:
        pre_assignments = BasicStatements(
            self._pre_assignment_statements, multi_line=False
        )
        return (
            f"{self.indent_spaces(indent_level)}"
            + f"{pre_assignments.basic09_text(indent_level)}"
            + (r" \ " if self._pre_assignment_statements else "")
        )

    def visit(self, vistor: "BasicConstructVisitor") -> None:
        return vistor.visit_statement(self)


class BasicArrayRef(AbstractBasicExpression):
    def __init__(self, var: "BasicVar", indices, is_str_expr: bool = False):
        super().__init__(is_str_expr=is_str_expr)
        self._var = BasicVar(f"arr_{var.name()}", is_str_expr=is_str_expr)
        self._indices = indices

    @property
    def var(self):
        return self._var

    @property
    def indices(self):
        return self._indices

    def basic09_text(self, indent_level: int) -> str:
        return (
            f"{self._var.basic09_text(indent_level)}"
            f"{self._indices.basic09_text(indent_level)}"
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_array_ref(self)
        for index in self._indices.exp_list:
            index.visit(visitor)


class BasicAssignment(AbstractBasicStatement):
    def __init__(
        self, var: "BasicVar", exp: AbstractBasicExpression, let_kw: bool = False
    ):
        super().__init__()
        self._let_kw: bool = let_kw
        self._var: AbstractBasicExpression = var
        self._exp: BasicVar = exp

    @property
    def var(self) -> "BasicVar":
        return self._var

    @property
    def exp(self) -> AbstractBasicExpression:
        return self._exp

    def basic09_text(self, indent_level) -> str:
        if isinstance(self._exp, BasicFunctionalExpression):
            return (
                f"{super().basic09_text(indent_level)}"
                f"{self._exp.statement.basic09_text(indent_level)}"
            )

        prefix = "LET " if self._let_kw else ""

        return (
            f"{super().basic09_text(indent_level)}"
            f"{prefix}"
            f"{self._var.basic09_text(indent_level)} := "
            f"{self._exp.basic09_text(indent_level)}"
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        self._var.visit(visitor)
        self._exp.visit(visitor)


class BasicBinaryExpFragment:
    def __init__(
        self,
        op: "BasicOperator",
        exp2: AbstractBasicExpression,
    ):
        self._op: BasicOperator = op
        self._exp2: AbstractBasicExpression = exp2

    @property
    def op(self) -> "BasicOperator":
        return self._op

    @property
    def exp2(self) -> AbstractBasicExpression:
        return self._exp2


class BinaryExpressionException(Exception):
    pass


class BasicBinaryExp(AbstractBasicExpression):
    @classmethod
    def from_exp_op_and_fragments(
        cls,
        exp: "BasicBinaryExp",
        op: "BasicOperator",
        fragments: List[BasicBinaryExpFragment],
    ):
        ii = len(fragments) - 1
        if ii < 0:
            raise BinaryExpressionException()

        current_fragment = fragments[ii]
        while ii >= 1:
            prior_fragment = fragments[ii - 1]
            current_fragment = BasicBinaryExpFragment(
                prior_fragment.op,
                BasicBinaryExp(
                    prior_fragment.exp2,
                    current_fragment.op.basic09_text(0),
                    current_fragment.exp2,
                    is_str_expr=exp.is_str_expr,
                ),
            )
            ii = ii - 1
        return BasicBinaryExp(
            exp, current_fragment.op.basic09_text(0), current_fragment.exp2
        )

    def __init__(
        self,
        exp1: AbstractBasicExpression,
        op: "BasicOperator",
        exp2: AbstractBasicExpression,
        is_str_expr: bool = False,
    ):
        super().__init__(is_str_expr=True)
        self._exp1: AbstractBasicExpression = exp1
        self._op: BasicOperator = op
        self._exp2: AbstractBasicExpression = exp2

    def basic09_text(self, indent_level: int) -> str:
        if self._op in {"AND", "OR"}:
            return (
                f"L{self._op}({self._exp1.basic09_text(indent_level)}, "
                f"{self._exp2.basic09_text(indent_level)})"
            )
        else:
            return (
                f"{self._exp1.basic09_text(indent_level)} {self._op} "
                f"{self._exp2.basic09_text(indent_level)}"
            )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_exp(self)
        self._exp1.visit(visitor)
        self._exp2.visit(visitor)


class BasicBooleanBinaryExp(BasicBinaryExp):
    def basic09_text(self, indent_level: int) -> str:
        return (
            f"{self._exp1.basic09_text(indent_level)} {self._op} "
            f"{self._exp2.basic09_text(indent_level)}"
        )


class BasicComment(AbstractBasicConstruct):
    def __init__(self, comment):
        self._comment = comment

    def basic09_text(self, indent_level: int) -> str:
        return f"(*{self._comment} *)"

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)


class BasicExpressionList(AbstractBasicConstruct):
    def __init__(self, exp_list, parens=True):
        self._exp_list = exp_list
        self._parens = parens

    @property
    def exp_list(self):
        return self._exp_list

    def basic09_text(self, indent_level: int) -> str:
        exp_list_text = ", ".join(
            exp.basic09_text(indent_level) for exp in self._exp_list
        )
        if self._parens:
            return f"({exp_list_text})" if exp_list_text else ""
        return exp_list_text

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        for exp in self.exp_list:
            exp.visit(visitor)


class BasicRunCall(AbstractBasicStatement):
    def __init__(self, run_invocation: str, arguments: BasicExpressionList):
        super().__init__()
        self._run_invocation = run_invocation
        self._arguments = arguments

    def basic09_text(self, indent_level: int) -> str:
        return (
            f"{super().basic09_text(indent_level)}"
            f"{self._run_invocation}"
            f"{self._arguments.basic09_text(indent_level)}"
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        self._arguments.visit(visitor)


class BasicGoto(AbstractBasicStatement):
    def __init__(self, linenum: int, implicit: bool, is_gosub: bool = False):
        super().__init__()
        self._linenum: int = linenum
        self._implicit: bool = implicit
        self._is_gosub: bool = is_gosub

    @property
    def implicit(self) -> bool:
        return self._implicit

    @property
    def linenum(self) -> int:
        return self._linenum

    def basic09_text(self, indent_level: int) -> str:
        if self._is_gosub:
            return f"{super().basic09_text(indent_level)}GOSUB {self._linenum}"
        return (
            f"{self._linenum}"
            if self._implicit
            else f"{super().basic09_text(indent_level)}GOTO {self._linenum}"
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        visitor.visit_go_statement(self)


class BasicOnErrGoStatement(AbstractBasicStatement):
    linenum: int

    def __init__(self, linenum: int):
        super().__init__()
        self._linenum = linenum

    @property
    def linenum(self) -> int:
        return self._linenum

    def basic09_text(self, indent_level) -> str:
        return "ON ERROR GOTO 32700"

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        visitor.visit_go_statement(self)


class BasicOnBrkGoStatement(BasicOnErrGoStatement):
    pass


class BasicOnGoStatement(AbstractBasicStatement):
    def __init__(self, exp, linenums, is_gosub=False):
        super().__init__()
        self._exp = exp
        self._linenums = linenums
        self._is_gosub = is_gosub

    @property
    def linenums(self):
        return self._linenums

    def basic09_text(self, indent_level: int) -> str:
        if self._is_gosub:
            return (
                f"{super().basic09_text(indent_level)}"
                f"ON {self._exp.basic09_text(indent_level)} GOSUB "
                + ", ".join((str(linenum) for linenum in self.linenums))
            )
        return (
            f"{super().basic09_text(indent_level)}"
            f"ON {self._exp.basic09_text(indent_level)} GOTO "
            + ", ".join((str(linenum) for linenum in self.linenums))
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        visitor.visit_go_statement(self)
        self._exp.visit(visitor)


BasicGoStatements = Union[
    BasicGoto, BasicOnBrkGoStatement, BasicOnErrGoStatement, BasicOnGoStatement
]
BasicStatementsOrBasicGoto = Union["BasicStatements", BasicGoto]


class BasicIf(AbstractBasicStatement):
    def __init__(
        self, exp: AbstractBasicExpression, statements: BasicStatementsOrBasicGoto
    ):
        super().__init__()
        self._exp: AbstractBasicExpression = exp
        self._statements: BasicStatements = statements

    def basic09_text(self, indent_level: int) -> str:
        if isinstance(self._statements, BasicGoto) and self._statements.implicit:
            return (
                f"{super().basic09_text(indent_level)}"
                f"IF {self._exp.basic09_text(indent_level)} "
                f"THEN {self._statements.basic09_text(0)}"
            )
        else:
            return (
                f"{super().basic09_text(indent_level)}"
                f"IF {self._exp.basic09_text(indent_level)} THEN\n"
                f"{self._statements.basic09_text(indent_level + 1)}\n"
                f"ENDIF"
            )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        self._exp.visit(visitor)
        self._statements.visit(visitor)

    @property
    def exp(self) -> AbstractBasicExpression:
        return self._exp

    @property
    def statements(self) -> AbstractBasicExpression:
        return self._statements


class BasicIfElse(BasicIf):
    _else_if_statements: List[BasicIf]
    _else_statements: BasicStatementsOrBasicGoto

    def __init__(
        self,
        *,
        if_exp: AbstractBasicExpression,
        then_statements: BasicStatementsOrBasicGoto,
        else_if_statements: List[BasicIf],
        else_statements: Union[BasicStatementsOrBasicGoto, None] = None,
    ):
        super().__init__(if_exp, then_statements)
        self._else_if_statements = else_if_statements
        self._else_statements = else_statements

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        super().visit(visitor)
        statement: BasicIf
        for statement in self._else_if_statements:
            statement.visit(visitor)
        if self._else_statements is not None:
            self._else_statements.visit(visitor)

    def basic09_text(self, indent_level: int) -> str:
        if self._else_if_statements:
            all_if_statements = [self] + self._else_if_statements

            exit_statements: str = "\n".join(
                (
                    f"{self.indent_spaces(indent_level + 1)}EXITIF {ifstmnt.exp.basic09_text(0)} THEN\n"
                    f"{ifstmnt.statements.basic09_text(indent_level + 2)}\n"
                    f"{self.indent_spaces(indent_level + 1)}ENDEXIT"
                    for ifstmnt in all_if_statements
                )
            )
            else_suffix = (
                ""
                if self._else_statements is None
                else f"{self.indent_spaces(indent_level + 1)}EXITIF TRUE THEN\n"
                f"{self._else_statements.basic09_text(indent_level + 2)}\n"
                f"{self.indent_spaces(indent_level + 1)}ENDEXIT\n"
            )
            return (
                f"{self.indent_spaces(indent_level)}LOOP\n"
                f"{exit_statements}\n"
                f"{else_suffix}"
                f"{self.indent_spaces(indent_level)}ENDLOOP"
            )

        else_suffix = (
            ""
            if self._else_statements is None
            else f"{self.indent_spaces(indent_level)}ELSE\n"
            f"{self._else_statements.basic09_text(indent_level + 1)}\n"
        )
        suffix = else_suffix + f"{self.indent_spaces(indent_level)}ENDIF"
        return (
            f"{self.indent_spaces(indent_level)}IF {self.exp.basic09_text(0)} THEN\n"
            f"{self.statements.basic09_text(indent_level + 1)}\n"
        ) + suffix


class BasicLine(AbstractBasicConstruct):
    def __init__(self, num: Union[int, None], statements: "BasicStatement"):
        self._num: Union[int, None] = num
        self._statements: BasicStatement = statements
        self._is_referenced: bool = True

    @property
    def num(self) -> Union[int, None]:
        return self._num

    @property
    def is_referenced(self) -> bool:
        return self._is_referenced

    def set_is_referenced(self, val: bool):
        self._is_referenced = val

    def basic09_text(self, indent_level) -> str:
        if self._is_referenced and self._num is not None:
            return f"{self._num} " f"{self._statements.basic09_text(indent_level)}"
        return f"{self._statements.basic09_text(indent_level)}"

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_line(self)
        self._statements.visit(visitor)


class BasicLiteral(AbstractBasicExpression):
    def __init__(self, literal, is_str_expr=False):
        super().__init__(is_str_expr=is_str_expr)
        self._literal = literal

    @property
    def literal(self):
        return self._literal

    @literal.setter
    def literal(self, val):
        self._literal = val
        self._is_str_expr = isinstance(val, str)

    def basic09_text(self, indent_level: int) -> str:
        return (
            f'"{self._literal}"' if type(self._literal) is str else f"{self._literal}"
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_exp(self)


class HexLiteral(AbstractBasicExpression):
    def __init__(self, literal, *, is_float=False):
        super().__init__(is_str_expr=False)
        self._literal: int = int(f"0x{literal}", 16)
        self._is_float: bool = is_float

    @property
    def literal(self):
        return self._literal

    def basic09_text(self, indent_level: int) -> str:
        return (
            (
                f"float(${hex(self._literal)[2:].upper()})"
                if self._literal < 0x8000
                else f"{self._literal}.0"
            )
            if self._is_float
            else (
                f"${hex(self._literal)[2:].upper()}"
                if self._literal < 0x8000
                else f"{self._literal}"
            )
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_exp(self)


class BasicOperator(AbstractBasicConstruct):
    def __init__(self, operator: str):
        self._operator: str = operator

    @property
    def operator(self) -> str:
        return self._operator

    def basic09_text(self, indent_level: int) -> str:
        return self._operator


class BasicOpExp(AbstractBasicConstruct):
    def __init__(self, operator, exp):
        self._operator = operator
        self._exp = exp

    @property
    def operator(self):
        return self._operator

    @property
    def exp(self):
        return self._exp

    def basic09_text(self, indent_level: int) -> str:
        if self.operator == "NOT":
            return f"L{self.operator}({self.exp.basic09_text(indent_level)})"
        else:
            return f"{self.operator} {self.exp.basic09_text(indent_level)}"

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_exp(self)
        self._exp.visit(visitor)


class BasicBooleanOpExp(BasicOpExp):
    def basic09_text(self, indent_level: int) -> str:
        if self.operator == "NOT":
            return f"{self.operator}({self.exp.basic09_text(indent_level)})"
        else:
            return f"{self.operator} {self.exp.basic09_text(indent_level)}"


class BasicParenExp(AbstractBasicExpression):
    def __init__(self, exp: AbstractBasicExpression):
        self._exp = exp
        self._is_str_expr = exp.is_str_expr

    def basic09_text(self, indent_level: int) -> str:
        return f"({self._exp.basic09_text(indent_level)})"

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_exp(self)
        self._exp.visit(visitor)


class BasicBooleanParenExp(BasicParenExp):
    def basic09_text(self, indent_level: int) -> str:
        return f"({self._exp.basic09_text(indent_level)})"


class BasicStatement(AbstractBasicStatement):
    def __init__(self, basic_construct):
        super().__init__()
        self._basic_construct = basic_construct

    def basic09_text(self, indent_level: int) -> str:
        return super().basic09_text(indent_level) + self._basic_construct.basic09_text(
            indent_level
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)


class Basic09CodeStatement(AbstractBasicStatement):
    def __init__(self, basic09_code):
        super().__init__()
        self._basic09_code = basic09_code

    def basic09_text(self, indent_level: int) -> str:
        return super().basic09_text(indent_level) + self._basic09_code

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)


class BasicStatements(AbstractBasicStatement):
    def __init__(self, statements: List[BasicStatement], multi_line: bool = True):
        super().__init__()
        self._statements = list(statements)
        self._multi_line: bool = multi_line

    @property
    def statements(self) -> List[BasicStatement]:
        return self._statements

    def set_statements(self, statements: List[BasicStatement]) -> None:
        self._statements = statements

    def basic09_text(self, indent_level: int, pre_indent: bool = True) -> str:
        joiner: str = "\n" if self._multi_line else r" \ "
        net_indent_level: int = indent_level if self._multi_line else 0

        prefix = (
            self.indent_spaces(indent_level)
            if pre_indent
            and self._statements
            and isinstance(self._statements[0], BasicStatements)
            else ""
        )

        return prefix + joiner.join(
            statement.basic09_text(indent_level, pre_indent=False)
            if isinstance(statement, BasicStatements)
            else statement.basic09_text(net_indent_level)
            for statement in self._statements
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        for idx, statement in enumerate(self.statements):
            statement.visit(visitor)
            if isinstance(statement, BasicPrintStatement):
                self.statements[idx] = visitor.visit_print_statement(statement)
            elif isinstance(statement, BasicReadStatement):
                self.statements[idx] = visitor.visit_read_statement(statement)
            elif isinstance(statement, BasicInputStatement):
                self.statements[idx] = visitor.visit_input_statement(statement)


class BasicVar(AbstractBasicExpression):
    def __init__(self, name: str, is_str_expr: bool = False):
        super().__init__(is_str_expr=is_str_expr)
        self._name: str = name

    def name(self) -> str:
        return self._name

    def basic09_text(self, indent_level) -> str:
        return self._name

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_var(self)


class BasicPrintStatement(AbstractBasicStatement):
    def __init__(self, print_args: "BasicPrintArgs"):
        super().__init__()
        self._print_args: BasicPrintArgs = print_args

    @property
    def print_args(self) -> "BasicPrintArgs":
        return self._print_args

    def basic09_text(self, indent_level: int) -> str:
        return (
            super().basic09_text(indent_level)
            + f"PRINT {self._print_args.basic09_text(indent_level)}"
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        self._print_args.visit(visitor)


class BasicPrintControl(AbstractBasicConstruct):
    def __init__(self, control_char):
        self._control_char = control_char

    def basic09_text(self, indent_level: int) -> str:
        return self._control_char


class BasicPrintArgs(AbstractBasicConstruct):
    def __init__(self, args):
        self._args = args

    @property
    def args(self):
        return self._args

    @args.setter
    def set_args(self, args):
        self._args = args

    def basic09_text(self, indent_level: int) -> str:
        processed_args = []

        for ii, arg in enumerate(self.args):
            is_control = isinstance(arg, BasicPrintControl)
            if is_control and (
                (ii <= 0) or isinstance(self.args[ii - 1], BasicPrintControl)
            ):
                processed_args.append('""')
            if not is_control and (
                (ii > 0) and not isinstance(self.args[ii - 1], BasicPrintControl)
            ):
                processed_args.append("; ")

            processed_args.append(arg.basic09_text(indent_level))
            if (ii < len(self.args) - 1) and is_control:
                processed_args.append(" ")

        return "".join(processed_args)

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        for arg in self._args:
            arg.visit(visitor)


class Basic2ParamStatement(AbstractBasicStatement):
    def __init__(self, exp1: AbstractBasicExpression, exp2: AbstractBasicExpression):
        super().__init__()
        self._exp1: AbstractBasicExpression = exp1
        self._exp2: AbstractBasicExpression = exp2

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        self._exp1.visit(visitor)
        self._exp2.visit(visitor)


class BasicSound(Basic2ParamStatement):
    def basic09_text(self, indent_level: int):
        return (
            f"{super().basic09_text(indent_level)}"
            f"RUN ecb_sound({self._exp1.basic09_text(indent_level)}, "
            f"{self._exp2.basic09_text(indent_level)}, 31.0, FIX(play.octo))"
        )


class BasicPoke(Basic2ParamStatement):
    def basic09_text(self, indent_level: int) -> str:
        known_loc: bool = isinstance(self._exp1, BasicLiteral) or isinstance(
            self._exp1, HexLiteral
        )
        if known_loc and self._exp1.literal == 65496:
            return f"{super().basic09_text(indent_level)}play.octo := 0"
        elif known_loc and self._exp1.literal == 65497:
            return f"{super().basic09_text(indent_level)}play.octo := 1"
        else:
            return (
                f"{super().basic09_text(indent_level)}"
                f"POKE {self._exp1.basic09_text(indent_level)}, "
                f"{self._exp2.basic09_text(indent_level)}"
            )


class BasicCls(AbstractBasicStatement):
    def __init__(self, exp=None):
        super().__init__()
        self._exp = exp

    def basic09_text(self, indent_level: int) -> str:
        return super().basic09_text(indent_level) + (
            f"RUN ecb_cls({self._exp.basic09_text(indent_level)}, display)"
            if self._exp
            else "RUN ecb_cls(1.0, display)"
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        if self._exp:
            self._exp.visit(visitor)


class BasicFunctionCall(AbstractBasicExpression):
    def __init__(self, func, args, is_str_expr=False):
        super().__init__(is_str_expr=is_str_expr)
        self._func = func
        self._args = args

    def basic09_text(self, indent_level: int) -> str:
        return f"{self._func}" f"{self._args.basic09_text(indent_level)}"


class BasicDataStatement(AbstractBasicStatement):
    def __init__(self, exp_list):
        super().__init__()
        self._exp_list = exp_list

    @property
    def exp_list(self):
        return self._exp_list

    def basic09_text(self, indent_level: int) -> str:
        return (
            f"{super().basic09_text(indent_level)}DATA "
            f"{self._exp_list.basic09_text(indent_level)}"
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        visitor.visit_data_statement(self)


class BasicKeywordStatement(AbstractBasicStatement):
    def __init__(self, keyword):
        super().__init__()
        self._keyword = keyword

    def basic09_text(self, indent_level: int) -> str:
        return f"{super().basic09_text(indent_level)}{self._keyword}"

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)


class BasicForStatement(AbstractBasicStatement):
    def __init__(self, var, start_exp, end_exp, step_exp=None):
        super().__init__()
        self._var = var
        self._start_exp = start_exp
        self._end_exp = end_exp
        self._step_exp = step_exp

    @property
    def var(self):
        return self._var

    def basic09_text(self, indent_level: int) -> str:
        return (
            f"{super().basic09_text(indent_level - 1)}FOR "
            f"{self._var.basic09_text(indent_level)} = "
            f"{self._start_exp.basic09_text(indent_level)} TO "
            f"{self._end_exp.basic09_text(indent_level)}"
            + (
                f" STEP {self._step_exp.basic09_text(indent_level)}"
                if self._step_exp
                else ""
            )
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        visitor.visit_for_statement(self)
        self._var.visit(visitor)
        self._start_exp.visit(visitor)
        self._end_exp.visit(visitor)
        if self._step_exp:
            self._step_exp.visit(visitor)


class BasicNextStatement(AbstractBasicStatement):
    def __init__(self, var_list):
        super().__init__()
        self._var_list = var_list

    @property
    def var_list(self):
        return self._var_list

    def basic09_text(self, indent_level: int) -> str:
        vlist = (
            [f"NEXT {var.basic09_text(indent_level)}" for var in self.var_list.exp_list]
            if self.var_list.exp_list
            else ["NEXT"]
        )
        return super().basic09_text(indent_level) + r" \ ".join(vlist)

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_statement(self)
        visitor.visit_next_statement(self)
        for var in self.var_list.exp_list:
            var.visit(visitor)


class BasicFunctionalExpression(AbstractBasicExpression):
    def __init__(self, func, args, is_str_expr=False):
        super().__init__(is_str_expr=is_str_expr)
        self._func = func
        self._args = args
        self._var = None
        self._statement = None

    @property
    def var(self):
        return self._var

    def set_var(self, var):
        self._var = var
        self._statement = BasicFunctionCall(
            self._func, BasicExpressionList(self._args.exp_list + [var])
        )

    @property
    def statement(self):
        return self._statement

    def basic09_text(self, indent_level: int) -> str:
        return self._var.basic09_text(indent_level) if self._var else ""

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        if self._var:
            self._statement.visit(visitor)
            self._var.visit(visitor)
        else:
            for arg in self._args.exp_list:
                arg.visit(visitor)

            visitor.visit_exp(self)


class BasicJoystkExpression(BasicFunctionalExpression):
    def __init__(self, args):
        super().__init__("RUN ecb_joystk", args)
        self._args = args

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        super().visit(visitor)
        visitor.visit_joystk(self)


class BasicDimStatement(AbstractBasicStatement):
    _default_str_storage: int
    _dim_vars: List["BasicArrayRef | BasicVar"]

    def __init__(self, dim_vars: List["BasicArrayRef | BasicVar"]):
        super().__init__()
        self._default_str_storage = DEFAULT_STR_STORAGE
        self._dim_vars = [
            var
            if isinstance(var, BasicVar)
            else BasicArrayRef(
                BasicVar(var.var.name()[4:], is_str_expr=var.is_str_expr),
                BasicExpressionList(
                    [
                        BasicLiteral(index.literal + 1)
                        if isinstance(index, BasicLiteral)
                        else HexLiteral(hex(index.literal + 1)[2:])
                        for index in var.indices.exp_list
                    ]
                ),
                is_str_expr=var.is_str_expr,
            )
            for var in dim_vars
        ]

    @property
    def default_str_storage(self):
        return self._default_str_storage

    @property
    def dim_vars(self) -> List["BasicArrayRef | BasicVar"]:
        return self._dim_vars

    @default_str_storage.setter
    def default_str_storage(self, val):
        self._default_str_storage = val

    def init_text_for_var(self, dim_var):
        for_statements = (
            BasicForStatement(
                BasicVar(f"tmp_{ii + 1}"),
                BasicLiteral(0),
                BasicLiteral(index.literal - 1)
                if isinstance(index, BasicLiteral)
                else HexLiteral(hex(index.literal - 1)[2:]),
            )
            for ii, index in enumerate(dim_var.indices.exp_list)
        )
        next_statements = (
            BasicNextStatement(BasicExpressionList([BasicVar(f"tmp_{ii}")]))
            for ii in range(len(dim_var.indices.exp_list), 0, -1)
        )
        init_val = BasicLiteral(
            "" if dim_var.is_str_expr else 0, is_str_expr=dim_var.is_str_expr
        )
        var = BasicVar(dim_var._var.name()[4:], dim_var._var.is_str_expr)

        assignment = BasicAssignment(
            BasicArrayRef(
                var,
                BasicExpressionList(
                    (
                        BasicVar(f"tmp_{ii}")
                        for ii in range(1, len(dim_var.indices.exp_list) + 1)
                    )
                ),
            ),
            init_val,
        )

        return BasicStatements(
            chain(for_statements, (assignment,), next_statements),
            multi_line=False,
        ).basic09_text(0)

    def basic09_text(self, indent_level: int) -> str:
        str_vars: List[BasicArrayRef | BasicVar] = [
            var
            for var in self._dim_vars
            if (isinstance(var, BasicVar) and var.name().endswith("$"))
            or (isinstance(var, BasicArrayRef) and var.var.name().endswith("$"))
        ]
        non_str_vars: List[BasicArrayRef | BasicVar] = [
            var
            for var in self._dim_vars
            if not (
                (isinstance(var, BasicVar) and var.name().endswith("$"))
                or (isinstance(var, BasicArrayRef) and var.var.name().endswith("$"))
            )
        ]

        str_vars_text: str = (
            self._basic09_text(
                str_vars,
                ""
                if self.default_str_storage == DEFAULT_STR_STORAGE
                else f": STRING[{self._default_str_storage}]",
                indent_level,
            )
            + ("\n" if non_str_vars else "")
            if str_vars
            else ""
        )
        non_str_vars_text: str = (
            self._basic09_text(non_str_vars, "", indent_level) if non_str_vars else ""
        )

        return str_vars_text + non_str_vars_text

    def _basic09_text(
        self, dim_vars: List["BasicArrayRef | BasicVar"], suffix: str, indent_level: int
    ):
        dim_var_text: str = ", ".join(
            (dim_var.basic09_text(indent_level) for dim_var in dim_vars)
        )
        init_text = "\n".join(
            (
                self.init_text_for_var(dim_var)
                for dim_var in dim_vars
                if isinstance(dim_var, BasicArrayRef)
            )
        )
        init_text = "\n" + init_text if init_text else ""

        return (
            f"{super().basic09_text(indent_level)}"
            f"DIM {dim_var_text}" + suffix + init_text
        )

    @property
    def scalar_str_vars(self) -> List[str]:
        """Returns list of scalar string variables"""
        return [
            var.name()
            for var in self._dim_vars
            if isinstance(var, BasicVar) and var.name().endswith("$")
        ]


class BasicReadStatement(BasicStatement):
    def __init__(self, rhs_list):
        super().__init__(None)
        self._rhs_list = rhs_list

    @property
    def rhs_list(self):
        return self._rhs_list

    def basic09_text(self, indent_level: int) -> str:
        return (
            self.indent_spaces(indent_level)
            + "READ "
            + ", ".join(rhs.basic09_text(indent_level) for rhs in self._rhs_list)
        )


class BasicInputStatement(BasicStatement):
    def __init__(self, message, rhs_list):
        self._message = message
        self._rhs_list = rhs_list

    def basic09_text(self, indent_level: int) -> str:
        prefix = (
            self.indent_spaces(indent_level)
            + "INPUT "
            + self._message.basic09_text(indent_level)
            + ", "
            if self._message
            else "INPUT "
        )
        return prefix + ", ".join(
            (rhs.basic09_text(indent_level) for rhs in self._rhs_list)
        )


class BasicVarptrExpression(AbstractBasicExpression):
    def __init__(self, var):
        super().__init__()
        self._var = var

    def basic09_text(self, indent_level: int) -> str:
        return (
            f"{self.indent_spaces(indent_level)}"
            f"ADDR({self._var.basic09_text(indent_level)})"
        )

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_exp(self)
        visitor.visit_exp(self._var)


class BasicWidthStatement(AbstractBasicStatement):
    def __init__(self, expr):
        super().__init__()
        self._expr = expr

    def basic09_text(self, indent_level: int) -> str:
        return (
            f"run _ecb_width("
            f"{self._expr.basic09_text(indent_level=indent_level)}, "
            f"display)"
        )


class BasicCircleStatement(BasicRunCall):
    _expr_x: AbstractBasicExpression
    _expr_y: AbstractBasicExpression
    _expr_r: AbstractBasicExpression
    _expr_color: AbstractBasicExpression
    _hires: bool

    def __init__(
        self,
        expr_x: AbstractBasicExpression,
        expr_y: AbstractBasicExpression,
        expr_r: AbstractBasicExpression,
        *,
        expr_color: AbstractBasicConstruct = None,
        hires: bool = True,
    ):
        super().__init__(
            f"run ecb_{'h' if hires else ''}circle",
            BasicExpressionList(
                [
                    expr_x,
                    expr_y,
                    expr_r,
                    expr_color
                    if expr_color is not None
                    else BasicRunCall(
                        "float", BasicExpressionList([BasicVar("display.hfore")])
                    ),
                    BasicLiteral(1.0),
                    BasicVar("display"),
                ]
            ),
        )
        self._expr_x = expr_x
        self._expr_y = expr_y
        self._expr_r = expr_r
        self._hires = hires
        self._expr_color = expr_color

    @property
    def hires(self) -> bool:
        return self._hires

    @property
    def expr_x(self) -> AbstractBasicExpression:
        return self._expr_x

    @property
    def expr_y(self) -> AbstractBasicExpression:
        return self._expr_y

    @property
    def expr_r(self) -> AbstractBasicExpression:
        return self._expr_r

    @property
    def expr_color(self) -> AbstractBasicExpression:
        return self._expr_color


class BasicEllipseStatement(BasicRunCall):
    _circle: BasicCircleStatement
    _expr_ratio: AbstractBasicExpression

    def __init__(
        self,
        circle: BasicCircleStatement,
        expr_ratio: AbstractBasicExpression,
    ):
        super().__init__(
            f"run ecb_{'h' if circle.hires else ''}circle",
            BasicExpressionList(
                [
                    circle.expr_x,
                    circle.expr_y,
                    circle.expr_r,
                    circle.expr_color
                    if circle.expr_color is not None
                    else BasicRunCall(
                        "float", BasicExpressionList([BasicVar("display.hfore")])
                    ),
                    expr_ratio,
                    BasicVar("display"),
                ]
            ),
        )
        self._circle = circle
        self._expr_ratio = expr_ratio

    @property
    def circle(self) -> BasicCircleStatement:
        return self._circle

    @property
    def expr_ratio(self) -> AbstractBasicExpression:
        return self._expr_ratio


class BasicArcStatement(BasicRunCall):
    _ellipse: BasicEllipseStatement
    _expr_start: AbstractBasicExpression
    _expr_end: AbstractBasicExpression

    def __init__(
        self,
        ellipse: BasicEllipseStatement,
        expr_start: AbstractBasicExpression,
        expr_end: AbstractBasicExpression,
    ):
        super().__init__(
            f"run ecb_{'h' if ellipse.circle.hires else ''}arc",
            BasicExpressionList(
                [
                    ellipse.circle.expr_x,
                    ellipse.circle.expr_y,
                    ellipse.circle.expr_r,
                    ellipse.circle.expr_color
                    if ellipse.circle.expr_color is not None
                    else BasicRunCall(
                        "float", BasicExpressionList([BasicVar("display.hfore")])
                    ),
                    ellipse.expr_ratio,
                    expr_start,
                    expr_end,
                    BasicVar("display"),
                ]
            ),
        )
        self._ellipse = ellipse
        self._expr_start = expr_start
        self._expr_end = expr_end

    @property
    def ellipse(self) -> BasicEllipseStatement:
        return self._ellipse

    @property
    def expr_start(self) -> AbstractBasicExpression:
        return self._expr_start

    @property
    def expr_end(self) -> AbstractBasicExpression:
        return self._expr_end


PsetOrPreset = Literal["PSET", "PRESET"]
LineType = Literal["L", "B", "BF"]


class Coordinates:
    _x: AbstractBasicExpression
    _y: AbstractBasicExpression

    def __init__(self, x: AbstractBasicExpression, y: AbstractBasicExpression):
        self._x = x
        self._y = y

    @property
    def x(self) -> AbstractBasicExpression:
        return self._x

    @property
    def y(self) -> AbstractBasicExpression:
        return self._y


class Coordinates3(Coordinates):
    _z: AbstractBasicExpression

    def __init__(
        self,
        x: AbstractBasicExpression,
        y: AbstractBasicExpression,
        z: AbstractBasicExpression,
    ):
        super().__init__(x=x, y=y)
        self._z = z

    @property
    def z(self) -> AbstractBasicExpression:
        return self._z


class HLineStatement(BasicRunCall):
    def __init__(
        self,
        *,
        source: Coordinates,
        destination: Coordinates,
        mode: PsetOrPreset,
        line_type: LineType,
    ):
        super().__init__(
            "run ecb_hline",
            BasicExpressionList(
                [
                    BasicLiteral("d" if source else "r"),
                    source.x if source else BasicLiteral(0.0),
                    source.y if source else BasicLiteral(0.0),
                    destination.x,
                    destination.y,
                    BasicLiteral(mode),
                    BasicLiteral(line_type),
                    BasicVar("display"),
                ]
            ),
        )

    def basic09_text(self, indent_level: int) -> str:
        return super().basic09_text(indent_level)


class LineSuffix:
    def __init__(
        self,
        *,
        destination: Coordinates,
        pset_or_preset: PsetOrPreset,
        line_type: LineType,
    ):
        self._destination: Coordinates = destination
        self._pset_or_preset: PsetOrPreset = pset_or_preset
        self._line_type: LineType = line_type

    @property
    def destination(self) -> Coordinates:
        return self._destination

    @property
    def pset_or_preset(self) -> PsetOrPreset:
        return self._pset_or_preset

    @property
    def line_type(self) -> LineType:
        return self._line_type


class BasicHbuffStatement(BasicRunCall):
    def __init__(
        self, *, buffer: AbstractBasicExpression, size: AbstractBasicExpression
    ):
        super().__init__(
            "run _ecb_hbuff",
            BasicExpressionList(
                [
                    buffer,
                    size,
                    BasicVar("pid"),
                    BasicVar("display"),
                ]
            ),
        )


PutDrawAction = Literal["AND", "NOT", "OR", "PRESET", "PSET", "XOR"]
