from typing import List, Union

from coco.b09.elements import (
    BasicAssignment,
    BasicBinaryExp,
    BasicGoto,
    BasicIf,
    BasicLine,
    BasicLiteral,
    BasicStatements,
    BasicVar,
)


def generate(
    *,
    brk_line: Union[int, None],
    err_line: Union[int, None],
) -> List[BasicLine]:
    lines: List[BasicLine] = []

    if brk_line is not None or err_line is not None:
        lines.append(
            BasicLine(
                32700,
                BasicStatements(
                    [
                        BasicAssignment(BasicVar("ERNO"), BasicVar("errnum")),
                    ]
                ),
            )
        )

        if brk_line is not None:
            lines.append(
                BasicLine(
                    None,
                    BasicStatements(
                        [
                            BasicIf(
                                BasicBinaryExp(
                                    BasicVar("ERNO"),
                                    "=",
                                    BasicLiteral(2),
                                ),
                                BasicGoto(brk_line, implicit=True),
                            ),
                        ]
                    ),
                )
            )

        if err_line is not None:
            lines.append(
                BasicLine(
                    None,
                    BasicStatements(
                        [
                            BasicGoto(err_line, implicit=False),
                        ]
                    ),
                )
            )

    return lines
