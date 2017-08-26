import os
import json


class CompileCommand(object):

    __slots__ = ("directory", "file", "command")

    def __init__(self, directory, file, command):
        self.directory = directory
        self.file = file
        self.command = command

    @property
    def normfile(self):
        return os.path.normpath(os.path.join(self.directory, self.file))

    def __repr__(self):
        return '{{directory:"{}",file:"{}",command:"{}"}}'.format(
            self.directory, self.file, self.command)

    def __str__(self):
        return self.__repr__()

    def _as_tuple(self):
        return (self.directory, self.file, self.command)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._as_tuple() == other._as_tuple()
        raise NotImplemented()

    def __ne__(self, other):
        return not self == other

    class JSONEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, CompileCommand):
                return o.__repr__()
            else:
                return super().default(o)


class CompilationDatabaseInterface(object):
    @classmethod
    def probe_directory(cls, directory):
        """Probe compilation database for a specific directory.

        Should return an instance of the compilation database
        if the directory contains a database.
        If the directory does not contain a database,
        a FileNotFoundError should be raised (the default action if not
        overriden).
        """
        raise FileNotFoundError(
            "{}: compilation databases not found".format(directory))

    def get_compile_commands(self, filepath):
        """Get the compile commands for the given file.

        Return an iterable of CompileCommand.
        """
        raise NotImplemented()

    def get_all_files(self):
        """Return an iterable of path strings."""
        raise NotImplemented()

    def get_all_compile_commands(self):
        """Return an iterable of CompileCommand."""
        raise NotImplemented()
