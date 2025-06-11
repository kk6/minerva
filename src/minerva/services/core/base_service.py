"""
Base service class providing common functionality for all service modules.

This module defines the BaseService class that encapsulates shared dependencies
and common operations used across all service modules.
"""

import logging
from typing import Any

from minerva.config import MinervaConfig
from minerva.error_handler import MinervaErrorHandler
from minerva.frontmatter_manager import FrontmatterManager

logger = logging.getLogger(__name__)


class BaseService:
    """
    Base service class providing common functionality for all service modules.

    This class encapsulates shared dependencies like configuration, frontmatter
    management, and error handling that are used across different service modules.
    """

    def __init__(
        self,
        config: MinervaConfig,
        frontmatter_manager: FrontmatterManager,
    ):
        """
        Initialize BaseService with common dependencies.

        Args:
            config: Configuration instance containing paths and settings
            frontmatter_manager: Manager for frontmatter operations
        """
        self.config = config
        self.frontmatter_manager = frontmatter_manager
        self.error_handler = MinervaErrorHandler(vault_path=config.vault_path)

    def _log_operation_start(self, operation: str, **kwargs: Any) -> None:
        """
        Log the start of an operation with relevant parameters.

        Args:
            operation: Name of the operation being performed
            **kwargs: Additional parameters to log
        """
        logger.debug("Starting %s operation with params: %s", operation, kwargs)

    def _log_operation_success(self, operation: str, result: Any = None) -> None:
        """
        Log successful completion of an operation.

        Args:
            operation: Name of the operation that completed
            result: Optional result to include in log
        """
        if result is not None:
            logger.debug("Successfully completed %s operation: %s", operation, result)
        else:
            logger.debug("Successfully completed %s operation", operation)

    def _log_operation_error(self, operation: str, error: Exception) -> None:
        """
        Log an error during operation execution.

        Args:
            operation: Name of the operation that failed
            error: The exception that occurred
        """
        logger.error("Error in %s operation: %s", operation, error)
