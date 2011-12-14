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

import sys

import serial as pyserial

from lava_tool.interface import Command, SubCommand
from lava.serial.direct import DirectSerialLine
from lava.serial.console import Console
from lava.serial import miniterm


class SerialCommand(SubCommand):
    """
    Interact with serial lines
    """

    namespace = "lava.serial.commands"

    @classmethod
    def get_name(cls):
        return "serial"
class ConsoleCommand(Command):
    """
    Open an interactive console on a selected serial line
    
    This command opens an interactive console, much like
    telnet, minicom or screen, that is connected to a
    selected serial line.

    There are a few connection methods:

        --direct will open a local serial device
        In this mode you will have to provide the
        connection details (baud rate, parity
        flow control and lots of others)

        --network will open a TCP/IP socket and
        connect to that device. The device can be
        exposed with `lava-tool serial service`

        --managed will open a connection to LAVA
        server and access a serial line defined there

    """

    @classmethod
    def get_name(cls):
        return "console"

    @classmethod
    def register_arguments(cls, parser):
        super(ConsoleCommand, cls).register_arguments(parser)

        parser.add_argument("-q", "--quiet",
            dest="quiet",
            action="store_true",
            help="suppress non error messages",
            default=False)

        connection_group = parser.add_mutually_exclusive_group(required=True)

        connection_group.add_argument(
            "--direct",
            metavar="DEVICE",
            help=("connect to a directly attached serial line"
                  "(such as /dev/ttyUSB0)"))
        connection_group.add_argument(
            "--network",
            metavar="IP:PORT",
            help="connect to a TCP/IP socket")
        connection_group.add_argument(
            "--managed",
            metavar="URL/device",
            help="connect to a LAVA Server with Serial extension")

        serial_group = parser.add_argument_group(title="serial line settings")

        serial_group.add_argument("-b", "--baud",
            dest="baudrate",
            type=int,
            help="set baud rate, default %(default)d",
            default=115200)

        serial_group.add_argument("--parity",
            dest="parity",
            help="set parity, default=%(default)s",
            choices="NEOSM",
            default='N')

        serial_group.add_argument("--rtscts",
            dest="rtscts",
            action="store_true",
            help="enable RTS/CTS flow control (default off)",
            default=False)

        serial_group.add_argument("--xonxoff",
            dest="xonxoff",
            action="store_true",
            help="enable software flow control (default off)",
            default=False)

        serial_group.add_argument("--dtr",
            dest="dtr_state",
            action="store",
            type=int,
            choices=[0, 1],
            help="set initial DTR line state",
            default=None)

        serial_group.add_argument("--rts",
            dest="rts_state",
            action="store",
            type=int,
            help="set initial RTS line state",
            choices=[0, 1],
            default=None)

        terminal_group = parser.add_argument_group(
            title="terminal emulator options")

        crlf_group = terminal_group.add_mutually_exclusive_group()

        crlf_group.add_argument("--lf",
            dest="convert_cr_lf",
            action="store_const",
            const=miniterm.CONVERT_LF,
            help="send LF for each newline (default)",
            default=miniterm.CONVERT_LF)

        crlf_group.add_argument("--cr",
            dest="convert_cr_lf",
            action="store_const",
            const=miniterm.CONVERT_CR,
            help="send CR for each newline")

        crlf_group.add_argument("--crlf",
            dest="convert_cr_lf",
            action="store_const",
            const=miniterm.CONVERT_CRLF,
            help="send CR+LF for each newline")

        terminal_group.add_argument("--exit-char",
            dest="exit_char",
            type=int,
            help=("ASCII code of special character that is used to exit the"
                  " application"),
            default=0x1d)

        terminal_group.add_argument("--menu-char",
            dest="menu_char",
            type=int,
            help=("ASCII code of special character that is used to control"
                  " miniterm (menu)"),
            default=0x14)

        terminal_group.add_argument("-e", "--echo",
            dest="echo",
            action="store_true",
            help="enable local echo (default off)",
            default=False)

        terminal_group.add_argument("-D", "--debug",
            dest="repr_mode",
            action="count",
            help="""debug received data (escape non-printable chars)
    --debug can be given multiple times:
    0: just print what is received
    1: escape non-printable characters, do newlines as unusual
    2: escape non-printable characters, newlines too
    3: hex dump everything""",
            default=0)

    def _config_miniterm(self, serial, console):
        if self.args.repr_mode > 3:
            self.args.repr_mode = 3
        term = miniterm.Miniterm(
            serial,
            console,
            echo=self.args.echo,
            convert_outgoing=self.args.convert_cr_lf,
            repr_mode=self.args.repr_mode)
        if not self.args.quiet:
            sys.stderr.write('--- Miniterm on %s: %d,%s,%s,%s ---\n' % (
                serial.portstr,
                serial.baudrate,
                serial.bytesize,
                serial.parity,
                serial.stopbits))
            sys.stderr.write(
                '--- Quit: %s  |  Menu: %s | Help: %s followed by %s ---\n' % (
                miniterm.key_description(miniterm.EXITCHARCTER),
                miniterm.key_description(miniterm.MENUCHARACTER),
                miniterm.key_description(miniterm.MENUCHARACTER),
                miniterm.key_description('\x08')))
        if self.args.dtr_state is not None:
            if not self.args.quiet:
                sys.stderr.write(
                    '--- forcing DTR %s\n' % (
                        self.args.dtr_state and 'active' or 'inactive'))
            serial.setDTR(self.args.dtr_state)
            term.dtr_state = self.args.dtr_state
        if self.args.rts_state is not None:
            if not self.args.quiet:
                sys.stderr.write(
                    '--- forcing RTS %s\n' % (
                        self.args.rts_state and 'active' or 'inactive'))
            serial.setRTS(self.args.rts_state)
            term.rts_state = self.args.rts_state
        return term

    def invoke(self):
        if self.args.direct:
            try:
                serial = DirectSerialLine(
                    port=self.args.direct,
                    baudrate=self.args.baudrate,
                    parity=self.args.parity,
                    rtscts=self.args.rtscts,
                    xonxoff=self.args.xonxoff)
            except pyserial.SerialException as exc:
                sys.stderr.write(
                    "could not open port %r: %s\n" % (self.args.direct, exc))
                return 1
        elif self.args.network:
            raise NotImplementedError(
                "Networked serial line is not implemented")
        elif self.args.managed:
            raise NotImplementedError("LAVA Server integration is not done")
        # Initialize our console object
        console = Console()
        try:
            # Initialize our terminal object, we do it here
            # as it already touches the serial line and
            # could raise exceptions
            terminal = self._config_miniterm(serial, console)
            with console.grab():
                # With a console grab (that essentially turns on per-keystroke
                # reads) run the terminal until the user explicitly stops it
                # with a command sequence
                terminal.run_until_stopped()
        finally:
            # Once everything is done stop the terminal (this shold be a non-op
            # by now but let's play it safe)
            terminal.stop()
            # And close the serial line
            serial.close()
        if not self.args.quiet:
            sys.stderr.write("\n--- exit ---\n")
