"""
Service layer for Minerva application.

This module provides backward compatibility by importing the ServiceManager
and exposing it as MinervaService. The actual implementation has been moved
to the ServiceManager class for better modularity.
"""

from minerva.services.service_manager import ServiceManager, create_minerva_service

# For backward compatibility, expose ServiceManager as MinervaService
MinervaService = ServiceManager

# Export the factory function as well
__all__ = ["MinervaService", "create_minerva_service"]
