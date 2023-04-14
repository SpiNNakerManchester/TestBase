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
        :param str broken_msg:
            message to print instead of raising an exception;
            no current use-case known
        :param skip_exceptions:
            list of exception classes to convert in SkipTest
        :type skip_exceptions: list(type) or None
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
            self.report(f"{duration} for {script}", "scripts_ran_successfully")
            if plotting:
                if not script_checker_shown:
                    raise SkipTest(f"{script} did not plot")
        except SkipTest:
            raise
        except Exception as ex:  # pylint: disable=broad-except
            if broken_msg:
                self.report(script, broken_msg)
            else:
                print(f"Error on {script}")
                raise ex
