import pytest
import pkg_resources
from typing import List

from coco import b09
from coco.b09.elements import (
    BasicHbuffStatement,
    BasicLiteral,
)
from coco.b09.grammar import grammar
from coco.b09.parser import BasicProg, BasicVisitor
from coco.b09.visitors import (
    BasicExpressionList,
    BasicFunctionalExpressionPatcherVisitor,
    BasicHbuffPresenceVisitor,
    BasicRunCall,
    StrVarAllocatorVisitor,
)


def parse_program(resource_name: str) -> BasicProg:
    path = pkg_resources.resource_filename(__name__, f"fixtures/{resource_name}")
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
