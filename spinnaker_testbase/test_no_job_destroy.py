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
from .base_test_case import BaseTestCase


class TestNoJobDestory(BaseTestCase):

    def test_no_destory_file(self):
        if os.path.exists(self.error_file(), encoding="utf-8"):
            with open(self.error_file()) as error_file:
                error_text = error_file.read()
            print(error_text)
            raise AssertionError(error_text)
