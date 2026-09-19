"""Keeps the ``FOR`` loops the converter emits inside Basic09's blocks.

Color BASIC matches a ``NEXT`` to a ``FOR`` on a stack at run time, so
a ``NEXT`` can sit inside an ``IF`` that its ``FOR`` is outside of --
or the other way around. Basic09's ``FOR`` is a block instead: its
``NEXT`` has to close it where it was opened, or the blocks cross and
Basic09 rejects the whole procedure as it loads::

    0690 ERROR #69 - Unmatched Control Structure

:func:`repair_early_loop_exits` rewrites the one crossing that has a
structured equivalent -- a ``NEXT`` that ends a single-line
``IF ... THEN``, which is how Color BASIC leaves a loop early -- and
:func:`check` rejects whatever crossings are left instead of emitting a
procedure that cannot load.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Union

from coco.b09.elements import (
    AbstractBasicConstruct,
    BasicForStatement,
    BasicGoto,
    BasicIf,
    BasicIfElse,
    BasicLine,
    BasicNextStatement,
    BasicStatements,
)
from coco.b09.errors import ParseError
from coco.b09.prog import BasicProg

# The block a statement is emitted in: the ``IF`` whose branch holds it,
# or ``None`` for the body of the procedure itself. Only an ``IF`` opens
# a block within a line, and no block spans lines, so two statements are
# emitted in the same block when this is the same object for both.
Block = Union[BasicIf, None]


@dataclass(frozen=True)
class _OpenFor:
    """A ``FOR`` whose ``NEXT`` has not been seen yet."""

    block: Block
    linenum: Union[int, None]


@dataclass(frozen=True)
class _Repair:
    """Everything needed to lift a ``NEXT`` out of the ``IF`` it ends."""

    if_statement: BasicIf
    if_container: BasicStatements
    if_index: int
    next_container: BasicStatements
    next_index: int
    next_statement: BasicNextStatement
    line_index: int
    exit_linenum: int


@dataclass(frozen=True)
class _Crossing:
    """A ``NEXT`` emitted in a different block than its ``FOR``."""

    linenum: Union[int, None]
    open_for: _OpenFor
    repair: Union[_Repair, None]


@dataclass(frozen=True)
class _Candidate:
    """The ``IF`` a ``NEXT`` could be lifted out of, if it ends it."""

    if_statement: BasicIf
    if_container: BasicStatements
    if_index: int
    outer_block: Block


class _Walker:
    """Matches every ``NEXT`` to a ``FOR`` the way Basic09 does."""

    def __init__(self, lines: Sequence[AbstractBasicConstruct]) -> None:
        self._lines = lines
        self._open_fors: List[_OpenFor] = []
        self._linenum: Union[int, None] = None
        self._line_index: int = 0
        self.crossings: List[_Crossing] = []
        self.unclosed: List[_OpenFor] = []
        self.unopened: List[Union[int, None]] = []

    def walk(self) -> "_Walker":
        for index, line in enumerate(self._lines):
            self._line_index = index
            # The generated prefix and suffix hold bare statements
            # rather than lines.
            self._linenum = line.num if isinstance(line, BasicLine) else None
            statements = line.statements if isinstance(line, BasicLine) else line
            if isinstance(statements, BasicStatements):
                self._walk_statements(statements, block=None, tail=True, candidate=None)
            else:
                self._walk_statement(
                    statements,
                    block=None,
                    container=None,
                    index=0,
                    tail=True,
                    candidate=None,
                )
        self.unclosed = list(self._open_fors)
        return self

    def _walk_statements(
        self,
        statements: BasicStatements,
        *,
        block: Block,
        tail: bool,
        candidate: Union[_Candidate, None],
    ) -> None:
        last = len(statements.statements) - 1
        for index, statement in enumerate(statements.statements):
            self._walk_statement(
                statement,
                block=block,
                container=statements,
                index=index,
                tail=tail and index == last,
                candidate=candidate,
            )

    def _walk_statement(
        self,
        statement: AbstractBasicConstruct,
        *,
        block: Block,
        container: Union[BasicStatements, None],
        index: int,
        tail: bool,
        candidate: Union[_Candidate, None],
    ) -> None:
        if isinstance(statement, BasicStatements):
            # Statements grouped within a line are emitted in the block
            # around them, so the group does not open one of its own.
            self._walk_statements(
                statement, block=block, tail=tail, candidate=candidate
            )
        elif isinstance(statement, BasicForStatement):
            self._open_fors.append(_OpenFor(block, self._linenum))
        elif isinstance(statement, BasicNextStatement):
            self._close(
                statement,
                block=block,
                container=container,
                index=index,
                tail=tail,
                candidate=candidate,
            )
        elif isinstance(statement, BasicIfElse):
            for branch in (
                statement.statements,
                *(else_if.statements for else_if in statement.else_if_statements),
                statement.else_statements,
            ):
                if isinstance(branch, BasicStatements):
                    self._walk_statements(
                        branch, block=statement, tail=False, candidate=None
                    )
        elif isinstance(statement, BasicIf):
            branch = statement.statements
            if isinstance(branch, BasicStatements):
                self._walk_statements(
                    branch,
                    block=statement,
                    tail=tail,
                    candidate=_Candidate(statement, container, index, block)
                    if tail and container is not None
                    else None,
                )

    def _exit_linenum(self) -> Union[int, None]:
        """The number of the line reached by falling off the current one."""
        for line in self._lines[self._line_index + 1 :]:
            if isinstance(line, BasicLine) and line.num is not None:
                return line.num
        return None

    def _close(
        self,
        statement: BasicNextStatement,
        *,
        block: Block,
        container: Union[BasicStatements, None],
        index: int,
        tail: bool,
        candidate: Union[_Candidate, None],
    ) -> None:
        # A bare NEXT closes the innermost loop; NEXT I, J closes two.
        for _ in range(len(statement.var_list.exp_list) or 1):
            if not self._open_fors:
                self.unopened.append(self._linenum)
                return
            open_for = self._open_fors.pop()
            if open_for.block is block:
                continue
            repair = None
            if (
                candidate is not None
                and container is not None
                and tail
                and len(statement.var_list.exp_list) <= 1
                and block is candidate.if_statement
                # The NEXT moves to a line of its own, which is emitted
                # in the body of the procedure, so that is where the
                # loop it closes has to have been opened.
                and candidate.outer_block is None
                and open_for.block is None
            ):
                # Everything in the branch that is not taken any more
                # falls through to the line after this one.
                exit_linenum = self._exit_linenum()
                if exit_linenum is not None:
                    repair = _Repair(
                        if_statement=candidate.if_statement,
                        if_container=candidate.if_container,
                        if_index=candidate.if_index,
                        next_container=container,
                        next_index=index,
                        next_statement=statement,
                        line_index=self._line_index,
                        exit_linenum=exit_linenum,
                    )
            self.crossings.append(_Crossing(self._linenum, open_for, repair))


def repair_early_loop_exits(prog: BasicProg) -> None:
    """Rewrite each ``NEXT`` that ends a single-line ``IF ... THEN``
    inside its own loop.

    ``FOR I = 1 TO 3`` followed by ``IF C THEN PRINT I: NEXT I`` runs
    the body while ``C`` holds and leaves the loop as soon as it does
    not. Basic09 gets the same program with the ``NEXT`` moved out to
    the loop's own block and the other branch jumping past it::

        IF C THEN
          PRINT I
        ELSE
          GOTO 30
        ENDIF
        NEXT I

    Anything else :func:`check` reports, so this only ever rewrites a
    program the converter could not emit in the first place.
    """
    lines = prog.lines
    repairs = [
        crossing.repair
        for crossing in _Walker(lines).walk().crossings
        if crossing.repair is not None
    ]
    if not repairs:
        return

    next_lines: dict[int, List[BasicLine]] = {}
    for repair in repairs:
        repair.next_container.statements.pop(repair.next_index)
        repair.if_container.statements[repair.if_index] = BasicIfElse.from_if(
            repair.if_statement,
            else_statements=BasicStatements(
                [BasicGoto(repair.exit_linenum, implicit=False)]
            ),
        )
        next_lines.setdefault(repair.line_index, []).append(
            BasicLine(None, BasicStatements([repair.next_statement]))
        )

    rewritten: List[BasicLine] = []
    for index, line in enumerate(lines):
        rewritten.append(line)
        rewritten.extend(next_lines.get(index, ()))
    prog.set_lines(rewritten)


def check(prog: BasicProg) -> None:
    """Raise :class:`ParseError` if the procedure's ``FOR`` loops would
    not load."""
    walker = _Walker(prog.all_lines).walk()
    problems: List[str] = []
    for crossing in walker.crossings:
        problems.append(
            f"the NEXT on line {crossing.linenum} closes the FOR "
            + (
                f"opened inside an IF on line {crossing.open_for.linenum}"
                if crossing.open_for.block is not None
                else f"on line {crossing.open_for.linenum} from inside an IF"
            )
        )
    problems.extend(
        f"the NEXT on line {linenum} has no FOR" for linenum in walker.unopened
    )
    problems.extend(
        f"the FOR on line {open_for.linenum} has no NEXT"
        for open_for in walker.unclosed
    )
    if problems:
        raise ParseError(
            "Basic09 needs each NEXT to close its FOR in the block it was "
            "opened in, but " + "; ".join(problems) + "."
        )
