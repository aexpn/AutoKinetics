# Use Ubuntu 24.04 as base image
FROM ubuntu:24.04

# Set noninteractive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        python3 \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        python3-dev \
        cython \
        git \
        && rm -rf /var/lib/apt/lists/*

# Set workdir
WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies (if any)
RUN pip3 install --upgrade pip && \
    if [ -f AutoKinetics/setup.py ]; then pip3 install ./AutoKinetics; fi

# Build C++ code
WORKDIR /app/AutoKinetics/cpp
RUN cmake . && make

# Set default workdir for running
WORKDIR /app/AutoKinetics/python

# Default command (can be changed as needed)
CMD ["python3", "backend_main.py"]
