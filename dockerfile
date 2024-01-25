# Select a PyTorch base image with CUDA support that is compatible with your torch and torchvision versions
FROM pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime

# Set working directory
WORKDIR /app

# Install Poetry
RUN pip install poetry


# Check Poetry version
RUN poetry --version

# Copy the poetry configuration files
COPY pyproject.toml poetry.lock* /app/



# Disable virtual environments creation by poetry
RUN poetry config virtualenvs.create false

# Install project dependencies
# No need to install torch and torchvision as they are already in the base image
RUN poetry install --no-dev --no-root

# Copy the application files
COPY . /app

# Default command - can be overridden when running the container
CMD ["poetry", "run", "api"]
