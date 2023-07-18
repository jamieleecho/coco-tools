import unittest
import pkg_resources

from coco import b09


class TestB09(unittest.TestCase):
    def get_resource(name):
        resource_path = pkg_resources.resource_filename(
            __name__, f'fixtures/{name}'
        )
        with open(resource_path, 'r') as resource_file:
            return resource_file.read()

    simple_prog = get_resource('simple.bas')
    simple2_prog = get_resource('simple2.bas')
    simple3_prog = get_resource('simple3.bas')

    def test_basic_assignment(self):
        var = b09.BasicVar('HW')
        exp = b09.BasicLiteral(123)
        target = b09.BasicAssignment(var, exp)
        assert target.basic09_text(1) == '  HW = 123'

    def test_basic_binary_exp(self):
        var = b09.BasicVar('HW')
        strlit = b09.BasicLiteral('HW')
        target = b09.BasicBinaryExp(var, '=', strlit)
        assert target.basic09_text(1) == 'HW = "HW"'

    def test_comment(self):
        target = b09.BasicComment(' hello world ')
        assert target.basic09_text(1) == '(* hello world  *)'

    def test_comment_statement(self):
        comment = b09.BasicComment(' hello world ')
        target = b09.BasicStatement(comment)
        assert target.basic09_text(2) == '    (* hello world  *)'

    def test_comment_statements(self):
        comment = b09.BasicComment(' hello world ')
        statement = b09.BasicStatement(comment)
        target = b09.BasicStatements((statement,))
        assert target.basic09_text(2) == '    (* hello world  *)'

    def test_comment_lines(self):
        comment = b09.BasicComment(' hello world ')
        statement = b09.BasicStatement(comment)
        statements = b09.BasicStatements((statement,))
        target = b09.BasicLine(25, statements)
        assert target.basic09_text(1) == '25   (* hello world  *)'

    def test_basic_float_literal(self):
        target = b09.BasicLiteral(123.0)
        assert target.basic09_text(2) == '123.0'

    def test_basic_goto(self):
        target = b09.BasicGoto(123, True)
        assert target.basic09_text(1) == '123'
        assert target.implicit is True
        target = b09.BasicGoto(1234, False)
        assert target.basic09_text(1) == '  GOTO 1234'
        assert target.implicit is False

    def test_if(self):
        strlit = b09.BasicLiteral('HW')
        exp = b09.BasicBinaryExp(strlit, '=', strlit)
        goto = b09.BasicGoto(123, True)
        target = b09.BasicIf(exp, goto)
        assert target.basic09_text(1) == '  IF "HW" = "HW" THEN 123'

    def test_basic_int_literal(self):
        target = b09.BasicLiteral(123)
        assert target.basic09_text(2) == '123'

    def test_basic_str_literal(self):
        target = b09.BasicLiteral('123.0')
        assert target.basic09_text(1) == '"123.0"'

    def test_basic_paren_exp(self):
        strlit = b09.BasicLiteral('HELLO WORLD')
        target = b09.BasicParenExp(strlit)
        assert target.basic09_text(2) == '("HELLO WORLD")'

    def test_basic_op_exp(self):
        strlit = b09.BasicLiteral('HELLO WORLD')
        target = b09.BasicOpExp('&', strlit)
        assert target.operator == '&'
        assert target.exp == strlit
        assert target.basic09_text(1) == '& "HELLO WORLD"'

    def test_basic_operator(self):
        target = b09.BasicOperator('*')
        assert target.basic09_text(2) == '*'

    def generic_test_parse(self, progin, progout,
                           filter_unused_linenum=False,
                           initialize_vars=False):
        b09_prog = b09.convert(
            progin,
            filter_unused_linenum=filter_unused_linenum,
            initialize_vars=initialize_vars
        )
        assert b09_prog == progout

    def test_parse_array_ref(self):
        self.generic_test_parse(
            '10 A = B(123 - 1 - (2/2),1,2)\n',
            '10 A = arr_B(123 - 1 - (2 / 2), 1, 2)')

    def test_parse_array_assignment(self):
        self.generic_test_parse(
            '10 A (123 - 1 - (2/2),1,2)=123+64',
            '10 arr_A(123 - 1 - (2 / 2), 1, 2) = 123 + 64')

    def test_parse_str_array_ref(self):
        self.generic_test_parse(
            '10 A$ = B$(123 - 1 - (2/2),1,2)',
            '10 A$ = arr_B$(123 - 1 - (2 / 2), 1, 2)')

    def test_parse_str_array_assignment(self):
        self.generic_test_parse(
            '10 A$ (123 - 1 - (2/2),1,2)="123"+"64"',
            '10 arr_A$(123 - 1 - (2 / 2), 1, 2) = "123" + "64"')

    def test_parse_comment_program(self):
        self.generic_test_parse(
            '15 REM HELLO WORLD\n',
            '15 (* HELLO WORLD *)')

    def test_parse_comments_program(self):
        self.generic_test_parse(
            '15 REM HELLO WORLD\n20 REM HERE',
            '15 (* HELLO WORLD *)\n20 (* HERE *)')

    def test_parse_simple_assignment(self):
        self.generic_test_parse(
            '10 A = 123\n20 B=123.4\n30C$="HELLO"\n35D$=C$',
            '10 A = 123\n20 B = 123.4\n30 C$ = "HELLO"\n35 D$ = C$')

    def test_parse_paren_expression(self):
        self.generic_test_parse(
            '10 A = (AB)',
            '10 A = (AB)')

    def test_parse_prod_expression(self):
        self.generic_test_parse(
            '10 A = 64 * 32\n20 B = 10/AB',
            '10 A = 64 * 32\n20 B = 10 / AB')

    def test_parse_add_expression(self):
        self.generic_test_parse(
            '10 A = 64 + 32\n20 B = 10-AB+32',
            '10 A = 64 + 32\n20 B = 10 - AB + 32')

    def test_parse_str_expression(self):
        self.generic_test_parse(
            '10 A$ = "A" + "Z"\n20B$=A$+B$',
            '10 A$ = "A" + "Z"\n20 B$ = A$ + B$')

    def test_parse_multi_expression(self):
        self.generic_test_parse(
            '10 A = 64 + 32*10 / AB -1',
            '10 A = 64 + 32 * 10 / AB - 1')

    def test_parse_gtle_expression(self):
        self.generic_test_parse(
            '10 A = 4 < 2\n15 B=4>2\n20C=A<>B',
            '10 A = 4 < 2\n15 B = 4 > 2\n20 C = A <> B')

    def test_parse_multi_expression2(self):
        self.generic_test_parse(
            '10 A=(64+32)*10/(AB-1)',
            '10 A = (64 + 32) * 10 / (AB - 1)')

    def test_parse_multi_expression3(self):
        # Note that the output is not a legal Basic09 construct
        self.generic_test_parse(
            '10 A = A + 2 AND 3 < 3',
            '10 A = LAND(A + 2, 3 < 3)')

    def test_parse_multi_statement(self):
        self.generic_test_parse(
            '10 A=A+2:B=B+1',
            '10 A = A + 2\nB = B + 1')

    def test_simple_if_statement(self):
        self.generic_test_parse(
            '1 IF A=1 THEN 2\n2 IF A<10 THEN B = B - 2 * 1',
            '1 IF A = 1 THEN 2\n2 IF A < 10 THEN\n  B = B - 2 * 1\nENDIF')

    def test_binary_if_statement(self):
        self.generic_test_parse(
            '1 IF A=1 AND B=2 THEN 2\n2 IF A<10 THEN B = B - 2 * 1',
            '1 IF A = 1 AND B = 2 THEN 2\n2 IF A < 10 THEN\n'
            '  B = B - 2 * 1\nENDIF')

    def test_paren_if_statement(self):
        self.generic_test_parse(
            '1 IF (A=1 AND B=2) THEN 2\n2 IF A<10 THEN B = B - 2 * 1',
            '1 IF (A = 1 AND B = 2) THEN 2\n2 IF A < 10 THEN\n'
            '  B = B - 2 * 1\nENDIF')

    def test_simple_print_statement(self):
        self.generic_test_parse(
            '11 PRINT "HELLO WORLD"',
            '11 PRINT "HELLO WORLD"'
        )

    def test_simple_print_statement2(self):
        self.generic_test_parse(
            '11 PRINT 3 + 3',
            '11 PRINT 3 + 3'
        )

    def test_simple_print_statement3(self):
        self.generic_test_parse(
            '11 PRINT A$ + B$',
            '11 PRINT A$ + B$'
        )

    def test_print_multi(self):
        self.generic_test_parse(
            '11 PRINT A$ , B$',
            '11 PRINT A$, B$'
        )

    def test_print_odd(self):
        self.generic_test_parse(
            '11 PRINT A$,,B$',
            '11 PRINT A$, "", B$'
        )

    def test_land(self):
        self.generic_test_parse(
            '11 PRINT A=A AND 4',
            '11 PRINT LAND(A = A, 4)'
        )

    def test_lor(self):
        self.generic_test_parse(
            '11 Z = A=B OR F=Z',
            '11 Z = LOR(A = B, F = Z)'
        )

    def test_lnot(self):
        self.generic_test_parse(
            '11 Z = NOT A=B',
            '11 Z = LNOT(A = B)'
        )

    def test_if_not(self):
        self.generic_test_parse(
            '100 IF NOT A=3 THEN 20',
            '100 IF NOT(A = 3) THEN 20'
        )

    def test_sound(self):
        self.generic_test_parse(
            '11 SOUND 100, A+B',
            '11 RUN ecb_sound(100, A + B, 31)'
        )

    def test_cls(self):
        self.generic_test_parse(
            '11 CLS A+B\n12 CLS',
            '11 RUN ecb_cls(A + B)\n12 RUN ecb_cls(1)'
        )

    def test_funcs(self):
        for ecb_func, b09_func in b09.FUNCTIONS.items():
            self.generic_test_parse(
                f'11X={ecb_func}(1)',
                f'11 X = {b09_func}(1)',
            )

    def test_hex_literal(self):
        self.generic_test_parse(
            f'11 PRINT&H1234',
            f'11 PRINT $1234',
        )

        self.generic_test_parse(
            f'11 PRINT&HFFFFFF',
            f'11 PRINT 16777215',
        )

    def test_left_and_right(self):
        self.generic_test_parse(
            f'11 AA$=LEFT$("HELLO" , 3)',
            f'11 AA$ = LEFT$("HELLO", 3)'
        )
        self.generic_test_parse(
            f'11 AA$=RIGHT$("HELLO" , 3)',
            f'11 AA$ = RIGHT$("HELLO", 3)'
        )

    def test_mid(self):
        self.generic_test_parse(
            f'11 AA$=MID$("HELLO" , 3,2)',
            f'11 AA$ = MID$("HELLO", 3, 2)'
        )

    def test_val(self):
        self.generic_test_parse(
            f'11 AA = VAL("2334")',
            f'11 AA = VAL("2334")'
        )

    def test_num_str_funcs(self):
        for ecb_func, b09_func in b09.NUM_STR_FUNCTIONS.items():
            self.generic_test_parse(
                f'11X$={ecb_func}(1)',
                f'11 X$ = {b09_func}(1)',
            )

    def test_builtin_statements(self):
        for ecb_func, b09_func in b09.STATEMENTS2.items():
            self.generic_test_parse(
                f'11{ecb_func}(1,2)',
                f'11 {b09_func}(1, 2)',
            )

        for ecb_func, b09_func in b09.STATEMENTS3.items():
            self.generic_test_parse(
                f'11{ecb_func}(1,2    , 3)',
                f'11 {b09_func}(1, 2, 3)',
            )

    def test_goto(self):
        self.generic_test_parse(
            f'11GOTO20',
            f'11 GOTO 20',
        )

    def test_gosub(self):
        self.generic_test_parse(
            f'11GOSUB20',
            f'11 GOSUB 20',
        )

    def test_data(self):
        self.generic_test_parse(
            '10 DATA 1,2,3,"",,"FOO","BAR", BAZ  \n'
            '20 DATA   , ',
            '10 DATA 1, 2, 3, "", "", "FOO", "BAR", "BAZ  "\n'
            '20 DATA "", ""'
        )

    def test_single_kw_statements(self):
        for ecb_func, b09_func in b09.SINGLE_KEYWORD_STATEMENTS.items():
            self.generic_test_parse(
                f'11{ecb_func}',
                f'11 {b09_func}',
            )

    def test_print(self):
        self.generic_test_parse(
            '11PRINT"HELLO WORLD"',
            '11 PRINT "HELLO WORLD"'
        )

    def test_print_at(self):
        self.generic_test_parse(
            '11PRINT@32,"HELLO WORLD"',
            '11 RUN ecb_at(32) \\ PRINT "HELLO WORLD"'
        )

    def test_for(self):
        self.generic_test_parse(
            '11FORII=1TO20',
            '11 FOR II = 1 TO 20'
        )

    def test_for_step(self):
        self.generic_test_parse(
            '11FORII=1TO20STEP30',
            '11 FOR II = 1 TO 20 STEP 30'
        )

    def test_next(self):
        self.generic_test_parse(
            '10NEXTJJ',
            '10 NEXT JJ'
        )

    def test_multiline(self):
        self.generic_test_parse(
            '10 PRINT "HELLO"\n'
            '20 A = 2',
            '10 PRINT "HELLO"\n'
            '20 A = 2'
        )

    def test_multiline2(self):
        self.generic_test_parse(
            '10 REM Hello World\n'
            '20 CLS 5\n'
            '30 PRINT "HELLO"\n'
            '40 B = 2',
            '10 (* Hello World *)\n'
            '20 RUN ecb_cls(5)\n'
            '30 PRINT "HELLO"\n'
            '40 B = 2'
        )

    def test_for_next(self):
        self.generic_test_parse(
            '10 FOR YY=1 TO 20 STEP 1\n'
            '20 FOR XX=1 TO 20 STEP 1\n'
            '30 PRINT XX, YY\n'
            '40 NEXT XX, YY\n'
            '50 PRINT "HELLO"',
            '10 FOR YY = 1 TO 20 STEP 1\n'
            '20   FOR XX = 1 TO 20 STEP 1\n'
            '30     PRINT XX, YY\n'
            '40 NEXT XX \\ NEXT YY\n'
            '50 PRINT "HELLO"'
        )

    def test_functions_to_statements(self):
        for ecb_func, b09_func in b09.FUNCTIONS_TO_STATEMENTS.items():
            self.generic_test_parse(
                f'11X={ecb_func}(1)',
                f'11 {b09_func}(1, X)',
            )

    def test_functions_to_statements2(self):
        for ecb_func, b09_func in b09.FUNCTIONS_TO_STATEMENTS2.items():
            self.generic_test_parse(
                f'11X={ecb_func}(1, 2)',
                f'11 {b09_func}(1, 2, X)',
            )

    def test_num_str_functions_to_statements(self):
        for ecb_func, b09_func in b09.NUM_STR_FUNCTIONS_TO_STATEMENTS.items():
            self.generic_test_parse(
                f'11X$={ecb_func}(1)',
                f'11 {b09_func}(1, X$)',
            )

    def test_str_functions_to_statements(self):
        for ecb_func, b09_func in b09.STR_FUNCTIONS_TO_STATEMENTS.items():
            self.generic_test_parse(
                f'11X$={ecb_func}(1)',
                f'11 {b09_func}(1, X$)',
            )

    def test_joystk(self):
        self.generic_test_parse(
            '11 PRINT JOYSTK(1)',
            'dim joy0x, joy0y, joy1x, joy0y: integer\n'
            '11 RUN ecb_joystk(1, tmp1) \\ PRINT tmp1'
        )

    def test_hex(self):
        self.generic_test_parse(
            '11 PRINT HEX$(1)',
            '11 RUN ecb_hex(1, tmp1$) \\ PRINT tmp1$'
        )

    def test_dim1(self):
        self.generic_test_parse(
            '11 DIMA(12)',
            '11 DIM arr_A(12) \\ '
            'FOR tmp1 = 1 TO 12 \\ '
            'arr_A(tmp1) = 0 \\ '
            'NEXT tmp1'
        )

    def test_dim2(self):
        self.generic_test_parse(
            '11 DIMA(12,&H123)',
            '11 DIM arr_A(12, $123) \\ '
            'FOR tmp1 = 1 TO 12 \\ '
            'FOR tmp2 = 1 TO $123 \\ '
            'arr_A(tmp1, tmp2) = 0 \\ '
            'NEXT tmp2 \\ '
            'NEXT tmp1'
        )

    def test_dim3(self):
        self.generic_test_parse(
            '11 DIMA(12,&H123,55)',
            '11 DIM arr_A(12, $123, 55) \\ '
            'FOR tmp1 = 1 TO 12 \\ '
            'FOR tmp2 = 1 TO $123 \\ '
            'FOR tmp3 = 1 TO 55 \\ '
            'arr_A(tmp1, tmp2, tmp3) = 0 \\ '
            'NEXT tmp3 \\ '
            'NEXT tmp2 \\ '
            'NEXT tmp1'
        )

    def test_str_dim1(self):
        self.generic_test_parse(
            '11 DIMA$(12)',
            '11 DIM arr_A$(12) \\ '
            'FOR tmp1 = 1 TO 12 \\ '
            'arr_A$(tmp1) = "" \\ '
            'NEXT tmp1'
        )

    def test_str_dim2(self):
        self.generic_test_parse(
            '11 DIMA$(12,&H123)',
            '11 DIM arr_A$(12, $123) \\ '
            'FOR tmp1 = 1 TO 12 \\ '
            'FOR tmp2 = 1 TO $123 \\ '
            'arr_A$(tmp1, tmp2) = "" \\ '
            'NEXT tmp2 \\ '
            'NEXT tmp1'
        )

    def test_str_dim3(self):
        self.generic_test_parse(
            '11 DIMA$(12,&H123,55)',
            '11 DIM arr_A$(12, $123, 55) \\ '
            'FOR tmp1 = 1 TO 12 \\ '
            'FOR tmp2 = 1 TO $123 \\ '
            'FOR tmp3 = 1 TO 55 \\ '
            'arr_A$(tmp1, tmp2, tmp3) = "" \\ '
            'NEXT tmp3 \\ '
            'NEXT tmp2 \\ '
            'NEXT tmp1'
        )

    def test_line_filter(self):
        self.generic_test_parse(
            '10 GOTO 10\n'
            '20 GOSUB 100\n'
            '30 GOTO 10\n'
            '100 REM\n',
            '10 GOTO 10\n'
            'GOSUB 100\n'
            'GOTO 10\n'
            '100 (* *)',
            filter_unused_linenum=True
        )

    def test_initializes_vars(self):
        self.generic_test_parse(
            '10 PRINT A+B, A$',
            'A = 0\n'
            'A$ = ""\n'
            'B = 0\n'
            '10 PRINT A + B, A$',
            filter_unused_linenum=False,
            initialize_vars=True
        )

    def test_on_goto(self):
        self.generic_test_parse(
            '10 ON NN GOTO 11, 22, 33, 44\n'
            '20 ON MM GOSUB 100\n',
            'ON NN GOTO 11, 22, 33, 44\n'
            'ON MM GOSUB 100',
            filter_unused_linenum=True,
        )
