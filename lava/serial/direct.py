import fcntl
import errno

import serial as pyserial


class DirectSerialLine(pyserial.Serial):
    """
    A subclass of serial.Serial that implements exclusive locking on
    the serial device
    """

    def open(self):
        """
        Open the serial port and lock the file descriptor used by the serial
        line. Locking will be pefromed only if there is a file descriptor
        method to call.
        """
        super(DirectSerialLine, self).open()
        if not hasattr(self, "fileno"):
            return
        fd = self.fileno()
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as exc:
            if exc.errno == errno.EAGAIN:
                self.close()
                raise pyserial.SerialException(
                    "Unable to lock the serial line "
                    "(perhaps somene is using it)")
            else:
                raise
