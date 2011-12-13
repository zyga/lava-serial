# Copyright (C) 2011 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of LAVA Serial 
#
# LAVA Serial is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# LAVA Serial is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with LAVA Serial.  If not, see <http://www.gnu.org/licenses/>.

from lava_tool.interface import SubCommand


class SerialCommand(SubCommand):
    """
    Interact with serial lines
    """

    namespace = "lava.serial.commands"

    @classmethod
    def get_name(cls):
        return "serial"
