---
applyTo: 'src/**/*.py'
---

# Dependency Injection Patterns for Minerva

## Overview

The Minerva project uses dependency injection patterns to improve testability, maintainability, and extensibility. This document outlines the established patterns and best practices for implementing dependency injection in the codebase.

## Architecture Overview

### Service Layer Pattern

The core business logic is encapsulated in service classes that receive their dependencies through constructor injection:

```python
class MinervaService:
    """Main service class for note operations with dependency injection."""
    
    def __init__(
        self,
        config: MinervaConfig,
        frontmatter_manager: FrontmatterManager,
    ):
        """Initialize service with injected dependencies."""
        self.config = config
        self.frontmatter_manager = frontmatter_manager
```

### Configuration Injection

Configuration is provided through a dedicated configuration class:

```python
@dataclass
class MinervaConfig:
    """Configuration dataclass for dependency injection."""
    vault_path: Path
    default_note_dir: str
    default_author: str
    encoding: str = "utf-8"
    
    @classmethod
    def from_env(cls) -> "MinervaConfig":
        """Create configuration from environment variables."""
        # Implementation...
```

## Factory Pattern

Use factory functions to create properly configured service instances:

```python
def create_minerva_service() -> MinervaService:
    """
    Create a MinervaService instance with default configuration.
    
    This factory function provides a convenient way to create a fully
    configured MinervaService instance using environment variables.
    """
    config = MinervaConfig.from_env()
    frontmatter_manager = FrontmatterManager(config.default_author)
    
    return MinervaService(config, frontmatter_manager)
```

## Backward Compatibility Pattern

Maintain existing function-based APIs as wrappers around the service layer:

```python
# Global service instance for backward compatibility
_service_instance = None

def _get_service() -> "MinervaService":
    """Get or create the global service instance with lazy initialization."""
    global _service_instance
    if _service_instance is None:
        from minerva.service import create_minerva_service
        _service_instance = create_minerva_service()
    return _service_instance

def create_note(
    text: str,
    filename: str,
    author: str | None = None,
    default_path: str = DEFAULT_NOTE_DIR,
) -> Path:
    """
    Create a new note in the Obsidian vault.
    
    This is a compatibility wrapper around the service-based implementation.
    """
    service = _get_service()
    return service.create_note(text, filename, author, default_path)
```

## Testing Patterns

### Service Instance Injection for Testing

Provide mechanisms to inject custom service instances for testing:

```python
def set_service_instance(service: "MinervaService") -> None:
    """
    Set a custom service instance for testing.
    
    This allows dependency injection for testing by replacing
    the default service instance with a custom one.
    """
    global _service_instance
    _service_instance = service

def get_service_instance() -> "MinervaService":
    """Get the current service instance for testing access."""
    return _get_service()
```

### Test Setup Example

```python
class TestNoteOperations:
    """Test note operations with dependency injection."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MinervaConfig(
            vault_path=Path("/test/vault"),
            default_note_dir="test_notes",
            default_author="Test Author",
        )
    
    @pytest.fixture
    def frontmatter_manager(self):
        """Create mock frontmatter manager."""
        return Mock(spec=FrontmatterManager)
    
    @pytest.fixture
    def service(self, config, frontmatter_manager):
        """Create service instance for testing."""
        return MinervaService(config, frontmatter_manager)
    
    def test_create_note(self, service):
        """Test note creation using service."""
        # Test implementation using injected service
        pass
```

### Integration Testing with Real Dependencies

```python
class TestServiceIntegration:
    """Integration tests with real file operations."""
    
    def setup_method(self):
        """Set up real test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = Path(self.temp_dir) / "test_vault"
        self.vault_path.mkdir(parents=True)
        
        self.config = MinervaConfig(
            vault_path=self.vault_path,
            default_note_dir="notes",
            default_author="Test Author",
        )
        
        self.frontmatter_manager = FrontmatterManager("Test Author")
        self.service = MinervaService(self.config, self.frontmatter_manager)
```

## Best Practices

### 1. Constructor Injection

Always use constructor injection for required dependencies:

```python
class ServiceClass:
    def __init__(self, required_dependency: DependencyType):
        self.dependency = required_dependency  # Required dependency
```

### 2. Interface Segregation

Depend on interfaces/protocols rather than concrete implementations when possible:

```python
from typing import Protocol

class FileHandler(Protocol):
    """Protocol for file handling operations."""
    def read_file(self, path: Path) -> str: ...
    def write_file(self, path: Path, content: str) -> None: ...

class Service:
    def __init__(self, file_handler: FileHandler):
        self.file_handler = file_handler
```

### 3. Configuration as Dependency

Treat configuration as a first-class dependency:

```python
# Good: Configuration injected as dependency
class Service:
    def __init__(self, config: AppConfig):
        self.config = config

# Avoid: Direct access to global configuration
class Service:
    def __init__(self):
        self.vault_path = VAULT_PATH  # Global dependency
```

### 4. Factory Functions for Complex Setup

Use factory functions for complex dependency setup:

```python
def create_production_service() -> MinervaService:
    """Create service with production configuration."""
    config = MinervaConfig.from_env()
    frontmatter_manager = FrontmatterManager(config.default_author)
    return MinervaService(config, frontmatter_manager)

def create_test_service(vault_path: Path) -> MinervaService:
    """Create service with test configuration."""
    config = MinervaConfig(
        vault_path=vault_path,
        default_note_dir="test_notes",
        default_author="Test Author",
    )
    frontmatter_manager = FrontmatterManager("Test Author")
    return MinervaService(config, frontmatter_manager)
```

### 5. Lazy Initialization Pattern

Use lazy initialization for backward compatibility:

```python
_service_instance = None

def get_service() -> ServiceType:
    """Lazy initialization of service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = create_service()
    return _service_instance
```

## Migration Strategy

### From Function-Based to Service-Based

1. **Create Service Class**: Encapsulate related functions in a service class
2. **Extract Dependencies**: Identify and extract dependencies (config, external services)
3. **Create Factory**: Provide factory function for default configuration
4. **Maintain Wrappers**: Keep existing functions as thin wrappers
5. **Update Tests**: Add service-level tests while maintaining existing function tests

### Example Migration

```python
# Before: Function-based
def create_note(text: str, filename: str) -> Path:
    # Direct dependency on globals
    full_path = VAULT_PATH / DEFAULT_NOTE_DIR / f"{filename}.md"
    # ... implementation

# After: Service-based with wrapper
class MinervaService:
    def __init__(self, config: MinervaConfig):
        self.config = config
    
    def create_note(self, text: str, filename: str) -> Path:
        # Uses injected configuration
        full_path = self.config.vault_path / self.config.default_note_dir / f"{filename}.md"
        # ... implementation

# Compatibility wrapper
def create_note(text: str, filename: str) -> Path:
    """Backward compatibility wrapper."""
    service = get_service()
    return service.create_note(text, filename)
```

## Error Handling with Dependency Injection

Service classes should maintain the same error handling patterns as function-based code:

```python
class MinervaService:
    def create_note(self, text: str, filename: str) -> Path:
        """Create note with proper error handling."""
        try:
            # Use injected dependencies
            return self._perform_create_operation(text, filename)
        except PermissionError as e:
            logger.error("Permission denied creating note %s: %s", filename, e)
            raise
        except Exception as e:
            logger.error("Unexpected error creating note %s: %s", filename, e)
            raise RuntimeError(f"Failed to create note {filename}") from e
```

## Common Anti-Patterns to Avoid

### 1. Service Locator Pattern

```python
# Avoid: Service locator
class Service:
    def __init__(self):
        self.dependency = ServiceLocator.get("dependency")  # Anti-pattern

# Prefer: Constructor injection
class Service:
    def __init__(self, dependency: DependencyType):
        self.dependency = dependency
```

### 2. Hidden Dependencies

```python
# Avoid: Hidden global dependencies
class Service:
    def method(self):
        return global_config.vault_path  # Hidden dependency

# Prefer: Explicit dependencies
class Service:
    def __init__(self, config: Config):
        self.config = config
    
    def method(self):
        return self.config.vault_path
```

### 3. Circular Dependencies

Design services to avoid circular dependencies. Use events, callbacks, or interface segregation to break cycles.

## Summary

Dependency injection in Minerva provides:

- **Improved Testability**: Easy to mock dependencies in tests
- **Better Separation of Concerns**: Clear boundaries between components
- **Enhanced Maintainability**: Changes to dependencies don't ripple through the codebase
- **Backward Compatibility**: Existing APIs continue to work during migration
- **Flexibility**: Easy to swap implementations for different environments