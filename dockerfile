# Select a PyTorch base image with CUDA support that is compatible with your torch and torchvision versions
FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime

# Argument for setting the version at build time
ARG VERSION="unknown"

# Set working directory
WORKDIR /app

# Install dependencies including libGL and cleanup in one layer to reduce image size
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/* && \
    pip install poetry && \
    poetry config virtualenvs.create false

# Copy the poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Install Python dependencies, excluding dev dependencies and already available packages
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy the application files
COPY . /app

# Set the version as an environment variable
ENV LEISAIR_ML_VERSION=${VERSION}

# Default command - can be overridden when running the container
CMD ["poetry", "run", "api"]
