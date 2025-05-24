---
applyTo: 'src/**/*.py'
---

# Logging Patterns for Minerva

Please use the following patterns for logging in the Minerva project.

## Getting a Logger

Get a module-specific logger at the top of each module:

```python
import logging

# Get logger at the module level
logger = logging.getLogger(__name__)
```

## Using Different Log Levels

- **DEBUG**: Detailed information useful during development or debugging
  ```python
  logger.debug("Processing file: %s", file_path)
  ```

- **INFO**: Progress information for normal operations
  ```python
  logger.info("File written to %s", file_path)
  ```

- **WARNING**: Situations that might cause issues but allow processing to continue
  ```python
  logger.warning("Could not read file %s. Skipping.", sanitized_path)
  ```

- **ERROR**: Errors that prevent a function from being executed
  ```python
  logger.error("Error writing file: %s", e)
  ```

- **CRITICAL**: Serious situations that make the entire application unable to function
  ```python
  logger.critical("Database connection failed: %s", e)
  ```

## Important Rules

1. **Do Not Use f-strings**
   - Using f-strings causes string evaluation to occur even if the log level is disabled
   - Use the older string format style instead

   ```python
   # Correct example
   logger.debug("Found %d matching files for query '%s'", len(results), query)

   # Incorrect example - do not use
   logger.debug(f"Found {len(results)} matching files for query '{query}'")
   ```

2. **Logging Exception Information**

   ```python
   try:
       # Some operation
       process_file(file_path)
   except Exception as e:
       # Log with stack trace
       logger.exception("Error processing file %s: %s", file_path, e)
       # Or
       logger.error("Error processing file %s: %s", file_path, e)
       raise
   ```

3. **Handling Sensitive Information**
   - Do not log sensitive information such as passwords or API keys
   - Sanitize user input data before logging it
   ```python
   sanitized_path = str(file_path).replace('\n', '_').replace('\r', '_')
   logger.info("Processing file: %s", sanitized_path)
   ```
