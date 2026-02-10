# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from io import TextIOBase
import os
import platform
from shutil import copyfile
import sys
from typing import Dict, List, Optional, Tuple, Union

SKIP_TOO_LONG = "        raise SkipTest(\"{}\")\n"
NO_SKIP_TOO_LONG = "        # raise SkipTest(\"{}\")\n"
WARNING_LONG = "        # Warning this test takes {}.\n" \
               "        # raise skiptest is uncommented on branch tests\n"


class RootScriptBuilder(object):
    """
    Looks for example scripts that can be made into integration tests.
    """

    def _add_script(self, test_file: TextIOBase, name: str, local_path: str,
                    skip_imports: Optional[List[str]]) -> None:
        """
        Adds a unit test that tests a script by importing it
        """
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

    def _add_split_script(self, test_file: TextIOBase, name: str,
                          local_path: str, split: bool) -> None:
        """
        Adds a test by running a scripts run_script method

        :param test_file: Where to write the test
        :param name: Partial name for the test
        :param local_path: Path to find the script
        :param split: Flag to say if the test should be run split
        """
        test_file.write("\n    def test_")
        test_file.write(name)
        if split:
            test_file.write("_split")
        else:
            test_file.write("_combined")
        test_file.write("(self):\n")

        import_text = local_path[:-3].replace(os.sep, ".")
        test_file.write(f"        from {import_text} import run_script\n")
        test_file.write(f"        run_script(split={split})\n")

    def _extract_binaries(self, text: str) -> List[str]:
        """
        Extracts the binaries from a comments

        :param text: The line(s) that contain the info
        :return: List of the binaries expected
        """
        # remove all whitespace
        text = "".join(text.split())
        # remove comment markers. There may be one between binaries
        text = text.replace("#", "")
        # ignore the part before the binaries and
        text = text[text.find("[")+1: text.find("]")]
        return text.split(",")

    def _script_details(
            self, local_path: str) -> Tuple[bool, bool, List[str], List[str]]:
        """
        Examine a script to see which tests should be added

        :param local_path: path to find the script
        """
        # Says if a run_script split has been found
        run_script = False
        # Says if there is an if def __main__
        has_main = False
        # List of binaries to check for if running not split
        combined_binaires = []
        # List of binaries to check for if running split
        split_binaires = []

        # Temp variables when looking at multiline stiff
        in_combined = False
        in_split = False
        text = ""

        with open(local_path, "r", encoding="utf-8") as script_file:
            for line in script_file:
                # second or more line of a comment
                if in_combined or in_split:
                    text += line
                elif "def run_script(" in line and " split:" in line:
                    print("Split ", local_path)
                    run_script = True
                elif "combined binaries" in line:
                    in_combined = True
                    text = line
                elif "split binaries" in line:
                    in_split = True
                    text = line
                elif "__name__" in line:
                    has_main = True
                # Have we found the end of the binaires list
                if in_combined:
                    if "]" in line:
                        combined_binaires = self._extract_binaries(text)
                        in_combined = False
                        text = ""
                elif in_split:
                    if "]" in line:
                        split_binaires = self._extract_binaries(text)
                        in_split = False
                        text = ""
        return (has_main, run_script, combined_binaires, split_binaires)

    def _add_not_testing(
            self, test_file: TextIOBase, reason: str, local_path: str) -> None:
        """
        Adds comments of what is not beiing tested and why
        """
        test_file.write(f"\n    # Not testing file due to: {reason}\n")
        test_file.write(f"    # {local_path}\n")

    def _add_binaries(
            self, test_file: TextIOBase, binaries: List[str]) -> None:
        """
        Appends binaries checks to a test

        :param test_file: Fle to write check to
        :param binaries: List possibly empty of binaries to check
        """
        if binaries:
            binaries = [f'"{binary}"' for binary in binaries]
            test_file.write(f"        self.check_binaries_used("
                            f"[{', '.join(binaries)}])\n")

    def _add_test_directory(
            self, a_dir: str, prefix_len: int, test_file: TextIOBase,
            too_long: Dict[str, str], exceptions: Dict[str, str],
            skip_exceptions: Dict[str, List[str]]) -> None:
        """
        Adds any required tests for the scripts in a directory
        """
        for a_script in os.listdir(a_dir):
            script_path = os.path.join(a_dir, a_script)
            if os.path.isdir(script_path) and not a_script.startswith("."):
                self._add_test_directory(
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
                    self._add_not_testing(
                        test_file, too_long[a_script], local_path)
                elif a_script in exceptions:
                    self._add_not_testing(
                        test_file, exceptions[a_script], local_path)
                else:
                    (has_main, run_script, combined_binaires,
                     split_binaires) = self._script_details(script_path)
                    name = local_path[:-3].replace(os.sep, "_").replace(
                        "-", "_")
                    skip_imports = skip_exceptions.get(a_script, None)
                    # use the run_Scripts method style
                    if run_script:
                        self._add_split_script(
                            test_file, name, local_path, False)
                        self._add_binaries(test_file, combined_binaires)
                        self._add_split_script(
                            test_file, name, local_path, True)
                        self._add_binaries(test_file, split_binaires)
                    # Due to a main the test will not run if imported
                    elif has_main:
                        self._add_not_testing(
                            test_file, "Unhandled main", local_path)
                        assert combined_binaires == []
                        assert split_binaires == []
                    # Use the import script style
                    else:
                        self._add_script(
                            test_file, name, local_path, skip_imports)
                        self._add_binaries(test_file, combined_binaires)

    def create_test_scripts(
            self, dirs: Union[str, List[str]],
            too_long: Optional[Dict[str, str]] = None,
            exceptions: Optional[Dict[str, str]] = None,
            skip_exceptions: Optional[Dict[str, List[str]]] = None) -> None:
        """
        Creates a file of integration tests to run the scripts/ examples

        :param dirs: List of dirs to find scripts in.
            These are relative paths to the repository
        :param too_long: Dict of files that take too long to run and how long.
            These are just the file name including the `.py`.
            They are mapped to a skip reason.
            These are only skip tests if asked to be (currently not done).
        :param exceptions: Dict of files that should be skipped.
            These are just the file name including the `.py`.
            They are mapped to a skip reason.
            These are always skipped.
        :param skip_exceptions:
            Dict of files and exceptions to skip on.
            These are just the file name including the `.py`.
            They are mapped to a list of INDIVIUAL import statements
            in the::

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
        assert class_file is not None
        integration_dir = os.path.dirname(class_file)
        assert integration_dir is not None
        repository_dir = os.path.dirname(integration_dir)
        assert repository_dir is not None
        test_base_directory = os.path.dirname(__file__)

        test_script = os.path.join(integration_dir, "test_scripts.py")
        header = os.path.join(test_base_directory, "test_scripts_header")
        copyfile(header, test_script)

        with open(test_script, "a", encoding="utf-8") as test_file:
            for script_dir in dirs:
                a_dir = os.path.join(repository_dir, script_dir)
                self._add_test_directory(
                    a_dir, len(repository_dir) + 1, test_file,
                    too_long, exceptions, skip_exceptions)
