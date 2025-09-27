"""Model Context Protocol server for local directory access.

This MCP server provides tools to read files, list directories, and search files
from the local file system. It's designed for the Onyx prototype to enable
local file access through MCP protocol.

Environment variables used:
    - ``ALLOWED_DIRECTORIES``: Comma-separated list of allowed directories. 
      Defaults to current working directory.
    - ``MAX_FILE_SIZE``: Maximum file size to read in bytes. Defaults to 10MB.
    - ``ALLOWED_EXTENSIONS``: Comma-separated list of allowed file extensions.
      Defaults to common text file extensions.

The script can also be configured via CLI flags. Run ``python server.py --help``
for details.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import logging
import mimetypes
import os
import re
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Optional
import aiohttp
import aiofiles

from fastmcp import FastMCP


logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_DIRS = [os.getcwd()]
DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_ALLOWED_EXTENSIONS = ['.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml', '.xml', '.csv', '.pdf', '.docx', '.doc', '.html', '.htm']
DEFAULT_ONYX_SERVER_URL = "http://localhost:3000"


class LocalDirectoryError(RuntimeError):
    """Raised when local directory operations fail."""


@dataclass
class LocalDirectoryConfig:
    allowed_directories: list[str]
    max_file_size: int
    allowed_extensions: list[str]
    onyx_server_url: str
    onyx_api_key: Optional[str] = None

    def is_path_allowed(self, file_path: str) -> bool:
        """Check if the given file path is within allowed directories."""
        try:
            abs_path = os.path.abspath(file_path)
            return any(abs_path.startswith(os.path.abspath(allowed_dir)) 
                      for allowed_dir in self.allowed_directories)
        except Exception:
            return False

    def is_extension_allowed(self, file_path: str) -> bool:
        """Check if the file extension is allowed."""
        if not self.allowed_extensions:
            return True
        file_ext = Path(file_path).suffix.lower()
        return file_ext in self.allowed_extensions


class LocalDirectoryClient:
    """Client for performing local directory operations."""

    def __init__(self, config: LocalDirectoryConfig) -> None:
        self._config = config

    async def read_file(self, file_path: str) -> dict[str, Any]:
        """Read a file from the local file system."""
        try:
            # Security checks
            if not self._config.is_path_allowed(file_path):
                raise LocalDirectoryError(f"Access denied: Path '{file_path}' is not in allowed directories")
            
            if not self._config.is_extension_allowed(file_path):
                raise LocalDirectoryError(f"File type not allowed: '{Path(file_path).suffix}'")

            # Check if file exists
            if not os.path.isfile(file_path):
                raise LocalDirectoryError(f"File not found: '{file_path}'")

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self._config.max_file_size:
                raise LocalDirectoryError(f"File too large: {file_size} bytes (max: {self._config.max_file_size})")

            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Get file info
            file_stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)

            return {
                "content": content,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": mime_type or "unknown",
                "modified_time": file_stat.st_mtime,
                "is_readable": True
            }

        except Exception as e:
            logger.error(f"Error reading file '{file_path}': {str(e)}")
            raise LocalDirectoryError(f"Failed to read file: {str(e)}")

    async def list_directory(self, dir_path: str) -> dict[str, Any]:
        """List contents of a directory."""
        try:
            # Security checks
            if not self._config.is_path_allowed(dir_path):
                raise LocalDirectoryError(f"Access denied: Path '{dir_path}' is not in allowed directories")

            # Check if directory exists
            if not os.path.isdir(dir_path):
                raise LocalDirectoryError(f"Directory not found: '{dir_path}'")

            # List directory contents
            items = []
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)
                try:
                    item_stat = os.stat(item_path)
                    items.append({
                        "name": item,
                        "path": item_path,
                        "is_file": os.path.isfile(item_path),
                        "is_directory": os.path.isdir(item_path),
                        "size": item_stat.st_size if os.path.isfile(item_path) else None,
                        "modified_time": item_stat.st_mtime
                    })
                except OSError:
                    # Skip items we can't access
                    continue

            return {
                "directory_path": dir_path,
                "items": sorted(items, key=lambda x: (not x["is_directory"], x["name"])),
                "total_items": len(items)
            }

        except Exception as e:
            logger.error(f"Error listing directory '{dir_path}': {str(e)}")
            raise LocalDirectoryError(f"Failed to list directory: {str(e)}")

    async def search_files(self, query: str, directory: str, file_pattern: str = "*") -> dict[str, Any]:
        """Search for text content in files within a directory."""
        try:
            # Security checks
            if not self._config.is_path_allowed(directory):
                raise LocalDirectoryError(f"Access denied: Path '{directory}' is not in allowed directories")

            if not os.path.isdir(directory):
                raise LocalDirectoryError(f"Directory not found: '{directory}'")

            # Compile search pattern
            search_regex = re.compile(query, re.IGNORECASE)
            file_pattern_regex = re.compile(file_pattern.replace("*", ".*"))

            matches = []
            total_files_searched = 0

            # Walk through directory
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip if not in allowed directories
                    if not self._config.is_path_allowed(file_path):
                        continue
                    
                    # Skip if extension not allowed
                    if not self._config.is_extension_allowed(file_path):
                        continue
                    
                    # Skip if doesn't match file pattern
                    if not file_pattern_regex.search(file):
                        continue

                    total_files_searched += 1

                    try:
                        # Check file size before reading
                        file_size = os.path.getsize(file_path)
                        if file_size > self._config.max_file_size:
                            continue

                        # Read and search file
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        if search_regex.search(content):
                            # Find line numbers with matches
                            lines = content.split('\n')
                            matching_lines = []
                            for i, line in enumerate(lines, 1):
                                if search_regex.search(line):
                                    matching_lines.append({
                                        "line_number": i,
                                        "content": line.strip()
                                    })

                            matches.append({
                                "file_path": file_path,
                                "relative_path": os.path.relpath(file_path, directory),
                                "file_size": file_size,
                                "matching_lines": matching_lines,
                                "total_matches": len(matching_lines)
                            })

                    except Exception as e:
                        logger.debug(f"Error searching file '{file_path}': {str(e)}")
                        continue

            return {
                "query": query,
                "directory": directory,
                "file_pattern": file_pattern,
                "matches": matches,
                "total_matches": len(matches),
                "total_files_searched": total_files_searched
            }

        except Exception as e:
            logger.error(f"Error searching files in '{directory}': {str(e)}")
            raise LocalDirectoryError(f"Failed to search files: {str(e)}")

    async def download_file(self, file_path: str) -> dict[str, Any]:
        """Download a file and return its content as base64 encoded data."""
        try:
            # Security checks
            if not self._config.is_path_allowed(file_path):
                raise LocalDirectoryError(f"Access denied: Path '{file_path}' is not in allowed directories")
            
            if not self._config.is_extension_allowed(file_path):
                raise LocalDirectoryError(f"File type not allowed: '{Path(file_path).suffix}'")

            # Check if file exists
            if not os.path.isfile(file_path):
                raise LocalDirectoryError(f"File not found: '{file_path}'")

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self._config.max_file_size:
                raise LocalDirectoryError(f"File too large: {file_size} bytes (max: {self._config.max_file_size})")

            # Read file as binary
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()

            # Encode as base64
            content_b64 = base64.b64encode(content).decode('utf-8')

            # Get file info
            file_stat = os.stat(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)

            return {
                "content": content_b64,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": file_size,
                "mime_type": mime_type or "unknown",
                "modified_time": file_stat.st_mtime,
                "checksum": hashlib.md5(content).hexdigest()
            }

        except Exception as e:
            logger.error(f"Error downloading file '{file_path}': {str(e)}")
            raise LocalDirectoryError(f"Failed to download file: {str(e)}")

    async def ingest_file_to_onyx(self, file_path: str, document_set: Optional[str] = None) -> dict[str, Any]:
        """Ingest a local file into Onyx server for RAG."""
        try:
            # First download the file
            file_data = await self.download_file(file_path)
            
            # Prepare ingestion payload
            payload = {
                "filePath": file_data["file_path"],
                "fileName": file_data["file_name"],
                "fileType": "file",
                "content": file_data["content"],
                "mimeType": file_data["mime_type"],
                "fileSize": file_data["file_size"],
                "checksum": file_data["checksum"],
                "documentSet": document_set
            }

            # Call Onyx API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json"
                }
                
                if self._config.onyx_api_key:
                    headers["Authorization"] = f"Bearer {self._config.onyx_api_key}"

                url = f"{self._config.onyx_server_url}/api/mcp/local-files"
                
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "file_path": file_path,
                            "file_name": file_data["file_name"],
                            "document_id": result.get("documentId"),
                            "file_id": result.get("fileId"),
                            "chunks": result.get("chunks", 0),
                            "message": result.get("message", "File ingested successfully")
                        }
                    else:
                        error_text = await response.text()
                        raise LocalDirectoryError(f"Onyx API error {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"Error ingesting file '{file_path}' to Onyx: {str(e)}")
            raise LocalDirectoryError(f"Failed to ingest file to Onyx: {str(e)}")

    async def sync_directory_to_onyx(self, dir_path: str, document_set: Optional[str] = None, recursive: bool = True) -> dict[str, Any]:
        """Sync all files in a directory to Onyx server."""
        try:
            # Security checks
            if not self._config.is_path_allowed(dir_path):
                raise LocalDirectoryError(f"Access denied: Path '{dir_path}' is not in allowed directories")

            if not os.path.isdir(dir_path):
                raise LocalDirectoryError(f"Directory not found: '{dir_path}'")

            # Collect all files
            files_to_sync = []
            if recursive:
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if (self._config.is_path_allowed(file_path) and 
                            self._config.is_extension_allowed(file_path)):
                            files_to_sync.append(file_path)
            else:
                for item in os.listdir(dir_path):
                    item_path = os.path.join(dir_path, item)
                    if (os.path.isfile(item_path) and 
                        self._config.is_path_allowed(item_path) and 
                        self._config.is_extension_allowed(item_path)):
                        files_to_sync.append(item_path)

            # Process files in batches
            results = {
                "successful": [],
                "failed": [],
                "total_files": len(files_to_sync),
                "successful_count": 0,
                "failed_count": 0
            }

            # Process files concurrently (limit to 5 at a time)
            semaphore = asyncio.Semaphore(5)
            
            async def process_file(file_path: str):
                async with semaphore:
                    try:
                        result = await self.ingest_file_to_onyx(file_path, document_set)
                        results["successful"].append(result)
                        results["successful_count"] += 1
                        logger.info(f"Successfully synced: {file_path}")
                    except Exception as e:
                        error_result = {
                            "file_path": file_path,
                            "error": str(e)
                        }
                        results["failed"].append(error_result)
                        results["failed_count"] += 1
                        logger.error(f"Failed to sync {file_path}: {str(e)}")

            # Process all files
            await asyncio.gather(*[process_file(fp) for fp in files_to_sync])

            return results

        except Exception as e:
            logger.error(f"Error syncing directory '{dir_path}' to Onyx: {str(e)}")
            raise LocalDirectoryError(f"Failed to sync directory to Onyx: {str(e)}")

    async def get_file_metadata(self, file_path: str) -> dict[str, Any]:
        """Get detailed metadata for a file."""
        try:
            # Security checks
            if not self._config.is_path_allowed(file_path):
                raise LocalDirectoryError(f"Access denied: Path '{file_path}' is not in allowed directories")

            if not os.path.isfile(file_path):
                raise LocalDirectoryError(f"File not found: '{file_path}'")

            # Get file info
            file_stat = os.stat(file_path)
            mime_type, encoding = mimetypes.guess_type(file_path)
            
            # Calculate checksum
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
                checksum = hashlib.md5(content).hexdigest()

            return {
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": file_stat.st_size,
                "mime_type": mime_type or "unknown",
                "encoding": encoding,
                "modified_time": file_stat.st_mtime,
                "created_time": file_stat.st_ctime,
                "checksum": checksum,
                "is_readable": os.access(file_path, os.R_OK),
                "is_writable": os.access(file_path, os.W_OK),
                "extension": Path(file_path).suffix.lower()
            }

        except Exception as e:
            logger.error(f"Error getting metadata for '{file_path}': {str(e)}")
            raise LocalDirectoryError(f"Failed to get file metadata: {str(e)}")


def build_mcp_server(config: LocalDirectoryConfig) -> FastMCP:
    """Build the MCP server with local directory tools."""
    client = LocalDirectoryClient(config)
    mcp = FastMCP("Local Directory MCP Server")

    @mcp.tool(
        name="read_file",
        description=(
            "Read the contents of a local file. The file must be within allowed directories "
            "and have an allowed file extension. Returns file content along with metadata."
        ),
    )
    async def read_file(path: str, file_name: str = None) -> dict[str, Any]:
        """Read a local file and return its contents with metadata."""
        return await client.read_file(path)

    @mcp.tool(
        name="list_directory",
        description=(
            "List the contents of a local directory. Shows files and subdirectories "
            "with their metadata (size, modification time, etc.)."
        ),
    )
    async def list_directory(dir_path: str) -> dict[str, Any]:
        """List the contents of a local directory."""
        return await client.list_directory(dir_path)

    @mcp.tool(
        name="search_files",
        description=(
            "Search for text content within files in a directory. Supports regex patterns "
            "and file name patterns. Returns matching files with line numbers and content."
        ),
    )
    async def search_files(
        query: str, 
        directory: str, 
        file_pattern: str = "*"
    ) -> dict[str, Any]:
        """Search for text content in files within a directory."""
        return await client.search_files(query, directory, file_pattern)

    @mcp.tool(
        name="download_file",
        description=(
            "Download a local file and return its content as base64 encoded data. "
            "Useful for transferring files to Onyx server for ingestion."
        ),
    )
    async def download_file(file_path: str) -> dict[str, Any]:
        """Download a local file and return its content as base64 encoded data."""
        return await client.download_file(file_path)

    @mcp.tool(
        name="ingest_file_to_onyx",
        description=(
            "Ingest a local file into Onyx server for RAG. Downloads the file, "
            "processes it, and stores it in Onyx's document database for search and retrieval."
        ),
    )
    async def ingest_file_to_onyx(
        file_path: str, 
        document_set: Optional[str] = None
    ) -> dict[str, Any]:
        """Ingest a local file into Onyx server for RAG."""
        return await client.ingest_file_to_onyx(file_path, document_set)

    @mcp.tool(
        name="sync_directory_to_onyx",
        description=(
            "Sync all files in a directory to Onyx server. Processes all files "
            "in the directory (optionally recursively) and ingests them into Onyx for RAG."
        ),
    )
    async def sync_directory_to_onyx(
        dir_path: str, 
        document_set: Optional[str] = None,
        recursive: bool = True
    ) -> dict[str, Any]:
        """Sync all files in a directory to Onyx server."""
        return await client.sync_directory_to_onyx(dir_path, document_set, recursive)

    @mcp.tool(
        name="get_file_metadata",
        description=(
            "Get detailed metadata for a file including size, type, checksum, "
            "permissions, and timestamps."
        ),
    )
    async def get_file_metadata(file_path: str) -> dict[str, Any]:
        """Get detailed metadata for a file."""
        return await client.get_file_metadata(file_path)

    # FastMCP automatically handles JSON-RPC endpoints
    # No need for manual @mcp.app.post decorator
    
    return mcp


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the Local Directory MCP server")
    
    parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default="http",
        help="Transport method for MCP server (default: %(default)s)",
    )
    parser.add_argument(
        "--allowed-dirs",
        default=os.environ.get("ALLOWED_DIRECTORIES", os.getcwd()),
        help="Comma-separated list of allowed directories (default: current directory)",
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=int(os.environ.get("MAX_FILE_SIZE", DEFAULT_MAX_FILE_SIZE)),
        help=f"Maximum file size to read in bytes (default: {DEFAULT_MAX_FILE_SIZE})",
    )
    parser.add_argument(
        "--allowed-extensions",
        default=os.environ.get("ALLOWED_EXTENSIONS", ",".join(DEFAULT_ALLOWED_EXTENSIONS)),
        help="Comma-separated list of allowed file extensions (default: common text files)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface for the MCP server (default: %(default)s)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for the MCP server (default: %(default)d)",
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="HTTP path for the MCP server (default: %(default)s)",
    )
    parser.add_argument(
        "--onyx-server-url",
        default=os.environ.get("ONYX_SERVER_URL", DEFAULT_ONYX_SERVER_URL),
        help=f"Onyx server URL for document ingestion (default: {DEFAULT_ONYX_SERVER_URL})",
    )
    parser.add_argument(
        "--onyx-api-key",
        default=os.environ.get("ONYX_API_KEY"),
        help="API key for Onyx server authentication (optional)",
    )
    
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    logging.basicConfig(level=logging.INFO)
    args = parse_args()

    # Parse allowed directories
    allowed_dirs = [d.strip() for d in args.allowed_dirs.split(",") if d.strip()]
    if not allowed_dirs:
        allowed_dirs = DEFAULT_ALLOWED_DIRS

    # Parse allowed extensions
    allowed_extensions = [ext.strip().lower() for ext in args.allowed_extensions.split(",") if ext.strip()]
    if not allowed_extensions:
        allowed_extensions = DEFAULT_ALLOWED_EXTENSIONS

    config = LocalDirectoryConfig(
        allowed_directories=allowed_dirs,
        max_file_size=args.max_file_size,
        allowed_extensions=allowed_extensions,
        onyx_server_url=args.onyx_server_url,
        onyx_api_key=args.onyx_api_key,
    )

    logger.info(f"Starting Local Directory MCP Server")
    logger.info(f"Transport: {args.transport}")
    logger.info(f"Allowed directories: {config.allowed_directories}")
    logger.info(f"Max file size: {config.max_file_size} bytes")
    logger.info(f"Allowed extensions: {config.allowed_extensions}")
    logger.info(f"Onyx server URL: {config.onyx_server_url}")
    logger.info(f"Onyx API key: {'***' if config.onyx_api_key else 'None'}")

    mcp = build_mcp_server(config)
    
    if args.transport == "stdio":
        logger.info("Starting MCP server with stdio transport")
        mcp.run(transport="stdio")
    else:
        logger.info(f"Starting MCP server with HTTP transport at {args.host}:{args.port}{args.path}")
        mcp.run(transport="http", host=args.host, port=args.port, path=args.path)


if __name__ == "__main__":
    main()
