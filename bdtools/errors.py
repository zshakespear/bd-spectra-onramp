"""Plain-language errors for students.

Every error that bdtools raises on purpose is a ``BDToolsError``. When
``bdtools.setup_notebook()`` has been run, these errors are shown as a short
message (no long traceback), because the traceback is almost never useful to
a student -- the message says what to fix.
"""


class BDToolsError(Exception):
    """An error with a message written for a student, not a programmer."""


class MissingDataError(BDToolsError):
    """A data file the notebook needs has not been built or supplied yet."""


class UnitError(BDToolsError):
    """A spectrum's units are missing or not ones bdtools understands."""
