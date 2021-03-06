import os
from datetime import datetime as dt


class Logger:
    def __init__(self, dirpath=None, filename=None):
        self.datetimeformat = "%Y%m%d_%H%M%S"
        self.dt = dt

        if dirpath is not None:
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            self.dirpath = dirpath
        else:
            self.dirpath = os.getcwd()

        self.PID = "PID" + str(os.getpid())

        self.datetimeval = self.dt.now().strftime(self.datetimeformat)  # timestamp this logger.

        if filename is not None:
            self.filename = filename
        else:
            self.filename = "summary_" + self.PID + "_" + self.datetimeval + ".txt"

        self.file_path = os.path.join(self.dirpath, self.filename)

    def write_to_file(self, msg, toprint=True):
        # append message in a new line
        if toprint:
            print(msg)
        outmsg = self.dt.now().strftime(self.datetimeformat) + ": " + msg + "\n"
        with open(self.file_path, "a") as myfile:
            myfile.write(outmsg)

    def change_dirpath(self, dirpath):
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        self.dirpath = dirpath
        self.file_path = os.path.join(self.dirpath, self.filename)
