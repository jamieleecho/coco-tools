import importlib.resources as importlib_resources
from typing import List

import pytest

from coco import b09
from coco.b09.elements import (
    BasicHbuffStatement,
    BasicLiteral,
)
from coco.b09.grammar import grammar
from coco.b09.parser import BasicProg, BasicVisitor
from coco.b09.procbank import ProcedureBank
from coco.b09.visitors import (
    BasicExpressionList,
    BasicFunctionalExpressionPatcherVisitor,
    BasicHbuffPresenceVisitor,
    BasicRunCall,
    IntegerVarVisitor,
    StrVarAllocatorVisitor,
)


def parse_program(resource_name: str) -> BasicProg:
    with importlib_resources.as_file(
        importlib_resources.files(str(__package__)) / f"fixtures/{resource_name}"
    ) as path:
        prog: str
        with open(path) as f:
            prog = f.read()

        tree = grammar.parse(prog)
        bv = BasicVisitor()
        prog: BasicProg = bv.visit(tree)
        prog.visit(BasicFunctionalExpressionPatcherVisitor())
        return prog


@pytest.fixture
def strfun_prog() -> BasicProg:
    return parse_program("strfun.bas")


def test_str_var_allocator(strfun_prog: BasicProg) -> None:
    target: StrVarAllocatorVisitor = StrVarAllocatorVisitor(
        default_str_storage=128,
        dimmed_var_names=set(),
    )
    strfun_prog.visit(target)
    print(strfun_prog.basic09_text(0))
    code: List[str] = [line.basic09_text(0) for line in target.allocation_lines]
    assert code == [
        "DIM A$:STRING[128]",
        "DIM B$:STRING[128]",
        "DIM tmp_1$:STRING[128]",
    ]


def test_str_var_allocator_default(strfun_prog: BasicProg) -> None:
    target: StrVarAllocatorVisitor = StrVarAllocatorVisitor(
        default_str_storage=b09.DEFAULT_STR_STORAGE,
        dimmed_var_names=set(),
    )
    strfun_prog.visit(target)
    print(strfun_prog.basic09_text(0))
    code: List[str] = [line.basic09_text(0) for line in target.allocation_lines]
    assert code == []


def test_str_var_allocator_with_dimmed_vars(strfun_prog: BasicProg) -> None:
    target: StrVarAllocatorVisitor = StrVarAllocatorVisitor(
        default_str_storage=128,
        dimmed_var_names=set(["B$"]),
    )
    strfun_prog.visit(target)
    print(strfun_prog.basic09_text(0))
    code: List[str] = [line.basic09_text(0) for line in target.allocation_lines]
    assert code == [
        "DIM A$:STRING[128]",
        "DIM tmp_1$:STRING[128]",
    ]


@pytest.fixture
def hbuff_visitor() -> BasicHbuffPresenceVisitor:
    return BasicHbuffPresenceVisitor()


def test_hbuff_visitor_init(hbuff_visitor: BasicHbuffPresenceVisitor) -> None:
    assert not hbuff_visitor.has_hbuff


def test_hbuff_visitor_detects_hbuff(hbuff_visitor: BasicHbuffPresenceVisitor) -> None:
    hbuff_visitor.visit_statement(
        BasicHbuffStatement(
            buffer=BasicLiteral(1),
            size=BasicLiteral(10),
        )
    )
    assert hbuff_visitor.has_hbuff


def test_hbuff_visitor_ignores_others(hbuff_visitor: BasicHbuffPresenceVisitor) -> None:
    hbuff_visitor.visit_statement(
        BasicRunCall(
            "run foo",
            BasicExpressionList([]),
        )
    )
    assert not hbuff_visitor.has_hbuff


def _collect_integer_vars(prog_text: str) -> set:
    tree = grammar.parse(prog_text)
    prog: BasicProg = BasicVisitor().visit(tree)
    prog.visit(BasicFunctionalExpressionPatcherVisitor())
    visitor = IntegerVarVisitor()
    prog.visit(visitor)
    return visitor.integer_vars


@pytest.fixture(scope="module")
def _ecb_signatures() -> dict:
    bank = ProcedureBank()
    bank.add_from_resource("ecb.b09")
    return bank.signatures


def _collect_integer_vars_with_signatures(prog_text: str, signatures: dict) -> set:
    tree = grammar.parse(prog_text)
    prog: BasicProg = BasicVisitor().visit(tree)
    prog.visit(BasicFunctionalExpressionPatcherVisitor())
    visitor = IntegerVarVisitor(signatures=signatures)
    prog.visit(visitor)
    return visitor.integer_vars


def test_integer_var_visitor_empty_program() -> None:
    assert _collect_integer_vars("10 END\n") == set()


def test_integer_var_visitor_simple_integer_assignment() -> None:
    assert _collect_integer_vars("10 A = 5\n") == {"A"}


def test_integer_var_visitor_multiple_integer_assignments_to_same_var() -> None:
    # Every assignment to A is integer -> A is an integer candidate.
    assert _collect_integer_vars("10 A = 5\n20 A = 10\n30 A = -100\n") == {"A"}


def test_integer_var_visitor_transcendental_disqualifies() -> None:
    prog = (
        "10 A = SIN(1)\n"
        "20 B = COS(1)\n"
        "30 C = TAN(1)\n"
        "40 D = ATN(1)\n"
        "50 E = LOG(1)\n"
        "60 F = EXP(1)\n"
        "70 G = SQR(4)\n"
    )
    assert _collect_integer_vars(prog) == set()


def test_integer_var_visitor_division_disqualifies() -> None:
    assert _collect_integer_vars("10 A = 6 / 2\n20 B = 3\n") == {"B"}


def test_integer_var_visitor_power_disqualifies() -> None:
    assert _collect_integer_vars("10 A = 2 ^ 3\n") == set()


def test_integer_var_visitor_fractional_literal_disqualifies() -> None:
    assert _collect_integer_vars("10 A = 1.5\n20 B = 2\n") == {"B"}


def test_integer_var_visitor_out_of_range_literal_disqualifies() -> None:
    # 40000 is out of the signed 16-bit range.
    assert _collect_integer_vars("10 A = 40000\n20 B = -40000\n") == set()


def test_integer_var_visitor_boundary_literals_are_integer() -> None:
    # 32767 and -32768 are the extrema of the signed 16-bit range.
    assert _collect_integer_vars("10 A = 32767\n20 B = -32768\n") == {"A", "B"}


def test_integer_var_visitor_just_out_of_range_literals_disqualify() -> None:
    assert _collect_integer_vars("10 A = 32768\n20 B = -32769\n") == set()


def test_integer_var_visitor_integer_arithmetic_is_integer() -> None:
    prog = "10 A = 1\n20 B = 2\n30 C = A + B * 3 - 4\n"
    assert _collect_integer_vars(prog) == {"A", "B", "C"}


def test_integer_var_visitor_propagates_non_integer_through_assignment() -> None:
    # B is only ever assigned from A; since A receives SIN, both are
    # non-integer. C is assigned a pure integer literal, so it stays.
    prog = "10 A = SIN(1)\n20 B = A\n30 C = 3\n"
    assert _collect_integer_vars(prog) == {"C"}


def test_integer_var_visitor_mutual_integer_propagation() -> None:
    # P and Q only see integer literals and each other, so both are
    # integer candidates.
    prog = "10 P = 2\n20 Q = P\n30 R = Q + P\n"
    assert _collect_integer_vars(prog) == {"P", "Q", "R"}


def test_integer_var_visitor_input_statement_taints() -> None:
    # INPUT can supply fractional or out-of-range data, so J is not
    # an integer candidate.
    assert _collect_integer_vars("10 INPUT J\n20 K = 5\n") == {"K"}


def test_integer_var_visitor_read_statement_taints() -> None:
    assert _collect_integer_vars("10 READ K\n20 DATA 3\n30 L = 4\n") == {"L"}


def test_integer_var_visitor_string_vars_are_ignored() -> None:
    # String variables never appear in the integer set.
    result = _collect_integer_vars('10 A$ = "HELLO"\n20 B = 1\n')
    assert "A$" not in result
    assert result == {"B"}


def test_integer_var_visitor_array_assignments() -> None:
    # Arrays are tracked with the "arr_" prefix, matching the
    # convention used elsewhere in the transpiler.
    prog = "10 DIM X(10), Y(10)\n20 X(3) = 7\n30 Y(2) = SIN(1)\n"
    assert _collect_integer_vars(prog) == {"arr_X"}


def test_integer_var_visitor_for_loop_variable_is_integer() -> None:
    prog = "10 FOR I = 1 TO 10\n20 NEXT I\n"
    assert _collect_integer_vars(prog) == {"I"}


def test_integer_var_visitor_for_loop_fractional_step_disqualifies() -> None:
    prog = "10 FOR I = 1 TO 10 STEP 0.5\n20 NEXT I\n"
    assert _collect_integer_vars(prog) == set()


def test_integer_var_visitor_int_and_peek_are_integer() -> None:
    # INT() and PEEK() always yield integer-valued results regardless
    # of their argument.
    prog = "10 A = INT(3.14)\n20 B = PEEK(1024)\n"
    assert _collect_integer_vars(prog) == {"A", "B"}


def test_integer_var_visitor_abs_passes_through_argument() -> None:
    # ABS of an integer is integer; ABS of a non-integer is not.
    prog = "10 A = ABS(3)\n20 B = ABS(SIN(1))\n"
    assert _collect_integer_vars(prog) == {"A"}


def test_integer_var_visitor_unassigned_variable_is_integer() -> None:
    # X is only ever read, never written, so it's trivially an
    # integer candidate (it defaults to 0).
    prog = "10 A = X + 1\n"
    assert _collect_integer_vars(prog) == {"A", "X"}


def test_integer_var_visitor_parenthesized_expression() -> None:
    prog = "10 A = (3 + 4) * 2\n20 B = (SIN(1))\n"
    assert _collect_integer_vars(prog) == {"A"}


def test_integer_var_visitor_hex_literal_in_range() -> None:
    prog = "10 A = &H7FFF\n"
    assert _collect_integer_vars(prog) == {"A"}


def test_integer_var_visitor_int_function_taints_target_with_signatures(
    _ecb_signatures: dict,
) -> None:
    # ``A = INT(3)`` emits ``run ecb_int(3, A)``. ecb_int's retval
    # parameter is declared REAL, so A must be REAL and cannot be
    # an integer candidate even though the source would otherwise
    # look like a pure integer assignment.
    prog = "10 A = INT(3)\n20 B = 5\n"
    assert _collect_integer_vars_with_signatures(prog, _ecb_signatures) == {"B"}


def test_integer_var_visitor_joystk_taints_target_with_signatures(
    _ecb_signatures: dict,
) -> None:
    # JOYSTK's retval is REAL, so the target of a JOYSTK
    # assignment is pinned to REAL.
    prog = "10 X = JOYSTK(0)\n20 Y = 1\n"
    assert _collect_integer_vars_with_signatures(prog, _ecb_signatures) == {"Y"}


def test_integer_var_visitor_int_function_without_signatures_is_integer() -> None:
    # Without signatures the visitor falls back to its built-in
    # heuristics, which treat INT() as returning an integer.
    prog = "10 A = INT(3)\n"
    assert _collect_integer_vars(prog) == {"A"}


def test_integer_var_visitor_run_call_does_not_taint_input_only_vars(
    _ecb_signatures: dict,
) -> None:
    # ``SOUND F, D`` compiles to ``run ecb_sound(F, D, 15, 1)`` and
    # all of those parameters are inputs. F and D must remain
    # integer candidates because input values can be coerced.
    prog = "10 F = 100\n20 D = 10\n30 SOUND F, D\n"
    assert _collect_integer_vars_with_signatures(prog, _ecb_signatures) == {
        "F",
        "D",
    }
