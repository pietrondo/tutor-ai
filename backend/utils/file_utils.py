"""
Async file utilities for optimized file I/O operations.
"""

import os
import aiofiles
import asyncio
from pathlib import Path
from typing import Optional, List, AsyncGenerator
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AsyncFileOperations:
    """Async file operations with performance optimizations."""

    @staticmethod
    async def read_file(file_path: str, chunk_size: int = 8192) -> bytes:
        """
        Asynchronously read a file in chunks for memory efficiency.

        Args:
            file_path: Path to the file
            chunk_size: Size of each chunk to read

        Returns:
            File content as bytes
        """
        try:
            async with aiofiles.open(file_path, 'rb') as file:
                content = bytearray()
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    content.extend(chunk)
                return bytes(content)
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    @staticmethod
    async def write_file(file_path: str, content: bytes, chunk_size: int = 8192) -> int:
        """
        Asynchronously write content to a file in chunks.

        Args:
            file_path: Path to write to
            content: Content to write
            chunk_size: Size of each chunk to write

        Returns:
            Number of bytes written
        """
        try:
            # Ensure parent directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(file_path, 'wb') as file:
                bytes_written = 0
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    await file.write(chunk)
                    bytes_written += len(chunk)
                return bytes_written
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            raise

    @staticmethod
    async def copy_file(src_path: str, dst_path: str, chunk_size: int = 8192) -> int:
        """
        Asynchronously copy a file with progress tracking.

        Args:
            src_path: Source file path
            dst_path: Destination file path
            chunk_size: Size of each chunk to copy

        Returns:
            Number of bytes copied
        """
        try:
            # Ensure destination directory exists
            Path(dst_path).parent.mkdir(parents=True, exist_ok=True)

            bytes_copied = 0
            async with aiofiles.open(src_path, 'rb') as src_file:
                async with aiofiles.open(dst_path, 'wb') as dst_file:
                    while True:
                        chunk = await src_file.read(chunk_size)
                        if not chunk:
                            break
                        await dst_file.write(chunk)
                        bytes_copied += len(chunk)
            return bytes_copied
        except Exception as e:
            logger.error(f"Error copying file from {src_path} to {dst_path}: {e}")
            raise

    @staticmethod
    async def file_exists(file_path: str) -> bool:
        """
        Asynchronously check if a file exists.

        Args:
            file_path: Path to check

        Returns:
            True if file exists
        """
        return await asyncio.get_event_loop().run_in_executor(
            None, os.path.exists, file_path
        )

    @staticmethod
    async def get_file_size(file_path: str) -> int:
        """
        Asynchronously get file size.

        Args:
            file_path: Path to file

        Returns:
            File size in bytes
        """
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, os.path.getsize, file_path
            )
        except OSError as e:
            logger.error(f"Error getting file size for {file_path}: {e}")
            raise

    @staticmethod
    async def delete_file(file_path: str) -> bool:
        """
        Asynchronously delete a file.

        Args:
            file_path: Path to delete

        Returns:
            True if successfully deleted
        """
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, os.remove, file_path
            )
            return True
        except OSError as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False

class FileCache:
    """Simple in-memory file cache with TTL."""

    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = {}
        self.timestamps = {}

    def _evict_if_needed(self):
        """Remove oldest entries if cache is full."""
        if len(self.cache) >= self.max_size:
            # Find oldest entry
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]

    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired."""
        if key not in self.timestamps:
            return True
        age = datetime.now().timestamp() - self.timestamps[key]
        return age > self.default_ttl

    async def get(self, file_path: str) -> Optional[bytes]:
        """Get file content from cache."""
        cache_key = hashlib.md5(file_path.encode()).hexdigest()

        if cache_key not in self.cache or self._is_expired(cache_key):
            return None

        # Update access time
        self.timestamps[cache_key] = datetime.now().timestamp()
        return self.cache[cache_key]

    async def set(self, file_path: str, content: bytes) -> None:
        """Set file content in cache."""
        cache_key = hashlib.md5(file_path.encode()).hexdigest()

        self._evict_if_needed()
        self.cache[cache_key] = content
        self.timestamps[cache_key] = datetime.now().timestamp()

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()

class FileIndexer:
    """Efficient file indexing for faster searches."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.index = {}
        self.last_update = 0

    async def build_index(self, force_rebuild: bool = False) -> None:
        """
        Build file index for faster directory operations.

        Args:
            force_rebuild: Force rebuilding even if index is recent
        """
        current_time = datetime.now().timestamp()

        # Only rebuild if older than 5 minutes or forced
        if not force_rebuild and (current_time - self.last_update) < 300:
            return

        self.index = {}

        async def scan_directory(directory: Path) -> None:
            """Recursively scan directory and build index."""
            try:
                for item in await asyncio.get_event_loop().run_in_executor(
                    None, list, directory.iterdir()
                ):
                    if item.is_file():
                        # Add file to index
                        rel_path = str(item.relative_to(self.base_path))
                        file_stat = await asyncio.get_event_loop().run_in_executor(
                            None, item.stat
                        )
                        self.index[rel_path] = {
                            'path': str(item),
                            'size': file_stat.st_size,
                            'modified': file_stat.st_mtime,
                            'extension': item.suffix.lower()
                        }
                    elif item.is_dir():
                        await scan_directory(item)
            except (OSError, PermissionError) as e:
                logger.warning(f"Error scanning directory {directory}: {e}")

        await scan_directory(self.base_path)
        self.last_update = current_time
        logger.info(f"File index built with {len(self.index)} files")

    def find_files(self, pattern: str, extensions: List[str] = None) -> List[str]:
        """
        Find files matching pattern and extensions.

        Args:
            pattern: Search pattern (supports wildcards)
            extensions: List of allowed extensions

        Returns:
            List of matching file paths
        """
        results = []
        pattern_lower = pattern.lower()

        for file_path, file_info in self.index.items():
            # Check pattern match
            if pattern_lower not in file_path.lower():
                continue

            # Check extension filter
            if extensions and file_info['extension'] not in extensions:
                continue

            results.append(file_info['path'])

        return results

    def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get file information from index."""
        rel_path = str(Path(file_path).relative_to(self.base_path))
        return self.index.get(rel_path)

class BatchFileProcessor:
    """Process multiple files concurrently with controlled concurrency."""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_files(
        self,
        file_paths: List[str],
        processor_func,
        *args,
        **kwargs
    ) -> List[tuple]:
        """
        Process multiple files concurrently.

        Args:
            file_paths: List of file paths to process
            processor_func: Async function to process each file
            *args, **kwargs: Arguments for processor function

        Returns:
            List of (file_path, result) tuples
        """
        async def process_with_semaphore(file_path: str) -> tuple:
            async with self.semaphore:
                try:
                    result = await processor_func(file_path, *args, **kwargs)
                    return (file_path, result, None)
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {e}")
                    return (file_path, None, e)

        tasks = [process_with_semaphore(fp) for fp in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if not isinstance(r, Exception)]

    async def process_directory(
        self,
        directory_path: str,
        processor_func,
        extensions: List[str] = None,
        *args,
        **kwargs
    ) -> List[tuple]:
        """
        Process all files in a directory concurrently.

        Args:
            directory_path: Directory to process
            processor_func: Async function to process each file
            extensions: Filter by file extensions
            *args, **kwargs: Arguments for processor function

        Returns:
            List of (file_path, result) tuples
        """
        # Get all files in directory
        file_paths = []
        for root, dirs, files in await asyncio.get_event_loop().run_in_executor(
            None, os.walk, directory_path
        ):
            for file in files:
                file_path = os.path.join(root, file)
                if not extensions or any(file_path.lower().endswith(ext.lower()) for ext in extensions):
                    file_paths.append(file_path)

        return await self.process_files(file_paths, processor_func, *args, **kwargs)

# Global instances for easy access
file_cache = FileCache()
async_ops = AsyncFileOperations()
batch_processor = BatchFileProcessor()