import logging
import argparse
import os
import sys
from typing import Optional

# Parse command line arguments first
parser = argparse.ArgumentParser(description='Gmail Newsletter Digest Backend')
parser.add_argument('--log-level', 
                   default='INFO',
                   choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                   help='Set the logging level')
args = parser.parse_args()

# Configure logging immediately
numeric_level = getattr(logging, args.log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f'Invalid log level: {args.log_level}')

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

class LoggerFactory:
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger with the configured level"""
        logger = logging.getLogger(name)
        logger.setLevel(numeric_level)
        return logger 