"""Vector indexing using DuckDB with VSS extension."""

import logging
from pathlib import Path
from typing import List, Tuple, Any
import numpy as np

# Import at module level for proper testing/mocking
try:
    import duckdb
except ImportError:
    duckdb = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class VectorIndexer:
    """Manages vector indexing operations using DuckDB with VSS extension."""

    def __init__(self, db_path: Path) -> None:
        """
        Initialize the vector indexer.

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = db_path
        self._connection: Any = None
        self._initialized = False

    def _get_connection(self) -> Any:
        """Get or create a DuckDB connection."""
        if self._connection is None:
            if duckdb is None:
                raise ImportError(
                    "duckdb is required for VectorIndexer. "
                    "Install it with: pip install duckdb"
                )

            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            self._connection = duckdb.connect(str(self.db_path))
            self._setup_home_directory()
            self._setup_vss_extension()
        return self._connection

    def _setup_home_directory(self) -> None:
        """Set up home directory for DuckDB extensions."""
        import os

        conn = self._connection
        try:
            # Get home directory, fallback to current user's home
            home_dir = os.path.expanduser("~")
            if not home_dir or home_dir == "~":
                # Fallback to a safe directory
                home_dir = str(self.db_path.parent)

            # Set home directory for DuckDB
            conn.execute(f"SET home_directory='{home_dir}'")
            logger.debug("DuckDB home directory set to: %s", home_dir)
        except Exception as e:
            logger.warning("Failed to set DuckDB home directory: %s", e)
            # Continue anyway as this might not be critical

    def _setup_vss_extension(self) -> None:
        """Install and load the VSS extension."""
        conn = self._connection
        try:
            # Check if VSS extension is already loaded
            try:
                conn.execute(
                    "SELECT * FROM duckdb_extensions() WHERE extension_name = 'vss' AND loaded = true"
                )
                result = conn.fetchone()
                if result:
                    logger.debug("VSS extension already loaded")
                    return
            except Exception:
                pass  # Extension might not exist yet

            # Install VSS extension if not already installed
            logger.info("Installing VSS extension...")
            conn.execute("INSTALL vss")

            # Load the extension
            logger.info("Loading VSS extension...")
            conn.execute("LOAD vss")
            logger.info("VSS extension loaded successfully")
        except Exception as e:
            logger.error("Failed to load VSS extension: %s", e)
            raise RuntimeError(
                f"Could not load VSS extension: {e}. "
                "This may be due to network issues or DuckDB configuration problems."
            ) from e

    def initialize_schema(self, embedding_dim: int) -> None:
        """
        Initialize the database schema for vector storage.

        Args:
            embedding_dim: Dimension of the embedding vectors
        """
        conn = self._get_connection()

        # Check if tables already exist and validate dimensions
        table_exists = False
        try:
            # First, check if the vectors table exists
            result = conn.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_name = 'vectors'
            """).fetchone()

            if result:
                table_exists = True
                # Try to get a sample embedding to check dimensions
                try:
                    sample = conn.execute(
                        "SELECT embedding FROM vectors LIMIT 1"
                    ).fetchone()
                    if sample and sample[0]:
                        existing_dim = len(sample[0])
                        if existing_dim != embedding_dim:
                            logger.warning(
                                "Existing vector table has dimension %d, but new embeddings have dimension %d. "
                                "Recreating table with dimension %d",
                                existing_dim,
                                embedding_dim,
                                embedding_dim,
                            )
                            # Drop existing tables to recreate with correct dimensions
                            conn.execute("DROP TABLE IF EXISTS vectors")
                            conn.execute("DROP TABLE IF EXISTS indexed_files")
                            conn.execute("DROP SEQUENCE IF EXISTS vectors_id_seq")
                            table_exists = False
                        else:
                            logger.info(
                                "Vector table already exists with correct dimension %d",
                                embedding_dim,
                            )
                            self._initialized = True
                            return
                except Exception:
                    # Table exists but is empty or corrupted, continue with creation
                    logger.debug("Vector table exists but cannot validate dimensions")
        except Exception as e:
            logger.debug("Could not check existing schema: %s", e)
            # Continue with creation

        if table_exists:
            logger.info("Vector table exists, assuming correct schema")
            self._initialized = True
            return

        # Create the main vectors table
        conn.execute(f"""
            CREATE SEQUENCE IF NOT EXISTS vectors_id_seq;
            CREATE TABLE IF NOT EXISTS vectors (
                id INTEGER PRIMARY KEY DEFAULT nextval('vectors_id_seq'),
                file_path TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                embedding FLOAT[{embedding_dim}] NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create metadata table for tracking indexed files
        conn.execute("""
            CREATE TABLE IF NOT EXISTS indexed_files (
                file_path TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                embedding_count INTEGER DEFAULT 0
            )
        """)

        self._initialized = True
        logger.info(
            "Vector database schema initialized with embedding dimension %d",
            embedding_dim,
        )

    def create_hnsw_index(self, index_name: str = "vectors_hnsw_idx") -> None:
        """
        Create HNSW index for fast similarity search.

        Args:
            index_name: Name for the HNSW index
        """
        if not self._initialized:
            raise RuntimeError(
                "Database schema not initialized. Call initialize_schema() first."
            )

        conn = self._get_connection()

        try:
            # Drop existing index if it exists
            conn.execute(f"DROP INDEX IF EXISTS {index_name}")

            # Create HNSW index
            conn.execute(f"""
                CREATE INDEX {index_name} ON vectors
                USING HNSW (embedding)
                WITH (metric = 'cosine')
            """)

            logger.info("HNSW index '%s' created successfully", index_name)
        except Exception as e:
            logger.error("Failed to create HNSW index: %s", e)
            raise

    def add_vectors(
        self, file_path: str, content_hash: str, embeddings: np.ndarray
    ) -> int:
        """
        Add vectors to the index.

        Args:
            file_path: Path to the source file
            content_hash: Hash of the file content
            embeddings: Array of embeddings to add

        Returns:
            Number of vectors added
        """
        if not self._initialized:
            raise RuntimeError(
                "Database schema not initialized. Call initialize_schema() first."
            )

        conn = self._get_connection()

        # Ensure embeddings is 2D
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        # Remove existing vectors for this file
        conn.execute("DELETE FROM vectors WHERE file_path = ?", (file_path,))

        # Insert new vectors
        for embedding in embeddings:
            conn.execute(
                "INSERT INTO vectors (file_path, content_hash, embedding) VALUES (?, ?, ?)",
                (file_path, content_hash, embedding.tolist()),
            )

        # Update indexed files tracking
        conn.execute(
            """
            INSERT OR REPLACE INTO indexed_files (file_path, content_hash, embedding_count)
            VALUES (?, ?, ?)
        """,
            (file_path, content_hash, len(embeddings)),
        )

        logger.debug("Added %d vectors for file: %s", len(embeddings), file_path)
        return len(embeddings)

    def remove_vectors(self, file_path: str) -> int:
        """
        Remove vectors for a specific file.

        Args:
            file_path: Path to the source file

        Returns:
            Number of vectors removed
        """
        if not self._initialized:
            raise RuntimeError(
                "Database schema not initialized. Call initialize_schema() first."
            )

        conn = self._get_connection()

        # Count vectors to be removed
        result = conn.execute(
            "SELECT COUNT(*) FROM vectors WHERE file_path = ?", (file_path,)
        ).fetchone()
        count = result[0] if result else 0

        # Remove vectors
        conn.execute("DELETE FROM vectors WHERE file_path = ?", (file_path,))

        # Remove from indexed files tracking
        conn.execute("DELETE FROM indexed_files WHERE file_path = ?", (file_path,))

        logger.debug("Removed %d vectors for file: %s", count, file_path)
        return count

    def get_indexed_files(self) -> List[Tuple[str, str]]:
        """
        Get list of indexed files with their content hashes.

        Returns:
            List of (file_path, content_hash) tuples
        """
        if not self._initialized:
            return []

        conn = self._get_connection()
        result = conn.execute(
            "SELECT file_path, content_hash FROM indexed_files"
        ).fetchall()
        return [(row[0], row[1]) for row in result]

    def get_vector_count(self) -> int:
        """
        Get total number of vectors in the index.

        Returns:
            Total number of vectors
        """
        if not self._initialized:
            return 0

        conn = self._get_connection()
        result = conn.execute("SELECT COUNT(*) FROM vectors").fetchone()
        return result[0] if result else 0

    def is_file_indexed(self, file_path: str) -> bool:
        """
        Check if a specific file has been indexed.

        Args:
            file_path: Path to check

        Returns:
            True if the file has an embedding in the database
        """
        if not self._initialized:
            return False

        conn = self._get_connection()

        try:
            result = conn.execute(
                "SELECT COUNT(*) FROM indexed_files WHERE file_path = ?", [file_path]
            ).fetchone()

            return result[0] > 0 if result else False

        except Exception as e:
            logger.error("Failed to check if file is indexed: %s", e)
            return False

    def store_embedding(
        self, file_path: str, embedding: np.ndarray, content: str
    ) -> None:
        """
        Store a single embedding for a file.

        This is a convenience method that wraps add_vectors for single embeddings.

        Args:
            file_path: Path to the source file
            embedding: Single embedding vector
            content: File content for hash calculation
        """
        import hashlib

        # Calculate content hash
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Use add_vectors to store the embedding
        self.add_vectors(file_path, content_hash, embedding)

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug("Database connection closed")
