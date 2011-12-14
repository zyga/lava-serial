# Copyright (C) 2011 Linaro Limited
# Copyright (C) 2002-2009 Chris Liechti
#
# Author: Chris Liechti <cliechti@gmx.net>
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>


import sys
import threading

import serial as pyserial


EXITCHARCTER = '\x1d'   # GS/CTRL+]
MENUCHARACTER = '\x14'  # Menu: CTRL+T

CONVERT_CRLF = 2
CONVERT_CR = 1
CONVERT_LF = 0
NEWLINE_CONVERISON_MAP = ('\n', '\r', '\r\n')
LF_MODES = ('LF', 'CR', 'CR/LF')

REPR_MODES = ('raw', 'some control', 'all control', 'hex')


def key_description(character):
    """generate a readable description for a key"""
    ascii_code = ord(character)
    if ascii_code < 32:
        return 'Ctrl+%c' % (ord('@') + ascii_code)
    else:
        return repr(character)


# help text, starts with blank line! it's a function so that the current values
# for the shortcut keys is used and not the value at program start
def get_help_text():
    return """
--- pySerial (%(version)s) - miniterm - help
---
--- %(exit)-8s Exit program
--- %(menu)-8s Menu escape key, followed by:
--- Menu keys:
---       %(itself)-8s Send the menu character itself to remote
---       %(exchar)-8s Send the exit character to remote
---       %(info)-8s Show info
---       %(upload)-8s Upload file (prompt will be shown)
--- Toggles:
---       %(rts)s  RTS          %(echo)s  local echo
---       %(dtr)s  DTR          %(break)s  BREAK
---       %(lfm)s  line feed    %(repr)s  Cycle repr mode
---
--- Port settings (%(menu)s followed by the following):
--- 7 8           set data bits
--- n e o s m     change parity (None, Even, Odd, Space, Mark)
--- 1 2 3         set stop bits (1, 2, 1.5)
--- b             change baud rate
--- x X           disable/enable software flow control
--- r R           disable/enable hardware flow control
""" % {
    'version': getattr(pyserial, 'VERSION', 'unknown'),
    'exit': key_description(EXITCHARCTER),
    'menu': key_description(MENUCHARACTER),
    'rts': key_description('\x12'),
    'repr': key_description('\x01'),
    'dtr': key_description('\x04'),
    'lfm': key_description('\x0c'),
    'break': key_description('\x02'),
    'echo': key_description('\x05'),
    'info': key_description('\x09'),
    'upload': key_description('\x15'),
    'itself': key_description(MENUCHARACTER),
    'exchar': key_description(EXITCHARCTER),
}


class Miniterm(object):

    def __init__(self, serial, console, echo=False,
                 convert_outgoing=CONVERT_CRLF, repr_mode=0):
        self.serial = serial
        self.console = console
        self.echo = echo
        self.repr_mode = repr_mode
        self.convert_outgoing = convert_outgoing
        self.newline = NEWLINE_CONVERISON_MAP[self.convert_outgoing]
        self.dtr_state = True
        self.rts_state = True
        self.break_state = False
        self.alive = False

    def run_until_stopped(self):
        try:
            self._start()
        finally:
            self._join()

    def stop(self):
        self.alive = False

    def _start(self):
        # set timeouts on the serial port so that we can reliably exit
        self.serial.setTimeout(1.0)
        self.serial.setWriteTimeout(1.0)
        # set alive so that threads keep looping
        self.alive = True
        # start serial->console thread
        self.receiver_thread = threading.Thread(
            target=self._reader,
            name="reader for serial %s" % self.serial.portstr)
        self.receiver_thread.start()
        # enter console->serial loop
        self.transmitter_thread = threading.Thread(
            target=self._writer,
            name="writer for serial %s" % self.serial.portstr)
        self.transmitter_thread.start()

    def _join(self):
        self.transmitter_thread.join()
        self.receiver_thread.join()

    def _dump_port_settings(self):
        sys.stderr.write("\n--- Settings: %s  %s,%s,%s,%s\n" % (
            self.serial.portstr,
            self.serial.baudrate,
            self.serial.bytesize,
            self.serial.parity,
            self.serial.stopbits,
        ))
        sys.stderr.write(
            '--- RTS %s\n' % (self.rts_state and 'active' or 'inactive'))
        sys.stderr.write(
            '--- DTR %s\n' % (self.dtr_state and 'active' or 'inactive'))
        sys.stderr.write(
            '--- BREAK %s\n' % (self.break_state and 'active' or 'inactive'))
        sys.stderr.write(
            '--- software flow control %s\n' % (
                self.serial.xonxoff and 'active' or 'inactive'))
        sys.stderr.write(
            '--- hardware flow control %s\n' % (
                self.serial.rtscts and 'active' or 'inactive'))
        sys.stderr.write(
            '--- data escaping: %s\n' % (
                REPR_MODES[self.repr_mode],))
        sys.stderr.write(
            '--- linefeed: %s\n' % (
                LF_MODES[self.convert_outgoing],))
        try:
            sys.stderr.write('--- CTS: %s  DSR: %s  RI: %s  CD: %s\n' % (
                (self.serial.getCTS() and 'active' or 'inactive'),
                (self.serial.getDSR() and 'active' or 'inactive'),
                (self.serial.getRI() and 'active' or 'inactive'),
                (self.serial.getCD() and 'active' or 'inactive')))
        except pyserial.SerialException:
            # on RFC 2217 ports it can happen to no modem state notification
            # was yet received. ignore this error.
            pass

    def _reader(self):
        """loop and copy serial->console"""
        try:
            while self.alive:
                data = self.serial.read(1)

                if self.repr_mode == 0:
                    # direct output, just have to care about newline setting
                    if data == '\r' and self.convert_outgoing == CONVERT_CR:
                        sys.stdout.write('\n')
                    else:
                        sys.stdout.write(data)
                elif self.repr_mode == 1:
                    # escape non-printable, let pass newlines
                    if (self.convert_outgoing == CONVERT_CRLF
                        and data in '\r\n'):
                        if data == '\n':
                            sys.stdout.write('\n')
                        elif data == '\r':
                            pass
                    elif data == '\n' and self.convert_outgoing == CONVERT_LF:
                        sys.stdout.write('\n')
                    elif data == '\r' and self.convert_outgoing == CONVERT_CR:
                        sys.stdout.write('\n')
                    else:
                        sys.stdout.write(repr(data)[1:-1])
                elif self.repr_mode == 2:
                    # escape all non-printable, including newline
                    sys.stdout.write(repr(data)[1:-1])
                elif self.repr_mode == 3:
                    # escape everything (hexdump)
                    for character in data:
                        sys.stdout.write("%s " % character.encode('hex'))
                sys.stdout.flush()
        except pyserial.SerialException:
            self.alive = False
            # would be nice if the console reader could be interruptted at this
            # point...
            raise

    def _writer(self):
        """loop and copy console->serial until EXITCHARCTER character is
           found. when MENUCHARACTER is found, interpret the next key
           locally.
        """
        menu_active = False
        try:
            while self.alive:
                try:
                    c = self.console.getkey()
                except KeyboardInterrupt:
                    c = '\x03'
                if menu_active:
                    if c == MENUCHARACTER or c == EXITCHARCTER:
                        # Menu character again/exit char -> send itself
                        self.serial.write(c)  # send character
                        if self.echo:
                            sys.stdout.write(c)
                    elif c == '\x15':
                        # CTRL+U -> upload file
                        sys.stderr.write('\n--- File to upload: ')
                        sys.stderr.flush()
                        self.console.cleanup()
                        filename = sys.stdin.readline().rstrip('\r\n')
                        if filename:
                            try:
                                file = open(filename, 'r')
                                sys.stderr.write(
                                    '--- Sending file %s ---\n' % filename)
                                while True:
                                    line = file.readline().rstrip('\r\n')
                                    if not line:
                                        break
                                    self.serial.write(line)
                                    self.serial.write('\r\n')
                                    # Wait for output buffer to drain.
                                    self.serial.flush()
                                    # Progress indicator.
                                    sys.stderr.write('.')
                                sys.stderr.write(
                                    '\n--- File %s sent ---\n' % filename)
                            except IOError, e:
                                sys.stderr.write(
                                    '--- ERROR opening file %s: %s ---\n' % (
                                        filename, e))
                        self.console.setup()
                    elif c in '\x08hH?':
                        # CTRL+H, h, H, ? -> Show help
                        sys.stderr.write(get_help_text())
                    elif c == '\x12':
                        # CTRL+R -> Toggle RTS
                        self.rts_state = not self.rts_state
                        self.serial.setRTS(self.rts_state)
                        sys.stderr.write('--- RTS %s ---\n' % (
                            self.rts_state and 'active' or 'inactive'))
                    elif c == '\x04':
                        # CTRL+D -> Toggle DTR
                        self.dtr_state = not self.dtr_state
                        self.serial.setDTR(self.dtr_state)
                        sys.stderr.write('--- DTR %s ---\n' % (
                            self.dtr_state and 'active' or 'inactive'))
                    elif c == '\x02':
                        # CTRL+B -> toggle BREAK condition
                        self.break_state = not self.break_state
                        self.serial.setBreak(self.break_state)
                        sys.stderr.write('--- BREAK %s ---\n' % (
                            self.break_state and 'active' or 'inactive'))
                    elif c == '\x05':
                        # CTRL+E -> toggle local echo
                        self.echo = not self.echo
                        sys.stderr.write('--- local echo %s ---\n' % (
                            self.echo and 'active' or 'inactive'))
                    elif c == '\x09':
                        # CTRL+I -> info
                        self._dump_port_settings()
                    elif c == '\x01':
                        # CTRL+A -> cycle escape mode
                        self.repr_mode += 1
                        if self.repr_mode > 3:
                            self.repr_mode = 0
                        sys.stderr.write('--- escape data: %s ---\n' % (
                            REPR_MODES[self.repr_mode],))
                    elif c == '\x0c':
                        # CTRL+L -> cycle linefeed mode
                        self.convert_outgoing += 1
                        if self.convert_outgoing > 2:
                            self.convert_outgoing = 0
                        self.newline = NEWLINE_CONVERISON_MAP[
                            self.convert_outgoing]
                        sys.stderr.write('--- line feed %s ---\n' % (
                            LF_MODES[self.convert_outgoing],))
                    #~ elif c in 'pP':
                        # P -> change port XXX reader thread would exit
                    elif c in 'bB':
                        # B -> change baudrate
                        sys.stderr.write('\n--- Baudrate: ')
                        sys.stderr.flush()
                        self.console.cleanup()
                        backup = self.serial.baudrate
                        try:
                            self.serial.baudrate = int(
                                sys.stdin.readline().strip())
                        except ValueError, e:
                            sys.stderr.write(
                                '--- ERROR setting baudrate: %s ---\n' % (e,))
                            self.serial.baudrate = backup
                        else:
                            self.dump_port_settings()
                        self.console.setup()
                    elif c == '8':
                        # 8 -> change to 8 bits
                        self.serial.bytesize = pyserial.EIGHTBITS
                        self.dump_port_settings()
                    elif c == '7':
                        # 7 -> change to 8 bits
                        self.serial.bytesize = pyserial.SEVENBITS
                        self.dump_port_settings()
                    elif c in 'eE':
                        # E -> change to even parity
                        self.serial.parity = pyserial.PARITY_EVEN
                        self.dump_port_settings()
                    elif c in 'oO':
                        # O -> change to odd parity
                        self.serial.parity = pyserial.PARITY_ODD
                        self.dump_port_settings()
                    elif c in 'mM':
                        # M -> change to mark parity
                        self.serial.parity = pyserial.PARITY_MARK
                        self.dump_port_settings()
                    elif c in 'sS':
                        # S -> change to space parity
                        self.serial.parity = pyserial.PARITY_SPACE
                        self.dump_port_settings()
                    elif c in 'nN':
                        # N -> change to no parity
                        self.serial.parity = pyserial.PARITY_NONE
                        self.dump_port_settings()
                    elif c == '1':
                        # 1 -> change to 1 stop bits
                        self.serial.stopbits = pyserial.STOPBITS_ONE
                        self.dump_port_settings()
                    elif c == '2':
                        # 2 -> change to 2 stop bits
                        self.serial.stopbits = pyserial.STOPBITS_TWO
                        self.dump_port_settings()
                    elif c == '3':
                        # 3 -> change to 1.5 stop bits
                        self.serial.stopbits = pyserial.STOPBITS_ONE_POINT_FIVE
                        self.dump_port_settings()
                    elif c in 'xX':
                        # X -> change software flow control
                        self.serial.xonxoff = (c == 'X')
                        self.dump_port_settings()
                    elif c in 'rR':
                        # R -> change hardware flow control
                        self.serial.rtscts = (c == 'R')
                        self.dump_port_settings()
                    else:
                        sys.stderr.write(
                            '--- unknown menu character %s --\n' % (
                            key_description(c),))
                    menu_active = False
                elif c == MENUCHARACTER:
                    # next char will be for menu
                    menu_active = True
                elif c == EXITCHARCTER:
                    # exit app
                    self.stop()
                    break
                elif c == '\n':
                    # send newline character(s)
                    self.serial.write(self.newline)
                    if self.echo:
                        # local echo is a real newline in any case
                        sys.stdout.write(c)
                        sys.stdout.flush()
                else:
                    # send character
                    self.serial.write(c)
                    if self.echo:
                        sys.stdout.write(c)
                        sys.stdout.flush()
        except:
            self.alive = False
            raise
