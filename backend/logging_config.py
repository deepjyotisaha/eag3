import logging
import argparse
import os
import sys

def setup_logging(log_level):
    """Configure logging with the specified level"""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    # Remove any existing handlers
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Set the root logger level
    logging.getLogger().setLevel(numeric_level)
    # Set the level for all existing loggers
    for logger_name in logging.root.manager.loggerDict:
        logging.getLogger(logger_name).setLevel(numeric_level)

    # Create a temporary logger for setup
    setup_logger = logging.getLogger(__name__)
    setup_logger.info(f"Logging level set to: {log_level}")

# Parse command line arguments
parser = argparse.ArgumentParser(description='Gmail Newsletter Digest Backend')
parser.add_argument('--log-level', 
                   default='INFO',
                   choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                   help='Set the logging level')
args = parser.parse_args()

# Setup logging
setup_logging(args.log_level) 