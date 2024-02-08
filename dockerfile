# Stage 1: Build stage to install dependencies
# Select a lighter PyTorch base image if possible, such as a minimal image that still meets your requirements
FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime as builder

# Set working directory
WORKDIR /app

# Install dependencies including libGL
# Combine update, install, and cleanup into a single RUN to reduce layer size
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy the poetry configuration files
COPY pyproject.toml poetry.lock* /app/

# Disable virtual environments creation by poetry
RUN poetry config virtualenvs.create false

# Install dependencies, skipping dev dependencies
# Note: No need to install torch and torchvision as they are already in the base image
RUN poetry install --no-dev

# Stage 2: Final stage to create a smaller image
# Use the same base image for compatibility
FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime

# Argument for setting the version at build time
ARG VERSION="unknown"

# Set working directory
WORKDIR /app

# Copy installed dependencies from builder stage
COPY --from=builder /app /app
COPY --from=builder /usr/local /usr/local
COPY --from=builder /opt /opt

# Install only the runtime dependencies needed for libGL, etc.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Copy the application files
COPY . /app

# Set the version as an environment variable
ENV LEISAIR_ML_VERSION=${VERSION}

# Default command - can be overridden when running the container
CMD ["poetry", "run", "api"]
