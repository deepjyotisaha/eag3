import logging
import os
import sys

def setup_logging():
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        encoding='utf-8',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(log_dir, 'agent.log'), encoding='utf-8')
        ]
    )
    
    # Disable Flask's default logging
    logging.getLogger('werkzeug').disabled = True
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    
    # Configure console output encoding
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    
    logger.info("Logging configured successfully")
    return logger 