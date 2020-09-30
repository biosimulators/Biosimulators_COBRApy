""" BioSimulators-compliant command-line interface to the `COBRApy <https://opencobra.github.io/cobrapy>`_ simulation program.

:Author: Azraf Anwar <aa3641@columbia.edu>
:Date: 2020-06-01
:Copyright: 2020, Center for Reproducible Biomedical Modeling
:License: MIT
"""

from .core import exec_combine_archive
import Biosimulators_cobrapy
import cement


class BaseController(cement.Controller):
    """ Base controller for command line application """

    class Meta:
        label = 'base'
        description = ("BioSimulators-compliant command-line interface to the "
                       "COBRApy simulation program <https://opencobra.github.io/cobrapy>.")
        help = "cobrapy"
        arguments = [
            (['-i', '--archive'], dict(type=str,
                                       required=True,
                                       help='Path to OMEX file which contains one or more SED-ML-encoded simulation experiments')),
            (['-o', '--out-dir'], dict(type=str,
                                       default='.',
                                       help='Directory to save outputs')),
            (['-v', '--version'], dict(action='version',
                                       version=Biosimulators_cobrapy.__version__)),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        exec_combine_archive(args.archive, args.out_dir)


class App(cement.App):
    """ Command line application """
    class Meta:
        label = 'cobrapy'
        base_controller = 'base'
        handlers = [
            BaseController,
        ]


def main():
    with App() as app:
        app.run()
