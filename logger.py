"""
Contains a function that creates a custom logger with the given name.
"""

import logging


def custom_logger(name):
    """
    Create a custom logger with the given name.
    """
    # Define the format for the logs
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create a stream handler (logs to console)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Create a logger with the given name and set its level to DEBUG
    logger = logging.getLogger(name)

    # Remove any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # Set the level of the logger
    logger.setLevel(logging.DEBUG)

    # stop logger from propagating to parent
    logger.propagate = False

    # Add the stream handler to the logger
    logger.addHandler(handler)

    # for when we want to log to a file
    # file_handler = logging.FileHandler('logs.log')
    # file_handler.setFormatter(formatter)
    # logger.addHandler(file_handler)

    return logger
