import re
from abc import ABC, abstractmethod
from itertools import chain, islice
from parsimonious.grammar import Grammar
from parsimonious.nodes import Node, NodeVisitor

from .procbank import ProcedureBank

PROCNAME_REGEX = re.compile(r'[a-zA-Z0-9_-]+')

SINGLE_KEYWORD_STATEMENTS = {
    'END': 'END',
    'RETURN': 'RETURN',
    'RESTORE': 'RESTORE',
}

QUOTED_SINGLE_KEYWORD_STATEMENTS = [
    f'"{name}"' for name in SINGLE_KEYWORD_STATEMENTS
]

FUNCTIONS = {
    'ABS': 'ABS',
    'ASC': 'ASC',
    'ATN': 'ATN',
    'COS': 'COS',
    'EXP': 'EXP',
    'LEN': 'LEN',
    'LOG': 'LOG',
    'PEEK': 'PEEK',
    'RND': 'RND',
    'SGN': 'SGN',
    'SIN': 'SIN',
    'SQR': 'SQR',
    'TAN': 'TAN',
}

QUOTED_FUNCTION_NAMES = [f'"{name}"' for name in FUNCTIONS]

STR2_FUNCTIONS = {
    'LEFT$': 'LEFT$',
    'RIGHT$': 'RIGHT$',
}

QUOTED_STR2_FUNCTION_NAMES = [f'"{name}"' for name in STR2_FUNCTIONS]

STR3_FUNCTIONS = {
    'MID$': 'MID$',
}

QUOTED_STR3_FUNCTION_NAMES = [f'"{name}"' for name in STR3_FUNCTIONS]

STR_NUM_FUNCTIONS = {
    'VAL': 'VAL',
    'LEN': 'LEN',
}

QUOTED_STR_NUM_FUNCTIONS_NAMES = [f'"{name}"' for name in STR_NUM_FUNCTIONS]

NUM_STR_FUNCTIONS = {
    'CHR$': 'CHR$',
    'TAB': 'TAB',
}

QUOTED_NUM_STR_FUNCTIONS_NAMES = [f'"{name}"' for name in NUM_STR_FUNCTIONS]

STATEMENTS2 = {
    'RESET': 'RUN ecb_reset',
}

QUOTED_STATEMENTS2_NAMES = [f'"{name}"' for name in STATEMENTS2]

STATEMENTS3 = {
    'SET': 'RUN ecb_set',
}

QUOTED_STATEMENTS3_NAMES = [f'"{name}"' for name in STATEMENTS3]

FUNCTIONS_TO_STATEMENTS = {
    'BUTTON': 'RUN ecb_button',
    'INT': 'RUN ecb_int',
}

QUOTED_FUNCTIONS_TO_STATEMENTS_NAMES = [
    f'"{name}"' for name in FUNCTIONS_TO_STATEMENTS
]

FUNCTIONS_TO_STATEMENTS2 = {
    'POINT': 'RUN ecb_point',
}

QUOTED_FUNCTIONS_TO_STATEMENTS2_NAMES = [
    f'"{name}"' for name in FUNCTIONS_TO_STATEMENTS2
]

NUM_STR_FUNCTIONS_TO_STATEMENTS = {
    'HEX$': 'RUN ecb_hex',
}

QUOTED_NUM_STR_FUNCTIONS_TO_STATEMENTS_NAMES = [
    f'"{name}"' for name in NUM_STR_FUNCTIONS_TO_STATEMENTS
]

STR_FUNCTIONS_TO_STATEMENTS = {
    'INKEY$': 'RUN ecb_inkey',
}

QUOTED_STR_FUNCTIONS_TO_STATEMENTS_NAMES = [
    f'"{name}"' for name in STR_FUNCTIONS_TO_STATEMENTS
]

KEYWORDS = '|'.join(
    chain((
        'AND',
        'DIM',
        'CLS',
        'CLEAR',
        'ELSE',
        'FOR',
        'GOSUB',
        'GOTO',
        'IF',
        'INPUT',
        'JOYSTK',
        'NOT',
        'OR',
        'PRINT',
        'READ',
        'REM',
        'SOUND',
        'STEP',
        'THEN',
    ), SINGLE_KEYWORD_STATEMENTS.keys(),
        FUNCTIONS.keys(),
        STR2_FUNCTIONS.keys(),
        STR3_FUNCTIONS.keys(),
        STR_NUM_FUNCTIONS.keys(),
        NUM_STR_FUNCTIONS.keys(),
        STATEMENTS2.keys(),
        STATEMENTS3.keys(),
        FUNCTIONS_TO_STATEMENTS.keys(),
        FUNCTIONS_TO_STATEMENTS2.keys(),
        NUM_STR_FUNCTIONS_TO_STATEMENTS.keys(),
        STR_FUNCTIONS_TO_STATEMENTS.keys()))

grammar = Grammar(
    rf"""
    aaa_prog           = multi_line eol* eof
    multi_line         = line space* multi_line_elements
    multi_line_elements = multi_line_element*
    multi_line_element  = eol+ line space*
    array_ref_exp   = var space* exp_list
    arr_assign      = array_ref_exp space* "=" space* exp
    str_array_ref_exp   = str_var space* exp_list
    str_arr_assign  = str_array_ref_exp space* "=" space* str_exp
    comment         = comment_token comment_text
    exp_list        = "(" space* exp space* exp_sublist ")"
    exp_sublist     = exp_sublist_mbr*
    exp_sublist_mbr = ("," space* exp space*)
    if_else_stmnt   = ("IF" space* if_exp space*
                       "THEN" space* line_or_stmnts2 space*
                       "ELSE" space* line_or_stmnts)
    if_stmnt        = ("IF" space* if_exp space*
                       "THEN" space* line_or_stmnts)
    line            = linenum space* statements space*
    line_or_stmnts  = linenum
                    / statements
    line_or_stmnts2 = linenum
                    / statements_else
    str_assign      = str_var space* "=" space* str_exp
    num_assign      = var space* "=" space* exp
    statement       = if_else_stmnt
                    / if_stmnt
                    / print_at_statement
                    / print_statement
                    / num_assign
                    / str_assign
                    / arr_assign
                    / str_arr_assign
                    / sound
                    / poke_statement
                    / cls
                    / go_statement
                    / on_n_go_statement
                    / statement2
                    / statement3
                    / data_statement
                    / single_kw_statement
                    / for_step_statement
                    / for_statement
                    / next_statement
                    / dim_statement
                    / clear_statement
                    / read_statement
                    / input_statement
    statement2      =({ ' / '.join(QUOTED_STATEMENTS2_NAMES)}) space* "(" space* exp space* "," space* exp space* ")" space*
    statement3      = ({ ' / '.join(QUOTED_STATEMENTS3_NAMES)}) space* "(" space* exp space* "," space* exp space* "," space* exp space* ")" space*
    statements      = (statement? (comment/((":"/space)+
                                            (comment / statements)))* space*)
    statements_else = (statement? (space* ":" statements)* space*)
    exp             = "NOT"? space* num_exp space*
    if_exp          = bool_exp
                    / num_exp
    bool_exp              = "NOT"? space* bool_or_exp
    bool_or_exp           = bool_and_exp space* bool_or_exp_elements
    bool_or_exp_elements  = bool_or_exp_element*
    bool_or_exp_element   = "OR" space* bool_and_exp space*
    bool_and_exp          = bool_val_exp space* bool_and_exp_elements
    bool_and_exp_elements = bool_and_exp_element*
    bool_and_exp_element  = "AND" space* bool_val_exp space*
    bool_val_exp    = bool_paren_exp
                    / bool_str_exp
                    / bool_bin_exp
    bool_paren_exp  = "(" space* bool_exp space* ")"
    bool_bin_exp    = num_sum_exp space* ("<=" / ">=" / "<>" / "<" / ">" / "=>" / "=<" / "=") space* num_sum_exp space*
    bool_str_exp    = str_exp space* ("<>" / "=") space* str_exp space*
    num_exp              = num_and_exp space* num_exp_elements
    num_exp_elements     = num_exp_element*
    num_exp_element      = "OR" space* num_and_exp space*
    num_and_exp          = num_gtle_exp space* num_and_exp_elements
    num_and_exp_elements = num_and_exp_element*
    num_and_exp_element  = "AND" space* num_gtle_exp space*
    num_gtle_exp    = num_sum_exp space* (("<=" / ">=" / "<>" / "<" / ">" / "=>" / "=<" / "=") space* num_sum_exp space*)*
    num_sum_exp     = num_prod_exp space* (("+" / "-") space*
                                           num_prod_exp space*)*
    num_prod_exp    = val_exp space* (("*" / "/") space* val_exp space*)*
    func_exp        = ({ ' / '.join(QUOTED_FUNCTION_NAMES)}) space* "(" space* exp space* ")" space*
    func_str_exp    = ({ ' / '.join(QUOTED_STR_NUM_FUNCTIONS_NAMES)}) space* "(" space* str_exp space* ")" space*
    val_exp         = num_literal
                    / hex_literal
                    / paren_exp
                    / unop_exp
                    / array_ref_exp
                    / var
                    / func_exp
                    / func_str_exp
                    / func_to_statements
                    / func_to_statements2
                    / joystk_to_statement
    unop_exp        = unop space* exp
    paren_exp       =  "(" space* exp space* ")" space*
    str_exp         = str_simple_exp space* ("+" space*
                                             str_simple_exp space*)* 
    str2_func_exp   = ({ ' / '.join(QUOTED_STR2_FUNCTION_NAMES)}) space* "(" space* str_exp space* "," space* exp space* ")" space*
    str3_func_exp   = ({ ' / '.join(QUOTED_STR3_FUNCTION_NAMES)}) space* "(" space* str_exp space* "," space* exp space* "," space* exp space* ")" space*
    num_str_func_exp= ({ ' / '.join(QUOTED_NUM_STR_FUNCTIONS_NAMES)}) space* "(" space* exp space* ")" space*
    num_str_func_exp_statements = ({ ' / '.join(QUOTED_NUM_STR_FUNCTIONS_TO_STATEMENTS_NAMES)}) space* "(" space* exp space* ")" space*
    str_func_exp_statements = ({ ' / '.join(QUOTED_STR_FUNCTIONS_TO_STATEMENTS_NAMES)}) space*

    str_simple_exp  = str_literal
                    / str_array_ref_exp
                    / str_var
                    / str2_func_exp
                    / str3_func_exp
                    / num_str_func_exp
                    / num_str_func_exp_statements
                    / str_func_exp_statements
    comment_text    = ~r"[^:\r\n$]*"
    comment_token   = ~r"(REM|')"
    eof             = ~r"$"
    eol             = ~r"[\n\r]+"
    linenum         = ~r"[0-9]+"
    literal         = num_literal
    hex_literal     = ~r"& *H *[0-9A-F][0-9A-F]?[0-9A-F]?[0-9A-F]?[0-9A-F]?[0-9A-F]?"
    num_literal     = ~r"([\+\- ]*(\d*\.\d*)( *(?!ELSE)E *[\+\-]? *\d*))|[\+\- ]*(\d*\.\d*)|[\+\- ]*(\d+( *(?!ELSE)E *[\+\-]? *\d*))|[\+\- ]*(\d+)"
    int_literal     = ~r"(\d+)"
    space           = ~r" "
    str_literal     = ~r'\"[^"\n]*\"'
    unop            = "+" / "-"
    var             = ~r"(?!{KEYWORDS}|([A-Z][A-Z0-9]*\$))([A-Z][A-Z0-9]?)"
    str_var         = ~r"(?!{KEYWORDS})([A-Z][A-Z0-9]?)\$"
    print_statement = ("PRINT"/"?") space* print_args space*
    print_at_statement = ("PRINT"/"?") space* "@" space* exp space* "," space* print_args space*
    print_args      = print_arg0*
    print_arg0      = print_arg1 space*
    print_arg1      = print_control
                    / print_arg
    print_arg       = exp
                    / str_exp
    print_control   = ~r"(;|,)"
    sound           = "SOUND" space* exp space* "," space* exp space*
    poke_statement  = "POKE" space* exp space* "," space* exp space*
    cls             = "CLS" space* exp? space*
    go_statement    = ("GOTO" / "GOSUB") space* linenum space*
    on_n_go_statement   = "ON" space* exp space* ("GOTO" / "GOSUB") space* linenum_list space*
    linenum_list        = linenum space* linenum_list0
    linenum_list0       = linenum_list_elem*
    linenum_list_elem   = "," space* linenum space*
    functions           = ~r"{'|'.join(FUNCTIONS.keys())}"
    data_statement      = "DATA" space* data_elements space*
    data_elements       = data_element space* data_elements0
    data_element        = data_num_element / data_str_element
    data_elements0      = data_element0*
    data_element0       = "," space* data_element
    data_num_element    = space* data_num_element0 space*
    data_num_element0   = (num_literal / hex_literal)
    data_str_element    = data_str_element0 / data_str_element1
    data_str_element0   = space* str_literal space*
    data_str_element1   = space* data_str_literal
    data_str_literal    = ~r'[^",:\n]*'
    single_kw_statement = ({ ' / '.join(QUOTED_SINGLE_KEYWORD_STATEMENTS)}) space*
    for_statement       = "FOR" space* var space* "=" space* exp space* "TO" space* exp space*
    for_step_statement  = "FOR" space* var space* "=" space* exp space* "TO" space* exp space* "STEP" space* exp space*
    next_statement      = next_var_statement / next_empty_statement
    next_var_statement  = "NEXT" space* var_list space*
    next_empty_statement= "NEXT" space*
    var_list            = var space* var_list_elements
    var_list_elements   = var_list_element*
    var_list_element    = "," space* var space*
    func_to_statements  = ({ ' / '.join(QUOTED_FUNCTIONS_TO_STATEMENTS_NAMES)}) space* "(" space* exp space* ")" space*
    func_to_statements2 = ({ ' / '.join(QUOTED_FUNCTIONS_TO_STATEMENTS2_NAMES)}) space* "(" space* exp space* "," space* exp space*")" space*
    joystk_to_statement = "JOYSTK" space* "(" space* exp space* ")" space*
    dim_element0        = (int_literal / hex_literal)
    dim_var             = (dim_array_var / str_var / var)
    dim_array_var       = dim_array_var3 / dim_array_var2 / dim_array_var1
    dim_array_var1      = (str_var / var) space* "(" space* dim_element0 space* ")" space*
    dim_array_var2      = (str_var / var) space* "(" space* dim_element0 space* "," space* dim_element0 space* ")" space*
    dim_array_var3      = (str_var / var) space* "(" space* dim_element0 space* "," space* dim_element0 space* "," space* dim_element0 space* ")" space*
    dim_array_var_list  = dim_var space* dim_array_var_list_elements
    dim_array_var_list_elements = dim_array_var_list_element*
    dim_array_var_list_element = "," space* dim_var space*
    dim_statement       = "DIM" space* dim_array_var_list
    clear_statement     = "CLEAR" space* exp? space*
    read_statement      = "READ" space* rhs space* rhs_list_elements
    rhs_list_elements   = rhs_list_element*
    rhs_list_element    = "," space* rhs space*
    rhs                 = array_ref_exp / str_array_ref_exp / str_var / var
    input_statement     = "INPUT" space* input_str_literal? space* rhs space* rhs_list_elements
    input_str_literal   = str_literal space* ';' space*
    """  # noqa
)


class BasicConstructVisitor():
    def visit_array_ref(self, array_ref):
        """
        Invoked when an array reference is encountered.
        """
        pass

    def visit_data_statement(self, for_statement):
        """
        Invoked when a DATA statement is encountered.
        """
        pass

    def visit_exp(self, exp):
        """
        Invoked when an expression is encountered.
        """
        pass

    def visit_for_statement(self, for_statement):
        """
        Invoked when a FOR statement is encountered.
        """
        pass

    def visit_go_statement(self, go_statement):
        """
        Invoked when a [ON] GOTO/GOSUB statement is encountered.
        """
        pass

    def visit_joystk(self, joystk_exp):
        """
        Invoked when a JOYSTK function is encountered.
        """
        pass

    def visit_line(self, line):
        """
        Invoked when a new line is encountered.
        """
        pass

    def visit_next_statement(self, next_statement):
        """
        Invoked when a NEXT statement is encountered.
        """
        pass

    def visit_program(self, line):
        """
        Invoked when a program is encountered.
        """
        pass

    def visit_read_statement(self, statement):
        """AI is creating summary for visit_read

        Args:
            statement (BasicReadStatement): input statement to transform.

        Returns:
            BasicStatement: BasicStatement to replace statement.
        """
        return statement

    def visit_statement(self, statement):
        """
        Invoked when a statement is encountered.
        """
        pass

    def visit_var(self, var):
        """
        Invoked when a variable is encountered.
        """
        pass


class AbstractBasicConstruct(ABC):
    def indent_spaces(self, indent_level):
        return '  ' * indent_level

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
            val = f'tmp_{len(self._str_temps) + 1}$'
            self._str_temps.add(val)
        else:
            val = f'tmp_{len(self._temps) + 1}'
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
            self._pre_assignment_statements,
            multi_line=False
        )
        return f'{self.indent_spaces(indent_level)}' + \
            f'{pre_assignments.basic09_text(indent_level)}' + \
            (r' \ ' if self._pre_assignment_statements else '')


class BasicArrayRef(AbstractBasicExpression):
    def __init__(self, var, indices, is_str_expr=False):
        super().__init__(is_str_expr=is_str_expr)
        self._var = BasicVar(f'arr_{var.name()}', is_str_expr=is_str_expr)
        self._indices = indices

    @property
    def var(self):
        return self._var

    @property
    def indices(self):
        return self._indices

    def basic09_text(self, indent_level):
        return f'{self._var.basic09_text(indent_level)}' \
            f'{self._indices.basic09_text(indent_level)}'

    def visit(self, visitor):
        visitor.visit_array_ref(self)
        for index in self._indices.exp_list:
            index.visit(visitor)


class BasicAssignment(AbstractBasicStatement):
    def __init__(self, var, exp):
        super().__init__()
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
            return f'{super().basic09_text(indent_level)}' \
                f'{self._exp.statement.basic09_text(indent_level)}'

        return f'{super().basic09_text(indent_level)}' \
            f'{self._var.basic09_text(indent_level)} = ' \
            f'{self._exp.basic09_text(indent_level)}'

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
        if self._op in {'AND', 'OR'}:
            return f'L{self._op}({self._exp1.basic09_text(indent_level)}, '\
                f'{self._exp2.basic09_text(indent_level)})'
        else:
            return (f'{self._exp1.basic09_text(indent_level)} {self._op} '
                    f'{self._exp2.basic09_text(indent_level)}')

    def visit(self, visitor):
        visitor.visit_exp(self)
        self._exp1.visit(visitor)
        self._exp2.visit(visitor)


class BasicBooleanBinaryExp(BasicBinaryExp):
    def basic09_text(self, indent_level):
        return (f'{self._exp1.basic09_text(indent_level)} {self._op} '
                f'{self._exp2.basic09_text(indent_level)}')


class BasicComment(AbstractBasicConstruct):
    def __init__(self, comment):
        self._comment = comment

    def basic09_text(self, indent_level):
        return f'(*{self._comment} *)'

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
        exp_list_text = ', '.join(
            exp.basic09_text(indent_level) for exp in self._exp_list)
        return f'({exp_list_text})' if self._parens else f'{exp_list_text}'

    def visit(self, visitor):
        for exp in self.exp_list:
            exp.visit(visitor)


class BasicRunCall(AbstractBasicStatement):
    def __init__(self, run_invocation, arguments):
        super().__init__()
        self._run_invocation = run_invocation
        self._arguments = arguments

    def basic09_text(self, indent_level):
        return f'{super().basic09_text(indent_level)}' \
            f'{self._run_invocation}' \
            f'{self._arguments.basic09_text(indent_level)}'

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
            return f'{super().basic09_text(indent_level)}GOSUB {self._linenum}'
        return f'{self._linenum}' \
            if self._implicit \
            else f'{super().basic09_text(indent_level)}GOTO {self._linenum}'

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
            return f'{super().basic09_text(indent_level)}' \
                f'ON {self._exp.basic09_text(indent_level)} GOSUB ' + \
                ', '.join((str(linenum) for linenum in self.linenums))
        return f'{super().basic09_text(indent_level)}' \
            f'ON {self._exp.basic09_text(indent_level)} GOTO ' + \
            ', '.join((str(linenum) for linenum in self.linenums))

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
        if (isinstance(self._statements, BasicGoto) and
                self._statements.implicit):
            return f'{super().basic09_text(indent_level)}' \
                f'IF {self._exp.basic09_text(indent_level)} ' \
                f'THEN {self._statements.basic09_text(0)}'
        else:
            return f'{super().basic09_text(indent_level)}' \
                f'IF {self._exp.basic09_text(indent_level)} THEN\n' \
                f'{self._statements.basic09_text(indent_level + 1)}\n' \
                f'ENDIF'

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
            return f'{self._num} ' \
                f'{self._statements.basic09_text(indent_level)}'
        return f'{self._statements.basic09_text(indent_level)}'

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
        return (f'"{self._literal}"' if type(self._literal) is str
                else f'{self._literal}')

    def visit(self, visitor):
        visitor.visit_exp(self)


class HexLiteral(AbstractBasicExpression):
    def __init__(self, literal):
        super().__init__(is_str_expr=False)
        self._literal = literal

    def basic09_text(self, indent_level):
        val = int(f'0x{self._literal}', 16)
        return f'${self._literal}' if val < 0x8000 \
            else f'{val}'

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
        if self.operator == 'NOT':
            return f'L{self.operator}({self.exp.basic09_text(indent_level)})'
        else:
            return f'{self.operator} {self.exp.basic09_text(indent_level)}'

    def visit(self, visitor):
        visitor.visit_exp(self)
        self._exp.visit(visitor)


class BasicBooleanOpExp(BasicOpExp):
    def basic09_text(self, indent_level):
        if self.operator == 'NOT':
            return f'{self.operator}({self.exp.basic09_text(indent_level)})'
        else:
            return f'{self.operator} {self.exp.basic09_text(indent_level)}'


class BasicParenExp(AbstractBasicExpression):
    def __init__(self, exp):
        self._exp = exp

    def basic09_text(self, indent_level):
        return f'({self._exp.basic09_text(indent_level)})'

    def visit(self, visitor):
        visitor.visit_exp(self)
        self._exp.visit(visitor)


class BasicBooleanParenExp(BasicParenExp):
    def basic09_text(self, indent_level):
        return f'({self._exp.basic09_text(indent_level)})'


class BasicProg(AbstractBasicConstruct):
    def __init__(self, lines):
        self._lines = lines
        self._prefix_lines = []
        self._procname = ''

    def set_procname(self, procname):
        self._procname = procname

    def extend_prefix_lines(self, prefix_lines):
        self._prefix_lines.extend(prefix_lines)

    def basic09_text(self, indent_level):
        lines = []
        if self._procname:
            lines.append(f'procedure {self._procname}')
        nest_counter = ForNextVisitor()
        for line in chain(self._prefix_lines, self._lines):
            line.visit(nest_counter)
            lines.append(line.basic09_text(nest_counter.count))

        return '\n'.join(lines)

    def visit(self, visitor):
        visitor.visit_program(self)
        for line in self._lines:
            line.visit(visitor)


class BasicStatement(AbstractBasicStatement):
    def __init__(self, basic_construct):
        super().__init__()
        self._basic_construct = basic_construct

    def basic09_text(self, indent_level):
        return super().basic09_text(indent_level) + \
            self._basic_construct.basic09_text(indent_level)

    def visit(self, visitor):
        visitor.visit_statement(self)


class Basic09CodeStatement(AbstractBasicStatement):
    def __init__(self, basic09_code):
        super().__init__()
        self._basic09_code = basic09_code

    def basic09_text(self, indent_level):
        return super().basic09_text(indent_level) + \
            self._basic09_code

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

    def basic09_text(self, indent_level):
        joiner = ('\n' + self.indent_spaces(indent_level)) \
            if self._multi_line else r' \ '
        net_indent_level = indent_level if self._multi_line else 0
        return joiner.join(statement.basic09_text(net_indent_level)
                           for statement in self._statements)

    def visit(self, visitor):
        for idx, statement in enumerate(self.statements):
            statement.visit(visitor)
            if isinstance(statement, BasicReadStatement):
                self.statements[idx] = visitor.visit_read_statement(statement)


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

    def basic09_text(self, indent_level):
        return super().basic09_text(indent_level) + \
            f'PRINT {self._print_args.basic09_text(indent_level)}'

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

    def basic09_text(self, indent_level):
        processed_args = []

        for ii, arg in enumerate(self.args):
            is_control = isinstance(arg, BasicPrintControl)
            if is_control and \
                ((ii <= 0) or
                    isinstance(self.args[ii - 1], BasicPrintControl)):
                processed_args.append('""')
            if not is_control and \
                ((ii > 0) and
                 not isinstance(self.args[ii - 1], BasicPrintControl)):
                processed_args.append('; ')

            processed_args.append(arg.basic09_text(indent_level))
            if (ii < len(self.args) - 1) and is_control:
                processed_args.append(' ')

        return ''.join(processed_args)

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
        return f'{super().basic09_text(indent_level)}' \
            f'RUN ecb_sound({self._exp1.basic09_text(indent_level)}, ' \
            f'{self._exp2.basic09_text(indent_level)}, 31.0)'


class BasicPoke(Basic2ParamStatement):
    def basic09_text(self, indent_level):
        return f'{super().basic09_text(indent_level)}' \
            f'POKE {self._exp1.basic09_text(indent_level)}, ' \
            f'{self._exp2.basic09_text(indent_level)}'


class BasicCls(AbstractBasicStatement):
    def __init__(self, exp=None):
        super().__init__()
        self._exp = exp

    def basic09_text(self, indent_level):
        return super().basic09_text(indent_level) \
            + (f'RUN ecb_cls({self._exp.basic09_text(indent_level)})'
               if self._exp else 'RUN ecb_cls(1.0)')

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
        return f'{self._func}' \
            f'{self._args.basic09_text(indent_level)}'


class BasicDataStatement(AbstractBasicStatement):
    def __init__(self, exp_list):
        super().__init__()
        self._exp_list = exp_list

    @property
    def exp_list(self):
        return self._exp_list

    def basic09_text(self, indent_level):
        return f'{super().basic09_text(indent_level)}DATA ' \
            f'{self._exp_list.basic09_text(indent_level)}'

    def visit(self, visitor):
        visitor.visit_statement(self)
        visitor.visit_data_statement(self)


class BasicKeywordStatement(AbstractBasicStatement):
    def __init__(self, keyword):
        super().__init__()
        self._keyword = keyword

    def basic09_text(self, indent_level):
        return f'{super().basic09_text(indent_level)}{self._keyword}'

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
        return f'{super().basic09_text(indent_level - 1)}FOR ' \
            f'{self._var.basic09_text(indent_level)} = ' \
            f'{self._start_exp.basic09_text(indent_level)} TO ' \
            f'{self._end_exp.basic09_text(indent_level)}' + \
            (f' STEP {self._step_exp.basic09_text(indent_level)}'
                if self._step_exp else '')

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
        vlist = [
            f'NEXT {var.basic09_text(indent_level)}'
            for var in self.var_list.exp_list
        ]
        return super().basic09_text(indent_level) + r' \ '.join(vlist)

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
        return self._var.basic09_text(indent_level) if self._var else ''

    def visit(self, visitor):
        if self._var:
            self._statement.visit(visitor)
            self._var.visit(visitor)
        else:
            visitor.visit_exp(self)


class BasicJoystkExpression(BasicFunctionalExpression):
    def __init__(self, args):
        super().__init__('RUN ecb_joystk', args)
        self._args = args

    def visit(self, visitor):
        super().visit(visitor)
        visitor.visit_joystk(self)


class BasicDimStatement(AbstractBasicStatement):
    def __init__(self, dim_vars):
        super().__init__()
        self._dim_vars = dim_vars

    def init_text_for_var(self, dim_var):
        for_statements = (
            BasicForStatement(
                BasicVar(f'tmp_{ii + 1}'),
                BasicLiteral(1),
                index
            )
            for ii, index in enumerate(dim_var.indices.exp_list)
        )
        next_statements = (
            BasicNextStatement(BasicExpressionList([BasicVar(f'tmp_{ii}')]))
            for ii in range(len(dim_var.indices.exp_list), 0, -1)
        )
        init_val = BasicLiteral(
            '' if dim_var.is_str_expr else 0,
            is_str_expr=dim_var.is_str_expr
        )
        var = BasicVar(
            dim_var._var.name()[4:],
            dim_var._var.is_str_expr
        )

        assignment = \
            BasicAssignment(
                BasicArrayRef(
                    var,
                    BasicExpressionList(
                        (
                            BasicVar(f'tmp_{ii}')
                            for ii in range(
                                1, len(dim_var.indices.exp_list) + 1
                            )
                        )
                    )
                ),
                init_val
            )

        return BasicStatements(
            chain(for_statements, (assignment, ), next_statements),
            multi_line=False
        ).basic09_text(0)

    def basic09_text(self, indent_level):
        dim_var_text = ', '.join((
            dim_var.basic09_text(indent_level) for dim_var in self._dim_vars
        ))
        init_text = ' \\ '.join((
            self.init_text_for_var(dim_var) for dim_var in self._dim_vars
            if isinstance(dim_var, BasicArrayRef)
        ))
        init_text = ' \\ ' + init_text if init_text else ''

        return f'{super().basic09_text(indent_level)}' \
            f'DIM {dim_var_text}' + init_text


class BasicReadStatement(BasicStatement):
    def __init__(self, rhs_list):
        super().__init__(None)
        self._rhs_list = rhs_list

    @property
    def rhs_list(self):
        return self._rhs_list

    def basic09_text(self, indent_level):
        return self.indent_spaces(indent_level) + \
               'READ ' + \
               ', '.join(rhs.basic09_text(indent_level)
                         for rhs in self._rhs_list)


class BasicInputStatement(BasicStatement):
    def __init__(self, message, rhs_list):
        self._message = message
        self._rhs_list = rhs_list

    def basic09_text(self, indent_level):
        prefix = self.indent_spaces(indent_level) + \
                 'INPUT ' + self._message.basic09_text(indent_level) + ', ' \
                 if self._message else 'INPUT '
        return prefix + ', '.join((
            rhs.basic09_text(indent_level) for rhs in self._rhs_list
        ))


class BasicFunctionalExpressionPatcherVisitor(BasicConstructVisitor):
    def __init__(self):
        self._statement = None

    def visit_statement(self, statement):
        self._statement = statement
        if isinstance(statement, BasicAssignment) and \
           isinstance(statement.exp, BasicFunctionalExpression):
            statement.exp.set_var(statement.var)

    def visit_exp(self, exp):
        if not isinstance(exp, BasicFunctionalExpression) or exp.var:
            return
        self._statement.transform_function_to_call(exp)


class ForNextVisitor(BasicConstructVisitor):
    def __init__(self):
        self._count = 0

    @property
    def count(self):
        return self._count

    def visit_for_statement(self, _):
        self._count = self._count + 1

    def visit_next_statement(self, next_statement):
        self._count = self._count - len(next_statement.var_list.exp_list)


class LineReferenceVisitor(BasicConstructVisitor):
    def __init__(self):
        self._references = set()

    @property
    def references(self):
        return self._references

    def visit_go_statement(self, go_statement):
        if isinstance(go_statement, BasicOnGoStatement):
            for linenum in go_statement.linenums:
                self.references.add(linenum)
        else:
            self.references.add(go_statement.linenum)


class LineNumberFilterVisitor(BasicConstructVisitor):
    def __init__(self, references):
        self._references = references

    def visit_line(self, line):
        line.set_is_referenced(line.num in self._references)


class LineZeroFilterVisitor(BasicConstructVisitor):
    def __init__(self, references):
        self._references = references

    def visit_line(self, line):
        if line.num == 0:
            line.set_is_referenced(line.num in self._references)


class VarInitializerVisitor(BasicConstructVisitor):
    def __init__(self):
        self._vars = set()

    @property
    def assignment_lines(self):
        return [
            BasicLine(
                None,
                BasicStatements([
                    BasicAssignment(
                        BasicVar(var, is_str_expr=(var[-1] == '$')),
                        BasicLiteral(
                            '' if (var[-1] == '$') else 0.0,
                            is_str_expr=(var[-1] == '$')
                        )
                    )
                    for var in sorted(self._vars)
                ])
            )] if self._vars else []

    def visit_var(self, var):
        self._vars.add(var.name())


class JoystickVisitor(BasicConstructVisitor):
    def __init__(self):
        self._uses_joystk = False

    @property
    def joystk_var_statements(self):
        return [
            Basic09CodeStatement('dim joy0x, joy0y, joy1x, joy0y: integer'),
        ] if self._uses_joystk else [
        ]

    def visit_joystk(self, joystk_exp):
        self._uses_joystk = True


class BasicEmptyDataElementVisitor(BasicConstructVisitor):
    def __init__(self):
        self._has_empty_data_elements = False

    @property
    def has_empty_data_elements(self):
        return self._has_empty_data_elements

    def visit_data_statement(self, statement):
        for exp in statement.exp_list.exp_list:
            self._has_empty_data_elements = \
                self._has_empty_data_elements or exp.literal == ''


class BasicReadStatementPatcherVisitor(BasicConstructVisitor):
    def visit_data_statement(self, statement):
        for exp in statement.exp_list.exp_list:
            if not isinstance(exp.literal, str):
                exp.literal = str(exp.literal)

    def visit_read_statement(self, statement):
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
            statement.rhs_list[idx] = rhs_to_temp.get(
                rhs, rhs
            )

        # Create statements for reading into the REAL vars
        filter_statements = [
            BasicRunCall(
              'RUN ecb_read_filter',
              BasicExpressionList((
                inval,
                outval)))
              for outval, inval in rhs_to_temp.items()
        ]

        return BasicStatements(
            [statement] + filter_statements,
            multi_line=False
        )


class BasicNextPatcherVisitor(BasicConstructVisitor):
    def __init__(self):
        self._last_for_var = None

    def visit_for_statement(self, for_statement):
        self._last_for_var = for_statement.var

    def visit_next_statement(self, next_statement):
        if self._last_for_var and len(next_statement.var_list.exp_list) == 0:
            next_statement.var_list.exp_list.append(self._last_for_var)


class BasicVisitor(NodeVisitor):
    def generic_visit(self, node, visited_children):
        if node.text.strip() == '':
            return ''

        if node.text in {'*', '/', '+', '-', '&', '<', '>', '<>', '=',
                         '<=', '=<', '>=', '=>', 'AND', 'OR', 'NOT'}:
            return BasicOperator(node.text)

        if len(visited_children) == 4 and \
           isinstance(visited_children[0], BasicOperator):
            operator, _, exp, _ = visited_children
            return BasicOpExp(operator.operator, exp)
        if len(visited_children) == 1:
            if isinstance(visited_children[0], AbstractBasicConstruct):
                return visited_children[0]

            if visited_children[0] is str:
                return visited_children[0]

        if len(visited_children) == 2:
            if isinstance(visited_children[0], BasicOpExp) and \
               isinstance(visited_children[1], BasicOpExp):
                exp1, exp2 = visited_children
                return BasicOpExp(
                            exp1.operator,
                            BasicBinaryExp(exp1.exp, exp2.operator, exp2.exp))
            if isinstance(visited_children[0], Node) and \
               visited_children[0].text == ':':
                return visited_children[1]

        return node

    def visit_aaa_prog(self, node, visited_children):
        return BasicProg(visited_children[0])

    def visit_arr_assign(self, node, visited_children):
        array_ref_exp, _, _, _, val_exp = visited_children
        return BasicAssignment(array_ref_exp, val_exp)

    def visit_array_ref_exp(self, node, visited_children):
        var, _, exp_list = visited_children
        return BasicArrayRef(var, exp_list)

    def visit_str_arr_assign(self, node, visited_children):
        str_array_ref_exp, _, _, _, str_exp = visited_children
        return BasicAssignment(str_array_ref_exp, str_exp)

    def visit_str_array_ref_exp(self, node, visited_children):
        str_var, _, exp_list = visited_children
        return BasicArrayRef(str_var, exp_list, is_str_expr=True)

    def visit_comment(self, node, visited_children):
        return BasicComment(visited_children[1])

    def visit_comment_text(self, node, visited_children):
        return node.full_text[node.start:node.end]

    def visit_exp(self, node, visited_children):
        not_keyword, _, exp, _ = visited_children
        if isinstance(not_keyword, BasicOperator):
            return BasicOpExp(not_keyword.operator, exp)
        return exp

    def visit_exp_list(self, node, visited_children):
        _, _, exp1, _, exp_sublist, _ = visited_children
        return BasicExpressionList((exp1, *exp_sublist))

    def visit_exp_sublist(self, node, visited_children):
        return visited_children

    def visit_exp_sublist_mbr(self, node, visited_children):
        _, _, exp, _ = visited_children
        return exp

    def visit_if_stmnt(self, node, visited_children):
        _, _, exp, _, _, _, statements = visited_children
        is_bool = isinstance(exp, (BasicBooleanBinaryExp, BasicBooleanOpExp,
                                   BasicBooleanParenExp))
        exp = exp if is_bool else \
            BasicBooleanBinaryExp(exp, '<>', BasicLiteral(0.0))
        return BasicIf(exp, statements)

    def visit_if_exp(self, node, visited_children):
        return visited_children[0]

    def visit_bool_exp(self, node, visited_children):
        not_keyword, _, exp = visited_children
        return BasicBooleanOpExp(not_keyword.operator, exp) \
            if isinstance(not_keyword, BasicOperator) else exp

    def visit_bool_or_exp(self, node, visited_children):
        exp1, _, exp_ops = visited_children
        if len(exp_ops) == 0:
            return exp1
        last_exp = exp1
        for exp_op in exp_ops:
            last_exp = BasicBooleanBinaryExp(
                last_exp, exp_op.operator, exp_op.exp
            )
        return last_exp

    def visit_bool_or_exp_elements(self, _, visited_children):
        return visited_children

    def visit_bool_or_exp_element(self, _, visited_children):
        _, _, exp, _ = visited_children
        return BasicBooleanOpExp('OR', exp)

    def visit_bool_and_exp(self, node, visited_children):
        return self.visit_bool_or_exp(node, visited_children)

    def visit_bool_and_exp_elements(self, _, visited_children):
        return visited_children

    def visit_bool_and_exp_element(self, _, visited_children):
        _, _, exp, _ = visited_children
        return BasicBooleanOpExp('AND', exp)

    def visit_bool_val_exp(self, node, visited_children):
        return visited_children[0]

    def visit_bool_paren_exp(self, node, visited_children):
        return BasicBooleanParenExp(visited_children[2])

    def visit_bool_bin_exp(self, node, visited_children):
        exp1, _, op, _, exp2, _ = visited_children
        return BasicBooleanBinaryExp(exp1, op.operator, exp2)

    def visit_bool_str_exp(self, node, visited_children):
        return self.visit_bool_bin_exp(node, visited_children)

    def visit_num_gtle_exp(self, node, visited_children):
        return self.visit_num_prod_exp(node, visited_children)

    def visit_line(self, node, visited_children):
        return BasicLine(
            visited_children[0],
            next(
                child for child in visited_children
                if isinstance(child, BasicStatements))
            )

    def visit_linenum(self, node, visited_children):
        return int(node.full_text[node.start:node.end])

    def visit_line_or_stmnts(self, node, visited_children):
        if isinstance(visited_children[0], int):
            return BasicGoto(visited_children[0], True)
        return visited_children[0]

    def visit_literal(self, node, visited_children):
        return visited_children[0]

    def visit_num_exp(self, node, visited_children):
        exp1, _, exp_ops = visited_children
        if len(exp_ops) == 0:
            return exp1
        last_exp = exp1
        for exp_op in exp_ops:
            last_exp = BasicBinaryExp(
                last_exp, exp_op.operator, exp_op.exp
            )
        return last_exp

    def visit_num_exp_elements(self, node, visited_children):
        return visited_children

    def visit_num_exp_element(self, node, visited_children):
        _, _, exp, _ = visited_children
        return BasicOpExp('OR', exp)

    def visit_num_and_exp(self, node, visited_children):
        return self.visit_num_exp(node, visited_children)

    def visit_num_and_exp_elements(self, node, visited_children):
        return visited_children

    def visit_num_and_exp_element(self, node, visited_children):
        _, _, exp, _ = visited_children
        return BasicOpExp('AND', exp)

    def visit_str_exp(self, node, visited_children):
        if len(visited_children) < 4:
            v1, v2, v3 = visited_children
            if isinstance(v2, str) and isinstance(v3, str):
                return visited_children[0]
            return BasicBinaryExp(v1, v3.operator, v3.exp, is_str_expr=True)
        return node

    def visit_str2_func_exp(self, node, visited_children):
        func, _, _, _, str_exp, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionCall(
            STR2_FUNCTIONS[func.text],
            BasicExpressionList([str_exp, exp]),
            is_str_expr=True
        )

    def visit_str3_func_exp(self, node, visited_children):
        func, _, _, _, str_exp, _, _, _, exp1, _, _, _, exp2, _, _, _ \
            = visited_children
        return BasicFunctionCall(
            STR3_FUNCTIONS[func.text],
            BasicExpressionList([str_exp, exp1, exp2]),
            is_str_expr=True
        )

    def visit_num_str_func_exp(self, node, visited_children):
        func, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionCall(
            NUM_STR_FUNCTIONS[func.text],
            BasicExpressionList([exp]),
            is_str_expr=True
        )

    def visit_num_str_func_exp_statements(self, node, visited_children):
        func, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionalExpression(
            NUM_STR_FUNCTIONS_TO_STATEMENTS[func.text],
            BasicExpressionList([exp]),
            is_str_expr=True
        )

    def visit_str_func_exp_statements(self, node, visited_children):
        func, _, = visited_children
        return BasicFunctionalExpression(
            STR_FUNCTIONS_TO_STATEMENTS[func.text],
            BasicExpressionList([]),
            is_str_expr=True
        )

    def visit_str_simple_exp(self, node, visited_children):
        return visited_children[0]

    def visit_multi_line(self, node, visited_children):
        line0, _, line1 = visited_children
        return [line0] + line1 if line1 else [line0]

    def visit_multi_line_elements(self, node, visited_children):
        return visited_children

    def visit_multi_line_element(self, node, visited_children):
        _, line, _ = visited_children
        return line

    def visit_num_literal(self, node, visited_children):
        num_literal = node.full_text[node.start:node.end].replace(' ', '')
        return BasicLiteral(float(num_literal))

    def visit_int_literal(self, node, visited_children):
        num_literal = node.full_text[node.start:node.end].replace(' ', '')
        return BasicLiteral(int(num_literal))

    def visit_hex_literal(self, node, visited_children):
        hex_literal = node.text[node.text.find('H') + 1:]
        return HexLiteral(hex_literal)

    def visit_unop_exp(self, node, visited_children):
        op, _, exp = visited_children
        return BasicOpExp(op.operator, exp)

    def visit_unop(self, node, visited_children):
        return visited_children[0]

    def visit_paren_exp(self, node, visited_children):
        return BasicParenExp(visited_children[2])

    def visit_num_prod_exp(self, node, visited_children):
        v1, v2, v3 = visited_children
        if isinstance(v2, str) and isinstance(v3, str):
            return v1
        return BasicBinaryExp(v1, v3.operator, v3.exp)

    def visit_func_exp(self, node, visited_children):
        func, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionCall(
            FUNCTIONS[func.text],
            BasicExpressionList([exp])
        )

    def visit_func_str_exp(self, node, visited_children):
        func, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionCall(
            STR_NUM_FUNCTIONS[func.text],
            BasicExpressionList([exp])
        )

    def visit_num_assign(self, node, visited_children):
        return BasicAssignment(visited_children[0], visited_children[4])

    def visit_str_assign(self, node, visited_children):
        return BasicAssignment(visited_children[0], visited_children[4])

    def visit_space(self, node, visited_children):
        return node.text

    def visit_statement(self, node, visited_children):
        return visited_children[0]

    def visit_statements(self, node, visited_children):
        return BasicStatements([child for child in visited_children
                                if isinstance(child, AbstractBasicConstruct)])

    def visit_str_literal(self, node, visited_children):
        return BasicLiteral(str(node.full_text[node.start+1:node.end-1]),
                            is_str_expr=True)

    def visit_num_sum_exp(self, node, visited_children):
        return self.visit_num_prod_exp(node, visited_children)

    def visit_val_exp(self, node, visited_children):
        return visited_children[0] if len(visited_children) < 2 else node

    def visit_var(self, node, visited_children):
        return BasicVar(node.full_text[node.start:node.end])

    def visit_str_var(self, node, visited_children):
        return BasicVar(node.full_text[node.start:node.end], True)

    def visit_print_statement(self, node, visited_children):
        _, _, print_args, _ = visited_children
        return BasicPrintStatement(print_args)

    def visit_print_at_statement(self, node, visited_children):
        _, _, _, _, loc, _, _, _, print_args, _ = visited_children
        at_statement = BasicRunCall('RUN ecb_at',
                                    BasicExpressionList([loc]))
        print_statement = BasicPrintStatement(print_args)
        return BasicStatements(
            [at_statement, print_statement],
            multi_line=False
        )

    def visit_print_args(self, node, visited_children):
        return BasicPrintArgs(visited_children)

    def visit_print_arg0(self, node, visited_children):
        arg, _ = visited_children
        return arg

    def visit_print_arg1(self, node, visited_children):
        return visited_children[0]

    def visit_print_arg(self, node, visited_children):
        return visited_children[0]

    def visit_print_control(self, node, visited_children):
        return BasicPrintControl(node.text)

    def visit_sound(self, node, visited_children):
        _, _, exp1, _, _, _, exp2, _ = visited_children
        return BasicSound(exp1, exp2)

    def visit_poke_statement(self, node, visited_children):
        _, _, exp1, _, _, _, exp2, _ = visited_children
        return BasicPoke(exp1, exp2)

    def visit_cls(self, node, visited_children):
        _, _, exp, _ = visited_children
        return BasicCls(exp if isinstance(exp, AbstractBasicExpression)
                        else None)

    def visit_statement2(self, node, visited_children):
        func, _, _, _, exp1, _, _, _, exp2, _, _, _ = visited_children
        return BasicRunCall(STATEMENTS2[func.text],
                            BasicExpressionList([exp1, exp2]))

    def visit_statement3(self, node, visited_children):
        func, _, _, _, exp1, _, _, _, exp2, _, _, _, exp3, _, _, _ \
            = visited_children
        return BasicRunCall(STATEMENTS3[func.text],
                            BasicExpressionList([exp1, exp2, exp3]))

    def visit_go_statement(self, _, visited_children):
        go, _, linenum, _ = visited_children
        return BasicGoto(linenum, False, is_gosub=go.text == 'GOSUB')

    def visit_go_statement(self, _, visited_children):
        go, _, linenum, _ = visited_children
        return BasicGoto(linenum, False, is_gosub=go.text == 'GOSUB')

    def visit_on_n_go_statement(self, node, visited_children):
        _, _, exp, _, go, _, lines, _ = visited_children
        return BasicOnGoStatement(exp, lines, is_gosub=(go.text == 'GOSUB'))

    def visit_linenum_list(self, node, visited_children):
        linenum, _, linenums = visited_children
        return [linenum] + linenums

    def visit_linenum_list0(self, node, visited_children):
        return visited_children

    def visit_linenum_list_elem(self, node, visited_children):
        _, _, linenum, space = visited_children
        return linenum

    def visit_data_statement(self, node, visited_children):
        _, _, exp_list, _ = visited_children
        return BasicDataStatement(exp_list)

    def visit_data_elements(self, node, visited_children):
        data_element, _, data_elements = visited_children
        return BasicExpressionList(
            [data_element] + data_elements.exp_list,
            parens=False
        )

    def visit_dim_element0(self, node, visited_children):
        return visited_children[0]

    def visit_dim_var(self, node, visited_children):
        return visited_children[0]

    def visit_dim_array_var1(self, node, visited_children):
        var, _, _, _, size1, _, _, _ = visited_children
        return BasicArrayRef(var, BasicExpressionList([size1]),
                             is_str_expr=var.is_str_expr)

    def visit_dim_array_var2(self, node, visited_children):
        var, _, _, _, size1, _, _, _, size2, _, _, _ = visited_children
        return BasicArrayRef(var, BasicExpressionList([size1, size2]),
                             is_str_expr=var.is_str_expr)

    def visit_dim_array_var3(self, node, visited_children):
        var, _, _, _, size1, _, _, _, size2, \
          _, _, _, size3, _, _, _ = visited_children
        return BasicArrayRef(var, BasicExpressionList([size1, size2, size3]),
                             is_str_expr=var.is_str_expr)

    def visit_dim_array_var_list(self, node, visited_children):
        dim_var, _, dim_vars = visited_children
        return [dim_var] + dim_vars

    def visit_dim_array_var_list_elements(self, node, visited_children):
        return visited_children

    def visit_dim_array_var_list_element(self, node, visited_children):
        _, _, dim_var, _ = visited_children
        return dim_var

    def visit_data_element0(self, node, visited_children):
        _, _, data_element = visited_children
        return data_element

    def visit_data_elements0(self, node, visited_children):
        return BasicExpressionList(visited_children, parens=False)

    def visit_data_element(self, node, visited_children):
        return visited_children[0]

    def visit_data_num_element(self, node, visited_children):
        _, literal, _ = visited_children
        return literal

    def visit_data_num_element0(self, node, visited_children):
        return visited_children[0]

    def visit_data_str_element(self, node, visited_children):
        return visited_children[0]

    def visit_data_str_element0(self, _, visited_children):
        _, literal, _ = visited_children
        return literal

    def visit_data_str_element1(self, node, visited_children):
        _, literal = visited_children
        return literal

    def visit_data_str_literal(self, node, visited_children):
        return BasicLiteral(node.text)

    def visit_single_kw_statement(self, node, visited_children):
        keyword, _ = visited_children
        return BasicKeywordStatement(SINGLE_KEYWORD_STATEMENTS[keyword.text])

    def visit_for_statement(self, node, visited_children):
        _, _, var, _, _, _, exp1, _, _, _, exp2, _ = visited_children
        return BasicForStatement(var, exp1, exp2)

    def visit_for_step_statement(self, node, visited_children):
        _, _, var, _, _, _, exp1, _, _, _, exp2, _, _, _, exp3, _ \
            = visited_children
        return BasicForStatement(var, exp1, exp2, step_exp=exp3)

    def visit_next_statement(self, node, visited_children):
        return visited_children[0]

    def visit_next_var_statement(self, node, visited_children):
        _, _, var_list, _ = visited_children
        return BasicNextStatement(var_list)

    def visit_next_empty_statement(self, node, visited_children):
        _, _ = visited_children
        return BasicNextStatement(BasicExpressionList([]))

    def visit_var_list(self, node, visited_children):
        var, _, var_list = visited_children
        if var_list:
            return BasicExpressionList([var] + var_list, parens=False)
        return BasicExpressionList([var], parens=False)

    def visit_var_list_elements(self, node, visited_children):
        return visited_children

    def visit_var_list_element(self, node, visited_children):
        _, _, var, _ = visited_children
        return var

    def visit_func_to_statements(self, node, visited_children):
        func, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionalExpression(
            FUNCTIONS_TO_STATEMENTS[func.text],
            BasicExpressionList([exp])
        )

    def visit_func_to_statements2(self, node, visited_children):
        func, _, _, _, exp1, _, _, _, exp2, _, _, _ = visited_children
        return BasicFunctionalExpression(
            FUNCTIONS_TO_STATEMENTS2[func.text],
            BasicExpressionList([exp1, exp2])
        )

    def visit_joystk_to_statement(self, node, visited_children):
        _, _, _, _, exp, _, _, _ = visited_children
        return BasicJoystkExpression(
            BasicExpressionList([exp])
        )

    def visit_dim_statement(self, node, visited_children):
        _, _, dim_var_list = visited_children
        return BasicDimStatement(dim_var_list)

    def visit_clear_statement(self, node, visited_children):
        return BasicComment(f' {node.text.strip() }')

    def visit_read_statement(self, node, visited_children):
        _, _, rhs, _, rhs_list = visited_children
        return BasicReadStatement([rhs] + rhs_list)

    def visit_rhs_list_elements(self, node, visited_children):
        return visited_children

    def visit_rhs_list_element(self, node, visited_children):
        _, _, rhs, _ = visited_children
        return rhs

    def visit_rhs(self, node, visited_children):
        return visited_children[0]

    def visit_input_statement(self, node, visited_children):
        _, _, str_literal, _, rhs, _, rhs_list = visited_children
        if isinstance(str_literal, BasicLiteral):
            str_literal.literal = f'{str_literal.literal}? '
        return BasicInputStatement(str_literal, [rhs] + rhs_list)

    def visit_input_str_literal(self, node, visited_children):
        str_literal, _, _, _ = visited_children
        return str_literal


def convert(progin,
            procname='',
            filter_unused_linenum=False,
            initialize_vars=False,
            skip_procedure_headers=False,
            output_dependencies=False):
    tree = grammar.parse(progin)
    bv = BasicVisitor()
    basic_prog = bv.visit(tree)

    if skip_procedure_headers := skip_procedure_headers or \
       not output_dependencies:
        procname = ''
    else:
        procname = procname if PROCNAME_REGEX.match(procname) else 'program'
    basic_prog.set_procname(procname)

    # Patch up READ statements to handle empty DATA elements
    empty_data_elements_visitor = BasicEmptyDataElementVisitor()
    basic_prog.visit(empty_data_elements_visitor)
    if empty_data_elements_visitor.has_empty_data_elements:
        basic_prog.visit(BasicReadStatementPatcherVisitor())

    # transform functions to proc calls
    basic_prog.visit(BasicFunctionalExpressionPatcherVisitor())

    # Update joystk stuff
    joystk_initializer = JoystickVisitor()
    basic_prog.visit(joystk_initializer)
    basic_prog.extend_prefix_lines(joystk_initializer.joystk_var_statements)

    # initialize variables
    if initialize_vars:
        var_initializer = VarInitializerVisitor()
        basic_prog.visit(var_initializer)
        basic_prog.extend_prefix_lines(var_initializer.assignment_lines)

    # remove unused line numbers
    line_ref_visitor = LineReferenceVisitor()
    basic_prog.visit(line_ref_visitor)
    line_num_filter = LineNumberFilterVisitor(line_ref_visitor.references) \
        if filter_unused_linenum \
        else LineZeroFilterVisitor(line_ref_visitor.references)
    basic_prog.visit(line_num_filter)

    # try to patch up empty next statements
    basic_prog.visit(BasicNextPatcherVisitor())

    # output the program
    program = basic_prog.basic09_text(0)
    if output_dependencies and procname:
        procedure_bank = ProcedureBank()
        procedure_bank.add_from_resource('ecb.b09')
        procedure_bank.add_from_str(program)
        program = procedure_bank.get_procedure_and_dependencies(procname)

    return program + '\n'


def convert_file(input_program_file,
                 output_program_file,
                 procname='',
                 filter_unused_linenum=False,
                 initialize_vars=False,
                 output_dependencies=False):
    progin = input_program_file.read()
    progout = convert(
        progin,
        procname=procname,
        filter_unused_linenum=filter_unused_linenum,
        initialize_vars=initialize_vars,
        output_dependencies=output_dependencies,
    )
    progout = progout.replace('\n', '\r')
    output_program_file.write(progout)