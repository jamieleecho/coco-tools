import pytest

from coco.b09 import compiler
from coco.b09.errors import ParseError


def convert(progin: str, **kwargs) -> str:
    return compiler.convert(
        progin,
        add_standard_prefix=False,
        add_suffix=False,
        skip_procedure_headers=True,
        **kwargs,
    )


def assert_converts(progin: str, progout: str, **kwargs) -> None:
    assert convert(progin, **kwargs) == progout + "\n"


class TestEarlyLoopExits:
    """A NEXT that ends a single-line IF leaves the loop early."""

    def test_next_ending_an_if(self) -> None:
        assert_converts(
            '10 FOR I=1 TO 3\n20 IF I<3 THEN PRINT "X";: NEXT I\n30 PRINT "DONE"\n',
            "10 FOR I = 1.0 TO 3.0\n"
            "20   IF I < 3.0 THEN\n"
            '    PRINT "X";\n'
            "  ELSE\n"
            "    GOTO 30\n"
            "  ENDIF\n"
            "NEXT I\n"
            '30 PRINT "DONE"',
        )

    def test_next_ending_an_if_with_nothing_else_in_it(self) -> None:
        assert_converts(
            '10 FOR I=1 TO 3\n20 IF I<3 THEN NEXT I\n30 PRINT "DONE"\n',
            "10 FOR I = 1.0 TO 3.0\n"
            "20   IF I < 3.0 THEN\n"
            "\n"
            "  ELSE\n"
            "    GOTO 30\n"
            "  ENDIF\n"
            "NEXT I\n"
            '30 PRINT "DONE"',
        )

    def test_bare_next_ending_an_if(self) -> None:
        assert_converts(
            '10 FOR I=1 TO 3\n20 IF I<3 THEN PRINT "X";: NEXT\n30 END\n',
            "10 FOR I = 1.0 TO 3.0\n"
            "20   IF I < 3.0 THEN\n"
            '    PRINT "X";\n'
            "  ELSE\n"
            "    GOTO 30\n"
            "  ENDIF\n"
            "NEXT I\n"
            "30 END",
        )

    def test_next_ending_an_if_in_an_inner_loop(self) -> None:
        assert_converts(
            "10 FOR I=1 TO 2\n"
            "20 FOR J=1 TO 2\n"
            '30 IF J<2 THEN PRINT "X";: NEXT J\n'
            "40 NEXT I\n",
            "10 FOR I = 1.0 TO 2.0\n"
            "20   FOR J = 1.0 TO 2.0\n"
            "30     IF J < 2.0 THEN\n"
            '      PRINT "X";\n'
            "    ELSE\n"
            "      GOTO 40\n"
            "    ENDIF\n"
            "  NEXT J\n"
            "40 NEXT I",
        )

    def test_the_line_jumped_to_keeps_its_number(self) -> None:
        # The GOTO added by the rewrite references line 30, so line 30
        # keeps its number even though nothing else refers to it.
        assert_converts(
            '10 FOR I=1 TO 3\n20 IF I<3 THEN PRINT "X";: NEXT I\n30 PRINT "DONE"\n',
            "FOR I = 1.0 TO 3.0\n"
            "  IF I < 3.0 THEN\n"
            '    PRINT "X";\n'
            "  ELSE\n"
            "    GOTO 30\n"
            "  ENDIF\n"
            "NEXT I\n"
            '30 PRINT "DONE"',
            filter_unused_linenum=True,
        )

    def test_the_calls_hoisted_out_of_the_condition_are_kept(self) -> None:
        assert_converts(
            "10 FOR I=1 TO 3\n20 IF VAL(A$)>0 THEN NEXT I\n30 END\n",
            "10 FOR I = 1.0 TO 3.0\n"
            "20   RUN ecb_val(A$, tmp_1) \\ IF tmp_1 > 0.0 THEN\n"
            "\n"
            "  ELSE\n"
            "    GOTO 30\n"
            "  ENDIF\n"
            "NEXT I\n"
            "30 END",
        )

    def test_a_loop_wholly_inside_an_if_is_left_alone(self) -> None:
        assert_converts(
            "10 IF A THEN FOR I=1 TO 3: NEXT I\n20 END\n",
            "10 IF A <> 0.0 THEN\nFOR I = 1.0 TO 3.0\n  NEXT I\nENDIF\n20 END",
        )


class TestUnbalancedControlStructures:
    """What Basic09 would reject with ERROR #69 is rejected here."""

    def test_next_reached_only_by_a_goto(self) -> None:
        # 04_Awari/awari.bas: the NEXT on line 20 belongs to another
        # loop, so the loop on line 30 never gets one of its own.
        with pytest.raises(ParseError) as excinfo:
            convert(
                "10 FOR I=1 TO 5\n"
                "20 NEXT I\n"
                "30 FOR I=7 TO 12:IF A(I)<>0 THEN E=1:END\n"
                "40 GOTO 20\n"
            )
        assert str(excinfo.value) == (
            "Basic09 needs each NEXT to close its FOR in the block it was "
            "opened in, but the FOR on line 30 has no NEXT."
        )

    def test_for_inside_an_if_closed_outside_it(self) -> None:
        # 23_Checkers/checkers.bas line 1350.
        with pytest.raises(ParseError) as excinfo:
            convert("10 IF A THEN FOR I=1 TO 3: PRINT I\n20 NEXT I\n")
        assert str(excinfo.value) == (
            "Basic09 needs each NEXT to close its FOR in the block it was "
            "opened in, but the NEXT on line 20 closes the FOR opened inside "
            "an IF on line 10."
        )

    def test_next_inside_an_if_that_goes_on(self) -> None:
        # The statements after the NEXT run once the loop is done, which
        # moving the NEXT out of the IF would not preserve.
        with pytest.raises(ParseError) as excinfo:
            convert('10 FOR I=1 TO 3\n20 IF A THEN NEXT I: PRINT "X"\n30 END\n')
        assert str(excinfo.value) == (
            "Basic09 needs each NEXT to close its FOR in the block it was "
            "opened in, but the NEXT on line 20 closes the FOR on line 10 "
            "from inside an IF."
        )

    def test_next_inside_an_if_on_the_last_line(self) -> None:
        # There is no line to leave the loop for.
        with pytest.raises(ParseError):
            convert("10 FOR I=1 TO 3\n20 IF A THEN NEXT I\n")

    def test_next_inside_an_if_closing_two_loops(self) -> None:
        with pytest.raises(ParseError) as excinfo:
            convert("10 FOR I=1 TO 2\n20 FOR J=1 TO 2\n30 IF A THEN NEXT J,I\n40 END\n")
        assert str(excinfo.value) == (
            "Basic09 needs each NEXT to close its FOR in the block it was "
            "opened in, but the NEXT on line 30 closes the FOR on line 20 "
            "from inside an IF; the NEXT on line 30 closes the FOR on line 10 "
            "from inside an IF."
        )

    def test_next_without_a_for(self) -> None:
        with pytest.raises(ParseError) as excinfo:
            convert("10 NEXT I\n")
        assert str(excinfo.value) == (
            "Basic09 needs each NEXT to close its FOR in the block it was "
            "opened in, but the NEXT on line 10 has no FOR."
        )

    def test_for_without_a_next(self) -> None:
        with pytest.raises(ParseError) as excinfo:
            convert("10 FOR I=1 TO 3\n20 PRINT I\n")
        assert str(excinfo.value) == (
            "Basic09 needs each NEXT to close its FOR in the block it was "
            "opened in, but the FOR on line 10 has no NEXT."
        )

    def test_a_program_with_balanced_loops_is_accepted(self) -> None:
        assert_converts(
            "10 FOR I=1 TO 2\n20 FOR J=1 TO 2\n30 NEXT J\n40 NEXT I\n",
            "10 FOR I = 1.0 TO 2.0\n20   FOR J = 1.0 TO 2.0\n30   NEXT J\n40 NEXT I",
        )
