# Build image:
#   docker build --tag crbm/biosimulations_cobrapy:0.17.1 --tag crbm/biosimulations_cobrapy:latest .

# Base OS
FROM ubuntu

# Install requirements
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
    && pip3 install -U pip \
    && pip3 install -U setuptools \
    && pip3 install biosimulations_utils \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulations_cobrapy
RUN pip3 install /root/Biosimulations_cobrapy

# Entrypoint
ENTRYPOINT ["cobrapy"]
CMD []
