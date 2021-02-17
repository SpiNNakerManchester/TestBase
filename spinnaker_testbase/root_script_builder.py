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


class RootScriptBuilder(object):

    def add_scripts(self, a_dir, prefix_len, test_file):
        for a_script in os.listdir(a_dir):
            script_path = os.path.join(a_dir, a_script)
            if os.path.isdir(script_path) and not a_script.startswith("."):
                self.add_scripts(script_path, prefix_len, test_file)
            if a_script.endswith(".py") and a_script != "__init__.py":
                print(a_script)
                local_path = script_path[prefix_len:]
                name = local_path[:-3].replace(os.sep, "_")
                test_file.write("\n    def test_")
                test_file.write(name)
                test_file.write("(self):\n        self.check_script(\"")
                # As the paths are written to strings in files Windows needs help!
                if platform.system() == "Windows":
                    the_path = local_path.replace("\\", "/")
                test_file.write(local_path)
                test_file.write("\")\n")

    def create_test_scripts(self, dirs):
        if isinstance(dirs, str):
            dirs = [dirs]

        class_file = sys.modules[self.__module__].__file__
        integration_dir = os.path.dirname(class_file)
        repository_dir = os.path.dirname(integration_dir)
        test_base_directory = os.path.dirname(__file__)

        test_script = os.path.join(integration_dir, "test_scripts.py")
        header = os.path.join(test_base_directory, "test_scripts_header")
        copyfile(header, test_script)

        with open(test_script, "a") as test_file:
            for script_dir in dirs:
                a_dir = os.path.join(repository_dir, script_dir)
                self.add_scripts(a_dir, len(repository_dir)+1, test_file)
