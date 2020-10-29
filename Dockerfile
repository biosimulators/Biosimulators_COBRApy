# Build image:
#   docker build --tag biosimulators/cobrapy:0.17.1 --tag biosimulators/cobrapy:latest .
#
# Run image:
#   docker run \
#     --tty \
#     --rm \
#     --mount type=bind,source="$(pwd)"/tests/fixtures,target=/root/in,readonly \
#     --mount type=bind,source="$(pwd)"/tests/results,target=/root/out \
#     biosimulators/cobrapy:latest \
#       -i /root/in/BIOMD0000000297.omex \
#       -o /root/out

# Base OS
FROM ubuntu

# metadata
LABEL base_image="ubuntu:18.04"
LABEL version="0.17.1"
LABEL software="COBRApy"
LABEL software.version="0.17.1"
LABEL about.summary="Package for constraint-based modeling of metabolic networks"
LABEL about.home="https://opencobra.github.io/cobrapy/"
LABEL about.documentation="https://cobrapy.readthedocs.io/en/stable/"
LABEL about.license_file="https://github.com/opencobra/cobrapy/blob/devel/LICENSE"
LABEL about.license="SPDX:GPL-2.0"
LABEL about.tags="constraint-based modeling,flux balance analysis,systems biology,biochemical networks,SBML,SED-ML,COMBINE,OMEX,BioSimulators"
LABEL maintainer="BioSimulators Team <info@biosimulators.org>"

# Install requirements
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
    && pip3 install -U pip \
    && pip3 install -U setuptools \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_cobrapy
RUN pip3 install /root/Biosimulators_cobrapy

# Entrypoint
ENTRYPOINT ["cobrapy"]
CMD []
