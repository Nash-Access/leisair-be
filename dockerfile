# Select a PyTorch base image with CUDA support that is compatible with your torch and torchvision versions
FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime

# Argument for setting the version at build time
ARG VERSION="unknown"

# Set working directory
WORKDIR /app

# Install dependencies including libGL
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

# Install Poetry
RUN pip install poetry

# Check Poetry version
RUN poetry --version

# Copy the poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Disable virtual environments creation by poetry
RUN poetry config virtualenvs.create false

# No need to install torch and torchvision as they are already in the base image
RUN poetry install --no-dev

# Copy the application files
COPY . /app

# Set the version as an environment variable
ENV LEISAIR_ML_VERSION=${VERSION}

# Default command - can be overridden when running the container
CMD ["poetry", "run", "api"]
