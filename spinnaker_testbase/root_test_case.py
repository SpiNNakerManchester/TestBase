# Copyright (c) 2017 The University of Manchester
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
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
from unittest import SkipTest
from spinnman.exceptions import SpinnmanException
from spinn_utilities.config_holder import (
    get_config_bool, get_config_str, has_config_option)
from pacman.exceptions import PacmanPartitionException, PacmanValueError
from spalloc.job import JobDestroyedError

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

        :raises: SkipTest
        """
        if has_config_option("Machine", "version"):
            version = get_config_str("Machine", "version")
            virtual = get_config_bool("Machine", "virtual_board")
            if version in ["2", "3"] and not virtual:
                raise SkipTest(
                    "This test will not run on a spin {} board".format(
                        version))

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
        test_base_directory = os.path.dirname(__file__)
        test_dir = os.path.dirname(test_base_directory)
        report_dir = os.path.join(test_dir, "global_reports")
        if not os.path.exists(report_dir):
            # It might now exist if run in parallel
            try:
                os.makedirs(report_dir)
            except Exception:  # pylint: disable=broad-except
                pass
        report_path = os.path.join(report_dir, file_name)
        with open(report_path, "a", encoding="utf-8") as report_file:
            report_file.write(message)

    def runsafe(self, method, retry_delay=3.0, skip_exceptions=None):
        """
        Will run the method possibly a few times


        :param method:
        :param retry_delay:
        :param skip_exceptions:
            list to expection classes to convert in SkipTest
        :type skip_exceptions: list(class) or None
        :return:
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
                        raise SkipTest(f"{ex} Still not fixed!") from ex
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
                        raise SkipTest(f"{ex} Still not fixed!") from ex
                raise ex
            print("")
            print("==========================================================")
            print(" Will run {} again in {} seconds".format(
                method, retry_delay))
            print("retry: {}".format(retries))
            print("==========================================================")
            print("")
            time.sleep(retry_delay)
