# Build image:
#   docker build --tag aa3641/biosimulations_cobrapy:0.17.1 --tag aa3641/biosimulations_cobrapy:latest .

# Base OS
FROM python:3.7

# Install requirements
RUN pip3 install -U pip \
    && pip3 install -U setuptools

# Copy code for command-line interface into image and install it
COPY . /root/Biosimulations_cobrapy
RUN pip3 install /root/Biosimulations_cobrapy

# Entrypoint
ENTRYPOINT ["cobrapy"]
CMD []
