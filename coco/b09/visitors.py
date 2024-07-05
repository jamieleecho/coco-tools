from coco.b09.elements import (
    AbstractBasicExpression,
    Basic09CodeStatement,
    BasicAssignment,
    BasicExpressionList,
    BasicFunctionalExpression,
    BasicLine,
    BasicLiteral,
    BasicOnGoStatement,
    BasicPrintArgs,
    BasicPrintStatement,
    BasicRunCall,
    BasicStatements,
    BasicVar,
)


class BasicConstructVisitor:
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

    def visit_input_statement(self, statement):
        """
        Args:
            statement (BasicInputStatement): input statement to transform.

        Returns:
            BasicStatement: BasicStatement to replace statement.
        """
        return statement

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

    def visit_print_statement(self, statement):
        """
        Args:
            statement (BasicPrintStatement): input statement to transform.

        Returns:
            BasicStatement: BasicStatement to replace statement.
        """
        return statement

    def visit_program(self, line):
        """
        Invoked when a program is encountered.
        """
        pass

    def visit_read_statement(self, statement):
        """
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
        return (
            [
                BasicLine(
                    None,
                    BasicStatements(
                        [
                            BasicAssignment(
                                BasicVar(var, is_str_expr=(var[-1] == "$")),
                                BasicLiteral(
                                    "" if (var[-1] == "$") else 0.0,
                                    is_str_expr=(var[-1] == "$"),
                                ),
                            )
                            for var in sorted(self._vars)
                            if (
                                (var.startswith("$") and len(var) <= 3) or len(var) <= 2
                            )
                        ]
                    ),
                )
            ]
            if self._vars
            else []
        )

    def visit_var(self, var):
        self._vars.add(var.name())


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

    def visit_data_statement(self, statement):
        for exp in statement.exp_list.exp_list:
            self._has_empty_data_elements = (
                self._has_empty_data_elements or exp.literal == ""
            )


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
            statement.rhs_list[idx] = rhs_to_temp.get(rhs, rhs)

        # Create statements for reading into the REAL vars
        filter_statements = [
            BasicRunCall("RUN ecb_read_filter", BasicExpressionList((inval, outval)))
            for outval, inval in rhs_to_temp.items()
        ]

        return BasicStatements([statement] + filter_statements, multi_line=False)


class BasicInputStatementPatcherVisitor(BasicConstructVisitor):
    def visit_input_statement(self, statement):
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
    def visit_print_statement(self, statement):
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

    def visit_for_statement(self, for_statement):
        self.for_stack.append(for_statement.var)

    def visit_next_statement(self, next_statement):
        if self.for_stack and len(next_statement.var_list.exp_list) == 0:
            next_statement.var_list.exp_list.append(self.for_stack.pop())


class BasicFunctionalExpressionPatcherVisitor(BasicConstructVisitor):
    def __init__(self):
        self._statement = None

    def visit_statement(self, statement):
        self._statement = statement
        if isinstance(statement, BasicAssignment) and isinstance(
            statement.exp, BasicFunctionalExpression
        ):
            statement.exp.set_var(statement.var)

    def visit_exp(self, exp):
        if not isinstance(exp, BasicFunctionalExpression) or exp.var:
            return
        self._statement.transform_function_to_call(exp)
