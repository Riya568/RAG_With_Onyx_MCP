# Real MCP Integration for Local File Access

## Overview

This document explains how the MCP (Model Context Protocol) integration works for real local file access in the Onyx prototype.

## Architecture

```
User Query → Frontend → API Route → MCP Server → Local Files → Real Processing → RAG Response
```

## Components

### 1. MCP Server (`mcp_server.py`)
- **Location:** `onyx/examples/mcp/local_directory_server/`
- **Purpose:** Provides secure access to local files
- **Features:**
  - File reading with security checks
  - Directory listing
  - File search with regex support
  - Base64 encoding for file transfer
  - Onyx integration for document ingestion

### 2. Frontend API Route (`/api/mcp/local-files/route.ts`)
- **Location:** `onyx/web/src/app/api/mcp/local-files/`
- **Purpose:** Bridge between frontend and MCP server
- **Features:**
  - Real MCP server communication
  - Document processing and chunking
  - Onyx backend integration
  - Error handling and fallbacks

### 3. Frontend Component (`LocalFilesDropdown.tsx`)
- **Location:** `onyx/web/src/components/`
- **Purpose:** UI for selecting local files
- **Features:**
  - File/folder selection
  - Search functionality
  - Real-time file listing
  - Progress indicators

## Setup Instructions

### 1. Start MCP Server

```bash
cd onyx/examples/mcp/local_directory_server
python start_real_mcp.py
```

### 2. Configure Environment Variables

Create `.env.local` in `onyx/web/`:

```env
MCP_SERVER_URL=http://localhost:8001
ALLOWED_DIRECTORY=/Users
ONYX_BACKEND_URL=http://localhost:8080
ONYX_API_KEY=your_api_key_here
```

### 3. Start Onyx Backend

```bash
cd onyx/backend
python onyx/main.py
```

### 4. Start Frontend

```bash
cd onyx/web
npm run dev
```

## Security Features

### File Access Control
- **Allowed Directories:** Only specified directories can be accessed
- **File Size Limits:** Maximum file size restrictions
- **Extension Filtering:** Only allowed file types can be processed
- **Path Validation:** Prevents directory traversal attacks

### Default Configuration
- **Allowed Directories:** `/Users`, `/home`, `/Documents`, `/Desktop`, `/Downloads`
- **Max File Size:** 50MB
- **Allowed Extensions:** `.txt`, `.md`, `.py`, `.js`, `.ts`, `.json`, `.yaml`, `.yml`, `.xml`, `.csv`, `.pdf`, `.docx`, `.doc`, `.html`, `.htm`, `.rtf`, `.odt`

## API Endpoints

### GET `/api/mcp/local-files`
- **Purpose:** List local files and directories
- **MCP Call:** `list_directory`
- **Response:** Array of file/folder objects

### POST `/api/mcp/local-files`
- **Purpose:** Ingest a local file into Onyx
- **MCP Call:** `read_file` → `processDocumentContent` → `addDocumentToOnyx`
- **Response:** Success status with document ID and chunk count

## MCP Tools Available

1. **`read_file`** - Read file content with metadata
2. **`list_directory`** - List directory contents
3. **`search_files`** - Search text in files
4. **`download_file`** - Download file as base64
5. **`ingest_file_to_onyx`** - Ingest file into Onyx
6. **`sync_directory_to_onyx`** - Sync entire directory
7. **`get_file_metadata`** - Get detailed file metadata

## Real vs Mock Implementation

### Mock Implementation (Previous)
```javascript
// Mock response
const mockContent = `This is mock content...`;
return { success: true, content: mockContent };
```

### Real Implementation (Current)
```javascript
// Real MCP server call
const response = await fetch(`${mcpServerUrl}/mcp`, {
  method: 'POST',
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: { name: tool, arguments: params }
  })
});
```

## Testing

### 1. Test MCP Server
```bash
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "list_directory",
      "arguments": {"dir_path": "/Users"}
    }
  }'
```

### 2. Test Frontend API
```bash
curl http://localhost:3001/api/mcp/local-files
```

### 3. Test File Ingestion
```bash
curl -X POST http://localhost:3001/api/mcp/local-files \
  -H "Content-Type: application/json" \
  -d '{
    "filePath": "/Users/username/Documents/test.txt",
    "fileName": "test.txt",
    "fileType": "file"
  }'
```

## Troubleshooting

### Common Issues

1. **MCP Server Not Running**
   - Check if port 8001 is available
   - Verify Python dependencies are installed

2. **File Access Denied**
   - Check allowed directories configuration
   - Verify file permissions

3. **Onyx Backend Connection Failed**
   - Ensure Onyx backend is running on port 8080
   - Check API key configuration

4. **Frontend Not Loading Files**
   - Check MCP server URL configuration
   - Verify CORS settings

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python start_real_mcp.py
```

## Production Deployment

### Google Cloud Setup

1. **Deploy MCP Server** as a separate service
2. **Configure allowed directories** for production
3. **Set up proper authentication** for Onyx backend
4. **Enable HTTPS** for secure communication
5. **Configure file size limits** based on requirements

### Security Considerations

- Use environment variables for sensitive configuration
- Implement proper authentication and authorization
- Set up monitoring and logging
- Regular security audits of file access patterns

## Performance Optimization

- **Concurrent Processing:** Files are processed in parallel
- **Caching:** File metadata is cached for better performance
- **Chunking:** Large files are split into manageable chunks
- **Compression:** Base64 encoding is optimized for transfer

## Future Enhancements

- **Real-time File Watching:** Monitor file changes
- **Batch Processing:** Process multiple files simultaneously
- **Advanced Search:** Full-text search with indexing
- **File Versioning:** Track file changes over time
- **Cloud Storage Integration:** Support for cloud file systems
