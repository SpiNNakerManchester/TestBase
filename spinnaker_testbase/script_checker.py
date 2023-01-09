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
from unittest import SkipTest
from .root_test_case import RootTestCase
matplotlib.use('Agg')

script_checker_shown = False


# This is a global function as pydevd calls _needsmain when debugging
def mockshow():
    # pylint: disable=global-statement
    global script_checker_shown
    script_checker_shown = True


class ScriptChecker(RootTestCase):

    def script_path(self, script):
        class_file = sys.modules[self.__module__].__file__
        integration_tests_directory = os.path.dirname(class_file)
        root_dir = os.path.dirname(integration_tests_directory)
        return os.path.join(root_dir, script)

    def check_script(self, script, broken_msg=None, skip_exceptions=None):
        """

        :param str script: relative path to the file to run
        :param str broken_msg: message to print instead of raisng an exception
            no current usecase known
        :param skip_exceptions:
            list to expection classes to convert in SkipTest
        :type skip_exceptions: list(class) or None

        """
        # pylint: disable=global-statement
        global script_checker_shown

        script_path = self.script_path(script)
        self._setUp(script_path)

        plotting = "import matplotlib.pyplot" in (
            open(script_path, encoding="utf-8").read())
        if plotting:
            script_checker_shown = False
            pyplot.show = mockshow
        from runpy import run_path
        try:
            start = time.time()
            self.runsafe(lambda: run_path(script_path),
                         skip_exceptions=skip_exceptions)
            duration = time.time() - start
            self.report("{} for {}".format(duration, script),
                        "scripts_ran_successfully")
            if plotting:
                if not script_checker_shown:
                    raise SkipTest("{} did not plot".format(script))
        except SkipTest:
            raise
        except Exception as ex:  # pylint: disable=broad-except
            if broken_msg:
                self.report(script, broken_msg)
            else:
                print("Error on {}".format(script))
                raise ex
