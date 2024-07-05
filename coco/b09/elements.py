from abc import ABC, abstractmethod
from itertools import chain


class AbstractBasicConstruct(ABC):
    def indent_spaces(self, indent_level):
        return "  " * indent_level

    @abstractmethod
    def basic09_text(self, indent_level):
        """Return the Basic09 text that represents this construct"""
        pass

    @property
    def is_expr(self):
        return False

    @property
    def is_str_expr(self):
        return False

    def visit(self, visitor):
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

    def basic09_text(self, indent_level):
        pre_assignments = BasicStatements(
            self._pre_assignment_statements, multi_line=False
        )
        return (
            f"{self.indent_spaces(indent_level)}"
            + f"{pre_assignments.basic09_text(indent_level)}"
            + (r" \ " if self._pre_assignment_statements else "")
        )


class BasicArrayRef(AbstractBasicExpression):
    def __init__(self, var, indices, is_str_expr=False):
        super().__init__(is_str_expr=is_str_expr)
        self._var = BasicVar(f"arr_{var.name()}", is_str_expr=is_str_expr)
        self._indices = indices

    @property
    def var(self):
        return self._var

    @property
    def indices(self):
        return self._indices

    def basic09_text(self, indent_level):
        return (
            f"{self._var.basic09_text(indent_level)}"
            f"{self._indices.basic09_text(indent_level)}"
        )

    def visit(self, visitor):
        visitor.visit_array_ref(self)
        for index in self._indices.exp_list:
            index.visit(visitor)


class BasicAssignment(AbstractBasicStatement):
    def __init__(self, var, exp, let_kw=False):
        super().__init__()
        self._let_kw = let_kw
        self._var = var
        self._exp = exp

    @property
    def var(self):
        return self._var

    @property
    def exp(self):
        return self._exp

    def basic09_text(self, indent_level):
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

    def visit(self, visitor):
        visitor.visit_statement(self)
        self._var.visit(visitor)
        self._exp.visit(visitor)


class BasicBinaryExp(AbstractBasicExpression):
    def __init__(self, exp1, op, exp2, is_str_expr=False):
        super().__init__(is_str_expr=True)
        self._exp1 = exp1
        self._op = op
        self._exp2 = exp2

    def basic09_text(self, indent_level):
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

    def visit(self, visitor):
        visitor.visit_exp(self)
        self._exp1.visit(visitor)
        self._exp2.visit(visitor)


class BasicBooleanBinaryExp(BasicBinaryExp):
    def basic09_text(self, indent_level):
        return (
            f"{self._exp1.basic09_text(indent_level)} {self._op} "
            f"{self._exp2.basic09_text(indent_level)}"
        )


class BasicComment(AbstractBasicConstruct):
    def __init__(self, comment):
        self._comment = comment

    def basic09_text(self, indent_level):
        return f"(*{self._comment} *)"

    def visit(self, visitor):
        visitor.visit_statement(self)


class BasicExpressionList(AbstractBasicConstruct):
    def __init__(self, exp_list, parens=True):
        self._exp_list = exp_list
        self._parens = parens

    @property
    def exp_list(self):
        return self._exp_list

    def basic09_text(self, indent_level):
        exp_list_text = ", ".join(
            exp.basic09_text(indent_level) for exp in self._exp_list
        )
        if self._parens:
            return f"({exp_list_text})" if exp_list_text else ""
        return exp_list_text

    def visit(self, visitor):
        for exp in self.exp_list:
            exp.visit(visitor)


class BasicRunCall(AbstractBasicStatement):
    def __init__(self, run_invocation, arguments):
        super().__init__()
        self._run_invocation = run_invocation
        self._arguments = arguments

    def basic09_text(self, indent_level):
        return (
            f"{super().basic09_text(indent_level)}"
            f"{self._run_invocation}"
            f"{self._arguments.basic09_text(indent_level)}"
        )

    def visit(self, visitor):
        visitor.visit_statement(self)
        self._arguments.visit(visitor)


class BasicGoto(AbstractBasicStatement):
    def __init__(self, linenum, implicit, is_gosub=False):
        super().__init__()
        self._linenum = linenum
        self._implicit = implicit
        self._is_gosub = is_gosub

    @property
    def implicit(self):
        return self._implicit

    @property
    def linenum(self):
        return self._linenum

    def basic09_text(self, indent_level):
        if self._is_gosub:
            return f"{super().basic09_text(indent_level)}GOSUB {self._linenum}"
        return (
            f"{self._linenum}"
            if self._implicit
            else f"{super().basic09_text(indent_level)}GOTO {self._linenum}"
        )

    def visit(self, visitor):
        visitor.visit_statement(self)
        visitor.visit_go_statement(self)


class BasicOnGoStatement(AbstractBasicStatement):
    def __init__(self, exp, linenums, is_gosub=False):
        super().__init__()
        self._exp = exp
        self._linenums = linenums
        self._is_gosub = is_gosub

    @property
    def linenums(self):
        return self._linenums

    def basic09_text(self, indent_level):
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

    def visit(self, visitor):
        visitor.visit_statement(self)
        visitor.visit_go_statement(self)
        self._exp.visit(visitor)


class BasicIf(AbstractBasicStatement):
    def __init__(self, exp, statements):
        super().__init__()
        self._exp = exp
        self._statements = statements

    def basic09_text(self, indent_level):
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

    def visit(self, visitor):
        visitor.visit_statement(self)
        self._exp.visit(visitor)
        self._statements.visit(visitor)


class BasicLine(AbstractBasicConstruct):
    def __init__(self, num, statements):
        self._num = num
        self._statements = statements
        self._is_referenced = True

    @property
    def num(self):
        return self._num

    @property
    def is_referenced(self):
        return self._is_referenced

    def set_is_referenced(self, val):
        self._is_referenced = val

    def basic09_text(self, indent_level):
        if self._is_referenced and self._num is not None:
            return f"{self._num} " f"{self._statements.basic09_text(indent_level)}"
        return f"{self._statements.basic09_text(indent_level)}"

    def visit(self, visitor):
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

    def basic09_text(self, indent_level):
        return (
            f'"{self._literal}"' if type(self._literal) is str else f"{self._literal}"
        )

    def visit(self, visitor):
        visitor.visit_exp(self)


class HexLiteral(AbstractBasicExpression):
    def __init__(self, literal):
        super().__init__(is_str_expr=False)
        self._literal = int(f"0x{literal}", 16)

    @property
    def literal(self):
        return self._literal

    def basic09_text(self, indent_level):
        return (
            f"${hex(self._literal)[2:].upper()}"
            if self._literal < 0x8000
            else f"{self._literal}"
        )

    def visit(self, visitor):
        visitor.visit_exp(self)


class BasicOperator(AbstractBasicConstruct):
    def __init__(self, operator):
        self._operator = operator

    @property
    def operator(self):
        return self._operator

    def basic09_text(self, indent_level):
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

    def basic09_text(self, indent_level):
        if self.operator == "NOT":
            return f"L{self.operator}({self.exp.basic09_text(indent_level)})"
        else:
            return f"{self.operator} {self.exp.basic09_text(indent_level)}"

    def visit(self, visitor):
        visitor.visit_exp(self)
        self._exp.visit(visitor)


class BasicBooleanOpExp(BasicOpExp):
    def basic09_text(self, indent_level):
        if self.operator == "NOT":
            return f"{self.operator}({self.exp.basic09_text(indent_level)})"
        else:
            return f"{self.operator} {self.exp.basic09_text(indent_level)}"


class BasicParenExp(AbstractBasicExpression):
    def __init__(self, exp):
        self._exp = exp

    def basic09_text(self, indent_level):
        return f"({self._exp.basic09_text(indent_level)})"

    def visit(self, visitor):
        visitor.visit_exp(self)
        self._exp.visit(visitor)


class BasicBooleanParenExp(BasicParenExp):
    def basic09_text(self, indent_level):
        return f"({self._exp.basic09_text(indent_level)})"


class BasicStatement(AbstractBasicStatement):
    def __init__(self, basic_construct):
        super().__init__()
        self._basic_construct = basic_construct

    def basic09_text(self, indent_level):
        return super().basic09_text(indent_level) + self._basic_construct.basic09_text(
            indent_level
        )

    def visit(self, visitor):
        visitor.visit_statement(self)


class Basic09CodeStatement(AbstractBasicStatement):
    def __init__(self, basic09_code):
        super().__init__()
        self._basic09_code = basic09_code

    def basic09_text(self, indent_level):
        return super().basic09_text(indent_level) + self._basic09_code

    def visit(self, visitor):
        visitor.visit_statement(self)


class BasicStatements(AbstractBasicStatement):
    def __init__(self, statements, multi_line=True):
        super().__init__()
        self._statements = list(statements)
        self._multi_line = multi_line

    @property
    def statements(self):
        return self._statements

    def set_statements(self, statements):
        self._statements = statements

    def basic09_text(self, indent_level, pre_indent=True):
        joiner = "\n" if self._multi_line else r" \ "
        net_indent_level = indent_level if self._multi_line else 0

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

    def visit(self, visitor):
        for idx, statement in enumerate(self.statements):
            statement.visit(visitor)
            if isinstance(statement, BasicPrintStatement):
                self.statements[idx] = visitor.visit_print_statement(statement)
            elif isinstance(statement, BasicReadStatement):
                self.statements[idx] = visitor.visit_read_statement(statement)
            elif isinstance(statement, BasicInputStatement):
                self.statements[idx] = visitor.visit_input_statement(statement)


class BasicVar(AbstractBasicExpression):
    def __init__(self, name, is_str_expr=False):
        super().__init__(is_str_expr=is_str_expr)
        self._name = name

    def name(self):
        return self._name

    def basic09_text(self, indent_level):
        return self._name

    def visit(self, visitor):
        visitor.visit_var(self)


class BasicPrintStatement(AbstractBasicStatement):
    def __init__(self, print_args):
        super().__init__()
        self._print_args = print_args

    @property
    def print_args(self):
        return self._print_args

    def basic09_text(self, indent_level):
        return (
            super().basic09_text(indent_level)
            + f"PRINT {self._print_args.basic09_text(indent_level)}"
        )

    def visit(self, visitor):
        visitor.visit_statement(self)
        self._print_args.visit(visitor)


class BasicPrintControl(AbstractBasicConstruct):
    def __init__(self, control_char):
        self._control_char = control_char

    def basic09_text(self, indent_level):
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

    def basic09_text(self, indent_level):
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

    def visit(self, visitor):
        for arg in self._args:
            arg.visit(visitor)


class Basic2ParamStatement(AbstractBasicStatement):
    def __init__(self, exp1, exp2):
        super().__init__()
        self._exp1 = exp1
        self._exp2 = exp2

    def visit(self, visitor):
        visitor.visit_statement(self)
        self._exp1.visit(visitor)
        self._exp2.visit(visitor)


class BasicSound(Basic2ParamStatement):
    def basic09_text(self, indent_level):
        return (
            f"{super().basic09_text(indent_level)}"
            f"RUN ecb_sound({self._exp1.basic09_text(indent_level)}, "
            f"{self._exp2.basic09_text(indent_level)}, 31.0)"
        )


class BasicPoke(Basic2ParamStatement):
    def basic09_text(self, indent_level):
        return (
            f"{super().basic09_text(indent_level)}"
            f"POKE {self._exp1.basic09_text(indent_level)}, "
            f"{self._exp2.basic09_text(indent_level)}"
        )


class BasicCls(AbstractBasicStatement):
    def __init__(self, exp=None):
        super().__init__()
        self._exp = exp

    def basic09_text(self, indent_level):
        return super().basic09_text(indent_level) + (
            f"RUN ecb_cls({self._exp.basic09_text(indent_level)}, display)"
            if self._exp
            else "RUN ecb_cls(1.0, display)"
        )

    def visit(self, visitor):
        visitor.visit_statement(self)
        if self._exp:
            self._exp.visit(visitor)


class BasicFunctionCall(AbstractBasicExpression):
    def __init__(self, func, args, is_str_expr=False):
        super().__init__(is_str_expr=is_str_expr)
        self._func = func
        self._args = args

    def basic09_text(self, indent_level):
        return f"{self._func}" f"{self._args.basic09_text(indent_level)}"


class BasicDataStatement(AbstractBasicStatement):
    def __init__(self, exp_list):
        super().__init__()
        self._exp_list = exp_list

    @property
    def exp_list(self):
        return self._exp_list

    def basic09_text(self, indent_level):
        return (
            f"{super().basic09_text(indent_level)}DATA "
            f"{self._exp_list.basic09_text(indent_level)}"
        )

    def visit(self, visitor):
        visitor.visit_statement(self)
        visitor.visit_data_statement(self)


class BasicKeywordStatement(AbstractBasicStatement):
    def __init__(self, keyword):
        super().__init__()
        self._keyword = keyword

    def basic09_text(self, indent_level):
        return f"{super().basic09_text(indent_level)}{self._keyword}"

    def visit(self, visitor):
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

    def basic09_text(self, indent_level):
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

    def visit(self, visitor):
        visitor.visit_statement(self)
        visitor.visit_for_statement(self)
        self._var.visit(visitor)
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

    def basic09_text(self, indent_level):
        vlist = (
            [f"NEXT {var.basic09_text(indent_level)}" for var in self.var_list.exp_list]
            if self.var_list.exp_list
            else ["NEXT"]
        )
        return super().basic09_text(indent_level) + r" \ ".join(vlist)

    def visit(self, visitor):
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
        self._statement = BasicRunCall(
            self._func, BasicExpressionList(self._args.exp_list + [var])
        )

    @property
    def statement(self):
        return self._statement

    def basic09_text(self, indent_level):
        return self._var.basic09_text(indent_level) if self._var else ""

    def visit(self, visitor):
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

    def visit(self, visitor):
        super().visit(visitor)
        visitor.visit_joystk(self)


class BasicDimStatement(AbstractBasicStatement):
    def __init__(self, dim_vars):
        super().__init__()
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

    def basic09_text(self, indent_level):
        dim_var_text = ", ".join(
            (dim_var.basic09_text(indent_level) for dim_var in self._dim_vars)
        )
        init_text = "\n".join(
            (
                self.init_text_for_var(dim_var)
                for dim_var in self._dim_vars
                if isinstance(dim_var, BasicArrayRef)
            )
        )
        init_text = "\n" + init_text if init_text else ""

        return f"{super().basic09_text(indent_level)}" f"DIM {dim_var_text}" + init_text


class BasicReadStatement(BasicStatement):
    def __init__(self, rhs_list):
        super().__init__(None)
        self._rhs_list = rhs_list

    @property
    def rhs_list(self):
        return self._rhs_list

    def basic09_text(self, indent_level):
        return (
            self.indent_spaces(indent_level)
            + "READ "
            + ", ".join(rhs.basic09_text(indent_level) for rhs in self._rhs_list)
        )


class BasicInputStatement(BasicStatement):
    def __init__(self, message, rhs_list):
        self._message = message
        self._rhs_list = rhs_list

    def basic09_text(self, indent_level):
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

    def basic09_text(self, indent_level):
        return (
            f"{self.indent_spaces(indent_level)}"
            f"ADDR({self._var.basic09_text(indent_level)})"
        )

    def visit(self, visitor):
        visitor.visit_exp(self)
        visitor.visit_exp(self._var)


class BasicWidthStatement(AbstractBasicStatement):
    def __init__(self, expr):
        super().__init__()
        self._expr = expr

    def basic09_text(self, indent_level):
        return (
            f"run _ecb_width("
            f"{self._expr.basic09_text(indent_level=indent_level)}, "
            f"display)"
        )
