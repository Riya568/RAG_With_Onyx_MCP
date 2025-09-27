# MCP Server File Sync & Ingestion Guide

## Overview
The enhanced MCP server now supports complete file synchronization and ingestion from local directories to Onyx server for RAG (Retrieval-Augmented Generation). This enables users to sync their local files and make them searchable through Onyx.

## 🚀 New MCP Tools

### 1. **download_file**
Downloads a local file and returns its content as base64 encoded data.

**Parameters:**
- `file_path` (string): Path to the local file

**Returns:**
```json
{
  "content": "base64_encoded_content",
  "file_path": "/path/to/file",
  "file_name": "filename.txt",
  "file_size": 1024,
  "mime_type": "text/plain",
  "modified_time": 1640995200.0,
  "checksum": "md5_hash"
}
```

### 2. **ingest_file_to_onyx**
Ingests a single local file into Onyx server for RAG.

**Parameters:**
- `file_path` (string): Path to the local file
- `document_set` (string, optional): Document set to categorize the file

**Returns:**
```json
{
  "success": true,
  "file_path": "/path/to/file",
  "file_name": "filename.txt",
  "document_id": "doc_abc123",
  "file_id": "file_xyz789",
  "chunks": 15,
  "message": "File ingested successfully"
}
```

### 3. **sync_directory_to_onyx**
Syncs all files in a directory to Onyx server.

**Parameters:**
- `dir_path` (string): Path to the directory
- `document_set` (string, optional): Document set for categorization
- `recursive` (boolean): Whether to process subdirectories (default: true)

**Returns:**
```json
{
  "successful": [
    {
      "file_path": "/path/to/file1.txt",
      "file_name": "file1.txt",
      "document_id": "doc_abc123",
      "chunks": 10
    }
  ],
  "failed": [],
  "total_files": 1,
  "successful_count": 1,
  "failed_count": 0
}
```

### 4. **get_file_metadata**
Gets detailed metadata for a file.

**Parameters:**
- `file_path` (string): Path to the file

**Returns:**
```json
{
  "file_path": "/path/to/file",
  "file_name": "filename.txt",
  "file_size": 1024,
  "mime_type": "text/plain",
  "encoding": "utf-8",
  "modified_time": 1640995200.0,
  "created_time": 1640995100.0,
  "checksum": "md5_hash",
  "is_readable": true,
  "is_writable": false,
  "extension": ".txt"
}
```

## 🔧 Configuration

### Environment Variables
```bash
# MCP Server Configuration
ALLOWED_DIRECTORIES="/home/user/documents,/home/user/downloads"
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=".txt,.md,.pdf,.docx,.html"
ONYX_SERVER_URL="http://localhost:3000"
ONYX_API_KEY="your_api_key_here"
```

### Command Line Arguments
```bash
python mcp_server.py \
  --transport http \
  --host 0.0.0.0 \
  --port 8001 \
  --allowed-dirs "/home/user/documents" \
  --max-file-size 10485760 \
  --allowed-extensions ".txt,.md,.pdf,.docx" \
  --onyx-server-url "http://localhost:3000" \
  --onyx-api-key "your_api_key"
```

## 📋 Supported File Types

| File Type | Extension | Processing | Status |
|-----------|-----------|------------|---------|
| Text | `.txt` | Direct processing | ✅ |
| Markdown | `.md` | Direct processing | ✅ |
| PDF | `.pdf` | Text extraction | ✅ |
| Word | `.docx`, `.doc` | Text extraction | ✅ |
| HTML | `.html`, `.htm` | Text extraction | ✅ |
| Code | `.py`, `.js`, `.ts` | Direct processing | ✅ |
| Data | `.json`, `.yaml`, `.csv` | Direct processing | ✅ |

## 🔄 Complete File Sync Flow

### 1. **File Discovery**
- MCP server scans allowed directories
- Filters by allowed file extensions
- Respects file size limits

### 2. **File Processing**
- Reads file content as binary
- Encodes as base64 for transfer
- Calculates checksum for integrity
- Extracts metadata (size, type, timestamps)

### 3. **Onyx Integration**
- Sends file to Onyx API endpoint
- Onyx processes and chunks content
- Creates embeddings for semantic search
- Stores in document database

### 4. **Search Integration**
- Files become searchable in Onyx
- Available for RAG queries
- Categorized by document sets

## 🧪 Testing

### Start MCP Server
```bash
cd onyx/examples/mcp/local_directory_server
python mcp_server.py --transport http --port 8001
```

### Start Onyx Server
```bash
cd onyx/web
npm run dev
```

### Run Test Script
```bash
python test_file_sync.py
```

### Manual Testing
```bash
# Test file download
curl -X POST http://localhost:8001/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "download_file",
    "arguments": {"file_path": "/path/to/your/file.txt"}
  }'

# Test file ingestion
curl -X POST http://localhost:8001/mcp/tools/call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ingest_file_to_onyx",
    "arguments": {
      "file_path": "/path/to/your/file.txt",
      "document_set": "my_documents"
    }
  }'
```

## 🎯 Use Cases

### 1. **Personal Document Sync**
```python
# Sync personal documents
await mcp_client.call_tool("sync_directory_to_onyx", {
    "dir_path": "/home/user/documents",
    "document_set": "personal",
    "recursive": True
})
```

### 2. **Project Documentation**
```python
# Sync project files
await mcp_client.call_tool("sync_directory_to_onyx", {
    "dir_path": "/home/user/projects/my_project",
    "document_set": "project_docs",
    "recursive": True
})
```

### 3. **Research Papers**
```python
# Sync research papers
await mcp_client.call_tool("sync_directory_to_onyx", {
    "dir_path": "/home/user/research/papers",
    "document_set": "research",
    "recursive": True
})
```

## 🔒 Security Features

### Path Validation
- Only files in allowed directories can be accessed
- Prevents directory traversal attacks
- Validates file paths before processing

### File Type Filtering
- Only allowed file extensions are processed
- Prevents execution of dangerous file types
- Configurable extension whitelist

### Size Limits
- Maximum file size limits prevent memory issues
- Configurable per deployment
- Graceful handling of oversized files

### Checksum Validation
- MD5 checksums ensure file integrity
- Prevents corruption during transfer
- Enables duplicate detection

## 📊 Performance Features

### Concurrent Processing
- Multiple files processed simultaneously
- Configurable concurrency limits
- Efficient resource utilization

### Batch Operations
- Directory sync processes multiple files
- Progress tracking and reporting
- Error handling per file

### Memory Management
- Streaming file reads for large files
- Base64 encoding for efficient transfer
- Cleanup after processing

## 🚨 Error Handling

### File Access Errors
- Permission denied handling
- File not found errors
- Path validation failures

### Network Errors
- Onyx server connectivity issues
- Timeout handling
- Retry mechanisms

### Processing Errors
- File format errors
- Content extraction failures
- Chunking errors

## 🔮 Future Enhancements

### Planned Features
- [ ] **Real-time Sync**: Watch directories for changes
- [ ] **Incremental Updates**: Only sync changed files
- [ ] **Conflict Resolution**: Handle file conflicts
- [ ] **Progress Tracking**: Real-time sync progress
- [ ] **File Versioning**: Track file versions
- [ ] **Selective Sync**: Choose specific files/folders

### Advanced Processing
- [ ] **OCR Support**: Extract text from images
- [ ] **Audio Transcription**: Convert audio to text
- [ ] **Video Processing**: Extract text from videos
- [ ] **Multi-language Support**: Process different languages

## ✅ Production Ready

The MCP server file sync system is **production ready** with:
- Comprehensive error handling
- Security validations
- Performance optimizations
- Detailed logging
- Test coverage

**Ready for deployment and user testing!** 🚀
