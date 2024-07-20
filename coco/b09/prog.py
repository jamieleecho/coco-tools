from itertools import chain
from typing import List

from coco.b09.elements import AbstractBasicConstruct, BasicLine
from coco.b09.visitors import BasicConstructVisitor, ForNextVisitor


class BasicProg(AbstractBasicConstruct):
    def __init__(self, lines: List[BasicLine]):
        self._lines: List[BasicLine] = lines
        self._prefix_lines: List[BasicLine] = []
        self._suffix_lines: List[BasicLine] = []
        self._procname: str = ""

    def set_procname(self, procname: str):
        self._procname = procname

    def extend_prefix_lines(self, prefix_lines: List[BasicLine]):
        self._prefix_lines.extend(prefix_lines)

    def insert_lines_at_beginning(self, lines: List[BasicLine]):
        for ii, line in enumerate(lines):
            self._lines.insert(ii, line)

    def append_lines(self, lines: List[BasicLine]):
        self._suffix_lines.extend(lines)

    def basic09_text(self, indent_level: int):
        lines: List[str] = []
        if self._procname:
            lines.append(f"procedure {self._procname}")
        nest_counter = ForNextVisitor()
        for line in chain(self._prefix_lines, self._lines, self._suffix_lines):
            line.visit(nest_counter)
            lines.append(line.basic09_text(nest_counter.count))

        return "\n".join(lines)

    def visit(self, visitor: "BasicConstructVisitor") -> None:
        visitor.visit_program(self)
        for line in self._lines:
            line.visit(visitor)
