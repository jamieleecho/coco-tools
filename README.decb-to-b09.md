# decb-to-b09

This utility converts Microsoft Color BASIC programs into Microware BASIC09
Programs that work on OS-9 Level 2. This conversion process has many benefits:
1. Makes the wealth of Color BASIC programs available to OS-9.
2. Makes the program run a lot faster in most cases.
3. Provides a gentle slope to learning BASIC09 as this language has many of
   its own quirks that can be hard to learn when coming from Color BASIC.

The utility provides a best effort for conversion which means:
* We make a reasonable effort to maintain the intended semantics of the source
  program.
* For valid programs, results will vary because it will use BASIC09's and
  OS-9's built in functionality such as floating point, random and drawing
  routines. This may introduce unintended differences in program behavior.
* It will flag a subset of known issues such as syntax errors or disallowed
  syntax.
* It will result in conversion to some BASIC09 programs that are not valid and
  will get flagged when loaded by BASIC09.
* Color BASIC has some not very well defined lexing and parsing behavior. We
  disallow these constructs because they lead to behavior that is not very
  clear.
* We currently only support VDG screens.

## Supported constructs
Most Color BASIC and some Extended Color BASIC and Super Extended Color BASIC
features are supported. These include:
include: ABS, +, AND, ASC, ATN, BUTTON, CHR$, CLS, COS, DATA, DIM, /,
END, ELSE, =, EXP, FOR, GOTO, GOSUB, >, IF, INKEY$, INPUT, INT, JOYSTK, LEFT$,
LEN, <, LET, LOG, MID$, *, NEXT, NOT, OPEN, OR, PRINT, READ, REM, RESET,
RESTORE, RETURN, RIGHT$, RND, SET, SGN, SIN, SOUND, SQR, STEP, STOP, STR$, -,
TAB, TAN, THEN, TO, VAL

## Supported constructs that need some explanation
* String literals must be closed.
* BASIC09 does not allow programs with line number zero. To handle this, the
  zero line number is stripped as long as there are no `GOTO` or `GOSUB`
  statements to line zero.
* When empty `DATA` elements are encountered, all `DATA` elements are
  converted to strings and dynamically converted to REALs. This is to mimic
  the different possible behaviors of Extended Color BASIC.
* Variables can have no more than 2 characters (3 including the $) and cannot
  be keywords including `IN`, `ON` or `TO`.
* By default variables are not DIMensioned and assumed to be STRING or REAL.
  They are initialized to "" or 0 at the beginning of the output program.
* Arrays are limited to no more than 3 dimensions. The size of each dimension
  must be specified as a numeric literal.
* When translated array names are prefixed with arr_.
* Hexadecimal literals of the form 0xABCDEF are supported. For values less
  than 0x8000, the values are converted to integers of the form $ABCD. For
  values greater than that, they are converted to REAL literals with the
  equivalent value.
* VAL is a direct port that uses BASIC09's implementation of VAL. This means
  that when parsing HEX numbers they should look like "$1234" instead of
  "&H1234".
* `CLEAR N` is mapped to `(* CLEAR N *)` but `CLEAR  N, M` is disallowed.
* `CLS` requires that we map the VDG screen for any value that is <> `1`.
  The same is true for `POINT`, `RESET` and `SET`. Note that this can easily
  result in unexpected memory errors while running the program. Running it
  with less space allocated may resolve the issue.
* `NOT (A) + 1` is parsed correctly as `NOT((A) + 1)` or `LNOT((A) + 1)`
* BASIC09 treats boolean operations differently than Color BASIC which
  largely treats them identically to numeric binary operations.
  Specifically, BASIC09 has keywords for boolean operations (AND, OR, NOT)
  that are distinct from the numeric operations (LAND, LOR, LNOT).
  decb-to-b09 will use the former in IF statements and the latter for other
  statements. There are some constructs that mix boolean and numeric
  operations such as `A = (1 < 2) + 1` that decb-to-b09 allows but
  results in BASIC09 programs with errors.
* Converting numeric values into strings formats the number with NO spaces
  and one decimal point, even if the value is an integer.
* When `NEXT` statements do not have an iteration variable specified, the
  previous `FOR` variable is assumed to be the iteration variable and added
  explicitly.
* `NEXT AA, BB` is translated to
```
  NEXT AA
NEXT BB
```
* PEEK and POKE are supported ... but with great power comes great
  responsibility.

* Some constructs require introducing an intermediary variable including
  BUTTON, INKEY, JOYSTK and POINT.
10 IF (INKEY$()="") THEN 10 is converted into a construct that looks like:
```
10 RUN INKEY$(TMP1): IF TMP1 = "" THEN 10
```

## Unsupported Color BASIC constructs
* These constructs are NOT supported by decb-to-b09:
AUDIO, CLEAR, CLOAD, CONT, CSAVE, EOF, EVAL, EXEC, LIST, LLIST, LOAD, MEM,
MOTOR, NEW, RUN, SKIPF, USR
* It is NOT possible to GOTO, GOSUB, ON GOTO or ON GOSUB to a variable.
* NEXT statements must be nested and not interleaved. For example, this is legal:
```
FOR II = 1 to 10
  FOR JJ = 1 to 10
  NEXT JJ
NEXT II
```
But this is illegal:
```
FOR II = 1 to 10
  FOR JJ = 1 to 10
  NEXT II
NEXT JJ
```

## Weird, unsupported Color BASIC constructs
* Numeric literals must NOT have whitespace. For example, this is illegal:
  `12 34`

## Known broken conversions
* Passing a hex literal value to something that results in a procedure call
  generate incorrect code.
* Statements like this do not generate working code: `A = 3 < 4`
## Common issues with converted programs
By default, BASIC09 strings have a maximum length of 32 characters. This often
results in strings getting truncated in non-obvious ways. Resolving these
problems typically involves finding the variable with the issue and DIMing
it to be large enough. For example:
```
DIM XX$: STRING[256]
```
