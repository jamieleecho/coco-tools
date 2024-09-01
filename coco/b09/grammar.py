import re
from itertools import chain
from parsimonious.grammar import Grammar


PROCNAME_REGEX = re.compile(r"[a-zA-Z0-9_-]+")

SINGLE_KEYWORD_STATEMENTS = {
    "END": "END",
    "RESTORE": "RESTORE",
    "RETURN": "RETURN",
    "STOP": "STOP",
    "TROFF": "TROFF",
    "TRON": "TRON",
}

QUOTED_SINGLE_KEYWORD_STATEMENTS = [f'"{name}"' for name in SINGLE_KEYWORD_STATEMENTS]

FUNCTIONS = {
    "ABS": "ABS",
    "ATN": "ATN",
    "COS": "COS",
    "EXP": "EXP",
    "FIX": "FIX",
    "LEN": "LEN",
    "LOG": "LOG",
    "PEEK": "PEEK",
    "RND": "RND",
    "SGN": "SGN",
    "SIN": "SIN",
    "SQR": "SQR",
    "TAN": "TAN",
}

QUOTED_FUNCTION_NAMES = [f'"{name}"' for name in FUNCTIONS]

STR2_FUNCTIONS = {
    "LEFT$": "LEFT$",
    "RIGHT$": "RIGHT$",
}

QUOTED_STR2_FUNCTION_NAMES = [f'"{name}"' for name in STR2_FUNCTIONS]

STR3_FUNCTIONS = {
    "MID$": "MID$",
}

QUOTED_STR3_FUNCTION_NAMES = [f'"{name}"' for name in STR3_FUNCTIONS]

STR_NUM_FUNCTIONS = {
    "ASC": "ASC",
    "VAL": "VAL",
    "LEN": "LEN",
}

QUOTED_STR_NUM_FUNCTIONS_NAMES = [f'"{name}"' for name in STR_NUM_FUNCTIONS]

NUM_STR_FUNCTIONS = {
    "CHR$": "CHR$",
    "TAB": "TAB",
}

QUOTED_NUM_STR_FUNCTIONS_NAMES = [f'"{name}"' for name in NUM_STR_FUNCTIONS]

STATEMENTS2 = {
    "RESET": "RUN ecb_reset",
}

QUOTED_STATEMENTS2_NAMES = [f'"{name}"' for name in STATEMENTS2]

STATEMENTS3 = {
    "SET": "RUN ecb_set",
}

QUOTED_STATEMENTS3_NAMES = [f'"{name}"' for name in STATEMENTS3]

FUNCTIONS_TO_STATEMENTS = {
    "BUTTON": "RUN ecb_button",
    "INT": "RUN ecb_int",
}

QUOTED_FUNCTIONS_TO_STATEMENTS_NAMES = [f'"{name}"' for name in FUNCTIONS_TO_STATEMENTS]

FUNCTIONS_TO_STATEMENTS2 = {
    "POINT": "RUN ecb_point",
}

QUOTED_FUNCTIONS_TO_STATEMENTS2_NAMES = [
    f'"{name}"' for name in FUNCTIONS_TO_STATEMENTS2
]

NUM_STR_FUNCTIONS_TO_STATEMENTS = {
    "HEX$": "RUN ecb_hex",
    "STR$": "RUN ecb_str",
}

QUOTED_NUM_STR_FUNCTIONS_TO_STATEMENTS_NAMES = [
    f'"{name}"' for name in NUM_STR_FUNCTIONS_TO_STATEMENTS
]

STR_FUNCTIONS_TO_STATEMENTS = {
    "INKEY$": "RUN inkey",
}

QUOTED_STR_FUNCTIONS_TO_STATEMENTS_NAMES = [
    f'"{name}"' for name in STR_FUNCTIONS_TO_STATEMENTS
]

KEYWORDS = "|".join(
    chain(
        (
            "ABS",
            "AND",
            "ASC",
            "ATN",
            "ATTR",
            "BRK",
            "BUTTON",
            "CHR$",
            "CLS",
            "CLEAR",
            "CMP",
            "COS",
            "DATA",
            "DIM",
            "ELSE",
            "END",
            "ERNO",
            "ERR",
            "EXP",
            "FIX",
            "FOR",
            "GOSUB",
            "GOTO",
            "HBUFF",
            "HGET" "HCIRCLE",
            "HCLS",
            "HCOLOR",
            "HEX$",
            "HLINE",
            "HPAINT",
            "HPRINT",
            "HPUT",
            "HRESET",
            "HSET",
            "HSCREEN",
            "IF",
            "INKEY$",
            "INPUT",
            "INSTR",
            "INT",
            "JOYSTK",
            "LEFT",
            "LEN",
            "LET",
            "LINE",
            "LOCATE",
            "LOG",
            "NOT",
            "OR",
            "MID$",
            "NEXT",
            "NOT",
            "OPEN",
            "OR",
            "PALETTE",
            "PEEK",
            "PLAY",
            "POKE",
            "PRESET",
            "PRINT",
            "PSET",
            "READ",
            "REM",
            "RESET",
            "RESTORE",
            "RETURN",
            "RGB",
            "RIGHT$",
            "RND",
            "SET",
            "SGN",
            "SIN",
            "SOUND",
            "SQRT",
            "STEP",
            "STOP",
            "STR$",
            "STRING$",
            "TAB",
            "TAN",
            "THEN",
            "TO",
            "TROFF",
            "TRON",
            "WIDTH",
            "VAL",
            "VARPTR",
        ),
        SINGLE_KEYWORD_STATEMENTS.keys(),
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
        STR_FUNCTIONS_TO_STATEMENTS.keys(),
    )
)

grammar = Grammar(
    rf"""
    aaa_prog            = multi_line eol* ~r"\x00?" eof
    multi_line          = line space* multi_line_elements
    multi_line_elements = multi_line_element*
    multi_line_element  = eol+ line space*
    lhs             = str_array_ref_exp / str_var / array_ref_exp / var
    array_ref_exp   = var space* exp_list
    arr_assign      = "LET"? space* array_ref_exp space* "=" space* exp
    str_array_ref_exp   = str_var space* exp_list
    str_arr_assign  = "LET"? space* str_array_ref_exp space* "=" space* str_exp
    comment         = comment_token comment_text
    exp_list        = "(" space* exp space* exp_sublist ")"
    exp_sublist     = exp_sublist_mbr*
    exp_sublist_mbr = ("," space* exp space*)
    if_if_else_stmnt = ("IF" space* if_exp space*
                        "THEN" space* explicit_line_or_stmnts space* else_if_stmnts
                        else_stmnts)
    if_else_stmnt    = ("IF" space* if_exp space*
                        "THEN" space* explicit_line_or_stmnts space* else_stmnt)
    else_if_stmnts  = else_if_stmnt+
    else_if_stmnt   = ("ELSE" space* "IF" space* if_exp space*
                       "THEN" space* explicit_line_or_stmnts space*)
    else_stmnts     = else_stmnt?
    else_stmnt      = ("ELSE" space* explicit_line_or_stmnts space*)
    if_stmnt        = ("IF" space* if_exp space*
                       "THEN" space* line_or_stmnts)
    line            = linenum space* statements space*
    line_or_stmnts  = linenum
                    / statements
    explicit_line_or_stmnts  = linenum
                             / statements
    str_assign      = "LET"? space* str_var space* "=" space* str_exp
    num_assign      = "LET"? space* var space* "=" space* exp
    statement       = if_if_else_stmnt
                    / if_else_stmnt
                    / if_stmnt
                    / print_at_statement
                    / print_at_statement0
                    / print_statement
                    / num_assign
                    / str_assign
                    / arr_assign
                    / str_arr_assign
                    / sound
                    / poke_statement
                    / cls
                    / go_statement
                    / on_brk_go_statement
                    / on_err_go_statement
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
                    / width_statement
                    / locate_statement
                    / attr_statement
                    / reset_colors_statement
                    / palette_reset_statement
                    / palette_statement
                    / hscreen_statement
                    / hcls_statement
                    / harc_statement
                    / hellipse_statement
                    / hcircle_statement
                    / hprint_statement
                    / hcolor_statement
                    / hcolor1_statement
                    / hline_relative_statement
                    / hline_statement
                    / hreset_statement
                    / hset3_statement
                    / hset_statement
                    / play_statement
                    / hdraw_statement
                    / hbuff_statement
                    / hget_statement
                    / hput_statement
                    / hpaint_statement
    statement2      = ({ ' / '.join(QUOTED_STATEMENTS2_NAMES)}) space* "(" space* exp space* "," space* exp space* ")" space*
    statement3      = ({ ' / '.join(QUOTED_STATEMENTS3_NAMES)}) space* "(" space* exp space* "," space* exp space* "," space* exp space* ")" space*
    statements           = statement? space* statements_elements space* last_statement?
    last_statement  = comment / partial_str_arr_assign / partial_str_assign
    partial_str_arr_assign = "LET"? space* str_array_ref_exp space* "=" space* partial_str_lit
    partial_str_assign = "LET"? space* str_var space* "=" space* partial_str_lit
    statements_elements  = statements_element*
    statements_element   = ":" space* statement? space*
    statements_else      = statements
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
    bool_paren_exp  = "(" space* bool_exp space* ")" space*
    bool_bin_exp    = num_sum_exp space* ("<=" / ">=" / "<>" / "<" / ">" / "=>" / "=<" / "=") space* num_sum_exp space*
    bool_str_exp    = str_exp space* ("<=" / ">=" / "<>" / "<" / ">" / "=>" / "=<" / "=") space* str_exp space*
    num_exp              = num_and_exp space* num_exp_elements
    num_exp_elements     = num_exp_element*
    num_exp_element      = "OR" space* num_and_exp space*
    num_and_exp          = num_gtle_exp space* num_and_exp_elements
    num_and_exp_elements = num_and_exp_element*
    num_and_exp_element  = "AND" space* num_gtle_exp space*
    num_gtle_exp         = num_sum_exp space* num_glte_sub_exps
    num_glte_sub_exps    = num_glte_sub_exp?
    num_glte_sub_exp     = (("<=" / ">=" / "<>" / "<" / ">" / "=>" / "=<" / "=") space* num_sum_exp space*)
    num_sum_exp          = num_prod_exp space* num_sum_sub_exps
    num_sum_sub_exps     = num_sum_sub_exp*
    num_sum_sub_exp      = (("+" / "-") space* num_prod_exp space*)
    num_prod_exp         = num_power_exp space* num_prod_sub_exps
    num_prod_sub_exps    = num_prod_sub_exp*
    num_prod_sub_exp     = (("*" / "/") space* num_power_exp space*)
    num_power_exp        = val_exp space* num_power_sub_exps
    num_power_sub_exps   = num_power_sub_exp*
    num_power_sub_exp    = ("^" space* val_exp space*)
    func_exp        = ({ ' / '.join(QUOTED_FUNCTION_NAMES)}) space* "(" space* exp space* ")" space*
    func_str_exp    = ({ ' / '.join(QUOTED_STR_NUM_FUNCTIONS_NAMES)}) space* "(" space* str_exp space* ")" space*
    val_exp         = num_literal
                    / hex_literal
                    / paren_exp
                    / unop_exp
                    / func_exp
                    / func_str_exp
                    / func_to_statements
                    / func_to_statements2
                    / joystk_to_statement
                    / varptr_expr
                    / erno_expr
                    / instr_expr
                    / array_ref_exp
                    / var
    unop_exp        = unop space* exp
    paren_exp       =  "(" space* exp space* ")" space*
    str_exp          = str_simple_exp space* str_exp_elements
    str_exp_elements = str_exp_element*
    str_exp_element  = "+" space* str_simple_exp space*
    str2_func_exp    = ({ ' / '.join(QUOTED_STR2_FUNCTION_NAMES)}) space* "(" space* str_exp space* "," space* exp space* ")" space*
    str3_func_exp    = ({ ' / '.join(QUOTED_STR3_FUNCTION_NAMES)}) space* "(" space* str_exp space* "," space* exp space* "," space* exp space* ")" space*
    num_str_func_exp = ({ ' / '.join(QUOTED_NUM_STR_FUNCTIONS_NAMES)}) space* "(" space* exp space* ")" space*
    num_str_func_exp_statements = ({ ' / '.join(QUOTED_NUM_STR_FUNCTIONS_TO_STATEMENTS_NAMES)}) space* "(" space* exp space* ")" space*
    str_func_exp_statements = ({ ' / '.join(QUOTED_STR_FUNCTIONS_TO_STATEMENTS_NAMES)}) space*
    str_simple_exp   = str_literal
                     / str2_func_exp
                     / str3_func_exp
                     / string_expr
                     / num_str_func_exp
                     / num_str_func_exp_statements
                     / str_func_exp_statements
                     / str_array_ref_exp
                     / str_var
    comment_text    = ~r".*"
    comment_token   = ~r"(REM|')"
    eof             = ~r"$"
    eol             = ~r"[\n\r]+"
    linenum         = ~r"[0-9]+"
    literal         = num_literal
    hex_literal     = ~r"& *H *[0-9A-F][0-9A-F]?[0-9A-F]?[0-9A-F]?[0-9A-F]?[0-9A-F]?"
    num_literal     = ~r"([\+\- ]*(\d*\.\d*)( *(?!ELSE)E *[\+\-]? *\d*))|[\+\- ]*(\d*\.\d*)|[\+\- ]*(\d+( *(?!ELSE)E *[\+\-]? *\d*))|[\+\- ]*(\d+)"
    int_literal     = ~r"(\d+)"
    int_hex_literal = ~r"& *H *[0-9A-F][0-9A-F]?[0-9A-F]?[0-9A-F]?[0-9A-F]?[0-9A-F]?"
    space           = ~r" "
    str_literal     = ~r'\"[^"\n]*\"'
    partial_str_lit = ~r'\"[^"\n]*'
    unop            = "+" / "-"
    var             = ~r"(?!{KEYWORDS}|([A-Z][A-Z0-9]*\$))([A-Z][A-Z0-9]*)"
    str_var         = ~r"(?!{KEYWORDS})([A-Z][A-Z0-9]*)\$"
    print_statement = ("PRINT"/"?") space* print_args space*
    print_at_statement = ("PRINT"/"?") space* "@" space* exp space* "," space* print_args space*
    print_at_statement0 = ("PRINT"/"?") space* "@" space* exp space*
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
    on_err_go_statement = "ON" space* "ERR" space* "GOTO" space* linenum space*
    on_brk_go_statement = "ON" space* "BRK" space* "GOTO" space* linenum space*
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
    dim_element0        = (int_literal / int_hex_literal)
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
    input_statement     = "LINE"? space* "INPUT" space* input_str_literal? space* rhs space* rhs_list_elements
    input_str_literal   = str_literal space* ';' space*
    varptr_expr         = "VARPTR" space* "(" space* lhs space* ")" space*
    instr_expr          = "INSTR" space* "(" space* exp space* "," space* str_exp space* "," space* str_exp space* ")" space*
    string_expr         = "STRING$" space* "(" space* exp space* "," space* str_exp space* ")" space*
    width_statement     = "WIDTH" space* exp space*
    locate_statement    = "LOCATE" space* exp space* "," space* exp space*
    attr_statement           = "ATTR" space* exp space* "," space* exp space* attr_option_list
    attr_option_list         = attr_option_list_element*
    attr_option_list_element = "," space* attr_option space*
    attr_option              = "B" / "U"
    reset_colors_statement   = ("CMP" / "RGB") space*
    palette_reset_statement  = "PALETTE" space* ("CMP" / "RGB") space*
    palette_statement        = "PALETTE" space* exp space* "," space* exp space*
    hscreen_statement        = "HSCREEN" space* exp? space*
    hcls_statement           = "HCLS" space* exp? space*
    hcircle_statement        = hcircle_prefix hcircle_optional?
    hcircle_prefix           = "HCIRCLE" space* coords "," space* exp space*
    hcircle_optional         = "," space* exp? space*
    hellipse_statement       = hcircle_prefix hcircle_optional "," space* exp space*
    harc_statement           = hellipse_statement "," space* exp space* "," space* exp space*
    hprint_statement         = "HPRINT" space* "(" space* exp space* "," space* exp space* ")" space* "," space* print_arg space*
    hcolor_statement         = "HCOLOR" space* exp space* "," space* exp space*
    hcolor1_statement        = "HCOLOR" space* exp space*
    hline_relative_statement = "HLINE" space* line_suffix
    hline_statement          = "HLINE" space* coords space* line_suffix
    line_suffix              = "-" space* coords space* "," space* pset_or_preset line_options_option
    pset_or_preset           = ("PSET" / "PRESET") space*
    coords                   = "(" space* exp space* "," space* exp space* ")" space*
    line_options_option      = line_options?
    line_options             = "," space* ("BF" / "B") space*
    hreset_statement         = "HRESET" space* coords
    hset3_statement          = "HSET" space* coords3
    hset_statement           = "HSET" space* coords
    coords3                  = "(" space* exp space* "," space* exp space* "," space* exp space* ")" space*
    erno_expr                = "ERNO" space*
    play_statement           = "PLAY" space* str_exp space*
    hdraw_statement          = "HDRAW" space* str_exp space*
    hbuff_statement          = "HBUFF" space* exp space* "," space* exp space*
    hget_statement           = "HGET" space* coords "-" space* coords "," space* exp space*
    hput_statement           = "HPUT" space* coords "-" space* coords "," space* exp space* "," space* draw_mode space*
    draw_mode                = "AND" / "NOT" / "OR" / "PRESET" / "PSET" / "XOR"
    hpaint_statement         = "HPAINT" space* coords space* hpaint_args
    hpaint_args              = hpaint_2arg / hpaint_1arg / space*
    hpaint_2arg              = hpaint_arg hpaint_arg
    hpaint_1arg              = hpaint_arg space*
    hpaint_arg               = "," space* exp space*
    """  # noqa
)
