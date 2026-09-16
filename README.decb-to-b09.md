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

## Supported constructs

Most Color BASIC and some Extended Color BASIC and Super Extended Color BASIC
features are supported. These include:
include: +, ^, ABS, AND, ASC, ATN, ATTR, BUTTON, CHR$, CLS, COS, DATA, DEF FN, DIM, /, END, ELSE, =, ERNO, EXP, FIX, FN, FOR, GOSUB, GOTO, >, HBUFF, HCIRCLE, HCLS, HCOLOR, HDRAW, HEX$, HGET, HLINE, HPAINT, HPRINT, HPUT, HRESET, HSET, HSCREEN, IF, INKEY$, INPUT, INSTR, INT, JOYSTK, LEFT$, LEN, <, LET, LINE INPUT, LOCATE, LOG, MID$, *, NEXT, NOT, OPEN, OR, PALETTE, PEEK, PLAY, POKE, PRINT, READ, REM, RESET, RESTORE, RETURN, RGB, RIGHT$, RND, SET, SGN, SIN, SOUND, SQR, STEP, STOP, STR$, STRING$, -, TAB, TAN, THEN, TO, TROFF, TRON, WIDTH, VAL, VARPTR

## Unsupported statements

AUDIO, CIRCLE, CLOAD, CLOADM, CLOSE, COLOR, CONT, CSAVE, CSAVEM, DEFUSR, DEL, DRAW, EDIT, END, EXEC, GET, HSTAT, INPUT #, LINE, LINE INPUT, LIST, LLIST, LPOKE, MOTOR, NEW, OPEN, PAINT, PCLEAR, PCLS, PCOPY, PMODE, PRINT USING, PSET, PUT, RENUM, RUN, SCREEN, SKIPF, TIMER

## Unsupported functions

EOF, ERLIN, HPOINT, LPEEK, MEM, POS, PPOINT, USR, VARPTR

## Unsupported disk functions and statements

BACKUP, CLOSE, COPY, CVN, DIR, DRIVE, DSKINI, DSKI, DSKO, EOF, FIELD, FILES, FREE, GET, INPUT #, KILL, LINE INPUT, LOAD, LOADM, LOC, LOF, LSET, MERGE, MKN, OPEN, PRINT #, PRINT # USING, PUT #, RENAME, RSET, RUN, SAVE, SAVEM, UNLOAD, VERIFY ON, VERIFY OFF, WRITE #

## Supported constructs that need some explanation

* BASIC09 does not allow strings to contain CHR$(255)
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
* If DIMmed, variables must be DIMmed earlier in the code (lower line number)
  being used.
* Re-DIMming variables will not work.
* Hexadecimal literals of the form 0xABCDEF are supported. For values less
  than 0x8000, the values are converted to integers of the form $ABCD. For
  values greater than that, they are converted to REAL literals with the
  equivalent value.
* VAL uses BASIC09's implementation of VAL. This means that when parsing
  HEX numbers they should look like "$1234" instead of "&H1234".
* `CLEAR N` is mapped to `(* CLEAR N *)` but `CLEAR  N, M` is disallowed.
* `CLS` requires that we map the VDG screen for any value that is <> `1`.
  The same is true for `POINT`, `RESET` and `SET`. Note that this can easily
  result in unexpected memory errors while running the program. Running it
  with less space allocated may resolve the issue.
* `NOT (A) + 1` is parsed correctly as `NOT((A) + 1)` or `LNOT((A) + 1)`
* Unary `+` and `-` bind more tightly than every binary operator except `^`,
  matching Color BASIC. So `-A <= B` is parsed as `(-A) <= B` and `-A ^ B` is
  parsed as `-(A ^ B)`. `NOT` is the exception: it binds too loosely to be a
  sign's operand at all, so a sign in front of it keeps `NOT`'s wide binding
  and `-NOT A + B` is parsed as `-(NOT(A + B))`.
* BASIC09 treats boolean operations differently than Color BASIC which
  largely treats them identically to numeric binary operations.
  Specifically, BASIC09 has keywords for boolean operations (AND, OR, NOT)
  that are distinct from the numeric operations (LAND, LOR, LNOT).
  decb-to-b09 will use the former in IF statements and the latter for other
  statements. There are some constructs that mix boolean and numeric
  operations such as `A = (1 < 2) + 1` that decb-to-b09 allows but
  results in BASIC09 programs with errors. Within an `IF` condition the
  mixing is rejected instead of silently emitting a program that BASIC09
  refuses to load, so `IF -(A < B) THEN 20` and `IF A AND B < C THEN 20`
  are reported as errors.
* Converting numeric values into strings formats the number with NO spaces
  and one decimal point, even if the value is an integer.
* When `NEXT` statements do not have an iteration variable specified, the
  previous `FOR` variable is assumed to be the iteration variable and added
  explicitly.
* `NEXT AA, BB` is translated to

```basic
  NEXT AA
NEXT BB
```

* `WIDTH` is supported, but use with caution as it really confuses BASIC09,
  making it hard to actually debug programs interactively. `WIDTH` does not
  cause issues if you don't have to switch between VDG and WIND windows. Use
  the -w option if the program can run in 40 or 80 columns to avoid
  unnecessary switching.
* `PRINT @` will not result in an error on 40 or 80 columns screens but will
  pretend that the screen is 32x16.
* `PRINT TAB` columns are renumbered. Color BASIC counts the leftmost column
  as 0 and BASIC09 counts it as 1, so `TAB(30)` is converted to `TAB(31.0)` and
  `TAB(A)` to `TAB(A + 1.0)`.
* `FOR` loops run at least once, as they do in Color BASIC, which only tests
  the limit at `NEXT`. BASIC09 tests it before the first pass, so
  `FOR B = 1 TO 0` would skip the body. A loop whose limit is not a literal
  gets its limit computed into `tmp_to` (and a variable step into `tmp_step`)
  and raised or lowered to the start when the start is already past it:

```basic09
tmp_to := arr_F(U) \ IF 1.0 > tmp_to THEN \ tmp_to := 1.0 \ ENDIF \ FOR B = 1.0 TO tmp_to
```

  This departs from Color BASIC only if the body of a loop that started past
  its limit changes the loop variable. Pass `--basic09-for-loops` to emit loops
  unchanged, with BASIC09's semantics.
* Fractions are dropped wherever Color BASIC needs a whole number, because
  BASIC09 rounds in the same places: `A(1.9)` is `A(1)` in Color BASIC and
  `A(2)` in BASIC09. Array subscripts, the arguments of `CHR$`, `LEFT$`,
  `MID$`, `PEEK`, `RIGHT$` and `TAB`, the selector of `ON ... GOTO/GOSUB`, the
  operands of `AND`, `OR`, `NOT` and `POKE`, and the `INTEGER` parameters of
  the `ecb_*` procedures are wrapped in `INT(...)` (`fix(INT(...))` for the
  parameters) unless they can be shown to hold a whole number, so `A(I)` in a
  `FOR I` loop is left alone but `A(X / 2)` becomes `arr_A(INT(X / 2.0))`.
  `INT` truncates toward zero, while Color BASIC rounds negative values down;
  that only matters for negative fractions, which are errors everywhere but
  `AND`, `OR` and `NOT`.
* `DEF FN` functions are inlined wherever they are called, since BASIC09 has
  no single expression functions. As in Color BASIC, the parameter shadows
  the variable of the same name rather than changing it, so each call assigns
  its argument to a variable of its own, named after the function, and the
  body reads that variable instead:

```basic
10 DEF FNA(Z) = 30 * EXP(-Z * Z / 100)
20 PRINT FNA(SQR(X * X + Y * Y))
```

```basic09
10 (* DEF FNA(Z) = 30 * EXP(-Z * Z / 100) *)
20 fnA_1 := SQR(X * X + Y * Y) \ run ecb_str((30.0 * EXP(- fnA_1 * fnA_1 / 100.0)), tmp_1$) \ PRINT tmp_1$
```

  The argument is evaluated once, however often the body reads the parameter.
  Functions are looked up by name wherever they are defined, so one can be
  called on a line before its `DEF FN`. It is an error to define a function
  twice, to call one that is never defined, or for a function to call itself.
* `FIX` is converted to BASIC09's `INT`. BASIC09's `FIX` rounds, while its
  `INT` truncates toward zero like Color BASIC's `FIX`. Color BASIC's `INT`
  rounds down and is converted to a call to `ecb_int`.
* `^` is inexact in both Color BASIC and BASIC09 (see
  [Exact powers](#exact-powers---exact-powers)).
* `PEEK` and `POKE` are supported ... but with great power comes great
  responsibility.
* `POKE 65497, 0` tells `PLAY` and `SOUND` to play an octave higher.
* `POKE 65496, 0` tells `PLAY` and `SOUND` to play at default octave.
* `PLAY` and `HDRAW` do not support the "X" command. Concatenate strings or
  repeat the command instead.
* Some constructs require introducing an intermediary variable including
  `BUTTON`, `INKEY`, `JOYSTK` and `POINT`.
`10 IF (INKEY$()="") THEN 10` is converted into a construct that looks like:

```basic
10 RUN INKEY$(TMP1): IF TMP1 = "" THEN 10
```

* Drawing commands use the OS-9 Windowing System drawing commands and will
  produce slighly different shapes.
* `HPAINT` ignores the stop color. Instead, the flood fill continues until
  it hits boundaries with colors that are different from the color under the
  initial pixel.
* `HBUFF` can reserve upto 8KB of space in total, but each buffer allocates
  20 bytes more than the equivalent DECB program. It is therefore possible that
  DECB programs that use close to 8KB of space may not run properly.
* `HPUT` ignores the end pixels and instead always draws the same shape
  specified by `HGET`. XOR is added as a drawing action.

## Unsupported Color BASIC constructs

* These constructs are NOT supported by decb-to-b09:
AUDIO, CLEAR, CLOAD, CONT, CSAVE, EOF, EVAL, EXEC, LIST, LLIST, LOAD, MEM,
MOTOR, NEW, RUN, SKIPF, USR
* It is NOT possible to GOTO, GOSUB, ON GOTO or ON GOSUB to a variable.
* NEXT statements must be nested and not interleaved. For example, this is legal:

```basic
FOR II = 1 to 10
  FOR JJ = 1 to 10
  NEXT JJ
NEXT II
```

But this is illegal:

```basic
FOR II = 1 to 10
  FOR JJ = 1 to 10
  NEXT II
NEXT JJ
```

## Weird, unsupported Color BASIC constructs

* Numeric literals must NOT have whitespace. For example, this is illegal:
  `12 34`

## Known broken conversions

* Statements like this do not generate working code: `A = 3 < 4`

## Line numbers

* The maximum supported line number is 32700

## Break and error handling

* There can be at most 1 ON BRK GOTO statement
* There can be at most 1 ON ERR GOTO statement
* When either is invoked, it is as if both are invoked at the same time

## Common issues with converted programs

By default, BASIC09 strings have a maximum length of 32 characters. This often
results in strings getting truncated in non-obvious ways.

The simplest way to resolve these issues is to pass the maximum storage space
for strings via the  `--default-string-storage` option. Alternatively,
resolving these problems typically involves finding the variable with the issue
and DIMing it to be large enough. For example:

```basic
DIM XX$: STRING[256]
```

Finer grain configuration of string sizes is possible via the `--config-file`
followed by a path to a YAML file that maps string variable names to sizes in
bytes. A file might look like:

```basic
string_configs:
  strname_to_size:
    A$: 100
    A$(): 200
    BC$: 300
```

## Running on a plain console (`-t`)

The generated program normally starts by calling `_ecb_start`, which sets up
a CoCo text screen: it programs the 16 color palette through `gfx2`, switches
to 32 columns and sets the cursor color. On an ordinary OS-9 console none of
that applies, and the escape sequences it writes turn into junk on screen.

Passing `--terminal` (`-t`) leaves the `_ecb_start` call out of the output, so
the program starts straight into its own code. `_ecb_start` then drops out of
the emitted dependencies as well, making the output smaller.

Everything else in the prologue is unchanged: `display` is still declared and
still passed to the `ecb_*` procedures.

Two things to know before reaching for it:

* The `display` record is left at BASIC09's zero initialization rather than the
  values `_ecb_start` would have written. Its path fields mean "no path open"
  when they hold `$ff`, and zero is a valid path number, so any statement that
  tests them acts on path 0 -- the program's own standard input. That covers
  the graphics statements (`HSCREEN`, `HCLS`, `HPUT`, ...), `PALETTE`, and also
  `WIDTH`, which is otherwise a text-mode statement. Programs that use any of
  them should be converted without `-t`.
* `_ecb_start` also runs `shell("tmode pau=0 eko=0 upc=0")`, which is terminal
  setup rather than screen setup, and `-t` skips that too. The console keeps
  whatever the shell had set, so output pauses at each screenful if `pau` is on,
  and keys read by `INKEY$` echo until the first `INPUT` turns `eko` off. Run
  `tmode pau=0 eko=0 upc=0` yourself before the program if that matters.

## Exact powers (`--exact-powers`)

Color BASIC and BASIC09 both compute `X ^ Y` through logarithms, so the result
is slightly off even for small whole numbers. In BASIC09 `2 ^ 7` is
128.0000002 and `2 ^ 9` is 512.000001; in Color BASIC every power from `2 ^ 1`
to `2 ^ 9` is a little high. The two are wrong in different places, so a program
that depends on exact powers breaks differently in each. BANNER, for example,
decodes its letters bit by bit and tests `S(U) = 1` after subtracting `2 ^ K`,
which never matches, so its letters come out garbled on a CoCo and garbled in
another way under BASIC09.

`--exact-powers` converts `^` into a call to `ecb_pow`, which multiplies whole
number exponents out exactly and uses `^` for everything else. Like any
function the transpiler replaces with a procedure, the call is hoisted in front
of the statement that uses it:

```basic09
RUN ecb_pow(2.0, K, tmp_1) \ IF tmp_1 < arr_S(U) THEN 270
```

This is not what Color BASIC does, so it is off by default. Use it for programs
that were written for a BASIC with exact powers, such as BANNER.

## Real-to-integer optimization (`-O`)

By default every numeric variable and array is emitted as a BASIC09 `REAL`,
matching Color BASIC semantics. Reals are 5 bytes each and slower than
integers, so for code paths that only ever deal with whole numbers `-O`
opts into a static analysis that promotes those variables to BASIC09
`INTEGER` instead.

A scalar or array becomes an integer candidate only if **every** value
ever assigned to it is statically provable to be an integer in the signed
16-bit range `[-32768, 32767]`. The analysis disqualifies a variable if
any of the following appears in its provenance:

* a transcendental or otherwise non-integer function (`SIN`, `COS`,
  `TAN`, `ATN`, `LOG`, `EXP`, `SQR`, `RND`, `VAL`),
* the division `/` or power `^` operator,
* a fractional literal, or a numeric literal outside the 16-bit range,
* a value coming from `INPUT` or `READ` (the data could be fractional or
  out of range),
* being passed as a `REAL` output parameter to a known procedure (output
  parameters write back through the caller's storage, so the caller's
  type is pinned by the callee — `INT()`, `JOYSTK()`, `VAL()`, `STR$()`,
  etc. all force their target back to `REAL`),
* a value flowing through another non-integer variable (transitively).

The disqualification rules propagate via fixpoint, so e.g. `A = SIN(1)`
followed by `B = A` correctly leaves both variables as `REAL`.

The optimization also rewrites the call sites of the `ecb_*` runtime
procedures: most of them now declare their numeric input parameters as
`INTEGER` (the exceptions are `ecb_int`, `ecb_str`, `ecb_val`, and
`ecb_hex`, where the type is load-bearing). At every call site:

* an integer-valued literal is rewritten in place (`5.0` → `5`),
* a real-typed variable or expression is wrapped with `fix(...)`, or with
  `fix(INT(...))` if it might hold a fraction, since `fix` rounds,
* an integer-typed variable or expression passed to a `REAL` slot is wrapped
  with `float(...)`. BASIC09 does not widen it: the procedure would read the
  integer's bytes as a real and see garbage,
* a redundant `float(x)` wrapper is unwrapped before re-coercing back to
  integer, so e.g. `HCIRCLE` emits `display.hfore` directly instead of
  `fix(float(display.hfore))`.

This call-site coercion runs unconditionally, even without `-O`, so a
non-optimized build still produces well-typed BASIC09 calls to the new
`INTEGER`-input `ecb_*` procedures.

### Inspecting the candidate set

To preview which variables `-O` would promote without actually compiling,
use `--list-integer-candidates`. The output is a sorted list, one
variable per line, with array names printed as `X()` to distinguish them
from a same-named scalar. For example:

```sh
decb-to-b09 program.bas candidates.txt --list-integer-candidates
```

might produce:

```
A
B
I
X()
```

### Excluding variables

If a particular variable should stay `REAL` even though it satisfies the
analysis (e.g. because the code later uses it in a fractional way that
the analysis can't see), pass `--no-optimize` with a comma-separated list
of names. Use plain names for scalars and a trailing `()` for arrays:

```sh
decb-to-b09 program.bas program.b09 -O --no-optimize="B,X()"
```

This produces a build where `A`, `I`, and any other safe variables are
`INTEGER`, but `B` and the array `X` remain `REAL`.

### Worked example

For
```basic
10 A = 5
20 B = A + 3
30 FOR I = 1 TO 10: NEXT I
40 SOUND B, A
50 DIM X(5)
60 X(2) = 7
70 LOCATE A, B
80 HCIRCLE(159, 95), 20
```
`decb-to-b09 -O` produces (excerpted):
```basic09
DIM A, B, I: INTEGER
A := 0
B := 0
I := 0
...
A := 5
B := A + 3
FOR I = 1 TO 10
NEXT I
RUN ecb_sound(B, A, 31, FIX(play.octo))
DIM arr_X(6): INTEGER
arr_X(2) := 7
run ecb_locate(A, B)
run ecb_hcircle(159, 95, 20, display.hfore, 1.0, display)
```

Without `-O`, the same source produces a build where `A`, `B`, `I`,
and `arr_X` are `REAL`, the scalar arguments are wrapped in `fix(...)`
at the now-`INTEGER` `ecb_*` call sites, and `arr_X` remains a `REAL`
array.
