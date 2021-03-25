# Build image:
#   docker build --tag biosimulators/cobrapy:0.20.0 --tag biosimulators/cobrapy:latest .
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
FROM python:3.7.9-slim-buster

ARG VERSION="0.1.7"
ARG SIMULATOR_VERSION="0.21.0"

# metadata
LABEL \
    org.opencontainers.image.title="COBRApy" \
    org.opencontainers.image.version="${SIMULATOR_VERSION}" \
    org.opencontainers.image.description="Package for constraint-based modeling of metabolic networks" \
    org.opencontainers.image.url="https://opencobra.github.io/cobrapy/" \
    org.opencontainers.image.documentation="https://cobrapy.readthedocs.io/" \
    org.opencontainers.image.source="https://github.com/biosimulators/biosimulators_cobrapy" \
    org.opencontainers.image.authors="BioSimulators Team <info@biosimulators.org>" \
    org.opencontainers.image.vendor="BioSimulators Team" \
    org.opencontainers.image.licenses="GPL-2.0" \
    \
    base_image="python:3.7.9-slim-buster" \
    version="${VERSION}" \
    software="COBRApy" \
    software.version="${SIMULATOR_VERSION}" \
    about.summary="Package for constraint-based modeling of metabolic networks" \
    about.home="https://opencobra.github.io/cobrapy/" \
    about.documentation="https://cobrapy.readthedocs.io/" \
    about.license_file="https://github.com/opencobra/cobrapy/blob/devel/LICENSE" \
    about.license="SPDX:GPL-2.0" \
    about.tags="constraint-based modeling,flux balance analysis,systems biology,biochemical networks,SBML,SED-ML,COMBINE,OMEX,BioSimulators" \
    maintainer="BioSimulators Team <info@biosimulators.org>"

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulators_COBRApy
RUN pip install /root/Biosimulators_COBRApy \
    && mkdir -p /.cache/cobrapy \
    && chmod ugo+rw /.cache/cobrapy \
    && rm -rf /root/Biosimulators_COBRApy
RUN pip install cobra==${SIMULATOR_VERSION}
ENV VERBOSE=0 \
    MPLBACKEND=PDF

# Entrypoint
ENTRYPOINT ["cobrapy"]
CMD []
