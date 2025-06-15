"""Vector search operations using DuckDB with VSS extension."""

import logging
from pathlib import Path
from typing import List, Tuple, Optional, Any
import numpy as np

# Import at module level for proper testing/mocking
try:
    import duckdb
except ImportError:
    duckdb = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class VectorSearcher:
    """Handles vector similarity search operations using DuckDB VSS."""

    def __init__(self, db_path: Path) -> None:
        """
        Initialize the vector searcher.

        Args:
            db_path: Path to the DuckDB database file
        """
        self.db_path = db_path
        self._connection: Any = None

    def _get_connection(self) -> Any:
        """Get or create a DuckDB connection."""
        if self._connection is None:
            if duckdb is None:
                raise ImportError(
                    "duckdb is required for VectorSearcher. "
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
            logger.debug("Installing VSS extension...")
            conn.execute("INSTALL vss")

            # Load the extension
            logger.debug("Loading VSS extension...")
            conn.execute("LOAD vss")
            logger.debug("VSS extension loaded successfully")
        except Exception as e:
            logger.error("Failed to load VSS extension: %s", e)
            raise RuntimeError(
                f"Could not load VSS extension: {e}. "
                "This may be due to network issues or DuckDB configuration problems."
            ) from e

    def search_similar(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        threshold: Optional[float] = None,
    ) -> List[Tuple[str, float]]:
        """
        Search for similar vectors using cosine similarity.

        Args:
            query_embedding: Query vector to search for
            k: Number of results to return
            threshold: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of (file_path, similarity_score) tuples ordered by similarity
        """
        conn = self._get_connection()

        try:
            # Convert numpy array to list for DuckDB and ensure FLOAT type
            query_vector = [float(x) for x in query_embedding.tolist()]

            # Build SQL query with optional threshold, specifying correct array dimension
            embedding_dim = len(query_vector)
            if threshold is not None:
                sql = f"""
                    SELECT file_path,
                           array_cosine_similarity(embedding, ?::FLOAT[{embedding_dim}]) as similarity
                    FROM vectors
                    WHERE array_cosine_similarity(embedding, ?::FLOAT[{embedding_dim}]) >= ?
                    ORDER BY similarity DESC
                    LIMIT ?
                """
                params = [query_vector, query_vector, threshold, k]
            else:
                sql = f"""
                    SELECT file_path,
                           array_cosine_similarity(embedding, ?::FLOAT[{embedding_dim}]) as similarity
                    FROM vectors
                    ORDER BY similarity DESC
                    LIMIT ?
                """
                params = [query_vector, k]

            result = conn.execute(sql, params).fetchall()

            # Convert to list of tuples with proper types
            search_results = [(str(row[0]), float(row[1])) for row in result]

            logger.debug(
                "Vector search found %d results (threshold: %s, k: %d)",
                len(search_results),
                threshold,
                k,
            )

            return search_results

        except Exception as e:
            logger.error("Vector search failed: %s", e)
            raise

    def find_similar_to_file(
        self, file_path: str, k: int = 10, exclude_self: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Find files similar to a given file using its stored embedding.

        Args:
            file_path: Path to the reference file
            k: Number of results to return
            exclude_self: Whether to exclude the reference file from results

        Returns:
            List of (file_path, similarity_score) tuples ordered by similarity
        """
        conn = self._get_connection()

        try:
            # First get the embedding for the reference file
            result = conn.execute(
                "SELECT embedding FROM vectors WHERE file_path = ?", [file_path]
            ).fetchone()

            if not result:
                logger.warning("No embedding found for file: %s", file_path)
                return []

            reference_embedding = np.array(result[0])

            # Search for similar files with correct array dimension
            reference_vector = [float(x) for x in reference_embedding.tolist()]
            embedding_dim = len(reference_vector)
            if exclude_self:
                sql = f"""
                    SELECT file_path,
                           array_cosine_similarity(embedding, ?::FLOAT[{embedding_dim}]) as similarity
                    FROM vectors
                    WHERE file_path != ?
                    ORDER BY similarity DESC
                    LIMIT ?
                """
                params = [reference_vector, file_path, k]
            else:
                sql = f"""
                    SELECT file_path,
                           array_cosine_similarity(embedding, ?::FLOAT[{embedding_dim}]) as similarity
                    FROM vectors
                    ORDER BY similarity DESC
                    LIMIT ?
                """
                params = [reference_vector, k]

            result = conn.execute(sql, params).fetchall()

            # Convert to list of tuples with proper types
            search_results = [(str(row[0]), float(row[1])) for row in result]

            logger.debug(
                "Found %d similar files to %s (exclude_self: %s)",
                len(search_results),
                file_path,
                exclude_self,
            )

            return search_results

        except Exception as e:
            logger.error("Similar file search failed for %s: %s", file_path, e)
            raise

    def get_indexed_files(self) -> List[str]:
        """
        Get list of all files that have been indexed.

        Returns:
            List of file paths that have embeddings in the database
        """
        conn = self._get_connection()

        try:
            result = conn.execute("SELECT DISTINCT file_path FROM vectors").fetchall()
            file_paths = [str(row[0]) for row in result]

            logger.debug("Found %d indexed files", len(file_paths))
            return file_paths

        except Exception as e:
            logger.error("Failed to get indexed files: %s", e)
            raise

    def is_file_indexed(self, file_path: str) -> bool:
        """
        Check if a specific file has been indexed.

        Args:
            file_path: Path to check

        Returns:
            True if the file has an embedding in the database
        """
        conn = self._get_connection()

        try:
            result = conn.execute(
                "SELECT COUNT(*) FROM vectors WHERE file_path = ?", [file_path]
            ).fetchone()

            return result[0] > 0 if result else False

        except Exception as e:
            logger.error("Failed to check if file is indexed: %s", e)
            raise

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug("Vector search connection closed")
