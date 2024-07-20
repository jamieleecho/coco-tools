from itertools import chain
from coco.b09.elements import AbstractBasicConstruct
from coco.b09.visitors import BasicConstructVisitor, ForNextVisitor


class BasicProg(AbstractBasicConstruct):
    def __init__(self, lines):
        self._lines = lines
        self._prefix_lines = []
        self._procname = ""

    def set_procname(self, procname):
        self._procname = procname

    def extend_prefix_lines(self, prefix_lines):
        self._prefix_lines.extend(prefix_lines)

    def insert_lines_at_beginning(self, lines):
        for ii, line in enumerate(lines):
            self._lines.insert(ii, line)

    def basic09_text(self, indent_level):
        lines = []
        if self._procname:
            lines.append(f"procedure {self._procname}")
        nest_counter = ForNextVisitor()
        for line in chain(self._prefix_lines, self._lines):
            line.visit(nest_counter)
            lines.append(line.basic09_text(nest_counter.count))

        return "\n".join(lines)

    def visit(self, visitor: "BasicConstructVisitor"):
        visitor.visit_program(self)
        for line in self._lines:
            line.visit(visitor)
