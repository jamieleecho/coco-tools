import importlib.resources as importlib_resources
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

from coco import b09

from .. import resources

# Procedure names that start with a procedure keyword.
PROCEDURE_START_PREFIX = re.compile(r"(?i)procedure\s+(\w+)\s*$")

# Procedures that have been called.
INVOKED_PROCEDURE_NAMES = re.compile(r'(?i)\s*RUN\s+(\w+)(?=[^"]*(?:"[^"]*"[^"]*)*$)')

# Finds STRING<<>> occurences so that they can be replaced with storage sizes
STR_STORAGE_TAG = re.compile(r'(?i)\:\s*STRING\<\<\>\>(?=[^"]*(?:"[^"]*"[^"]*)*$)')

# Matches a ``param`` declaration line. The type match is greedy so
# that annotations like ``string[80]`` and ``string<<>>`` are kept
# intact.
PARAM_LINE_REGEX = re.compile(r"(?i)^\s*param\s+(.+?)\s*:\s*(.+?)\s*$")

# Matches an ``(* Out *)`` annotation on its own line. Basic09 does
# not accept end-of-line comments inside a procedure, nor does it
# parse them on the same line as another statement, so the marker
# must occupy its own line and apply to the next ``param`` line.
OUTPUT_MARKER_REGEX = re.compile(r"(?i)^\s*\(\*\s*out\s*\*\)\s*$")


# Basic09 parameter types that classify a numeric value as an
# integer, as opposed to a real or some other type. Stored lowercase
# for comparison after normalization.
INTEGER_PARAM_TYPES: frozenset = frozenset({"integer", "byte"})

# Basic09 parameter types that classify a numeric value as a
# floating-point real.
REAL_PARAM_TYPES: frozenset = frozenset({"real"})


@dataclass(frozen=True)
class ProcedureParam:
    """A single formal parameter of a BASIC09 procedure."""

    name: str
    type: str
    is_output: bool

    @property
    def is_integer(self) -> bool:
        return self.type.lower() in INTEGER_PARAM_TYPES

    @property
    def is_real(self) -> bool:
        return self.type.lower() in REAL_PARAM_TYPES


@dataclass(frozen=True)
class ProcedureSignature:
    """The ordered formal parameter list of a BASIC09 procedure."""

    name: str
    params: Tuple[ProcedureParam, ...]


def parse_param_line(line: str, *, is_output: bool = False) -> List[ProcedureParam]:
    """Parse a single ``param`` declaration and return the
    ``ProcedureParam`` list it declares.

    Multi-name declarations like ``param a, b, c: real`` are split
    into one ``ProcedureParam`` per name, sharing the same type
    and the supplied ``is_output`` flag. Output parameters are
    denoted by an ``(* Out *)`` marker on the line *immediately
    above* the ``param`` declaration; the caller is responsible
    for tracking that marker and passing ``is_output=True`` here.
    """
    parsed = PARAM_LINE_REGEX.match(line.strip())
    if not parsed:
        return []

    names = [name.strip() for name in parsed.group(1).split(",")]
    type_text = parsed.group(2).strip()
    return [
        ProcedureParam(name=name, type=type_text, is_output=is_output)
        for name in names
        if name
    ]


class ProcedureBank(object):
    """
    This class is responsible for loading BASIC09 procedures from a file,
    determining their dependencies on each other and making it easy to
    extract one or more procedures and their dependencies as text.

    In addition to the raw source, the bank also parses each
    procedure's formal parameter list into a
    :class:`ProcedureSignature`. Output parameters must be annotated
    with a trailing ``(* Output *)`` comment on the ``param`` line.
    """

    _name_to_procedure: Dict[str, str]
    _name_to_dependencies: Dict[str, Set[str]]
    _name_to_signature: Dict[str, ProcedureSignature]
    _default_str_storage: int

    def __init__(
        self,
        *,
        default_str_storage: int = b09.DEFAULT_STR_STORAGE,
    ):
        self._name_to_procedure = defaultdict(lambda: "")
        self._name_to_dependencies = defaultdict(lambda: set())
        self._name_to_signature = {}
        self._default_str_storage = default_str_storage

    @property
    def signatures(self) -> Dict[str, ProcedureSignature]:
        """Return a mapping from procedure name to its parsed
        signature. Lookup is case-sensitive; procedure names in
        ``ecb.b09`` are lowercase (or underscore-prefixed lowercase).
        """
        return self._name_to_signature

    def add_from_resource(self, resource_name: str) -> None:
        """
        Loads the BASIC09 file and stores the procedures and determines the
        dependencies.
        """
        resource_file = importlib_resources.files(resources) / resource_name
        with resource_file.open("r") as f:
            return self.add_from_str(f.read())

    def add_from_str(self, procedures: str) -> None:
        """
        Loads the BASIC09 procedures, storing the procedures and determining
        the dependencies.
        """
        name_to_procedure_array: Dict[str, List[str]] = {}
        name_to_params: Dict[str, List[ProcedureParam]] = {}
        current_procedure: List[str] = []
        name = ""
        # ``output_pending`` is set when we have just seen a line
        # containing only an ``(* Out *)`` marker. The very next
        # ``param`` declaration consumes the flag and is annotated
        # as an output parameter. The flag is cleared on procedure
        # boundaries and on any line that is neither blank nor a
        # ``param`` declaration, so a stray marker can never leak
        # past its intended target.
        output_pending = False
        for line in re.split(r"[\r\n]", procedures):
            if match := PROCEDURE_START_PREFIX.match(line):
                current_procedure = []
                name = match[1]
                name_to_procedure_array[name] = current_procedure
                name_to_params[name] = []
                output_pending = False
            current_procedure.append(line)
            invoked_names = INVOKED_PROCEDURE_NAMES.findall(line)
            self._name_to_dependencies[name].update(invoked_names)
            if not name:
                continue

            stripped = line.strip()
            if not stripped:
                # blank lines preserve the pending marker
                continue
            if OUTPUT_MARKER_REGEX.match(stripped):
                output_pending = True
                continue

            params = parse_param_line(line, is_output=output_pending)
            if params:
                name_to_params[name].extend(params)
            output_pending = False

        for name, procedure in name_to_procedure_array.items():
            self._name_to_procedure[name] = "\n".join(procedure).strip()
            self._name_to_signature[name] = ProcedureSignature(
                name=name,
                params=tuple(name_to_params[name]),
            )

    def get_procedure_and_dependencies(self, procedure_name: str) -> str:
        """
        Given a procedure name, returns a string that includes the procedure
        implementation for all of its dependencies in alphabetical order
        first followed by the implementation of the procedure.
        """
        dependency_set = self._get_procedure_and_dependency_names(procedure_name)
        dependency_set.remove(procedure_name)
        dependency_list = sorted(dependency_set) + [procedure_name]
        output_array = [
            self._name_to_procedure[dependency]
            for dependency in dependency_list
            if dependency in self._name_to_procedure
        ]
        raw_text: str = "\n".join(output_array)
        str_storage_text: str = ": STRING" + (
            ""
            if self._default_str_storage == b09.DEFAULT_STR_STORAGE
            else f"[{self._default_str_storage}]"
        )
        return re.sub(STR_STORAGE_TAG, str_storage_text, raw_text)

    def _get_procedure_and_dependency_names(self, procedure_name):
        """
        Given a procedure name, returns a set that includes the procedure
        name and all of its dependencies.
        """
        procedure_dependencies = set()
        self._add_procedure_dependencies(procedure_name, procedure_dependencies)
        return procedure_dependencies

    def _add_procedure_dependencies(self, procedure_name, dependencies):
        """
        Given a a procedure name and a set of known dependencies, recurses
        through the dependencies of the procedure, adding them to
        dependencies.
        """
        if procedure_name in dependencies:
            return
        dependencies.add(procedure_name)
        for dependency in self._name_to_dependencies[procedure_name]:
            self._add_procedure_dependencies(dependency, dependencies)
