# first choose a platform dependant way to read single characters from the console
global console

if os.name == 'nt':
    import msvcrt
    class Console:
        def __init__(self):
            pass

        def setup(self):
            pass    # Do nothing for 'nt'

        def cleanup(self):
            pass    # Do nothing for 'nt'

        def getkey(self):
            while 1:
                z = msvcrt.getch()
                if z == '\0' or z == '\xe0':    # functions keys
                    msvcrt.getch()
                else:
                    if z == '\r':
                        return '\n'
                    return z

    console = Console()

elif os.name == 'posix':
    import termios, sys, os
    class Console:
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

    console = Console()

    def cleanup_console():
        console.cleanup()

    console.setup()
    sys.exitfunc = cleanup_console      #terminal modes have to be restored on exit...

else:
    raise NotImplementedError, "Sorry no implementation for your platform (%s) available." % sys.platform


