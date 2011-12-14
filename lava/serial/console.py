# Copyright (C) 2011 Linaro Limited
# Copyright (C) 2002-2009 Chris Liechti
#
# Author: Chris Liechti <cliechti@gmx.net>
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
import os

from contextlib import contextmanager


class ConsoleBase(object):

    def setup(self):
        pass

    def cleanup(self):
        pass

    @contextmanager
    def grab(self):
        try:
            self.setup()
            yield
        finally:
            self.cleanup()


if os.name == 'nt':
    import msvcrt

    class Console(ConsoleBase):

        def getkey(self):
            while 1:
                z = msvcrt.getch()
                if z == '\0' or z == '\xe0':    # functions keys
                    msvcrt.getch()
                else:
                    if z == '\r':
                        return '\n'
                    return z

elif os.name == 'posix':
    import termios
    import sys

    class Console(ConsoleBase):

        def __init__(self):
            self.fd = sys.stdin.fileno()

        def setup(self):
            self.old = termios.tcgetattr(self.fd)
            new = termios.tcgetattr(self.fd)
            new[3] = new[3] & ~termios.ICANON & ~termios.ECHO & ~termios.ISIG
            new[6][termios.VMIN] = 1
            new[6][termios.VTIME] = 0
            termios.tcsetattr(self.fd, termios.TCSANOW, new)

        def getkey(self):
            c = os.read(self.fd, 1)
            return c

        def cleanup(self):
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old)

else:
    raise NotImplementedError(
        "Sorry no implementation for your platform (%s) available." % (
            sys.platform,))
