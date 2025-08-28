import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Determine log level based on DEBUG_MODE environment variable
    debug_mode = os.getenv("DEBUG_MODE", "False").lower() == "true"
    log_level = logging.DEBUG if debug_mode else logging.INFO

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to prevent duplicate logs in reloads (e.g., uvicorn --reload)
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add a file handler (rotating file handler for production readiness)
    log_file = os.path.join(os.path.dirname(__file__), 'app.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024 * 5, # 5 MB
        backupCount=5 # Keep 5 backup files
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Special handling for debug mode: more verbose logging for specific modules
    if debug_mode:
        # Example: Log HTTP request/response bodies in debug mode
        # This would require custom middleware or deeper integration for full request/response
        # For now, just setting a higher level for general logging.
        logging.getLogger("httpx").setLevel(logging.DEBUG) # For requests made by httpx (used by FastAPI/Groq)
        logging.getLogger("elasticsearch").setLevel(logging.DEBUG) # For Elasticsearch client
        logging.getLogger("neo4j").setLevel(logging.DEBUG) # For Neo4j client
        logger.info("DEBUG_MODE is ENABLED. Logging level set to DEBUG.")
    else:
        logger.info("DEBUG_MODE is DISABLED. Logging level set to INFO.")

# Call setup_logging when this module is imported
setup_logging()