"""
Batch and background indexing functionality for vector search.

This module provides batch processing and background updating capabilities
for vector embeddings to optimize performance for large vaults.
"""

import logging
import threading
import time
from typing import Dict, List, Optional
from queue import Queue, Empty
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IndexingTask:
    """Represents a single indexing task."""

    file_path: str
    content: str
    operation: str  # 'add', 'update', 'remove'
    priority: int = 1  # Lower numbers = higher priority


class BatchIndexer:
    """
    Manages batch and background indexing operations.

    This class provides functionality to queue indexing operations and process
    them in batches or in the background to optimize performance.
    """

    def __init__(
        self,
        config,
        batch_size: int = 10,
        batch_timeout: float = 30.0,
        background_enabled: bool = False,
    ):
        """
        Initialize the batch indexer.

        Args:
            config: Minerva configuration object
            batch_size: Number of files to process in each batch
            batch_timeout: Maximum time to wait before processing partial batch (seconds)
            background_enabled: Whether to process tasks in background thread
        """
        self.config = config
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.background_enabled = background_enabled

        # Task queue for batch processing
        self._task_queue: Queue[IndexingTask] = Queue()
        self._processing_enabled = True
        self._background_thread: Optional[threading.Thread] = None

        # Statistics
        self._stats = {
            "tasks_queued": 0,
            "tasks_processed": 0,
            "batches_processed": 0,
            "errors": 0,
        }

        if self.background_enabled:
            self._start_background_processing()

    def queue_task(
        self, file_path: str, content: str, operation: str = "update"
    ) -> None:
        """
        Queue a file for indexing.

        Args:
            file_path: Path to the file to be indexed
            content: Content of the file
            operation: Type of operation ('add', 'update', 'remove')
        """
        if not self._processing_enabled:
            logger.warning("Batch indexer is stopped, ignoring task for %s", file_path)
            return

        # Validate inputs for security
        self._validate_task_inputs(file_path, content, operation)

        task = IndexingTask(
            file_path=file_path,
            content=content,
            operation=operation,
        )

        self._task_queue.put(task)
        self._stats["tasks_queued"] += 1

        logger.debug("Queued %s task for file: %s", operation, file_path)

        # If background processing is disabled, check if we should process batch immediately
        if not self.background_enabled and self._task_queue.qsize() >= self.batch_size:
            self.process_batch()

    def _validate_task_inputs(
        self, file_path: str, content: str, operation: str
    ) -> None:
        """Validate task inputs for security."""
        from pathlib import Path

        # Validate operation type
        valid_operations = {"add", "update", "remove"}
        if operation not in valid_operations:
            raise ValueError(f"Invalid operation: {operation}")

        # Validate file path against path traversal
        try:
            path = Path(file_path).resolve()
            vault_path = Path(self.config.vault_path).resolve()
            if not path.is_relative_to(vault_path):
                raise ValueError(f"Path traversal detected: {file_path}")
        except (ValueError, OSError) as e:
            raise ValueError(f"Invalid file path: {file_path}") from e

        # Validate content size to prevent memory exhaustion
        MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB
        if len(content.encode("utf-8")) > MAX_CONTENT_SIZE:
            raise ValueError(f"Content too large for file: {file_path}")

        # Validate file extension
        if not file_path.endswith((".md", ".txt")):
            logger.warning("Unusual file extension for indexing: %s", file_path)

    def process_batch(self) -> int:
        """
        Process a batch of queued tasks immediately.

        Returns:
            int: Number of tasks processed
        """
        if not self.config.vector_search_enabled:
            logger.debug("Vector search disabled, skipping batch processing")
            self._stats["batches_processed"] += 1
            return 0

        tasks = self._collect_batch_tasks()

        # Always increment batches_processed counter, even for empty batches
        self._stats["batches_processed"] += 1

        if not tasks:
            return 0

        processed_count = self._process_tasks_batch(tasks)

        logger.info("Processed batch of %d tasks", processed_count)
        return processed_count

    def process_all_pending(self) -> int:
        """
        Process all pending tasks in the queue.

        Returns:
            int: Total number of tasks processed
        """
        total_processed = 0

        while not self._task_queue.empty():
            batch_processed = self.process_batch()
            total_processed += batch_processed

            if batch_processed == 0:
                break  # No more tasks to process

        return total_processed

    def get_queue_size(self) -> int:
        """Get the current number of tasks in the queue."""
        return self._task_queue.qsize()

    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics."""
        return self._stats.copy()

    def stop(self) -> None:
        """Stop the batch indexer and background processing."""
        self._processing_enabled = False

        if self._background_thread and self._background_thread.is_alive():
            self._background_thread.join(timeout=5.0)
            if self._background_thread.is_alive():
                logger.warning("Background thread did not stop within timeout")

    def _collect_batch_tasks(self) -> List[IndexingTask]:
        """Collect tasks for a batch."""
        tasks = []

        # Collect up to batch_size tasks
        for _ in range(self.batch_size):
            try:
                task = self._task_queue.get_nowait()
                tasks.append(task)
            except Empty:
                break

        return tasks

    def _initialize_components(self, tasks: List[IndexingTask]):
        """Initialize embedding provider and indexer components."""
        from minerva.vector.embeddings import SentenceTransformerProvider
        from minerva.vector.indexer import VectorIndexer

        embedding_provider = SentenceTransformerProvider(self.config.embedding_model)
        indexer = VectorIndexer(self.config.vector_db_path)

        if tasks:
            sample_embedding = embedding_provider.embed(tasks[0].content[:500])
            embedding_dim = (
                sample_embedding.shape[1]
                if sample_embedding.ndim == 2
                else len(sample_embedding)
            )
            indexer.initialize_schema(embedding_dim)

        return embedding_provider, indexer

    def _process_single_task(
        self, task: IndexingTask, embedding_provider, indexer
    ) -> bool:
        """Process a single indexing task."""
        try:
            if task.operation in ["add", "update"]:
                embedding = embedding_provider.embed(task.content)
                indexer.store_embedding(task.file_path, embedding, task.content)
            elif task.operation == "remove":
                indexer.remove_file(task.file_path)

            self._stats["tasks_processed"] += 1
            return True
        except Exception as e:
            logger.error("Failed to process task for %s: %s", task.file_path, e)
            self._stats["errors"] += 1
            return False

    def _process_tasks_batch(self, tasks: List[IndexingTask]) -> int:
        """
        Process a batch of indexing tasks.

        Args:
            tasks: List of tasks to process

        Returns:
            int: Number of successfully processed tasks
        """
        if not tasks:
            return 0

        indexer = None
        try:
            embedding_provider, indexer = self._initialize_components(tasks)
            processed_count = 0

            for task in tasks:
                if self._process_single_task(task, embedding_provider, indexer):
                    processed_count += 1

            return processed_count

        except ImportError:
            logger.debug(
                "Vector search dependencies not available, skipping batch processing"
            )
            return 0
        except Exception as e:
            logger.error("Batch processing failed: %s", e)
            self._stats["errors"] += len(tasks)
            return 0
        finally:
            if indexer:
                try:
                    indexer.close()
                except Exception as e:
                    logger.warning("Error closing indexer: %s", e)

    def _start_background_processing(self) -> None:
        """Start background thread for processing tasks."""
        self._background_thread = threading.Thread(
            target=self._background_worker, name="VectorIndexBatchWorker", daemon=True
        )
        self._background_thread.start()
        logger.info("Started background batch processing thread")

    def _background_worker(self) -> None:
        """Background worker that processes batches periodically."""
        last_batch_time = time.time()

        while self._processing_enabled:
            try:
                current_time = time.time()
                queue_size = self._task_queue.qsize()

                # Process batch if we have enough tasks or timeout reached
                should_process = queue_size >= self.batch_size or (
                    queue_size > 0
                    and (current_time - last_batch_time) >= self.batch_timeout
                )

                if should_process:
                    self.process_batch()
                    last_batch_time = current_time

                # Sleep briefly to avoid busy waiting
                time.sleep(1.0)

            except Exception as e:
                logger.error("Error in background batch worker: %s", e)
                time.sleep(5.0)  # Sleep longer on error

        logger.info("Background batch processing stopped")


# Global batch indexer instance with thread safety
_global_batch_indexer: Optional[BatchIndexer] = None
_indexer_lock = threading.Lock()


def get_batch_indexer(config, strategy: str = "immediate") -> Optional[BatchIndexer]:
    """
    Get or create a global batch indexer instance.

    Args:
        config: Minerva configuration
        strategy: Index update strategy ('immediate', 'batch', 'background')

    Returns:
        BatchIndexer instance or None if not needed for the strategy
    """
    global _global_batch_indexer

    if strategy == "immediate":
        return None

    # Thread-safe singleton pattern
    with _indexer_lock:
        if _global_batch_indexer is None:
            background_enabled = strategy == "background"
            batch_size = getattr(config, "batch_size", 10)
            batch_timeout = getattr(config, "batch_timeout", 30.0)

            _global_batch_indexer = BatchIndexer(
                config=config,
                batch_size=batch_size,
                batch_timeout=batch_timeout,
                background_enabled=background_enabled,
            )

            logger.info("Created global batch indexer with strategy: %s", strategy)
        else:
            # Update background_enabled if strategy changes
            requested_background = strategy == "background"
            if _global_batch_indexer.background_enabled != requested_background:
                logger.warning(
                    "Global batch indexer already exists with different background setting. "
                    "Current: %s, Requested: %s",
                    _global_batch_indexer.background_enabled,
                    requested_background,
                )

        return _global_batch_indexer


def stop_batch_indexer() -> None:
    """Stop the global batch indexer if it exists."""
    global _global_batch_indexer

    with _indexer_lock:
        if _global_batch_indexer:
            _global_batch_indexer.stop()
            _global_batch_indexer = None
            logger.info("Stopped global batch indexer")
