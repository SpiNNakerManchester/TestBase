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
import random
import sys
import sqlite3
from spinn_front_end_common.utilities import globals_variables
from .root_test_case import RootTestCase


random.seed(os.environ.get('P8_INTEGRATION_SEED', None))


class BaseTestCase(RootTestCase):

    def setUp(self):
        self._setUp(sys.modules[self.__module__].__file__)

    def assert_logs_messages(
            self, log_records, sub_message, log_level='ERROR', count=1,
            allow_more=False):
        """ Tool to assert the log messages contain the sub-message

        :param log_records: list of log message
        :param sub_message: text to look for
        :param log_level: level to look for
        :param count: number of times this message should be found
        :param allow_more: If True, OK to have more than count repeats
        :return: None
        """
        seen = 0
        for record in log_records:
            if record.levelname == log_level and \
                    sub_message in str(record.msg):
                seen += 1
        if allow_more and seen > count:
            return
        if seen != count:
            raise self.failureException(
                "\"{}\" not found in any {} logs {} times, was found {} "
                "times".format(sub_message, log_level, count, seen))

    def get_provenance(self, description_name):
        """
        Gets the provenance item(s) from the last run

        :param str description_name: The value to LIKE search for in the
        description_name column. Can be the full name have %  amd _ wildcards

        :return: A possibly multiline string with
        for each row which matches the like a line
        description_name: value
        """
        provenance_file_path = globals_variables.provenance_file_path()
        prov_file = os.path.join(provenance_file_path, "provenance.sqlite3")
        prov_db = sqlite3.connect(prov_file)
        prov_db.row_factory = sqlite3.Row
        results = []
        for row in prov_db.execute(
                "SELECT description_name AS description, the_value AS 'value' "
                "FROM provenance_view  "
                "WHERE description_name LIKE ?", (description_name,)):
            results.append("{}: {}\n".format(row["description"], row["value"]))
        return "".join(results)

    def get_provenance_files(self):
        provenance_file_path = globals_variables.provenance_file_path()
        return os.listdir(provenance_file_path)

    def get_system_iobuf_files(self):
        system_iobuf_file_path = (
            globals_variables.system_provenance_file_path())
        return os.listdir(system_iobuf_file_path)

    def get_app_iobuf_files(self):
        app_iobuf_file_path = (
            globals_variables.app_provenance_file_path())
        return os.listdir(app_iobuf_file_path)

    def get_run_time_of_BufferExtractor(self):
        """
        Gets the BufferExtractor provenance item(s) from the last run

        :return: A possibly multiline string with
        for each row which matches the like %BufferExtractor
        description_name: value
        """
        return self.get_provenance("%BufferExtractor")

    def get_placements(self, label):
        """
        Gets the placements for a population in the last run

        :param str label:
        :return: A list (one for each core) of lists (x, y, p) values as str
        :rtpye: list(list(str))
        """
        report_default_directory = globals_variables.run_report_directory()
        placement_path = os.path.join(
            report_default_directory, "placement_by_vertex_using_graph.rpt")
        placements = []
        in_core = False
        with open(placement_path, "r") as placement_file:
            for line in placement_file:
                if in_core:
                    if "**** Vertex: '" in line:
                        in_core = False
                    elif "on core (" in line:
                        all = line[line.rfind("(")+1: line.rfind(")")]
                        [x, y, p] = all.split(",")
                        placements.append([x.strip(), y.strip(), p.strip()])
                if line == "**** Vertex: '" + label + "'\n":
                    in_core = True
        return placements
