from typing import List

from coco.b09 import error_handler
from coco.b09.elements import BasicLine


def test_generate_no_handlers() -> None:
    lines: List[BasicLine] = error_handler.generate(brk_line=None, err_line=None)
    assert lines == []


def test_generates_break_handler() -> None:
    lines: List[BasicLine] = error_handler.generate(brk_line=100, err_line=None)
    assert len(lines) == 2
    assert lines[0].basic09_text(0) == "32700 ERNO := errnum"
    assert lines[1].basic09_text(0) == "IF ERNO = 2 THEN 100"


def test_generates_error_handler() -> None:
    lines: List[BasicLine] = error_handler.generate(brk_line=None, err_line=234)
    assert len(lines) == 2
    assert lines[0].basic09_text(0) == "32700 ERNO := errnum"
    assert lines[1].basic09_text(0) == "GOTO 234"


def test_generates_both_handlers() -> None:
    lines: List[BasicLine] = error_handler.generate(brk_line=1000, err_line=234)
    assert len(lines) == 3
    assert lines[0].basic09_text(0) == "32700 ERNO := errnum"
    assert lines[1].basic09_text(0) == "IF ERNO = 2 THEN 1000"
    assert lines[2].basic09_text(0) == "GOTO 234"
