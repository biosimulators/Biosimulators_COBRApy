# Contributing to `BioSimulators-COBRApy`

We enthusiastically welcome contributions to BioSimulators-COBRApy!

## Coordinating contributions

Before getting started, please contact the lead developers at [info@biosimulators.org](mailto:info@biosimulators.org) to coordinate your planned contributions with other ongoing efforts. Please also use GitHub issues to announce your plans to the community so that other developers can provide input into your plans and coordinate their own work.

## Repository organization

The repository follows standard Python conventions:

* `README.md`: Overview of the repository
* `biosimulators_cobrapy/`: Python code for a BioSimulators-compliant command-line interface to COBRApy
* `tests/`: unit tests for the command-line interface
* `setup.py`: installation script for the command-line interface
* `setup.cfg`: configuration for the installation of the command-line interface
* `requirements.txt`: dependencies for the command-line interface
* `requirements.optional.txt`: optional dependencies for the command-line interface
* `MANIFEST.in`: a list of files to include in the package for the command-line interface
* `LICENSE`: License
* `CONTRIBUTING.md`: Guide to contributing to BioSimulators-COBRApy (this document)
* `CODE_OF_CONDUCT.md`: Code of conduct for developers of BioSimulators-COBRApy

## Coding convention

BioSimulators-COBRApy follows standard Python style conventions:

* Class names: `UpperCamelCase`
* Function names: `lower_snake_case`
* Variable names: `lower_snake_case`

## Testing and continuous integration

We strive to have complete test coverage for BioSimulators-COBRApy.

The unit tests for BioSimulators-COBRApy are located in the `tests`  directory. The tests can be executed by running the following command:
```
pip install pytest
python -m pytest tests
```

The tests are also automatically evaluated upon each push to GitHub.

The coverage of the tests can be evaluated by running the following commands and then opening `/path/to/biosimulators_cobrapy/htmlcov/index.html` with your browser.
```
pip install pytest pytest-cov coverage
python -m pytest tests --cov biosimulators_cobrapy
coverage html
```

## Documentation convention

BioSimulators-COBRApy is documented using [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html) and the [napoleon Sphinx plugin](https://www.sphinx-doc.org/en/master/usage/extensions/napoleon.html).

## Submitting changes   

Please use GitHub pull requests to submit changes. Each request should include a brief description of the new and/or modified features.

## Releasing and deploying new versions

Contact the [BioSimulators Team](mailto:info@biosimulators.org) to request release and deployment of new changes. 

## Reporting issues

Please use [GitHub issues](https://github.com/biosimulators/Biosimulators_COBRApy/issues) to report any issues to the development community.
    
## Getting help

Please use [GitHub issues](https://github.com/biosimulators/Biosimulators_COBRApy/issues) to post questions or contact the lead developers at [info@biosimulators.org](mailto:info@biosimulators.org).
