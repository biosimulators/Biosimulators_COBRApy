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
