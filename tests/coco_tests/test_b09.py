import unittest
import pkg_resources

from coco import b09


class TestB09(unittest.TestCase):
    def test_convert_with_dependencies(self):
        program = b09.convert('10 CLS B', procname='do_cls',
                              initialize_vars=True,
                              filter_unused_linenum=True,
                              skip_procedure_headers=False,
                              output_dependencies=True)
        assert program.endswith('procedure do_cls\nB = 0.0\nbase 0\n'
                                'RUN _ecb_start\nRUN ecb_cls(B)\n')
        assert program.startswith('procedure _ecb_cursor_color\n')
        assert program.find('procedure _ecb_text_address\n') >= 0

    def test_convert_no_header_with_dependencies(self):
        program = b09.convert('10 CLS B', procname='do_cls',
                              initialize_vars=True,
                              filter_unused_linenum=True,
                              skip_procedure_headers=True,
                              output_dependencies=True)
        assert program == 'B = 0.0\nbase 0\nRUN _ecb_start\nRUN ecb_cls(B)\n'

    def test_convert_header_no_name_with_dependencies(self):
        program = b09.convert('10 CLS B',
                              initialize_vars=True,
                              filter_unused_linenum=True,
                              skip_procedure_headers=False,
                              output_dependencies=True)
        assert program.endswith('procedure program\nB = 0.0\nbase 0\n'
                                'RUN _ecb_start\nRUN ecb_cls(B)\n')
        assert program.startswith('procedure _ecb_cursor_color\n')

    def test_basic_assignment(self):
        var = b09.BasicVar('HW')
        exp = b09.BasicLiteral(123.0)
        target = b09.BasicAssignment(var, exp)
        assert target.basic09_text(1) == '  HW = 123.0'

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

    def test_basic_real_literal(self):
        target = b09.BasicLiteral(123.)
        assert target.basic09_text(2) == '123.0'

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

    def generic_test_parse(
            self, progin, progout,
            filter_unused_linenum=False,
            initialize_vars=False,
            add_standard_prefix=False,
            output_dependencies=False,
            skip_procedure_headers=True,):
        b09_prog = b09.convert(
            progin,
            filter_unused_linenum=filter_unused_linenum,
            initialize_vars=initialize_vars,
            skip_procedure_headers=skip_procedure_headers,
            output_dependencies=output_dependencies,
            add_standard_prefix=add_standard_prefix,
        )
        assert b09_prog == progout + '\n'

    def test_parse_array_ref(self):
        self.generic_test_parse(
            '10 A = B(123 - 1 - (2/2),1,2)\n',
            '10 A = arr_B(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0)')

    def test_parse_array_assignment(self):
        self.generic_test_parse(
            '10 A (123 - 1 - (2/2),1,2)=123+64',
            '10 arr_A(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0) = 123.0 + 64.0')

    def test_parse_str_array_ref(self):
        self.generic_test_parse(
            '10 A$ = B$(123 - 1 - (2/2),1,2)',
            '10 A$ = arr_B$(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0)')

    def test_parse_str_array_assignment(self):
        self.generic_test_parse(
            '10 A$ (123 - 1 - (2/2),1,2)="123"+"64"',
            '10 arr_A$(123.0 - 1.0 - (2.0 / 2.0), 1.0, 2.0) = "123" + "64"')

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
            '10 A = 123.0\n20 B = 123.4\n30 C$ = "HELLO"\n35 D$ = C$')

    def test_parse_paren_expression(self):
        self.generic_test_parse(
            '10 A = (AB)',
            '10 A = (AB)')

    def test_parse_prod_expression(self):
        self.generic_test_parse(
            '10 A = 64 * 32\n20 B = 10/AB',
            '10 A = 64.0 * 32.0\n20 B = 10.0 / AB')

    def test_parse_add_expression(self):
        self.generic_test_parse(
            '10 A = 64 + 32\n20 B = 10-AB+32',
            '10 A = 64.0 + 32.0\n20 B = 10.0 - AB + 32.0')

    def test_parse_str_expression(self):
        self.generic_test_parse(
            '10 A$ = "A" + "Z"\n20B$=A$+B$',
            '10 A$ = "A" + "Z"\n20 B$ = A$ + B$')

    def test_parse_str_expression2(self):
        self.generic_test_parse(
            '10 IF A$<>"" THEN 10',
            '10 IF A$ <> "" THEN 10')

    def test_parse_multi_expression(self):
        self.generic_test_parse(
            '10 A = 64 + 32*10 / AB -1',
            '10 A = 64.0 + 32.0 * 10.0 / AB - 1.0')

    def test_parse_gtle_expression(self):
        self.generic_test_parse(
            '10 A = 4 < 2\n15 B=4>2\n20C=A<>B',
            '10 A = 4.0 < 2.0\n15 B = 4.0 > 2.0\n20 C = A <> B')

    def test_parse_multi_expression2(self):
        self.generic_test_parse(
            '10 A=(64+32)*10/(AB-1)',
            '10 A = (64.0 + 32.0) * 10.0 / (AB - 1.0)')

    def test_parse_multi_expression3(self):
        # Note that the output is not a legal Basic09 construct
        self.generic_test_parse(
            '10 A = A + 2 AND 3 < 3',
            '10 A = LAND(A + 2.0, 3.0 < 3.0)')

    def test_parse_multi_statement(self):
        self.generic_test_parse(
            '10 A=A+2:B=B+1',
            '10 A = A + 2.0\nB = B + 1.0')

    def test_simple_if_statement(self):
        self.generic_test_parse(
            '1 IF A=1 THEN 2\n2 IF A<10 THEN B = B - 2 * 1',
            '1 IF A = 1.0 THEN 2\n2 IF A < 10.0 THEN\n  B = B - 2.0 * 1.0'
            '\nENDIF')

    def test_binary_if_statement(self):
        self.generic_test_parse(
            '1 IF A=1 AND B=2 THEN 2\n2 IF A<10 THEN B = B - 2 * 1',
            '1 IF A = 1.0 AND B = 2.0 THEN 2\n2 IF A < 10.0 THEN\n'
            '  B = B - 2.0 * 1.0\nENDIF')

    def test_paren_if_statement(self):
        self.generic_test_parse(
            '1 IF (A=1 AND B=2) THEN 2\n2 IF A<10 THEN B = B - 2 * 1',
            '1 IF (A = 1.0 AND B = 2.0) THEN 2\n2 IF A < 10.0 THEN\n'
            '  B = B - 2.0 * 1.0\nENDIF')

    def test_simple_print_statement(self):
        self.generic_test_parse(
            '11 PRINT "HELLO WORLD"',
            '11 PRINT "HELLO WORLD"'
        )

    def test_simple_print_statement2(self):
        self.generic_test_parse(
            '11 PRINT 3 + 3',
            '11 PRINT 3.0 + 3.0'
        )

    def test_simple_print_statement3(self):
        self.generic_test_parse(
            '11 PRINT A$ + B$',
            '11 PRINT A$ + B$'
        )

    def test_simple_print_statement4(self):
        self.generic_test_parse(
            '11 PRINT"TIME"T/10;',
            '11 PRINT "TIME"; T / 10.0;'
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
            '11 PRINT LAND(A = A, 4.0)'
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
            '100 IF NOT(A = 3.0) THEN 20'
        )

    def test_sound(self):
        self.generic_test_parse(
            '11 SOUND 100, A+B',
            '11 RUN ecb_sound(100.0, A + B, 31.0)'
        )

    def test_poke(self):
        self.generic_test_parse(
            '11 POKE65497,A+B',
            '11 POKE 65497.0, A + B'
        )

    def test_cls(self):
        self.generic_test_parse(
            '11 CLS A+B\n12 CLS',
            '11 RUN ecb_cls(A + B)\n12 RUN ecb_cls(1.0)'
        )

    def test_funcs(self):
        for ecb_func, b09_func in b09.FUNCTIONS.items():
            self.generic_test_parse(
                f'11X={ecb_func}(1)',
                f'11 X = {b09_func}(1.0)',
            )

    def test_hex_literal(self):
        self.generic_test_parse(
            '11 PRINT&H1234',
            '11 run ecb_str($1234, tmp_1$) \\ PRINT tmp_1$',
        )

        self.generic_test_parse(
            '11 PRINT&HFFFFFF',
            '11 run ecb_str(16777215, tmp_1$) \\ PRINT tmp_1$',
        )

    def test_left_and_right(self):
        self.generic_test_parse(
            '11 AA$=LEFT$("HELLO" , 3)',
            '11 AA$ = LEFT$("HELLO", 3.0)'
        )
        self.generic_test_parse(
            '11 AA$=RIGHT$("HELLO" , 3.0)',
            '11 AA$ = RIGHT$("HELLO", 3.0)'
        )

    def test_mid(self):
        self.generic_test_parse(
            f'11 AA$=MID$("HELLO" , 3,2)',
            f'11 AA$ = MID$("HELLO", 3.0, 2.0)'
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
                f'11 X$ = {b09_func}(1.0)',
            )

    def test_builtin_statements(self):
        for ecb_func, b09_func in b09.STATEMENTS2.items():
            self.generic_test_parse(
                f'11{ecb_func}(1,2)',
                f'11 {b09_func}(1.0, 2.0)',
            )

        for ecb_func, b09_func in b09.STATEMENTS3.items():
            self.generic_test_parse(
                f'11{ecb_func}(1,2    , 3)',
                f'11 {b09_func}(1.0, 2.0, 3.0)',
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
            '10 DATA "1.0", "2.0", "3.0", "", "", "FOO", "BAR", "BAZ  "\n'
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
            '11 RUN ecb_at(32.0) \\ PRINT "HELLO WORLD"'
        )

    def test_for(self):
        self.generic_test_parse(
            '11FORII=1TO20',
            '11 FOR II = 1.0 TO 20.0'
        )

    def test_for_step(self):
        self.generic_test_parse(
            '11FORII=1TO20STEP30',
            '11 FOR II = 1.0 TO 20.0 STEP 30.0'
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
            '20 A = 2.0'
        )

    def test_multiline2(self):
        self.generic_test_parse(
            '10 REM Hello World\n'
            '20 CLS 5.0\n'
            '30 PRINT "HELLO"\n'
            '40 B = 2.0',
            '10 (* Hello World *)\n'
            '20 RUN ecb_cls(5.0)\n'
            '30 PRINT "HELLO"\n'
            '40 B = 2.0'
        )

    def test_for_next(self):
        self.generic_test_parse(
            '10 FOR YY=1 TO 20 STEP 1\n'
            '20 FOR XX=1 TO 20 STEP 1\n'
            '30 PRINT XX, YY\n'
            '40 NEXT XX, YY\n'
            '50 PRINT "HELLO"',
            '10 FOR YY = 1.0 TO 20.0 STEP 1.0\n'
            '20   FOR XX = 1.0 TO 20.0 STEP 1.0\n'
            '30     run ecb_str(XX, tmp_1$) \\ run ecb_str(YY, tmp_2$) \\ '
            'PRINT tmp_1$, tmp_2$\n'
            '40 NEXT XX \\ NEXT YY\n'
            '50 PRINT "HELLO"'
        )

    def test_functions_to_statements(self):
        for ecb_func, b09_func in b09.FUNCTIONS_TO_STATEMENTS.items():
            self.generic_test_parse(
                f'11X={ecb_func}(1)',
                f'11 {b09_func}(1.0, X)',
            )

    def test_functions_to_statements2(self):
        for ecb_func, b09_func in b09.FUNCTIONS_TO_STATEMENTS2.items():
            self.generic_test_parse(
                f'11X={ecb_func}(1, 2)',
                f'11 {b09_func}(1.0, 2.0, X)',
            )

    def test_num_str_functions_to_statements(self):
        for ecb_func, b09_func in b09.NUM_STR_FUNCTIONS_TO_STATEMENTS.items():
            self.generic_test_parse(
                f'11X$={ecb_func}(1)',
                f'11 {b09_func}(1.0, X$)',
            )

    def test_str_functions_to_statements(self):
        for ecb_func, b09_func in b09.STR_FUNCTIONS_TO_STATEMENTS.items():
            self.generic_test_parse(
                f'11X$={ecb_func}',
                f'11 {b09_func}(X$)',
            )

    def test_joystk(self):
        self.generic_test_parse(
            '11 PRINT JOYSTK(1)',
            'dim joy0x, joy0y, joy1x, joy0y: integer\n'
            '11 RUN ecb_joystk(1.0, tmp_1) \\ run ecb_str(tmp_1, tmp_1$) \\ '
            'PRINT tmp_1$'
        )

    def test_hex(self):
        self.generic_test_parse(
            '11 PRINT HEX$(1)',
            '11 RUN ecb_hex(1.0, tmp_1$) \\ PRINT tmp_1$'
        )

    def test_dim1(self):
        self.generic_test_parse(
            '11 DIMA(12),B(3),CC(20)',
            '11 DIM arr_A(13), arr_B(4), arr_CC(21)\n'
            'FOR tmp_1 = 0 TO 12 \\ '
            'arr_A(tmp_1) = 0 \\ '
            'NEXT tmp_1\n'
            'FOR tmp_1 = 0 TO 3 \\ '
            'arr_B(tmp_1) = 0 \\ '
            'NEXT tmp_1\n'
            'FOR tmp_1 = 0 TO 20 \\ '
            'arr_CC(tmp_1) = 0 \\ '
            'NEXT tmp_1'
        )

    def test_dim2(self):
        self.generic_test_parse(
            '11 DIMA(12,&H123)',
            '11 DIM arr_A(13, $124)\n'
            'FOR tmp_1 = 0 TO 12 \\ '
            'FOR tmp_2 = 0 TO $123 \\ '
            'arr_A(tmp_1, tmp_2) = 0 \\ '
            'NEXT tmp_2 \\ '
            'NEXT tmp_1'
        )

    def test_dim3(self):
        self.generic_test_parse(
            '11 DIMA(12,&H123,55)',
            '11 DIM arr_A(13, $124, 56)\n'
            'FOR tmp_1 = 0 TO 12 \\ '
            'FOR tmp_2 = 0 TO $123 \\ '
            'FOR tmp_3 = 0 TO 55 \\ '
            'arr_A(tmp_1, tmp_2, tmp_3) = 0 \\ '
            'NEXT tmp_3 \\ '
            'NEXT tmp_2 \\ '
            'NEXT tmp_1'
        )

    def test_str_dim1(self):
        self.generic_test_parse(
            '11 DIMA$(12)',
            '11 DIM arr_A$(13)\n'
            'FOR tmp_1 = 0 TO 12 \\ '
            'arr_A$(tmp_1) = "" \\ '
            'NEXT tmp_1'
        )

    def test_str_dim2(self):
        self.generic_test_parse(
            '11 DIMA$(12,&H123)',
            '11 DIM arr_A$(13, $124)\n'
            'FOR tmp_1 = 0 TO 12 \\ '
            'FOR tmp_2 = 0 TO $123 \\ '
            'arr_A$(tmp_1, tmp_2) = "" \\ '
            'NEXT tmp_2 \\ '
            'NEXT tmp_1'
        )

    def test_str_dim3(self):
        self.generic_test_parse(
            '11 DIMA$(12,&H123,55)',
            '11 DIM arr_A$(13, $124, 56)\n'
            'FOR tmp_1 = 0 TO 12 \\ '
            'FOR tmp_2 = 0 TO $123 \\ '
            'FOR tmp_3 = 0 TO 55 \\ '
            'arr_A$(tmp_1, tmp_2, tmp_3) = "" \\ '
            'NEXT tmp_3 \\ '
            'NEXT tmp_2 \\ '
            'NEXT tmp_1'
        )

    def test_dim_misc(self):
        self.generic_test_parse(
            '11 DIMA$,B',
            '11 DIM A$, B'
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

    def test_clear_statement(self):
        self.generic_test_parse(
            '10 CLEAR\n20CLEAR 200',
            '10 (* CLEAR *)\n20 (* CLEAR 200 *)'
        )

    def test_initializes_vars(self):
        self.generic_test_parse(
            '10 PRINT A+B, A$',
            'A = 0.0\n'
            'A$ = ""\n'
            'B = 0.0\n'
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

    def test_simple_read(self):
        self.generic_test_parse(
            '10 READA$,B,D(II,JJ),E$(XX)',
            '10 READ A$, B, arr_D(II, JJ), arr_E$(XX)')

    def test_mars_data(self):
        self.generic_test_parse(
            '120 DATAA CONTROL ROOM,AN ENGINE ROOM,A BARREN FIELD,A MOAT',
            '120 DATA "A CONTROL ROOM", "AN ENGINE ROOM", '
            '"A BARREN FIELD", "A MOAT"')

    def test_input(self):
        self.generic_test_parse(
            '10 INPUT "HELLO WORLD";A$,B(1,2,3),C,D$(3)',
            '10 RUN _ecb_input_prefix \\ '
            'INPUT "HELLO WORLD? ", A$, arr_B(1.0, 2.0, 3.0), C, '
            'arr_D$(3.0) \\ RUN _ecb_input_suffix')

    def test_input_no_message(self):
        self.generic_test_parse(
            '10 INPUT A$,B(1,2,3)',
            '10 RUN _ecb_input_prefix \\ '
            'INPUT "? ", A$, arr_B(1.0, 2.0, 3.0) \\ '
            'RUN _ecb_input_suffix')

    def test_mars_if(self):
        self.generic_test_parse(
            '480 IFL(4)<>11ORL(6)<>11ORL(32)<>11'
            'ORL(30)<>11ORGR=0THEN500',
            '480 IF arr_L(4.0) <> 11.0 '
            'OR arr_L(6.0) <> 11.0 '
            'OR arr_L(32.0) <> 11.0 '
            'OR arr_L(30.0) <> 11.0 OR GR = 0.0 THEN 500')

    def test_multi_and_or(self):
        self.generic_test_parse(
            '480 Z=A ANDB ORC ANDD ORC',
            '480 Z = LOR(LOR(LAND(A, B), LAND(C, D)), C)')

    def test_multi_arithmetic(self):
        self.generic_test_parse(
            '480 Z=A+B*C-D/C',
            '480 Z = A + B * C - D / C')

    def test_num_if(self):
        self.generic_test_parse(
            '480 IFA THEN100',
            '480 IF A <> 0.0 THEN 100')

    def test_read_empty_data(self):
        self.generic_test_parse(
            '10 READ A,B$,C\n'
            '20 DATA ,FOO,',
            '10 READ tmp_1$, B$, tmp_2$ \\ '
            'RUN ecb_read_filter(tmp_1$, A) \\ '
            'RUN ecb_read_filter(tmp_2$, C)\n'
            '20 DATA "", "FOO", ""'
        )

    def test_filter_line_zero(self):
        self.generic_test_parse(
            '0 CLS\n',
            'RUN ecb_cls(1.0)'
        )

    def test_does_not_filter_line_zero(self):
        self.generic_test_parse(
            '0 CLS:GOTO 0\n',
            '0 RUN ecb_cls(1.0)\n'
            'GOTO 0'
        )

    def test_handles_empty_next(self):
        self.generic_test_parse(
            '10 FORX=1TO10\n'
            '20 FORY=1TO10\n'
            '30 NEXT\n'
            '40 NEXT\n'
            '50 NEXT\n',
            '10 FOR X = 1.0 TO 10.0\n'
            '20   FOR Y = 1.0 TO 10.0\n'
            '30   NEXT Y\n'
            '40 NEXT X\n'
            '50 NEXT'
        )

    def test_adds_standard_prefix(self):
        program = b09.convert('10 REM', procname='do_cls',
                              initialize_vars=True,
                              filter_unused_linenum=True,
                              skip_procedure_headers=False,
                              add_standard_prefix=True,
                              output_dependencies=True)
        assert program.startswith('procedure _ecb_cursor_color\n')
        assert 'procedure _ecb_start' in program
        assert program.endswith('procedure do_cls\nbase 0\nRUN _ecb_start\n'
                                '(* *)\n')

    def test_multiple_print_ats(self):
        self.generic_test_parse(
            '130 PRINT@64,"COLOR (1-8)";: INPUT CO\n'
            '140 IF (CO<1 OR CO>8) THEN PRINT@64," ": GOTO 130\n',
            '130 RUN ecb_at(64.0) \\ PRINT "COLOR (1-8)";\n'
            'RUN _ecb_input_prefix \\ INPUT "? ", CO \\ '
            'RUN _ecb_input_suffix\n'
            '140 IF (CO < 1.0 OR CO > 8.0) THEN\n'
            '  RUN ecb_at(64.0) \\ PRINT " "\n'
            '  GOTO 130\n'
            'ENDIF'
        )
