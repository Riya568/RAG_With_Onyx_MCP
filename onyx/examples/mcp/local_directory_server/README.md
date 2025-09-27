# Local Directory MCP Server

This MCP (Model Context Protocol) server provides tools for accessing local files and directories. It's designed for the Onyx prototype to enable local file access through MCP protocol.

## Features

- **Read Local Files**: Read text files from allowed directories
- **List Directories**: Browse directory contents with metadata
- **Search Files**: Search for text content within files using regex patterns

## Security Features

- **Directory Restrictions**: Only access files within specified allowed directories
- **File Type Filtering**: Only allow specific file extensions
- **File Size Limits**: Prevent reading of excessively large files
- **Path Validation**: Prevent directory traversal attacks

## Requirements

- Python 3.11+
- The `fastmcp` package (already included in `backend/requirements/default.txt`)
- Network access to an Onyx deployment
- Proper file system permissions for target directories

## Configuration

The server reads its configuration from environment variables (command-line flags take precedence):

- `ALLOWED_DIRECTORIES` – Comma-separated list of allowed directories. Defaults to current directory.
- `MAX_FILE_SIZE` – Maximum file size to read in bytes. Defaults to 10MB.
- `ALLOWED_EXTENSIONS` – Comma-separated list of allowed file extensions. Defaults to common text files.

## Running the server

### HTTP Transport (Default)
```bash
cd examples/mcp/local_directory_server
python3 mcp_server.py --transport http --host 127.0.0.1 --port 8001
```

### Stdio Transport
```bash
cd examples/mcp/local_directory_server
python3 mcp_server.py --transport stdio
```

### Configuration Options

```bash
python3 mcp_server.py \
  --transport http \
  --allowed-dirs "/home/user/documents,/home/user/projects" \
  --max-file-size 5242880 \
  --allowed-extensions ".txt,.md,.py,.js" \
  --host 0.0.0.0 \
  --port 8001
```

## Transport Options

### HTTP Transport
- **Use case**: Web-based clients, REST APIs, browser testing
- **Default**: `http://127.0.0.1:8001/mcp`
- **Testing**: Use curl, Postman, or browser

```bash
# Start HTTP server
python3 mcp_server.py --transport http --port 8001

# Test with curl
curl http://127.0.0.1:8001/mcp

# Test with PowerShell
Invoke-WebRequest -Uri "http://127.0.0.1:8001/mcp" -Method GET
```

### Stdio Transport
- **Use case**: CLI tools, MCP clients, direct integration
- **Communication**: stdin/stdout JSON-RPC
- **Testing**: Use MCP client tools

```bash
# Start stdio server
python3 mcp_server.py --transport stdio

# Test with MCP client (if available)
mcp-client stdio python3 mcp_server.py --transport stdio
```

The server can be referenced from Onyx or any other MCP-capable client using either transport method.

## Tool Reference

### `read_local_file(file_path: str)`

Reads a local file and returns its contents with metadata.

**Parameters:**
- `file_path` (str): Path to the file to read

**Returns:**
- `content` (str): File contents
- `file_path` (str): Full path to the file
- `file_size` (int): File size in bytes
- `mime_type` (str): Detected MIME type
- `modified_time` (float): Last modification timestamp
- `is_readable` (bool): Whether file was successfully read

### `list_directory(dir_path: str)`

Lists the contents of a directory with metadata.

**Parameters:**
- `dir_path` (str): Path to the directory to list

**Returns:**
- `directory_path` (str): Full path to the directory
- `items` (list): List of files and directories with metadata
- `total_items` (int): Total number of items found

### `search_files(query: str, directory: str, file_pattern: str = "*")`

Searches for text content within files in a directory.

**Parameters:**
- `query` (str): Text to search for (supports regex)
- `directory` (str): Directory to search in
- `file_pattern` (str): File name pattern to match (supports wildcards)

**Returns:**
- `query` (str): The search query used
- `directory` (str): Directory that was searched
- `file_pattern` (str): File pattern that was used
- `matches` (list): List of files containing matches
- `total_matches` (int): Total number of files with matches
- `total_files_searched` (int): Total number of files examined

## Security Considerations

1. **Directory Access**: Only files within allowed directories can be accessed
2. **File Types**: Only files with allowed extensions can be read
3. **File Size**: Files larger than the maximum size limit are skipped
4. **Path Validation**: Directory traversal attacks are prevented
5. **Error Handling**: Sensitive information is not exposed in error messages

## Integration with Onyx

To use this MCP server with Onyx:

1. Start the MCP server
2. In Onyx admin panel, add a new MCP server with URL `http://localhost:8001/mcp`
3. Configure authentication as "None" for local access
4. Select the available tools to enable
5. Users can now access local files through Onyx chat

## Example Usage

Once integrated with Onyx, users can ask questions like:

- "Read the file at /home/user/documents/notes.txt"
- "List the contents of /home/user/projects"
- "Search for 'TODO' in all Python files in /home/user/projects"
- "Find all files containing 'error' in /home/user/logs"
