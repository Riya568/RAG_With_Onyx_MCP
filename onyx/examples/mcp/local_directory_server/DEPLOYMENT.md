# Local Directory MCP Server - Deployment Guide

This guide covers deployment options for the Local Directory MCP Server in the Onyx prototype.

## Quick Start

### 1. HTTP Transport (Recommended for Onyx Integration)
```bash
# Start HTTP server
python mcp_server.py --transport http --port 8001

# Or use the startup script
python start_server.py
```

### 2. Stdio Transport (For CLI Integration)
```bash
# Start stdio server
python mcp_server.py --transport stdio

# Or use the startup script
python start_server.py --interactive
```

## Deployment Options

### Option 1: Local Development
- **HTTP**: `http://localhost:8001/mcp`
- **Stdio**: Direct process communication
- **Use case**: Development, testing, single-user

### Option 2: Docker Container
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8001
CMD ["python", "mcp_server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "8001"]
```

### Option 3: System Service (Linux)
```ini
[Unit]
Description=Local Directory MCP Server
After=network.target

[Service]
Type=simple
User=mcp
WorkingDirectory=/opt/mcp-server
ExecStart=/usr/bin/python3 mcp_server.py --transport http --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

### Option 4: Cloud Deployment (AWS/GCP)
- **Container**: Deploy as Docker container
- **Serverless**: Use AWS Lambda or GCP Cloud Functions
- **VM**: Deploy on EC2 or Compute Engine

## Configuration for Onyx Integration

### 1. Onyx Admin Panel Setup
1. Go to **Admin Panel** → **MCP Servers**
2. Click **Add New MCP Server**
3. Configure:
   - **Name**: `Local Directory Server`
   - **URL**: `http://localhost:8001/mcp` (or your server URL)
   - **Auth Type**: `None`
   - **Tools**: Select all available tools

### 2. User Access
- Users can access local files through Onyx chat
- Files must be within allowed directories
- Only allowed file types can be accessed

## Security Configuration

### Production Settings
```bash
# Restrict directories
--allowed-dirs "/home/user/documents,/home/user/projects"

# Limit file size (5MB)
--max-file-size 5242880

# Allow only specific file types
--allowed-extensions ".txt,.md,.py,.js,.json,.yaml"

# Bind to specific interface
--host 127.0.0.1
```

### Environment Variables
```bash
export ALLOWED_DIRECTORIES="/home/user/documents,/home/user/projects"
export MAX_FILE_SIZE=5242880
export ALLOWED_EXTENSIONS=".txt,.md,.py,.js,.json,.yaml"
```

## Monitoring and Logging

### Log Levels
- **INFO**: General operation logs
- **DEBUG**: Detailed debugging information
- **ERROR**: Error conditions

### Health Checks
```bash
# HTTP health check
curl http://localhost:8001/mcp

# Process health check
ps aux | grep "mcp_server.py"
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Check file/directory permissions
   - Ensure user has read access to allowed directories

2. **Port Already in Use**
   - Change port: `--port 8002`
   - Kill existing process: `lsof -ti:8001 | xargs kill`

3. **File Not Found**
   - Verify file path is within allowed directories
   - Check file extension is allowed

4. **Connection Refused**
   - Ensure server is running
   - Check firewall settings
   - Verify host/port configuration

### Debug Mode
```bash
# Enable debug logging
python mcp_server.py --transport http --port 8001 2>&1 | tee debug.log
```

## Performance Tuning

### File Size Limits
- **Small files** (< 1MB): No restrictions
- **Medium files** (1-10MB): Default limit
- **Large files** (> 10MB): Increase `--max-file-size`

### Directory Scanning
- **Shallow directories**: Fast performance
- **Deep directories**: May be slower
- **Many files**: Consider pagination

### Memory Usage
- **Single file**: ~2x file size in memory
- **Multiple files**: Cumulative memory usage
- **Large files**: Consider streaming

## Integration Examples

### With Onyx Chat
```
User: "Read the file at /home/user/documents/notes.txt"
Onyx: [Uses read_local_file tool]

User: "List files in /home/user/projects"
Onyx: [Uses list_directory tool]

User: "Search for 'TODO' in Python files"
Onyx: [Uses search_files tool]
```

### With Other MCP Clients
```python
# Python MCP client example
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def main():
    async with stdio_client(["python", "mcp_server.py", "--transport", "stdio"]) as (read, write):
        async with ClientSession(read, write) as session:
            result = await session.call_tool("read_local_file", {"file_path": "/path/to/file.txt"})
            print(result)
```

## Next Steps

1. **Deploy server** using preferred method
2. **Configure Onyx** to connect to MCP server
3. **Test integration** with sample files
4. **Monitor performance** and adjust settings
5. **Scale as needed** for production use
