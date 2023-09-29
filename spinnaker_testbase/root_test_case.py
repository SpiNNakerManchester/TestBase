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
import unittest
from spinn_utilities.exceptions import NotSetupException
from spinnman.exceptions import SpinnmanException
from pacman.exceptions import PacmanPartitionException, PacmanValueError
from spalloc_client.job import JobDestroyedError
from spinn_front_end_common.data import FecDataView

if os.environ.get('CONTINUOUS_INTEGRATION', 'false').lower() == 'true':
    max_tries = 3
else:
    max_tries = 1


class RootTestCase(unittest.TestCase):

    def _setUp(self, script):
        # Remove random effect for testing
        # Set test_seed to None to allow random
        # pylint: disable=attribute-defined-outside-init
        self._test_seed = 1

        path = os.path.dirname(script)
        os.chdir(path)

    @staticmethod
    def assert_not_spin_three():
        """
        Will raise a SkipTest if run on a none virtual 4 chip board

        :raises SkipTest: If we're on the wrong sort of board
        """
        version = FecDataView.get_machine_version().number
        if not version == 5:
            raise unittest.SkipTest(
                f"This test will not run on a spinn-{version} board")

    def error_file(self):
        """
        The file any error where reported to before a second run attempt

        :return: Path to (possibly non existent) error file
        """
        test_base_directory = os.path.dirname(__file__)
        test_dir = os.path.dirname(test_base_directory)
        return os.path.join(test_dir, "ErrorFile.txt")

    def report(self, message, file_name):
        if not message.endswith("\n"):
            message += "\n"
        global_reports = os.environ.get("GLOBAL_REPORTS", None)
        if not global_reports:
            try:
                global_reports = FecDataView.get_timestamp_dir_path()
            except NotSetupException:
                # This may happen if you are running none script fiels locally
                return

        if not os.path.exists(global_reports):
            # It might now exist if run in parallel
            try:
                os.makedirs(global_reports)
            except Exception:  # pylint: disable=broad-except
                pass
        report_path = os.path.join(global_reports, file_name)
        with open(report_path, "a", encoding="utf-8") as report_file:
            report_file.write(message)

    def runsafe(self, method, retry_delay=3.0, skip_exceptions=None):
        """
        Will run the method possibly a few times

        :param callable method:
        :param float retry_delay:
        :param skip_exceptions:
            list of exception classes to convert in SkipTest
        :type skip_exceptions: list(class)
        """
        if skip_exceptions is None:
            skip_exceptions = []
        retries = 0
        while True:
            try:
                method()
                break
            except (JobDestroyedError, SpinnmanException) as ex:
                for skip_exception in skip_exceptions:
                    if isinstance(ex, skip_exception):
                        FecDataView.raise_skiptest(
                            f"{ex} Still not fixed!", ex)
                class_file = sys.modules[self.__module__].__file__
                with open(self.error_file(), "a", encoding="utf-8") \
                        as error_file:
                    error_file.write(class_file)
                    error_file.write("\n")
                    error_file.write(str(ex))
                    error_file.write("\n")
                retries += 1
                if retries >= max_tries:
                    raise ex
            except (PacmanValueError, PacmanPartitionException) as ex:
                # skip out if on a spin three
                self.assert_not_spin_three()
                for skip_exception in skip_exceptions:
                    if isinstance(ex, skip_exception):
                        FecDataView.raise_skiptest(
                            f"{ex} Still not fixed!", ex)
                raise ex
            print("")
            print("==========================================================")
            print(f" Will run {method} again in {retry_delay} seconds")
            print(f" retry: {retries}")
            print("==========================================================")
            print("")
            time.sleep(retry_delay)
