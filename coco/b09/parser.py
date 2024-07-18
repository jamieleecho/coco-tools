from parsimonious import NodeVisitor
from coco.b09.grammar import (
    FUNCTIONS,
    FUNCTIONS_TO_STATEMENTS,
    FUNCTIONS_TO_STATEMENTS2,
    NUM_STR_FUNCTIONS,
    NUM_STR_FUNCTIONS_TO_STATEMENTS,
    SINGLE_KEYWORD_STATEMENTS,
    STATEMENTS2,
    STATEMENTS3,
    STR2_FUNCTIONS,
    STR3_FUNCTIONS,
    STR_FUNCTIONS_TO_STATEMENTS,
    STR_NUM_FUNCTIONS,
    grammar,
)

from coco.b09.elements import (
    AbstractBasicConstruct,
    AbstractBasicExpression,
    Basic09CodeStatement,
    BasicArcStatement,
    BasicArrayRef,
    BasicAssignment,
    BasicBinaryExp,
    BasicBooleanBinaryExp,
    BasicBooleanOpExp,
    BasicBooleanParenExp,
    BasicCircleStatement,
    BasicCls,
    BasicComment,
    BasicDataStatement,
    BasicDimStatement,
    BasicEllipseStatement,
    BasicExpressionList,
    BasicForStatement,
    BasicFunctionCall,
    BasicFunctionalExpression,
    BasicGoto,
    BasicIf,
    BasicInputStatement,
    BasicJoystkExpression,
    BasicKeywordStatement,
    BasicLine,
    BasicLiteral,
    BasicNextStatement,
    BasicOnGoStatement,
    BasicOpExp,
    BasicOperator,
    BasicParenExp,
    BasicPoke,
    BasicPrintArgs,
    BasicPrintControl,
    BasicPrintStatement,
    BasicReadStatement,
    BasicRunCall,
    BasicSound,
    BasicStatements,
    BasicVar,
    BasicVarptrExpression,
    BasicWidthStatement,
    HexLiteral,
)
from coco.b09.grammar import PROCNAME_REGEX
from coco.b09.prog import BasicProg
from coco.b09.visitors import (
    BasicEmptyDataElementVisitor,
    BasicFunctionalExpressionPatcherVisitor,
    BasicInputStatementPatcherVisitor,
    BasicNextPatcherVisitor,
    BasicPrintStatementPatcherVisitor,
    BasicReadStatementPatcherVisitor,
    JoystickVisitor,
    LineNumberFilterVisitor,
    LineReferenceVisitor,
    LineZeroFilterVisitor,
    VarInitializerVisitor,
)
from coco.b09.procbank import ProcedureBank


class BasicVisitor(NodeVisitor):
    def generic_visit(self, node, visited_children):
        if node.text.strip() == "":
            return ""

        if node.text in {
            "^",
            "*",
            "/",
            "+",
            "-",
            "&",
            "<",
            ">",
            "<>",
            "=",
            "<=",
            "=<",
            ">=",
            "=>",
            "AND",
            "OR",
            "NOT",
        }:
            return BasicOperator(node.text)

        if len(visited_children) == 4 and isinstance(
            visited_children[0], BasicOperator
        ):
            operator, _, exp, _ = visited_children
            return BasicOpExp(operator.operator, exp)
        if len(visited_children) == 1:
            if isinstance(visited_children[0], AbstractBasicConstruct):
                return visited_children[0]

            if visited_children[0] is str:
                return visited_children[0]

        if len(visited_children) == 2:
            if isinstance(visited_children[0], BasicOpExp) and isinstance(
                visited_children[1], BasicOpExp
            ):
                exp1, exp2 = visited_children
                return BasicOpExp(
                    exp1.operator,
                    BasicBinaryExp(exp1.exp, exp2.operator, exp2.exp),
                )
            if (
                isinstance(visited_children[0], node)
                and visited_children[0].text == ":"
            ):
                return visited_children[1]

        return node

    def visit_aaa_prog(self, node, visited_children):
        return BasicProg(visited_children[0])

    def visit_arr_assign(self, node, visited_children):
        let_kw, _, array_ref_exp, _, _, _, val_exp = visited_children
        return BasicAssignment(array_ref_exp, val_exp, let_kw=let_kw != "")

    def visit_array_ref_exp(self, node, visited_children):
        var, _, exp_list = visited_children
        return BasicArrayRef(var, exp_list)

    def visit_str_arr_assign(self, node, visited_children):
        let_kw, _, str_array_ref_exp, _, _, _, str_exp = visited_children
        return BasicAssignment(str_array_ref_exp, str_exp, let_kw=let_kw != "")

    def visit_str_array_ref_exp(self, node, visited_children):
        str_var, _, exp_list = visited_children
        return BasicArrayRef(str_var, exp_list, is_str_expr=True)

    def visit_comment(self, node, visited_children):
        return BasicComment(visited_children[1])

    def visit_comment_text(self, node, visited_children):
        return node.full_text[node.start : node.end]

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
        is_bool = isinstance(
            exp,
            (BasicBooleanBinaryExp, BasicBooleanOpExp, BasicBooleanParenExp),
        )
        exp = exp if is_bool else BasicBooleanBinaryExp(exp, "<>", BasicLiteral(0.0))
        return BasicIf(exp, statements)

    def visit_if_exp(self, node, visited_children):
        return visited_children[0]

    def visit_bool_exp(self, node, visited_children):
        not_keyword, _, exp = visited_children
        return (
            BasicBooleanOpExp(not_keyword.operator, exp)
            if isinstance(not_keyword, BasicOperator)
            else exp
        )

    def visit_bool_or_exp(self, node, visited_children):
        exp1, _, exp_ops = visited_children
        if len(exp_ops) == 0:
            return exp1
        last_exp = exp1
        for exp_op in exp_ops:
            last_exp = BasicBooleanBinaryExp(last_exp, exp_op.operator, exp_op.exp)
        return last_exp

    def visit_bool_or_exp_elements(self, _, visited_children):
        return visited_children

    def visit_bool_or_exp_element(self, _, visited_children):
        _, _, exp, _ = visited_children
        return BasicBooleanOpExp("OR", exp)

    def visit_bool_and_exp(self, node, visited_children):
        return self.visit_bool_or_exp(node, visited_children)

    def visit_bool_and_exp_elements(self, _, visited_children):
        return visited_children

    def visit_bool_and_exp_element(self, _, visited_children):
        _, _, exp, _ = visited_children
        return BasicBooleanOpExp("AND", exp)

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
        return self.visit_binary_exp(node, visited_children)

    def visit_line(self, node, visited_children):
        return BasicLine(
            visited_children[0],
            next(
                child
                for child in visited_children
                if isinstance(child, BasicStatements)
            ),
        )

    def visit_linenum(self, node, visited_children):
        return int(node.full_text[node.start : node.end])

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
            last_exp = BasicBinaryExp(last_exp, exp_op.operator, exp_op.exp)
        return last_exp

    def visit_num_exp_elements(self, node, visited_children):
        return visited_children

    def visit_num_exp_element(self, node, visited_children):
        _, _, exp, _ = visited_children
        return BasicOpExp("OR", exp)

    def visit_num_and_exp(self, node, visited_children):
        return self.visit_num_exp(node, visited_children)

    def visit_num_and_exp_elements(self, node, visited_children):
        return visited_children

    def visit_num_and_exp_element(self, node, visited_children):
        _, _, exp, _ = visited_children
        return BasicOpExp("AND", exp)

    def visit_str_exp(self, node, visited_children):
        """
        str_exp          = str_simple_exp space* str_exp_elements
        str_exp_element  = "+" space* str_simple_exp space*
        """
        exp, _, exps = visited_children
        if len(exps) == 0:
            return exp
        last_exp = exp
        for exp in exps:
            last_exp = BasicBinaryExp(last_exp, "+", exp)
        return last_exp

    def visit_str_exp_elements(self, node, visited_children):
        """str_exp_elements = str_exp_element*"""
        return visited_children

    def visit_str_exp_element(self, node, visited_children):
        """str_exp_element  = "+" space* str_simple_exp space*"""
        _, _, exp, _ = visited_children
        return exp

    def visit_str2_func_exp(self, node, visited_children):
        func, _, _, _, str_exp, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionCall(
            STR2_FUNCTIONS[func.text],
            BasicExpressionList([str_exp, exp]),
            is_str_expr=True,
        )

    def visit_str3_func_exp(self, node, visited_children):
        (
            func,
            _,
            _,
            _,
            str_exp,
            _,
            _,
            _,
            exp1,
            _,
            _,
            _,
            exp2,
            _,
            _,
            _,
        ) = visited_children
        return BasicFunctionCall(
            STR3_FUNCTIONS[func.text],
            BasicExpressionList([str_exp, exp1, exp2]),
            is_str_expr=True,
        )

    def visit_num_str_func_exp(self, node, visited_children):
        func, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionCall(
            NUM_STR_FUNCTIONS[func.text],
            BasicExpressionList([exp]),
            is_str_expr=True,
        )

    def visit_num_str_func_exp_statements(self, node, visited_children):
        func, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionalExpression(
            NUM_STR_FUNCTIONS_TO_STATEMENTS[func.text],
            BasicExpressionList([exp]),
            is_str_expr=True,
        )

    def visit_str_func_exp_statements(self, node, visited_children):
        (
            func,
            _,
        ) = visited_children
        return BasicFunctionalExpression(
            STR_FUNCTIONS_TO_STATEMENTS[func.text],
            BasicExpressionList([]),
            is_str_expr=True,
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

    def visit_lhs(self, node, visited_children):
        return visited_children[0]

    def visit_num_literal(self, node, visited_children):
        num_literal = node.full_text[node.start : node.end].replace(" ", "")
        return BasicLiteral(float(num_literal))

    def visit_int_literal(self, node, visited_children):
        num_literal = node.full_text[node.start : node.end].replace(" ", "")
        return BasicLiteral(int(num_literal))

    def visit_hex_literal(self, node, visited_children):
        hex_literal = node.text[node.text.find("H") + 1 :]
        return HexLiteral(hex_literal)

    def visit_unop_exp(self, node, visited_children):
        op, _, exp = visited_children
        return BasicOpExp(op.operator, exp)

    def visit_unop(self, node, visited_children):
        return visited_children[0]

    def visit_paren_exp(self, node, visited_children):
        return BasicParenExp(visited_children[2])

    def visit_num_prod_exp(self, node, visited_children):
        return self.visit_binary_exp(node, visited_children)

    def visit_num_power_exp(self, node, visited_children):
        return self.visit_binary_exp(node, visited_children)

    def visit_binary_exp(self, node, visited_children):
        v1, v2, v3 = visited_children
        if isinstance(v2, str) and isinstance(v3, str):
            return v1
        return BasicBinaryExp(v1, v3.operator, v3.exp)

    def visit_func_exp(self, node, visited_children):
        func, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionCall(FUNCTIONS[func.text], BasicExpressionList([exp]))

    def visit_func_str_exp(self, node, visited_children):
        func, _, _, _, exp, _, _, _ = visited_children
        return BasicFunctionCall(
            STR_NUM_FUNCTIONS[func.text], BasicExpressionList([exp])
        )

    def visit_num_assign(self, node, visited_children):
        let_kw, _, var, _, _, _, val = visited_children
        return BasicAssignment(var, val, let_kw=let_kw != "")

    def visit_str_assign(self, node, visited_children):
        return self.visit_num_assign(node, visited_children)

    def visit_space(self, node, visited_children):
        return node.text

    def visit_statement(self, node, visited_children):
        return visited_children[0]

    def visit_statements(self, node, visited_children):
        statement, _, statement_elements, _, basic_comment = visited_children
        statement_elements = (
            [statement] + statement_elements if statement else statement_elements
        )
        statement_elements = (
            statement_elements + [basic_comment]
            if basic_comment
            else statement_elements
        )
        return BasicStatements(statement_elements)

    def visit_statements_elements(self, node, visited_children):
        return [statement for statement in visited_children if statement]

    def visit_statements_element(self, node, visited_children):
        _, _, statement, _ = visited_children
        return statement or None

    def visit_statements_else(self, node, visited_children):
        return visited_children[0]

    def visit_str_literal(self, node, visited_children):
        return BasicLiteral(
            str(node.full_text[node.start + 1 : node.end - 1]),
            is_str_expr=True,
        )

    def visit_num_sum_exp(self, node, visited_children):
        return self.visit_binary_exp(node, visited_children)

    def visit_val_exp(self, node, visited_children):
        return visited_children[0] if len(visited_children) < 2 else node

    def visit_var(self, node, visited_children):
        return BasicVar(node.full_text[node.start : node.end])

    def visit_str_var(self, node, visited_children):
        return BasicVar(node.full_text[node.start : node.end], True)

    def visit_print_statement(self, node, visited_children):
        _, _, print_args, _ = visited_children
        return BasicPrintStatement(print_args)

    def visit_print_at_statement(self, node, visited_children):
        _, _, _, _, loc, _, _, _, print_args, _ = visited_children
        at_statement = BasicRunCall("RUN ecb_at", BasicExpressionList([loc]))
        print_statement = BasicPrintStatement(print_args)
        return BasicStatements([at_statement, print_statement], multi_line=False)

    def visit_print_at_statement0(self, node, visited_children):
        _, _, _, _, loc, _ = visited_children
        return BasicRunCall("RUN ecb_at", BasicExpressionList([loc]))

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
        return BasicCls(exp if isinstance(exp, AbstractBasicExpression) else None)

    def visit_statement2(self, node, visited_children):
        func, _, _, _, exp1, _, _, _, exp2, _, _, _ = visited_children
        return BasicRunCall(STATEMENTS2[func.text], BasicExpressionList([exp1, exp2]))

    def visit_statement3(self, node, visited_children):
        (
            func,
            _,
            _,
            _,
            exp1,
            _,
            _,
            _,
            exp2,
            _,
            _,
            _,
            exp3,
            _,
            _,
            _,
        ) = visited_children
        return BasicRunCall(
            STATEMENTS3[func.text], BasicExpressionList([exp1, exp2, exp3])
        )

    def visit_go_statement(self, _, visited_children):
        go, _, linenum, _ = visited_children
        return BasicGoto(linenum, False, is_gosub=go.text == "GOSUB")

    def visit_on_n_go_statement(self, node, visited_children):
        _, _, exp, _, go, _, lines, _ = visited_children
        return BasicOnGoStatement(exp, lines, is_gosub=(go.text == "GOSUB"))

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
            [data_element] + data_elements.exp_list, parens=False
        )

    def visit_dim_element0(self, node, visited_children):
        return visited_children[0]

    def visit_dim_var(self, node, visited_children):
        return visited_children[0]

    def visit_dim_array_var1(self, node, visited_children):
        var, _, _, _, size1, _, _, _ = visited_children
        return BasicArrayRef(
            var, BasicExpressionList([size1]), is_str_expr=var.is_str_expr
        )

    def visit_dim_array_var2(self, node, visited_children):
        var, _, _, _, size1, _, _, _, size2, _, _, _ = visited_children
        return BasicArrayRef(
            var,
            BasicExpressionList([size1, size2]),
            is_str_expr=var.is_str_expr,
        )

    def visit_dim_array_var3(self, node, visited_children):
        (
            var,
            _,
            _,
            _,
            size1,
            _,
            _,
            _,
            size2,
            _,
            _,
            _,
            size3,
            _,
            _,
            _,
        ) = visited_children
        return BasicArrayRef(
            var,
            BasicExpressionList([size1, size2, size3]),
            is_str_expr=var.is_str_expr,
        )

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
        (
            _,
            _,
            var,
            _,
            _,
            _,
            exp1,
            _,
            _,
            _,
            exp2,
            _,
            _,
            _,
            exp3,
            _,
        ) = visited_children
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
            FUNCTIONS_TO_STATEMENTS[func.text], BasicExpressionList([exp])
        )

    def visit_func_to_statements2(self, node, visited_children):
        func, _, _, _, exp1, _, _, _, exp2, _, _, _ = visited_children
        return BasicFunctionalExpression(
            FUNCTIONS_TO_STATEMENTS2[func.text],
            BasicExpressionList([exp1, exp2]),
        )

    def visit_joystk_to_statement(self, node, visited_children):
        _, _, _, _, exp, _, _, _ = visited_children
        return BasicJoystkExpression(BasicExpressionList([exp]))

    def visit_dim_statement(self, node, visited_children):
        _, _, dim_var_list = visited_children
        return BasicDimStatement(dim_var_list)

    def visit_clear_statement(self, node, visited_children):
        return BasicComment(f" {node.text.strip() }")

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
        line, _, _, _, str_literal, _, rhs, _, rhs_list = visited_children
        if isinstance(str_literal, BasicLiteral):
            str_literal.literal = (
                str_literal.literal if line != "" else f"{str_literal.literal}? "
            )
        else:
            str_literal = BasicLiteral("" if line != "" else "? ", is_str_expr=True)
        return BasicInputStatement(str_literal, [rhs] + rhs_list)

    def visit_input_str_literal(self, node, visited_children):
        str_literal, _, _, _ = visited_children
        return str_literal

    def visit_varptr_expr(self, node, visited_children):
        _, _, _, _, var, _, _, _ = visited_children
        return BasicVarptrExpression(var)

    def visit_instr_expr(self, node, visited_children):
        (
            _,
            _,
            _,
            _,
            index,
            _,
            _,
            _,
            str0,
            _,
            _,
            _,
            str1,
            _,
            _,
            _,
        ) = visited_children
        return BasicFunctionalExpression(
            "run ecb_instr", BasicExpressionList([index, str0, str1])
        )

    def visit_string_expr(self, node, visited_children):
        _, _, _, _, count, _, _, _, strexp, _, _, _ = visited_children
        return BasicFunctionalExpression(
            "run ecb_string", BasicExpressionList([count, strexp])
        )

    def visit_width_statement(self, node, visited_children):
        _, _, exp, _ = visited_children
        return BasicWidthStatement(exp)

    def visit_locate_statement(self, node, visited_children):
        _, _, col, _, _, _, row, _ = visited_children
        return BasicRunCall("run ecb_locate", BasicExpressionList([col, row]))

    def visit_attr_statement(self, node, visited_children):
        _, _, background_color, _, _, _, foreground_color, _, options = visited_children
        blink = BasicLiteral(1.0 if "B" in options else 0.0)
        undrln = BasicLiteral(1.0 if "U" in options else 0.0)
        return BasicRunCall(
            "run ecb_attr",
            BasicExpressionList(
                [
                    background_color,
                    foreground_color,
                    blink,
                    undrln,
                    BasicVar("display"),
                ]
            ),
        )

    def visit_attr_option_list(self, node, visited_children):
        return visited_children

    def visit_attr_option_list_element(self, node, visited_children):
        _, _, attr_option, _ = visited_children
        return attr_option

    def visit_attr_option(self, node, visited_children):
        return node.text

    def visit_reset_colors_statement(self, node, visited_children):
        color_set, _ = visited_children
        return BasicRunCall(
            f"run ecb_set_palette_{color_set.text.lower()}",
            BasicExpressionList([BasicVar("display")]),
        )

    def visit_palette_reset_statement(self, node, visited_children):
        _, _, color_set, _ = visited_children
        return BasicRunCall(
            f"run ecb_set_palette_{color_set.text.lower()}",
            BasicExpressionList([BasicVar("display")]),
        )

    def visit_palette_statement(self, node, visited_children):
        _, _, register, _, _, _, color_code, _ = visited_children
        return BasicRunCall(
            "run ecb_set_palette",
            BasicExpressionList(
                [
                    register,
                    color_code,
                    BasicVar("display"),
                ]
            ),
        )

    def visit_hscreen_statement(self, node, visited_children):
        _, _, exp, _ = visited_children
        exp = BasicLiteral(0) if not isinstance(exp, AbstractBasicExpression) else exp
        return BasicRunCall(
            "run ecb_hscreen",
            BasicExpressionList(
                [
                    exp,
                    BasicVar("display"),
                ]
            ),
        )

    def visit_hcls_statement(self, node, visited_children):
        _, _, exp, _ = visited_children
        exp = BasicLiteral(-1) if not isinstance(exp, AbstractBasicExpression) else exp
        return BasicRunCall(
            "run ecb_hcls",
            BasicExpressionList(
                [
                    exp,
                    BasicVar("display"),
                ]
            ),
        )

    def visit_hcircle_prefix(self, node, visited_children):
        _, _, _, _, expr_x, _, _, _, expr_y, _, _, _, _, _, expr_r, _ = visited_children
        return BasicCircleStatement(expr_x, expr_y, expr_r)

    def visit_hcircle_optional(self, node, visited_children):
        _, _, expr_color, _ = visited_children
        return expr_color

    def visit_hcircle_statement(self, node, visited_children):
        circle_statement, expr_color = visited_children
        return BasicCircleStatement(
            circle_statement.expr_x,
            circle_statement.expr_y,
            circle_statement.expr_r,
            expr_color=None if expr_color == "" else expr_color,
        )

    def visit_hellipse_statement(self, node, visited_children):
        circle_statement, expr_color, _, _, expr_rt, _ = visited_children
        new_circle_statement: BasicCircleStatement = BasicCircleStatement(
            circle_statement.expr_x,
            circle_statement.expr_y,
            circle_statement.expr_r,
            expr_color=None if expr_color == "" else expr_color,
        )
        return BasicEllipseStatement(
            new_circle_statement,
            expr_rt,
        )

    def visit_harc_statement(self, node, visited_children):
        ellipse_statement, _, _, expr_start, _, _, _, expr_end, _ = visited_children
        return BasicArcStatement(
            ellipse_statement,
            expr_start,
            expr_end,
        )

    def visit_hprint_statement(self, node, visited_children):
        _, _, _, _, expr_x, _, _, _, expr_y, _, _, _, _, _, str_exp, _ = (
            visited_children
        )
        return BasicRunCall(
            "run ecb_hprint",
            BasicExpressionList(
                [
                    expr_x,
                    expr_y,
                    str_exp,
                    BasicVar("display"),
                ]
            ),
        )


def convert(
    progin,
    procname="",
    filter_unused_linenum=False,
    initialize_vars=False,
    skip_procedure_headers=False,
    output_dependencies=False,
    add_standard_prefix=True,
    default_width32=True,
):
    tree = grammar.parse(progin)
    bv = BasicVisitor()
    basic_prog = bv.visit(tree)

    if add_standard_prefix:
        prefix_lines = [
            BasicLine(None, Basic09CodeStatement("base 0")),
            BasicLine(
                None,
                Basic09CodeStatement(
                    "type display_t = tpth, vpth, wpth, hpth, pal(16), blnk, "
                    "undrln, bck, fore, brdr, hbck, hfore, hscl: byte"
                ),
            ),
            BasicLine(None, Basic09CodeStatement("dim display: display_t")),
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

    # try to patch up empty next statements
    basic_prog.visit(BasicNextPatcherVisitor())

    # output the program
    program = basic_prog.basic09_text(0)
    if output_dependencies and procname:
        procedure_bank = ProcedureBank()
        procedure_bank.add_from_resource("ecb.b09")
        procedure_bank.add_from_str(program)
        program = procedure_bank.get_procedure_and_dependencies(procname)

    return program + "\n"


def convert_file(
    input_program_file,
    output_program_file,
    procname="",
    filter_unused_linenum=False,
    initialize_vars=False,
    output_dependencies=False,
    add_standard_prefix=True,
    default_width32=True,
):
    progin = input_program_file.read()
    progout = convert(
        progin,
        procname=procname,
        filter_unused_linenum=filter_unused_linenum,
        initialize_vars=initialize_vars,
        output_dependencies=output_dependencies,
        add_standard_prefix=add_standard_prefix,
        default_width32=default_width32,
    )
    progout = progout.replace("\n", "\r")
    output_program_file.write(progout)
