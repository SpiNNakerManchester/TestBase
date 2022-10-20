# Copyright (c) 2017-2021 The University of Manchester
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
import time
import traceback
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
        report_dir = os.path.join(test_dir, "reports")
        if not os.path.exists(report_dir):
            # It might now exist if run in parallel
            try:
                os.makedirs(report_dir)
            except Exception:  # pylint: disable=broad-except
                pass
        report_path = os.path.join(report_dir, file_name)
        with open(report_path, "a") as report_file:
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
                with open(self.error_file(), "a") as error_file:
                    traceback.print_exc(file=error_file)
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
