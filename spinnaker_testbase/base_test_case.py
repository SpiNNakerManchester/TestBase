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
import random
import sys
from spinn_front_end_common.data import FecDataView
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

    def get_provenance_files(self):
        provenance_file_path = FecDataView().get_provenance_dir_path()
        return os.listdir(provenance_file_path)

    def get_system_iobuf_files(self):
        system_iobuf_file_path = (FecDataView.get_system_provenance_dir_path())
        return os.listdir(system_iobuf_file_path)

    def get_app_iobuf_files(self):
        app_iobuf_file_path = (FecDataView.get_app_provenance_dir_path())
        return os.listdir(app_iobuf_file_path)

    def get_placements(self, label):
        """
        Gets the placements for a population in the last run

        :param str label:
        :return: A list (one for each core) of lists (x, y, p) values as str
        :rtype: list(list(str))
        """
        placement_path = os.path.join(
            FecDataView.get_run_dir_path(),
            "placement_by_vertex_using_graph.rpt")
        placements = []
        in_core = False
        with open(placement_path, "r", encoding="utf-8") as placement_file:
            for line in placement_file:
                if in_core:
                    if "**** Vertex: '" in line:
                        in_core = False
                    elif "on core (" in line:
                        xyp = line[line.rfind("(")+1: line.rfind(")")]
                        [x, y, p] = xyp.split(",")
                        placements.append([x.strip(), y.strip(), p.strip()])
                if line == "**** Vertex: '" + label + "'\n":
                    in_core = True
        return placements
