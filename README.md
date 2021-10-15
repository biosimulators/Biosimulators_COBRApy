[![Latest release](https://img.shields.io/github/v/tag/biosimulators/Biosimulators_COBRApy)](https://github.com/biosimulations/Biosimulators_COBRApy/releases)
[![PyPI](https://img.shields.io/pypi/v/biosimulators_cobrapy)](https://pypi.org/project/biosimulators_cobrapy/)
[![CI status](https://github.com/biosimulators/Biosimulators_COBRApy/workflows/Continuous%20integration/badge.svg)](https://github.com/biosimulators/Biosimulators_COBRApy/actions?query=workflow%3A%22Continuous+integration%22)
[![Test coverage](https://codecov.io/gh/biosimulators/Biosimulators_COBRApy/branch/dev/graph/badge.svg)](https://codecov.io/gh/biosimulators/Biosimulators_COBRApy)
[![All Contributors](https://img.shields.io/github/all-contributors/biosimulators/Biosimulators_COBRApy/HEAD)](#contributors-)

# BioSimulators-COBRApy
BioSimulators-compliant command-line interface and Docker image for the [COBRApy](https://opencobra.github.io/cobrapy/) simulation program.

This command-line interface and Docker image enable users to use COBRApy to execute [COMBINE/OMEX archives](https://combinearchive.org/) that describe one or more simulation experiments (in [SED-ML format](https://sed-ml.org)) of one or more models (in [SBML format](http://sbml.org])).

A list of the algorithms and algorithm parameters supported by COBRApy is available at [BioSimulators](https://biosimulators.org/simulators/cobrapy).

A simple web application and web service for using COBRApy to execute COMBINE/OMEX archives is also available at [runBioSimulations](https://run.biosimulations.org).

## Installation

### Install Python package
```
pip install biosimulators-cobrapy
```

### Install Docker image
```
docker pull ghcr.io/biosimulators/cobrapy
```

## Usage

### SED-ML targets for simulation predictions

BioSimulators-COBRApy recognizes the following targets for simulation predictions:

- FBA (`KISAO_0000437`), parsimonious FBA (`KISAO_0000528`), geometric FBA (`KISAO_0000527`):
  - Objective: `fbc:objective/@value`
  - Reaction flux: `sbml:reaction/@flux`
  - Reaction reduced cost: `sbml:reaction/@reducedCost`
  - Species shadow price: `sbml:species/@shadowPrice`
- FVA (`KISAO_0000526`):
  - Minimum reaction flux: `sbml:reaction/@minFlux`
  - Maximum reaction flux: `sbml:reaction/@maxFlux`

Please see https://biosimulators.org/conventions/simulation-experiments for more information.

### Local usage
```
usage: biosimulators-cobrapy [-h] [-d] [-q] -i ARCHIVE [-o OUT_DIR] [-v]

BioSimulators-compliant command-line interface to the COBRApy simulation program <https://opencobra.github.io/cobrapy/>.

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           full application debug mode
  -q, --quiet           suppress all console output
  -i ARCHIVE, --archive ARCHIVE
                        Path to OMEX file which contains one or more SED-ML-
                        encoded simulation experiments
  -o OUT_DIR, --out-dir OUT_DIR
                        Directory to save outputs
  -v, --version         show program's version number and exit
```

### Usage through Docker container
The entrypoint to the Docker image supports the same command-line interface described above.

For example, the following command could be used to use the Docker image to execute the COMBINE/OMEX archive `./modeling-study.omex` and save its outputs to `./`.

```
docker run \
  --tty \
  --rm \
  --mount type=bind,source="$(pwd)",target=/root/in,readonly \
  --mount type=bind,source="$(pwd)",target=/root/out \
  ghcr.io/biosimulators/cobrapy:latest \
    -i /root/in/modeling-study.omex \
    -o /root/out
```

## Documentation
Documentation is available at https://docs.biosimulators.org/Biosimulators_COBRApy/.

## License
This package is released under the [MIT license](LICENSE).

## Development team
This package was developed by the [Center for Reproducible Biomedical Modeling](http://reproduciblebiomodels.org) and the [Karr Lab](https://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai with assistance from the contributors listed [here](CONTRIBUTORS.md).

## Questions and comments
Please contact the [BioSimulators Team](mailto:info@biosimulators.org) with any questions or comments.
