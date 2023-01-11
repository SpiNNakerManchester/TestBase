# Copyright (c) 2017-2019 The University of Manchester
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import platform
from shutil import copyfile
import sys

SKIP_TOO_LONG = "        raise SkipTest(\"{}\")\n"
NO_SKIP_TOO_LONG = "        # raise SkipTest(\"{}\")\n"
WARNING_LONG = "        # Warning this test takes {}.\n" \
               "        # raise skiptest is uncommented on branch tests\n"


class RootScriptBuilder(object):

    def add_script(self, test_file, name, local_path, skip_imports):
        test_file.write("\n    def test_")
        test_file.write(name)
        test_file.write("(self):\n")
        if skip_imports:
            if isinstance(skip_imports, str):
                skip_imports = [skip_imports]
            for skip_import in skip_imports:
                test_file.write("        ")
                test_file.write(skip_import)
                test_file.write("\n")
        test_file.write("        self.check_script(\"")
        test_file.write(local_path)
        test_file.write("\"")
        if skip_imports:
            test_file.write(", skip_exceptions=[")
            test_file.write(
                ",".join(map(lambda x: x.split()[-1], skip_imports)))
            test_file.write("]")
        test_file.write(")\n")

    def add_scripts(self, a_dir, prefix_len, test_file, too_long, exceptions,
                    skip_exceptions):
        for a_script in os.listdir(a_dir):
            script_path = os.path.join(a_dir, a_script)
            if os.path.isdir(script_path) and not a_script.startswith("."):
                self.add_scripts(
                    script_path, prefix_len, test_file, too_long, exceptions,
                    skip_exceptions)
            if a_script.endswith(".py") and a_script != "__init__.py":
                local_path = script_path[prefix_len:]
                # As the paths are written to strings in files
                # Windows needs help!
                if platform.system() == "Windows":
                    local_path = local_path.replace("\\", "/")
                if a_script in too_long and len(sys.argv) > 1:
                    # Lazy boolean distinction based on presence of parameter
                    test_file.write("\n    # Not testing file due to: ")
                    test_file.write(too_long[a_script])
                    test_file.write("\n    # ")
                    test_file.write(local_path)
                    test_file.write("\n")
                elif a_script in exceptions:
                    test_file.write("\n    # Not testing file due to: ")
                    test_file.write(exceptions[a_script])
                    test_file.write("\n    # ")
                    test_file.write(local_path)
                    test_file.write("\n")
                else:
                    name = local_path[:-3].replace(os.sep, "_").replace(
                        "-", "_")
                    skip_imports = skip_exceptions.get(a_script, None)
                    self.add_script(test_file, name, local_path, skip_imports)

    def create_test_scripts(self, dirs, too_long=None, exceptions=None,
                            skip_exceptions=None):
        """

        :param dirs: List of dirs to fins scripts in
            These are relative paths to the repository
        :type dirs: str or list(str)
        :param too_long: Dict of files that take too long to run and how long
            These are just the file name including the .py
            They are mapped to a skip reason
            These are only skip testes if asked to be (currently not done)
        :type too_long: dict(str, str) or None
        :param exceptions:  Dict of files that should be skipped
            These are just the file name including the .py
            They are mapped to a skip reason
            These are always skipped
        :type exceptions: dict(str, str) or None
        :param skip_exceptions:
            Dict of files and exc eptions to skip on
            These are just the file name including the .py
            They are mapped to a list of INDIVIUAL import statements
            in the
            from xyz import Abc
            format.
        """
        if too_long is None:
            too_long = {}
        if exceptions is None:
            exceptions = {}
        if skip_exceptions is None:
            skip_exceptions = {}
        if isinstance(dirs, str):
            dirs = [dirs]

        class_file = sys.modules[self.__module__].__file__
        integration_dir = os.path.dirname(class_file)
        repository_dir = os.path.dirname(integration_dir)
        test_base_directory = os.path.dirname(__file__)

        test_script = os.path.join(integration_dir, "test_scripts.py")
        header = os.path.join(test_base_directory, "test_scripts_header")
        copyfile(header, test_script)

        with open(test_script, "a", encoding="utf-8") as test_file:
            for script_dir in dirs:
                a_dir = os.path.join(repository_dir, script_dir)
                self.add_scripts(a_dir, len(repository_dir)+1, test_file,
                                 too_long, exceptions, skip_exceptions)
