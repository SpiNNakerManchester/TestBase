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
import sys
import time
import matplotlib
import matplotlib.pyplot as pyplot
from .root_test_case import RootTestCase
matplotlib.use('Agg')

script_checker_shown = False


# This is a global function as pydevd calls _needsmain when debugging
def mockshow():
    global script_checker_shown
    script_checker_shown = True


class ScriptChecker(RootTestCase):

    def check_script(self, script, broken_msg=None):
        global script_checker_shown

        class_file = sys.modules[self.__module__].__file__
        integration_tests_directory = os.path.dirname(class_file)
        root_dir = os.path.dirname(integration_tests_directory)
        script_path = os.path.join(root_dir, script)
        self._setUp(script_path)

        plotting = "import matplotlib.pyplot" in open(script_path).read()
        if plotting:
            script_checker_shown = False
            pyplot.show = mockshow
        from runpy import run_path
        try:
            start = time.time()
            self.runsafe(lambda: run_path(script_path))
            duration = time.time() - start
            self.report("{} for {}".format(duration, script),
                        "scripts_ran_successfully")
            if plotting:
                self.assertTrue(script_checker_shown)
        except Exception as ex:  # pylint: disable=broad-except
            if broken_msg:
                self.report(script, broken_msg)
            else:
                print("Error on {}".format(script))
                raise ex
