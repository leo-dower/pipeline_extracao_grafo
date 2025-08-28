import pytest
import logging
import os
from unittest.mock import patch, MagicMock

# We need to import logging_config directly to test its setup_logging function
# and ensure it's re-executed for each test to reset handlers.

@pytest.fixture(autouse=True)
def reset_logging_handlers():
    """Resets logging handlers before each test to prevent interference."""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    yield
    # Clean up after test if needed, though autouse fixture handles most of it

def test_setup_logging_default_info_level(caplog):
    # Ensure DEBUG_MODE is not set for this test
    with patch.dict(os.environ, {}, clear=True):
        # Import and call setup_logging within the test to ensure fresh setup
        import logging_config
        logging_config.setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
        assert any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers)
        assert any(isinstance(h, logging.handlers.RotatingFileHandler) for h in root_logger.handlers)
        
        root_logger.info("Test info message")
        root_logger.debug("Test debug message") # Should not be captured by INFO level
        
        assert "Test info message" in caplog.text
        assert "Test debug message" not in caplog.text
        assert "DEBUG_MODE is DISABLED. Logging level set to INFO." in caplog.text

def test_setup_logging_debug_mode_enabled(caplog):
    # Set DEBUG_MODE to True for this test
    with patch.dict(os.environ, {"DEBUG_MODE": "True"}):
        # Import and call setup_logging within the test to ensure fresh setup
        import logging_config
        logging_config.setup_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
        
        root_logger.info("Test info message in debug")
        root_logger.debug("Test debug message in debug") # Should be captured by DEBUG level
        
        assert "Test info message in debug" in caplog.text
        assert "Test debug message in debug" in caplog.text
        assert "DEBUG_MODE is ENABLED. Logging level set to DEBUG." in caplog.text

def test_setup_logging_file_handler_config():
    with patch.dict(os.environ, {}, clear=True):
        import logging_config
        logging_config.setup_logging()

        root_logger = logging.getLogger()
        file_handler = next(h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler))
        
        assert file_handler.baseFilename.endswith(os.path.join('plataforma_juridica', 'app.log'))
        assert file_handler.maxBytes == 1024 * 1024 * 5
        assert file_handler.backupCount == 5

def test_setup_logging_specific_module_debug_levels():
    with patch.dict(os.environ, {"DEBUG_MODE": "True"}):
        import logging_config
        logging_config.setup_logging()

        assert logging.getLogger("httpx").level == logging.DEBUG
        assert logging.getLogger("elasticsearch").level == logging.DEBUG
        assert logging.getLogger("neo4j").level == logging.DEBUG
