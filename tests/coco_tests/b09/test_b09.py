import unittest

from coco import b09
from coco.b09 import compiler
from coco.b09.compiler import ParseError
from coco.b09.configs import CompilerConfigs, StringConfigs
from coco.b09.visitors import LineNumberTooLargeException


class TestB09(unittest.TestCase):
    def test_convert_with_dependencies(self) -> None:
        program = compiler.convert(
            "10 CLS B",
            procname="do_cls",
            initialize_vars=True,
            filter_unused_linenum=True,
            skip_procedure_headers=False,
            output_dependencies=True,
        )
        assert "procedure do_cls\n" in program
        assert "procedure _ecb_cursor_color\n" in program
        assert "procedure _ecb_text_address\n" in program

    def test_convert_no_header_with_dependencies(self) -> None:
        program = compiler.convert(
            "10 CLS B",
            procname="do_cls",
            initialize_vars=True,
            filter_unused_linenum=True,
            skip_procedure_headers=True,
            output_dependencies=True,
        )
        assert "B := 0.0\n" in program
        assert "base 0\n" in program
        assert "RUN _ecb_start" in program
        assert "RUN ecb_cls(B, display)" in program

    def test_convert_header_no_name_with_dependencies(self) -> None:
        program = compiler.convert(
            "10 CLS B",
            initialize_vars=True,
            filter_unused_linenum=True,
            skip_procedure_headers=False,
            output_dependencies=True,
        )
        assert "B := 0.0\n"
        assert "base 0\n" in program
        assert "RUN _ecb_start" in program
        assert "RUN ecb_cls(B, display)" in program
        assert "procedure _ecb_cursor_color\n" in program

    def test_convert_no_default_width32(self) -> None:
        program = compiler.convert(
            "10 A=0",
            procname="do_cls",
            initialize_vars=False,
            filter_unused_linenum=True,
            skip_procedure_headers=True,
            output_dependencies=False,
            default_width32=False,
        )
        assert "RUN _ecb_start(display, 0)\n" in program

    def test_convert_default_width32(self) -> None:
        program = compiler.convert(
            "10 A=0",
            procname="do_cls",
            initialize_vars=False,
            filter_unused_linenum=True,
            skip_procedure_headers=True,
            output_dependencies=False,
            default_width32=True,
        )
        assert "RUN _ecb_start(display, 1)\n" in program

    def test_basic_assignment(self) -> None:
        var = b09.elements.BasicVar("HW")
        exp = b09.elements.BasicLiteral(123.0)
        target = b09.elements.BasicAssignment(var, exp)
        assert target.basic09_text(1) == "  HW := 123.0"

    def test_basic_binary_exp(self) -> None:
        var = b09.elements.BasicVar("HW")
        strlit = b09.elements.BasicLiteral("HW")
        target = b09.elements.BasicBinaryExp(var, "=", strlit)
        assert target.basic09_text(1) == 'HW = "HW"'

    def test_comment(self) -> None:
        target = b09.elements.BasicComment(" hello world ")
        assert target.basic09_text(1) == "(* hello world  *)"

    def test_comment_statement(self) -> None:
        comment = b09.elements.BasicComment(" hello world ")
        target = b09.elements.BasicStatement(comment)
        assert target.basic09_text(2) == "    (* hello world  *)"

    def test_comment_statements(self) -> None:
        comment = b09.elements.BasicComment(" hello world ")
        statement = b09.elements.BasicStatement(comment)
        target = b09.elements.BasicStatements((statement,))
        assert target.basic09_text(2) == "    (* hello world  *)"

    def test_comment_lines(self) -> None:
        comment = b09.elements.BasicComment(" hello world ")
        statement = b09.elements.BasicStatement(comment)
        statements = b09.elements.BasicStatements((statement,))
        target = b09.elements.BasicLine(25, statements)
        assert target.basic09_text(1) == "25   (* hello world  *)"

    def test_basic_float_literal(self) -> None:
        target = b09.elements.BasicLiteral(123.0)
        assert target.basic09_text(2) == "123.0"

    def test_basic_goto(self) -> None:
        target = b09.elements.BasicGoto(123, True)
        assert target.basic09_text(1) == "123"
        assert target.implicit is True
        target = b09.elements.BasicGoto(1234, False)
        assert target.basic09_text(1) == "  GOTO 1234"
        assert target.implicit is False

    def test_if(self) -> None:
        strlit = b09.elements.BasicLiteral("HW")
        exp = b09.elements.BasicBinaryExp(strlit, "=", strlit)
        goto = b09.elements.BasicGoto(123, True)
        target = b09.elements.BasicIf(exp, goto)
        assert target.basic09_text(1) == '  IF "HW" = "HW" THEN 123'

    def test_basic_real_literal(self) -> None:
        target = b09.elements.BasicLiteral(123.0)
        assert target.basic09_text(2) == "123.0"

    def test_basic_int_literal(self) -> None:
        target = b09.elements.BasicLiteral(123)
        assert target.basic09_text(2) == "123"

    def test_basic_str_literal(self) -> None:
        target = b09.elements.BasicLiteral("123.0")
        assert target.basic09_text(1) == '"123.0"'

    def test_basic_paren_exp(self) -> None:
        strlit = b09.elements.BasicLiteral("HELLO WORLD")
        target = b09.elements.BasicParenExp(strlit)
        assert target.basic09_text(2) == '("HELLO WORLD")'

    def test_basic_op_exp(self) -> None:
        strlit = b09.elements.BasicLiteral("HELLO WORLD")
        target = b09.elements.BasicOpExp("&", strlit)
        assert target.operator == "&"
        assert target.exp == strlit
        assert target.basic09_text(1) == '& "HELLO WORLD"'

    def test_basic_operator(self) -> None:
        target = b09.elements.BasicOperator("*")
        assert target.basic09_text(2) == "*"

    def generic_test_parse(
        self,
        progin,
        progout,
        *,
        add_standard_prefix=False,
        add_suffix=False,
        default_str_storage=b09.DEFAULT_STR_STORAGE,
        filter_unused_linenum=False,
        initialize_vars=False,
        output_dependencies=False,
        skip_procedure_headers=True,
    ):
        b09_prog = compiler.convert(
            progin,
            add_standard_prefix=add_standard_prefix,
            add_suffix=add_suffix,
            default_str_storage=default_str_storage,
            filter_unused_linenum=filter_unused_linenum,
            initialize_vars=initialize_vars,
            output_dependencies=output_dependencies,
            skip_procedure_headers=skip_procedure_headers,
        )
        assert b09_prog == progout + "\n"

    def test_parse_array_ref(self) -> None:
        self.generic_test_parse(
            "10 A = B(123 - 1 - (2/2),1,2)\n",
            "A := 0.0\n"
            "DIM arr_B(11)\n"
            "FOR tmp_1 = 0 TO 10 \\ arr_B(tmp_1) := 0 \\ NEXT tmp_1\n"
            "10 A := arr_B(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0)",
            initialize_vars=True,
        )

    def test_parse_array_assignment(self) -> None:
        self.generic_test_parse(
            "10 A (123 - 1 - (2/2),1,2)=123+64",
            "DIM arr_A(11)\n"
            "FOR tmp_1 = 0 TO 10 \\ arr_A(tmp_1) := 0 \\ NEXT tmp_1\n"
            "10 arr_A(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0) := 123.0 + 64.0",
            initialize_vars=True,
        )

        self.generic_test_parse(
            "10 LETA (123 - 1 - (2/2),1,2)=123+64",
            "DIM arr_A(11)\n"
            "FOR tmp_1 = 0 TO 10 \\ arr_A(tmp_1) := 0 \\ NEXT tmp_1\n"
            "10 LET arr_A(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0) := "
            "123.0 + 64.0",
            initialize_vars=True,
        )

    def test_parse_str_array_ref(self) -> None:
        self.generic_test_parse(
            "10 A$ = B$(123 - 1 - (2/2),1,2)",
            'A$ := ""\n'
            "DIM arr_B$(11)\n"
            'FOR tmp_1 = 0 TO 10 \\ arr_B$(tmp_1) := "" \\ NEXT tmp_1\n'
            "10 A$ := arr_B$(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0)",
            initialize_vars=True,
        )

        self.generic_test_parse(
            "10 LETA$ = B$(123 - 1 - (2/2),1,2)",
            'A$ := ""\n'
            "DIM arr_B$(11)\n"
            'FOR tmp_1 = 0 TO 10 \\ arr_B$(tmp_1) := "" \\ NEXT tmp_1\n'
            "10 LET A$ := arr_B$(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0)",
            initialize_vars=True,
        )

    def test_parse_str_array_assignment(self) -> None:
        self.generic_test_parse(
            '10 A$ (123 - 1 - (2/2),1,2)="123"+"64"',
            "DIM arr_A$(11)\n"
            'FOR tmp_1 = 0 TO 10 \\ arr_A$(tmp_1) := "" \\ NEXT tmp_1\n'
            '10 arr_A$(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0) := "123" + "64"',
            initialize_vars=True,
        )

    def test_parse_comment_program(self) -> None:
        self.generic_test_parse("15 REM HELLO WORLD\n", "15 (* HELLO WORLD *)")

    def test_parse_comments_program(self) -> None:
        self.generic_test_parse(
            "15 REM HELLO WORLD\n20 REM HERE",
            "15 (* HELLO WORLD *)\n20 (* HERE *)",
        )

    def test_parse_simple_assignment(self) -> None:
        self.generic_test_parse(
            '10 A = 123\n20 B=123.4\n30C$="HELLO"\n35D$=C$',
            '10 A := 123.0\n20 B := 123.4\n30 C$ := "HELLO"\n35 D$ := C$',
        )

        self.generic_test_parse(
            '10 LETA = 123\n20 B=123.4\n30C$="HELLO"\n35D$=C$',
            '10 LET A := 123.0\n20 B := 123.4\n30 C$ := "HELLO"\n35 D$ := C$',
        )

    def test_parse_paren_expression(self) -> None:
        self.generic_test_parse("10 A = (AB)", "10 A := (AB)")

    def test_parse_prod_expression(self) -> None:
        self.generic_test_parse(
            "10 A = 64 * 32\n20 B = 10/AB",
            "10 A := 64.0 * 32.0\n20 B := 10.0 / AB",
        )

    def test_parse_power_expression(self) -> None:
        self.generic_test_parse(
            "10 A = 64 ^ 32\n",
            "10 A := 64.0 ^ 32.0",
        )

    def test_parse_add_expression(self) -> None:
        self.generic_test_parse(
            "10 A = 64 + 32\n20 B = 10-AB+32",
            "10 A := 64.0 + 32.0\n20 B := 10.0 - AB + 32.0",
        )

    def test_parse_str_expression(self) -> None:
        self.generic_test_parse(
            '10 A$ = "A" + "Z"\n20B$=A$+B$',
            '10 A$ := "A" + "Z"\n20 B$ := A$ + B$',
        )
        self.generic_test_parse(
            '10 LETA$ = "A" + "Z"\n20B$=A$+B$',
            '10 LET A$ := "A" + "Z"\n20 B$ := A$ + B$',
        )

    def test_parse_str_expression2(self) -> None:
        self.generic_test_parse('10 IF A$<>"" THEN 10', '10 IF A$ <> "" THEN 10')

    def test_parse_string_expression(self) -> None:
        self.generic_test_parse(
            '10 PRINT STRING$(32, "*")',
            '10 run ecb_string(32.0, "*", tmp_1$) \\ PRINT tmp_1$',
        )

    def test_parse_multi_expression(self) -> None:
        self.generic_test_parse(
            "10 A = 64 + 32*10 / AB -1",
            "10 A := 64.0 + 32.0 * 10.0 / AB - 1.0",
        )

    def test_parse_gtle_expression(self) -> None:
        self.generic_test_parse(
            "10 A = 4 < 2\n15 B=4>2\n20C=A<>B",
            "10 A := 4.0 < 2.0\n15 B := 4.0 > 2.0\n20 C := A <> B",
        )

    def test_parse_multi_expression2(self) -> None:
        self.generic_test_parse(
            "10 A=(64+32)*10/(AB-1)",
            "10 A := (64.0 + 32.0) * 10.0 / (AB - 1.0)",
        )

    def test_parse_multi_expression3(self) -> None:
        # Note that the output is not a legal Basic09 construct
        self.generic_test_parse(
            "10 A = A + 2 AND 3 < 3", "10 A := LAND(A + 2.0, 3.0 < 3.0)"
        )

    def test_parse_multi_statement(self) -> None:
        self.generic_test_parse("10 A=A+2:B=B+1", "10 A := A + 2.0\nB := B + 1.0")

    def test_simple_if_statement(self) -> None:
        self.generic_test_parse(
            "1 IF A=1 THEN 2\n2 IF A<10 THEN B = B - 2 * 1",
            "1 IF A = 1.0 THEN 2\n2 IF A < 10.0 THEN\n  B := B - 2.0 * 1.0\nENDIF",
        )

    def test_binary_if_statement(self) -> None:
        self.generic_test_parse(
            "1 IF A=1 AND B=2 THEN 2\n2 IF A<10 THEN B = B - 2 * 1",
            "1 IF A = 1.0 AND B = 2.0 THEN 2\n2 IF A < 10.0 THEN\n"
            "  B := B - 2.0 * 1.0\nENDIF",
        )

    def test_paren_if_statement(self) -> None:
        self.generic_test_parse(
            "1 IF (A=1 AND B=2) THEN 2\n2 IF A<10 THEN B = B - 2 * 1",
            "1 IF (A = 1.0 AND B = 2.0) THEN 2\n2 IF A < 10.0 THEN\n"
            "  B := B - 2.0 * 1.0\nENDIF",
        )

    def test_simple_print_statement(self) -> None:
        self.generic_test_parse('11 PRINT "HELLO WORLD"', '11 PRINT "HELLO WORLD"')

    def test_simple_print_statement2(self) -> None:
        self.generic_test_parse("11 PRINT 3 + 3", "11 PRINT 3.0 + 3.0")

    def test_simple_print_statement3(self) -> None:
        self.generic_test_parse("11 PRINT A$ + B$", "11 PRINT A$ + B$")

    def test_simple_print_statement4(self) -> None:
        self.generic_test_parse('11 PRINT"TIME"T/10;', '11 PRINT "TIME"; T / 10.0;')

    def test_print_multi(self) -> None:
        self.generic_test_parse("11 PRINT A$ , B$", "11 PRINT A$, B$")

    def test_print_odd(self) -> None:
        self.generic_test_parse("11 PRINT A$,,B$", '11 PRINT A$, "", B$')

    def test_land(self) -> None:
        self.generic_test_parse("11 PRINT A=A AND 4", "11 PRINT LAND(A = A, 4.0)")

    def test_lor(self) -> None:
        self.generic_test_parse("11 Z = A=B OR F=Z", "11 Z := LOR(A = B, F = Z)")

    def test_lnot(self) -> None:
        self.generic_test_parse("11 Z = NOT A=B", "11 Z := LNOT(A = B)")

    def test_if_not(self) -> None:
        self.generic_test_parse(
            "100 IF NOT A=3 THEN 100", "100 IF NOT(A = 3.0) THEN 100"
        )

    def test_sound(self) -> None:
        self.generic_test_parse(
            "11 SOUND 100, A+B", "11 RUN ecb_sound(100.0, A + B, 31.0, FIX(play.octo))"
        )

    def test_poke(self) -> None:
        self.generic_test_parse("11 POKE65498,A+B", "11 POKE 65498.0, A + B")

    def test_poke_65496(self) -> None:
        self.generic_test_parse("11 POKE65496,A+B", "11 play.octo := 0")

    def test_poke_65497(self) -> None:
        self.generic_test_parse("11 POKE&HFFD9,A+B", "11 play.octo := 1")

    def test_cls(self) -> None:
        self.generic_test_parse(
            "11 CLS A+B\n12 CLS",
            "11 RUN ecb_cls(A + B, display)\n12 RUN ecb_cls(1.0, display)",
        )

    def test_funcs(self) -> None:
        for ecb_func, b09_func in b09.grammar.FUNCTIONS.items():
            self.generic_test_parse(
                f"11X={ecb_func}(1)",
                f"11 X := {b09_func}(1.0)",
            )

    def test_hex_literal(self) -> None:
        self.generic_test_parse(
            "11 PRINT&H1234",
            "11 run ecb_str(float($1234), tmp_1$) \\ PRINT tmp_1$",
        )

        self.generic_test_parse(
            "11 PRINT&HFFFFFF",
            "11 run ecb_str(16777215.0, tmp_1$) \\ PRINT tmp_1$",
        )

    def test_left_and_right(self) -> None:
        self.generic_test_parse(
            '11 AA$=LEFT$("HELLO" , 3)', '11 AA$ := LEFT$("HELLO", 3.0)'
        )
        self.generic_test_parse(
            '11 AA$=RIGHT$("HELLO" , 3.0)', '11 AA$ := RIGHT$("HELLO", 3.0)'
        )

    def test_mid(self) -> None:
        self.generic_test_parse(
            '11 AA$=MID$("HELLO" , 3,2)', '11 AA$ := MID$("HELLO", 3.0, 2.0)'
        )

    def test_val(self) -> None:
        self.generic_test_parse('11 AA = VAL("2334")', '11 RUN ecb_val("2334", AA)')

    def test_num_str_funcs(self) -> None:
        for ecb_func, b09_func in b09.grammar.NUM_STR_FUNCTIONS.items():
            self.generic_test_parse(
                f"11X$={ecb_func}(1)",
                f"11 X$ := {b09_func}(1.0)",
            )

    def test_builtin_statements(self) -> None:
        for ecb_func, b09_func in b09.grammar.STATEMENTS2.items():
            self.generic_test_parse(
                f"11{ecb_func}(1,2)",
                f"11 {b09_func}(1.0, 2.0)",
            )

        for ecb_func, b09_func in b09.grammar.STATEMENTS3.items():
            self.generic_test_parse(
                f"11{ecb_func}(1,2    , 3)",
                f"11 {b09_func}(1.0, 2.0, 3.0)",
            )

    def test_goto(self) -> None:
        self.generic_test_parse(
            "11GOTO20\n20GOTO11",
            "11 GOTO 20\n20 GOTO 11",
        )

    def test_gosub(self) -> None:
        self.generic_test_parse(
            "11GOSUB20\n20GOSUB11",
            "11 GOSUB 20\n20 GOSUB 11",
        )

    def test_data(self) -> None:
        self.generic_test_parse(
            '10 DATA 1,2,3,"",,"FOO","BAR", BAZ  \n20 DATA   , ',
            '10 DATA "1.0", "2.0", "3.0", "", "", "FOO", "BAR", "BAZ  "\n'
            '20 DATA "", ""',
        )

    def test_single_kw_statements(self) -> None:
        for (
            ecb_func,
            b09_func,
        ) in b09.grammar.SINGLE_KEYWORD_STATEMENTS.items():
            self.generic_test_parse(
                f"11{ecb_func}",
                f"11 {b09_func}",
            )

    def test_print(self) -> None:
        self.generic_test_parse('11PRINT"HELLO WORLD"', '11 PRINT "HELLO WORLD"')

    def test_print_at(self) -> None:
        self.generic_test_parse(
            '11PRINT@32,"HELLO WORLD"',
            '11 RUN ecb_at(32.0) \\ PRINT "HELLO WORLD"',
        )

    def test_for(self) -> None:
        self.generic_test_parse("11FORII=1TO20", "11 FOR II = 1.0 TO 20.0")

    def test_for_step(self) -> None:
        self.generic_test_parse(
            "11FORII=1TO20STEP30", "11 FOR II = 1.0 TO 20.0 STEP 30.0"
        )

    def test_next(self) -> None:
        self.generic_test_parse("10NEXTJJ", "10 NEXT JJ")

    def test_multiline(self) -> None:
        self.generic_test_parse(
            '10 PRINT "HELLO"\n20 A = 2', '10 PRINT "HELLO"\n20 A := 2.0'
        )

    def test_multiline2(self) -> None:
        self.generic_test_parse(
            '10 REM Hello World\n20 CLS 5.0\n30 PRINT "HELLO"\n40 B = 2.0',
            "10 (* Hello World *)\n"
            "20 RUN ecb_cls(5.0, display)\n"
            '30 PRINT "HELLO"\n'
            "40 B := 2.0",
        )

    def test_for_next(self) -> None:
        self.generic_test_parse(
            "10 FOR YY=1 TO 20 STEP 1\n"
            "20 FOR XX=1 TO 20 STEP 1\n"
            "30 PRINT XX, YY\n"
            "40 NEXT XX, YY\n"
            '50 PRINT "HELLO"',
            "10 FOR YY = 1.0 TO 20.0 STEP 1.0\n"
            "20   FOR XX = 1.0 TO 20.0 STEP 1.0\n"
            "30     run ecb_str(XX, tmp_1$) \\ run ecb_str(YY, tmp_2$) \\ "
            "PRINT tmp_1$, tmp_2$\n"
            "40 NEXT XX \\ NEXT YY\n"
            '50 PRINT "HELLO"',
        )

    def test_functions_to_statements(self) -> None:
        for ecb_func, b09_func in b09.grammar.FUNCTIONS_TO_STATEMENTS.items():
            self.generic_test_parse(
                f"11X={ecb_func}(1)",
                f"11 {b09_func}(1.0, X)",
            )

    def test_functions_to_statements2(self) -> None:
        for ecb_func, b09_func in b09.grammar.FUNCTIONS_TO_STATEMENTS2.items():
            self.generic_test_parse(
                f"11X={ecb_func}(1, 2)",
                f"11 {b09_func}(1.0, 2.0, X)",
            )

    def test_num_str_functions_to_statements(self) -> None:
        for (
            ecb_func,
            b09_func,
        ) in b09.grammar.NUM_STR_FUNCTIONS_TO_STATEMENTS.items():
            self.generic_test_parse(
                f"11X$={ecb_func}(1)",
                f"11 {b09_func}(1.0, X$)",
            )

    def test_str_functions_to_statements(self) -> None:
        for (
            ecb_func,
            b09_func,
        ) in b09.grammar.STR_FUNCTIONS_TO_STATEMENTS.items():
            self.generic_test_parse(
                f"11X$={ecb_func}",
                f"11 {b09_func}(X$)",
            )

    def test_joystk(self) -> None:
        self.generic_test_parse(
            "11 PRINT JOYSTK(1)",
            "dim joy0x, joy0y, joy1x, joy0y: integer\n"
            "11 RUN ecb_joystk(1.0, tmp_1) \\ run ecb_str(tmp_1, tmp_1$) \\ "
            "PRINT tmp_1$",
        )

    def test_hex(self) -> None:
        self.generic_test_parse(
            "11 PRINT HEX$(1)", "11 RUN ecb_hex(1.0, tmp_1$) \\ PRINT tmp_1$"
        )

    def test_dim1(self) -> None:
        self.generic_test_parse(
            "11 DIMA(12),B(3),CC(20)",
            "11 DIM arr_A(13), arr_B(4), arr_CC(21)\n"
            "FOR tmp_1 = 0 TO 12 \\ "
            "arr_A(tmp_1) := 0 \\ "
            "NEXT tmp_1\n"
            "FOR tmp_1 = 0 TO 3 \\ "
            "arr_B(tmp_1) := 0 \\ "
            "NEXT tmp_1\n"
            "FOR tmp_1 = 0 TO 20 \\ "
            "arr_CC(tmp_1) := 0 \\ "
            "NEXT tmp_1",
            initialize_vars=True,
        )

    def test_dim2(self) -> None:
        self.generic_test_parse(
            "11 DIMA(12,&H123)",
            "11 DIM arr_A(13, $124)\n"
            "FOR tmp_1 = 0 TO 12 \\ "
            "FOR tmp_2 = 0 TO $123 \\ "
            "arr_A(tmp_1, tmp_2) := 0 \\ "
            "NEXT tmp_2 \\ "
            "NEXT tmp_1",
            initialize_vars=True,
        )

    def test_dim3(self) -> None:
        self.generic_test_parse(
            "11 DIMA(12,&H123,55)",
            "11 DIM arr_A(13, $124, 56)\n"
            "FOR tmp_1 = 0 TO 12 \\ "
            "FOR tmp_2 = 0 TO $123 \\ "
            "FOR tmp_3 = 0 TO 55 \\ "
            "arr_A(tmp_1, tmp_2, tmp_3) := 0 \\ "
            "NEXT tmp_3 \\ "
            "NEXT tmp_2 \\ "
            "NEXT tmp_1",
            initialize_vars=True,
        )

    def test_dim4(self) -> None:
        self.generic_test_parse(
            "11 DIM A, B(12)",
            "11 DIM A, arr_B(13)\n"
            "A := 0\n"
            "FOR tmp_1 = 0 TO 12 \\ "
            "arr_B(tmp_1) := 0 \\ "
            "NEXT tmp_1",
            initialize_vars=True,
        )

    def test_dim5(self) -> None:
        self.generic_test_parse(
            "11 DIM A$, B, C$(12)",
            "11 DIM A$, arr_C$(13)\n"
            'A$ := ""\n'
            "FOR tmp_1 = 0 TO 12 \\ "
            'arr_C$(tmp_1) := "" \\ '
            "NEXT tmp_1\n"
            "DIM B\n"
            "B := 0",
            initialize_vars=True,
        )

    def test_dim6(self) -> None:
        self.generic_test_parse(
            "11 DIM A$, B, C$(12)",
            "11 DIM A$, arr_C$(13): STRING[80]\n"
            'A$ := ""\n'
            "FOR tmp_1 = 0 TO 12 \\ "
            'arr_C$(tmp_1) := "" \\ '
            "NEXT tmp_1\n"
            "DIM B\n"
            "B := 0",
            default_str_storage=80,
            initialize_vars=True,
        )

    def test_dim7(self) -> None:
        self.generic_test_parse(
            "11 DIM A$, C$(12):PRINT B$\n",
            "DIM B$:STRING[80]\n"
            'B$ := ""\n'
            "11 DIM A$, arr_C$(13): STRING[80]\n"
            'A$ := ""\n'
            "FOR tmp_1 = 0 TO 12 \\ "
            'arr_C$(tmp_1) := "" \\ '
            "NEXT tmp_1\n"
            "PRINT B$",
            default_str_storage=80,
            initialize_vars=True,
        )

    def test_str_dim1(self) -> None:
        self.generic_test_parse(
            "11 DIMA$(12)",
            "11 DIM arr_A$(13)\n"
            "FOR tmp_1 = 0 TO 12 \\ "
            'arr_A$(tmp_1) := "" \\ '
            "NEXT tmp_1",
            initialize_vars=True,
        )

    def test_str_dim2(self) -> None:
        self.generic_test_parse(
            "11 DIMA$(12,&H123)",
            "11 DIM arr_A$(13, $124)\n"
            "FOR tmp_1 = 0 TO 12 \\ "
            "FOR tmp_2 = 0 TO $123 \\ "
            'arr_A$(tmp_1, tmp_2) := "" \\ '
            "NEXT tmp_2 \\ "
            "NEXT tmp_1",
            initialize_vars=True,
        )

    def test_str_dim3(self) -> None:
        self.generic_test_parse(
            "11 DIMA$(12,&H123,55)",
            "11 DIM arr_A$(13, $124, 56)\n"
            "FOR tmp_1 = 0 TO 12 \\ "
            "FOR tmp_2 = 0 TO $123 \\ "
            "FOR tmp_3 = 0 TO 55 \\ "
            'arr_A$(tmp_1, tmp_2, tmp_3) := "" \\ '
            "NEXT tmp_3 \\ "
            "NEXT tmp_2 \\ "
            "NEXT tmp_1",
            initialize_vars=True,
        )

    def test_dim_misc(self) -> None:
        self.generic_test_parse(
            "11 DIMA$,B",
            '11 DIM A$\nA$ := ""\nDIM B\nB := 0',
            initialize_vars=True,
        )

    def test_line_filter(self) -> None:
        self.generic_test_parse(
            "10 GOTO 10\n20 GOSUB 100\n30 GOTO 10\n100 REM\n",
            "10 GOTO 10\nGOSUB 100\nGOTO 10\n100 (* *)",
            filter_unused_linenum=True,
        )

    def test_clear_statement(self) -> None:
        self.generic_test_parse(
            "10 CLEAR\n20CLEAR 200", "10 (* CLEAR *)\n20 (* CLEAR 200 *)"
        )

    def test_initializes_vars(self) -> None:
        self.generic_test_parse(
            "10 PRINT A+B, A$",
            'A := 0.0\nA$ := ""\nB := 0.0\n10 PRINT A + B, A$',
            filter_unused_linenum=False,
            initialize_vars=True,
        )

    def test_on_goto(self) -> None:
        self.generic_test_parse(
            "10 ON NN GOTO 11, 22, 33, 44\n11 ON MM GOSUB 100\n22 '\n33 '\n44 '\n100 '",
            "ON NN GOTO 11, 22, 33, 44\n"
            "11 ON MM GOSUB 100\n"
            "22 (* *)\n"
            "33 (* *)\n"
            "44 (* *)\n"
            "100 (* *)",
            filter_unused_linenum=True,
        )

    def test_simple_read(self) -> None:
        self.generic_test_parse(
            "10 READA$,B,D(II,JJ),E$(XX)",
            "10 READ A$, B, arr_D(II, JJ), arr_E$(XX)",
        )

    def test_mars_data(self) -> None:
        self.generic_test_parse(
            "120 DATAA CONTROL ROOM,AN ENGINE ROOM,A BARREN FIELD,A MOAT",
            '120 DATA "A CONTROL ROOM", "AN ENGINE ROOM", "A BARREN FIELD", "A MOAT"',
        )

    def test_input(self) -> None:
        self.generic_test_parse(
            '10 INPUT "HELLO WORLD";A$,B(1,2,3),C,D$(3)',
            "10 RUN _ecb_input_prefix \\ "
            'INPUT "HELLO WORLD? ", A$, arr_B(1.0, 2.0, 3.0), C, '
            "arr_D$(3.0) \\ RUN _ecb_input_suffix",
        )

    def test_input_no_message(self) -> None:
        self.generic_test_parse(
            "10 INPUT A$,B(1,2,3)",
            "10 RUN _ecb_input_prefix \\ "
            'INPUT "? ", A$, arr_B(1.0, 2.0, 3.0) \\ '
            "RUN _ecb_input_suffix",
        )

    def test_line_input(self) -> None:
        self.generic_test_parse(
            '10 LINE INPUT "HELLO WORLD";A$,B(1,2,3),C,D$(3)',
            "10 RUN _ecb_input_prefix \\ "
            'INPUT "HELLO WORLD", A$, arr_B(1.0, 2.0, 3.0), C, '
            "arr_D$(3.0) \\ RUN _ecb_input_suffix",
        )

    def test_line_input_no_message(self) -> None:
        self.generic_test_parse(
            "10 LINE INPUT A$,B(1,2,3)",
            "10 RUN _ecb_input_prefix \\ "
            'INPUT "", A$, arr_B(1.0, 2.0, 3.0) \\ '
            "RUN _ecb_input_suffix",
        )

    def test_mars_if(self) -> None:
        self.generic_test_parse(
            "480 IFL(4)<>11ORL(6)<>11ORL(32)<>11ORL(30)<>11ORGR=0THEN500\n500 '\n",
            "GR := 0.0\n"
            "DIM arr_L(11)\n"
            "FOR tmp_1 = 0 TO 10 \\ arr_L(tmp_1) := 0 \\ NEXT tmp_1\n"
            "480 IF arr_L(4.0) <> 11.0 "
            "OR arr_L(6.0) <> 11.0 "
            "OR arr_L(32.0) <> 11.0 "
            "OR arr_L(30.0) <> 11.0 OR GR = 0.0 THEN 500\n"
            "500 (* *)",
            initialize_vars=True,
        )

    def test_multi_and_or(self) -> None:
        self.generic_test_parse(
            "480 Z=A ANDB ORC ANDD ORC",
            "480 Z := LOR(LOR(LAND(A, B), LAND(C, D)), C)",
        )

    def test_multi_arithmetic(self) -> None:
        self.generic_test_parse("480 Z=A+B*C-D/C", "480 Z := A + B * C - D / C")

    def test_num_if(self) -> None:
        self.generic_test_parse(
            "100 '\n480 IFA THEN100", "100 (* *)\n480 IF A <> 0.0 THEN 100"
        )

    def test_read_empty_data(self) -> None:
        self.generic_test_parse(
            "10 READ A,B$,C\n20 DATA ,FOO,",
            "10 READ tmp_1$, B$, tmp_2$ \\ "
            "RUN ecb_read_filter(tmp_1$, A) \\ "
            "RUN ecb_read_filter(tmp_2$, C)\n"
            '20 DATA "", "FOO", ""',
        )

    def test_filter_line_zero(self) -> None:
        self.generic_test_parse("0 CLS\n", "RUN ecb_cls(1.0, display)")

    def test_does_not_filter_line_zero(self) -> None:
        self.generic_test_parse("0 CLS:GOTO 0\n", "0 RUN ecb_cls(1.0, display)\nGOTO 0")

    def test_handles_empty_next(self) -> None:
        self.generic_test_parse(
            "10 FORX=1TO10\n20 FORY=1TO10\n30 NEXT\n40 NEXT\n50 NEXT\n",
            "10 FOR X = 1.0 TO 10.0\n"
            "20   FOR Y = 1.0 TO 10.0\n"
            "30   NEXT Y\n"
            "40 NEXT X\n"
            "50 NEXT",
        )

    def test_adds_standard_prefix(self) -> None:
        program = compiler.convert(
            "10 REM",
            procname="do_cls",
            initialize_vars=True,
            filter_unused_linenum=True,
            skip_procedure_headers=False,
            add_standard_prefix=True,
            output_dependencies=True,
        )
        assert program.startswith("procedure _ecb_cursor_color\n")
        assert "procedure _ecb_start\n" in program
        assert "base 0\n" in program
        assert "procedure do_cls" in program

    def test_multiple_print_ats(self) -> None:
        self.generic_test_parse(
            '130 PRINT@64,"COLOR (1-8)";: INPUT CO\n'
            '140 IF (CO<1 OR CO>8) THEN PRINT@64," ": GOTO 130\n',
            '130 RUN ecb_at(64.0) \\ PRINT "COLOR (1-8)";\n'
            'RUN _ecb_input_prefix \\ INPUT "? ", CO \\ '
            "RUN _ecb_input_suffix\n"
            "140 IF (CO < 1.0 OR CO > 8.0) THEN\n"
            '  RUN ecb_at(64.0) \\ PRINT " "\n'
            "  GOTO 130\n"
            "ENDIF",
        )

    def test_empty_print_at(self) -> None:
        self.generic_test_parse("130 PRINT@64", "130 RUN ecb_at(64.0)")

    def test_print_char(self) -> None:
        self.generic_test_parse(
            '130 PRINT@170,"*  "+CHR$(191)+"  " +CHR$(191)+ "  *"',
            '130 RUN ecb_at(170.0) \\ PRINT "*  " + CHR$(191.0) + "  " + '
            'CHR$(191.0) + "  *"',
        )

    def test_varptr(self) -> None:
        self.generic_test_parse(
            "10 A = VARPTR(A)\n"
            "20 A = VARPTR(A$)\n"
            "30 A = VARPTR(A(1,2))\n"
            "40 A = VARPTR(A$(1,2))\n",
            "10 A := ADDR(A)\n"
            "20 A := ADDR(A$)\n"
            "30 A := ADDR(arr_A(1.0, 2.0))\n"
            "40 A := ADDR(arr_A$(1.0, 2.0))",
        )

    def test_instr(self) -> None:
        self.generic_test_parse(
            '10 A = INSTR(10,"HELLO","LL")\n',
            '10 run ecb_instr(10.0, "HELLO", "LL", A)',
        )

    def test_string(self) -> None:
        self.generic_test_parse(
            '10 A$ = STRING$(10,"HELLO")\n',
            '10 run ecb_string(10.0, "HELLO", A$)',
        )

    def test_width(self) -> None:
        self.generic_test_parse(
            "10 WIDTH 80\n",
            "10 run _ecb_width(80.0, display)",
        )

    def test_locate(self) -> None:
        self.generic_test_parse(
            "10 LOCATE 10, 5\n",
            "10 run ecb_locate(10.0, 5.0)",
        )

    def test_attr(self) -> None:
        self.generic_test_parse(
            "10 ATTR 2, 3\n",
            "10 run ecb_attr(2.0, 3.0, 0.0, 0.0, display)",
        )

    def test_attr_b(self) -> None:
        self.generic_test_parse(
            "10 ATTR 2, 3, B\n",
            "10 run ecb_attr(2.0, 3.0, 1.0, 0.0, display)",
        )

    def test_attr_u(self) -> None:
        self.generic_test_parse(
            "10 ATTR 2, 3, U\n",
            "10 run ecb_attr(2.0, 3.0, 0.0, 1.0, display)",
        )

    def test_attr_ub(self) -> None:
        self.generic_test_parse(
            "10 ATTR 2, 3, U, B\n",
            "10 run ecb_attr(2.0, 3.0, 1.0, 1.0, display)",
        )

    def test_attr_ububu(self) -> None:
        self.generic_test_parse(
            "10 ATTR 2, 3, U, B, U, B, U\n",
            "10 run ecb_attr(2.0, 3.0, 1.0, 1.0, display)",
        )

    def test_rgb(self) -> None:
        self.generic_test_parse(
            "10 RGB\n",
            "10 run ecb_set_palette_rgb(display)",
        )

    def test_cmp(self) -> None:
        self.generic_test_parse(
            "10 CMP\n",
            "10 run ecb_set_palette_cmp(display)",
        )

    def test_palette_rgb(self) -> None:
        self.generic_test_parse(
            "10 PALETTE RGB\n",
            "10 run ecb_set_palette_rgb(display)",
        )

    def test_palette_cmp(self) -> None:
        self.generic_test_parse(
            "10 PALETTE  CMP   \n",
            "10 run ecb_set_palette_cmp(display)",
        )

    def test_pal(self) -> None:
        self.generic_test_parse(
            "10 PALETTE 1, 2\n",
            "10 run ecb_set_palette(1.0, 2.0, display)",
        )

    def test_hscreen(self) -> None:
        self.generic_test_parse(
            "10 HSCREEN\n",
            "10 run ecb_hscreen(0, display)",
        )

    def test_hscreen_n(self) -> None:
        self.generic_test_parse(
            "10 HSCREEN 2\n",
            "10 run ecb_hscreen(2.0, display)",
        )

    def test_hcls(self) -> None:
        self.generic_test_parse(
            "10 HCLS\n",
            "10 run ecb_hcls(-1, display)",
        )

    def test_hcls_n(self) -> None:
        self.generic_test_parse(
            "10 HCLS 2\n",
            "10 run ecb_hcls(2.0, display)",
        )

    def test_hcircle(self) -> None:
        self.generic_test_parse(
            "10 HCIRCLE(159, 95), 20\n",
            "10 run ecb_hcircle(159.0, 95.0, 20.0, float(display.hfore), 1.0, display)",
        )

    def test_hcircle_with_color(self) -> None:
        self.generic_test_parse(
            "10 HCIRCLE(159, 95), 20, 4\n",
            "10 run ecb_hcircle(159.0, 95.0, 20.0, 4.0, 1.0, display)",
        )

    def test_hcircle_without_color_with_ratio(self) -> None:
        self.generic_test_parse(
            "10 HCIRCLE(159, 95), 20, , 4\n",
            "10 run ecb_hcircle(159.0, 95.0, 20.0, float(display.hfore), 4.0, display)",
        )

    def test_hcircle_with_color_and_ratio(self) -> None:
        self.generic_test_parse(
            "10 HCIRCLE(159, 95), 20, 3, 4\n",
            "10 run ecb_hcircle(159.0, 95.0, 20.0, 3.0, 4.0, display)",
        )

    def test_harc(self) -> None:
        self.generic_test_parse(
            "10 HCIRCLE(159, 95), 20, 3, 4, .2, .9\n",
            "10 run ecb_harc(159.0, 95.0, 20.0, 3.0, 4.0, 0.2, 0.9, display)",
        )

    def test_hprint(self) -> None:
        self.generic_test_parse(
            '10 HPRINT(10, 20), "HELLO WORLD"',
            '10 run ecb_hprint(10.0, 20.0, "HELLO WORLD", display)',
        )

    def test_hprint_num(self) -> None:
        self.generic_test_parse(
            "10 HPRINT(10, 20), 3.0",
            "10 run ecb_str(3.0, tmp_1) \\ run ecb_hprint(10.0, 20.0, tmp_1, display)",
        )

    def test_on_brk(self) -> None:
        self.generic_test_parse(
            "10 ON BRK GOTO 10",
            "10 ON ERROR GOTO 32700",
        )

    def test_on_err(self) -> None:
        self.generic_test_parse(
            "10 ON ERR GOTO 10",
            "10 ON ERROR GOTO 32700",
        )

    def test_line_number_too_big(self) -> None:
        with self.assertRaises(LineNumberTooLargeException):
            self.generic_test_parse(
                "32700 GOTO 32700",
                "32700 GOTO 32700",
            )

    def test_line_number_does_not_exist(self) -> None:
        with self.assertRaises(ParseError):
            self.generic_test_parse(
                "32699 GOTO 10",
                "32699 GOTO 10",
            )

    def test_outputs_suffix(self) -> None:
        program = compiler.convert(
            "10 ON ERR GOTO 100\n100 END",
            procname="do_cls",
            initialize_vars=True,
            filter_unused_linenum=False,
            skip_procedure_headers=False,
            output_dependencies=False,
            add_suffix=True,
        )
        assert "32700" in program

    def test_truncates_vars(self) -> None:
        self.generic_test_parse(
            '10 AAA = 3: AAA$ = "3"',
            '10 AA := 3.0\nAA$ := "3"',
        )

    def test_tron_toff(self) -> None:
        self.generic_test_parse(
            "10 TRON: TROFF",
            "10 TRON\nTROFF",
        )

    def test_hcolor(self) -> None:
        self.generic_test_parse(
            "10 HCOLOR 2, 3",
            "10 run ecb_hcolor(2.0, 3.0, display)",
        )

    def test_hcolor1(self) -> None:
        self.generic_test_parse(
            "10 HCOLOR 5",
            "10 run ecb_hcolor(5.0, -1.0, display)",
        )

    def test_hline(self) -> None:
        self.generic_test_parse(
            "10 HLINE (123, 25) - (50, 30), PSET",
            '10 run ecb_hline("d", 123.0, 25.0, 50.0, 30.0, "PSET", "L", display)',
        )

    def test_hline_relative(self) -> None:
        self.generic_test_parse(
            "10 HLINE-(50, 30),PRESET",
            '10 run ecb_hline("r", 0.0, 0.0, 50.0, 30.0, "PRESET", "L", display)',
        )

    def test_hbox(self) -> None:
        self.generic_test_parse(
            "10 HLINE (123, 25) - (50, 30), PSET, B",
            '10 run ecb_hline("d", 123.0, 25.0, 50.0, 30.0, "PSET", "B", display)',
        )

    def test_hbar(self) -> None:
        self.generic_test_parse(
            "10 HLINE (123, 25) - (50, 30), PSET, BF",
            '10 run ecb_hline("d", 123.0, 25.0, 50.0, 30.0, "PSET", "BF", display)',
        )

    def test_hreset(self) -> None:
        self.generic_test_parse(
            "10 HRESET(20, 30)",
            "10 run ecb_hreset(20.0, 30.0, display)",
        )

    def test_hset(self) -> None:
        self.generic_test_parse(
            "10 HSET(20, 30)",
            "10 run ecb_hset(20.0, 30.0, display)",
        )

    def test_hset3(self) -> None:
        self.generic_test_parse(
            "10 HSET(20, 30, 5)",
            "10 run ecb_hset3(20.0, 30.0, 5.0, display)",
        )

    def test_erno(self) -> None:
        self.generic_test_parse(
            "10 PRINT ERNO",
            "10 run ecb_str(erno, tmp_1$) \\ PRINT tmp_1$",
        )

    def test_play(self) -> None:
        self.generic_test_parse(
            '10 PLAY "CDE"',
            '10 run ecb_play("CDE", play)',
        )

    def test_allocates_extra_str_space(self) -> None:
        program: str = compiler.convert(
            "10 PRINT A$",
            default_str_storage=128,
        )
        assert "DIM A$:STRING[128]\n" in program

    def test_subs_str_storage_tags(self) -> None:
        program: str = compiler.convert(
            '10 A$=STRING$(10, "*")', default_str_storage=128, output_dependencies=True
        )
        assert "param str: STRING[128]\n" in program

    def test_initializes_for(self) -> None:
        program: str = compiler.convert("10 FOR X=A TO 10", initialize_vars=True)
        assert "A := 0.0" in program

    def test_comment_wth_colon(self) -> None:
        self.generic_test_parse(
            "10 REM PRINT:PRINT",
            "10 (* PRINT:PRINT *)",
        )

    def test_hdraw(self) -> None:
        self.generic_test_parse(
            '10 HDRAW "UDLR"',
            '10 run ecb_hdraw("UDLR", display)',
        )

    def test_hbuff(self) -> None:
        self.generic_test_parse(
            "10 HBUFF 10, 123",
            "10 run _ecb_hbuff(10.0, 123.0, pid, display)",
        )

    def test_adds_hbuff_prefix(self) -> None:
        program = compiler.convert(
            "10 HBUFF 10, 123",
            procname="do_cls",
            initialize_vars=True,
            filter_unused_linenum=True,
            skip_procedure_headers=False,
            output_dependencies=True,
        )
        assert "dim pid: integer\n" in program
        assert "RUN _ecb_init_hbuff(pid)" in program

    def test_hget_statement(self) -> None:
        self.generic_test_parse(
            "10 HGET(123, 45) - (32, 25), 10",
            "10 run ecb_hget(123.0, 45.0, 32.0, 25.0, 10.0, pid, display)",
        )

    def test_hput_statement(self) -> None:
        self.generic_test_parse(
            "10 HPUT(123, 45) - (32, 25), 10, AND",
            '10 run ecb_hput(123.0, 45.0, 32.0, 25.0, 10.0, "AND", pid, display)',
        )

    def test_hpaint_statement(self) -> None:
        self.generic_test_parse(
            "10 HPAINT(123, 45), 10, 5",
            "10 run ecb_hpaint(123.0, 45.0, 10.0, 5.0, display)",
        )

    def test_hpaint_statement_no_color(self) -> None:
        self.generic_test_parse(
            "10 HPAINT(123, 45)",
            "10 run ecb_hpaint(123.0, 45.0, FLOAT(display.hfore), FLOAT(display.hfore), display)",
        )

    def test_hpaint_statement_only_fill_color(self) -> None:
        self.generic_test_parse(
            "10 HPAINT(123, 45), 2",
            "10 run ecb_hpaint(123.0, 45.0, 2.0, FLOAT(display.hfore), display)",
        )

    def test_tolerates_null_char_at_end(self) -> None:
        self.generic_test_parse(
            "10 CLS 0\0",
            "10 RUN ecb_cls(0.0, display)",
        )

    def test_4x_sum(self) -> None:
        self.generic_test_parse(
            "10 DP = A + B + C + D",
            "10 DP := A + B + C + D",
        )

    def test_4x_mul(self) -> None:
        self.generic_test_parse(
            "10 DP = A * B * C * D",
            "10 DP := A * B * C * D",
        )

    def test_4x_pow(self) -> None:
        self.generic_test_parse(
            "10 DP = A ^ B ^ C ^ D",
            "10 DP := A ^ B ^ C ^ D",
        )

    def test_if_else_if(self) -> None:
        self.generic_test_parse(
            "10 IF RN<D1 THEN X = 2 ELSE IF RN=2 THEN 10",
            "10 LOOP\n"
            "  EXITIF RN < D1 THEN\n"
            "    X := 2.0\n"
            "  ENDEXIT\n"
            "  EXITIF RN = 2.0 THEN\n"
            "    GOTO 10\n"
            "  ENDEXIT\n"
            "ENDLOOP",
        )

    def test_if_else_if_else(self) -> None:
        self.generic_test_parse(
            "10 IF RN<D1 THEN X = 2 ELSE IF RN=2 THEN 10 ELSE X=3",
            "10 LOOP\n"
            "  EXITIF RN < D1 THEN\n"
            "    X := 2.0\n"
            "  ENDEXIT\n"
            "  EXITIF RN = 2.0 THEN\n"
            "    GOTO 10\n"
            "  ENDEXIT\n"
            "  EXITIF TRUE THEN\n"
            "    X := 3.0\n"
            "  ENDEXIT\n"
            "ENDLOOP",
        )

    def test_else(self) -> None:
        self.generic_test_parse(
            "10 IF RN<D1 THEN X = 2 ELSE 10",
            "10 IF RN < D1 THEN\n  X := 2.0\nELSE\n  GOTO 10\nENDIF",
        )

    def test_if_then_else(self) -> None:
        self.generic_test_parse(
            "100 IF WW>0 THEN 100 ELSE CC=SC/CT",
            "100 IF WW > 0.0 THEN\n  GOTO 100\nELSE\n  CC := SC / CT\nENDIF",
        )

    def test_int_lvalue(self) -> None:
        self.generic_test_parse(
            "100 IF WW=1 AND INT(WW)>0 THEN 100 ELSE 100",
            "100 IF WW = 1.0 AND tmp_1 > 0.0 THEN\n  GOTO 100\nELSE\n  GOTO 100\nENDIF",
        )

    def test_partial_str_assign(self) -> None:
        self.generic_test_parse(
            '100 A$ = "HELLO',
            '100 A$ := "HELLO"',
        )

    def test_partial_arr_str_assign(self) -> None:
        self.generic_test_parse(
            '100 A$ = "HELLO',
            '100 A$ := "HELLO"',
        )

    def test_str_less_than(self) -> None:
        self.generic_test_parse(
            '100 IF "A" < "B" THEN 100',
            '100 IF "A" < "B" THEN 100',
        )

    def test_str_greater_than(self) -> None:
        self.generic_test_parse(
            '100 IF "A" > "B" THEN 100',
            '100 IF "A" > "B" THEN 100',
        )

    def test_str_less_than_or_equal(self) -> None:
        self.generic_test_parse(
            '100 IF "A" <= "B" THEN 100',
            '100 IF "A" <= "B" THEN 100',
        )

    def test_str_greater_than_or_equal(self) -> None:
        self.generic_test_parse(
            '100 IF "A" >= "B" THEN 100',
            '100 IF "A" >= "B" THEN 100',
        )

    def test_str_not_equal(self) -> None:
        self.generic_test_parse(
            '100 IF "A" <> "B" THEN 100',
            '100 IF "A" <> "B" THEN 100',
        )

    def test_implicit_array_ref(self) -> None:
        self.generic_test_parse(
            "10 A(10) = 3",
            "DIM arr_A(11)\n"
            "FOR tmp_1 = 0 TO 10 \\ arr_A(tmp_1) := 0 \\ NEXT tmp_1\n"
            "10 arr_A(10.0) := 3.0",
            initialize_vars=True,
        )

    def test_tolerates_blank_lines(self) -> None:
        self.generic_test_parse(
            "\n5 CLEAR1000\n10 DIM A(100)\n",
            "5 (* CLEAR1000 *)\n"
            "10 DIM arr_A(101)\n"
            "FOR tmp_1 = 0 TO 100 \\ arr_A(tmp_1) := 0 \\ NEXT tmp_1",
            initialize_vars=True,
        )

    def test_wont_initialize_dimmed_vars(self) -> None:
        program = compiler.convert(
            "10 DIM A",
            procname="test",
            initialize_vars=True,
            filter_unused_linenum=True,
            skip_procedure_headers=False,
            output_dependencies=True,
        )
        assert "A = 0" not in "\n".join(program.split("\n")[:-1])

    def test_initializes_string_with_default(self) -> None:
        program = compiler.convert(
            "10 DIM A$",
            procname="test",
            initialize_vars=True,
            default_str_storage=123,
        )
        assert "STRING[123]" in program

    def test_initializes_strings_with_str_options(self) -> None:
        string_configs = StringConfigs()
        compiler_configs = CompilerConfigs(string_configs=string_configs)
        string_configs.strname_to_size["A$"] = 321
        program = compiler.convert(
            "10 DIM A$",
            add_standard_prefix=False,
            compiler_configs=compiler_configs,
            default_str_storage=123,
            initialize_vars=True,
            output_dependencies=True,
            procname="test",
            skip_procedure_headers=True,
        )
        assert program == '10 DIM A$: STRING[321]\nA$ := ""\n'

    def test_only_initializes_strings_with_str_options(self) -> None:
        string_configs = StringConfigs()
        compiler_configs = CompilerConfigs(string_configs=string_configs)
        string_configs.strname_to_size["A$"] = 321
        program = compiler.convert(
            "10 DIM A$, B$",
            add_standard_prefix=False,
            compiler_configs=compiler_configs,
            default_str_storage=123,
            initialize_vars=True,
            output_dependencies=True,
            procname="test",
            skip_procedure_headers=True,
        )
        assert (
            program == "10 DIM A$: STRING[321]\n"
            'A$ := ""\n'
            "DIM B$: STRING[123]\n"
            'B$ := ""\n'
        )

    def test_initializes_multi_string_with_str_options(self) -> None:
        string_configs = StringConfigs()
        compiler_configs = CompilerConfigs(string_configs=string_configs)
        string_configs.strname_to_size["A$"] = 321
        string_configs.strname_to_size["BB$"] = 456
        program = compiler.convert(
            "10 DIM A$, BB$",
            add_standard_prefix=False,
            compiler_configs=compiler_configs,
            default_str_storage=123,
            initialize_vars=True,
            output_dependencies=True,
            procname="test",
            skip_procedure_headers=True,
        )
        assert (
            program == "10 DIM A$: STRING[321]\n"
            'A$ := ""\n'
            "DIM BB$: STRING[456]\n"
            'BB$ := ""\n'
        )

    def test_only_initializes_string_arrays_with_str_options(self) -> None:
        string_configs = StringConfigs()
        compiler_configs = CompilerConfigs(string_configs=string_configs)
        string_configs.strname_to_size["A$()"] = 321
        program = compiler.convert(
            "10 DIM A$(10), B$",
            add_standard_prefix=False,
            compiler_configs=compiler_configs,
            default_str_storage=123,
            initialize_vars=True,
            output_dependencies=True,
            procname="test",
            skip_procedure_headers=True,
        )
        assert (
            program == "10 DIM arr_A$(11): STRING[321]\n"
            'FOR tmp_1 = 0 TO 10 \\ arr_A$(tmp_1) := "" \\ NEXT tmp_1\n'
            "DIM B$: STRING[123]\n"
            'B$ := ""\n'
        )
