from ._version import __version__  # noqa: F401
# :obj:`str`: version

from .core import exec_sedml_docs_in_combine_archive  # noqa: F401

import cobra


def get_simulator_version():
    """ Get the version of COBRApy

    Returns:
        :obj:`str`: version
    """
    return cobra.__version__
