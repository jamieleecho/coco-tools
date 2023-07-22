import importlib.resources as pkg_resources
import re
from collections import defaultdict

from . import resources

# Procedure names that start with a procedure keyword.
PROCEDURE_START_PREFIX = re.compile(r'(?i)procedure\s+(\w+)\s*$')

# Procedures that have been called.
INVOKED_PROCEDURE_NAMES = \
    re.compile(r'(?i)\s*RUN\s+(\w+)(?=[^"]*(?:"[^"]*"[^"]*)*$)')


class ProcedureBank(object):
    """
    This class is responsible for loading BASIC09 procedures from a file,
    determining their dependencies on each other and making it easy to
    extract one or more procedures and their dependencies as text.
    """
    def __init__(self):
        self._name_to_procedure = defaultdict(lambda: "")
        self._name_to_dependencies = defaultdict(lambda: set())

    def add_from_resource(self, resource_name):
        """
        Loads the BASIC09 file and stores the procedures and determines the
        dependencies.
        """
        resource_file = (pkg_resources.files(resources) / resource_name)
        with resource_file.open('r') as f:
            return self.add_from_str(f.read())

    def add_from_str(self, procedures):
        """
        Loads the BASIC09 procedures, storing the procedures and determining
        the dependencies.
        """
        name_to_procedure_array = {}
        current_procedure = []
        for line in re.split(r'[\r\n]', procedures):
            if match := PROCEDURE_START_PREFIX.match(line):
                current_procedure = []
                name = match[1]
                name_to_procedure_array[name] = current_procedure
            current_procedure.append(line)
            invoked_names = INVOKED_PROCEDURE_NAMES.findall(line)
            self._name_to_dependencies[name].update(invoked_names)

        for name, procedure in name_to_procedure_array.items():
            self._name_to_procedure[name] = '\n'.join(procedure)

    def get_procedure_and_dependencies(self, procedure_name):
        """
        Given a procedure name, returns a string that includes the procedure
        implementation for all of its dependencies in alphabetical order
        first followed by the implementation of the procedure.
        """
        dependency_set = \
            self._get_procedure_and_dependency_names(procedure_name)
        dependency_set.remove(procedure_name)
        dependency_list = sorted(dependency_set) + [procedure_name]
        output_array = [
            self._name_to_procedure[dependency]
            for dependency in dependency_list
            if dependency in self._name_to_procedure
        ]
        return '\n'.join(output_array)

    def _get_procedure_and_dependency_names(self, procedure_name):
        """
        Given a procedure name, returns a set that includes the procedure
        name and all of its dependencies.
        """
        procedure_dependencies = set()
        self._add_procedure_dependencies(procedure_name,
                                         procedure_dependencies)
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
