# Local Files Integration with Onyx UI

## Overview
This integration adds a local files dropdown to the Onyx chat interface, allowing users to easily browse and select local files and folders for processing through the MCP (Model Context Protocol) server.

## What Was Added

### 1. LocalFilesDropdown Component
**File:** `onyx/web/src/components/LocalFilesDropdown.tsx`

A reusable dropdown component that:
- Displays local files and folders in a searchable interface
- Shows file icons, names, paths, and sizes
- Supports both file and folder selection
- Includes loading states and error handling
- Has a clean, modern UI that matches Onyx's design system

### 2. API Endpoint
**File:** `onyx/web/src/app/api/mcp/local-files/route.ts`

REST API endpoints for:
- `GET /api/mcp/local-files` - Fetch local files from MCP server
- `POST /api/mcp/local-files` - Add local file/folder to Onyx

Currently uses mock data for demonstration, but ready for MCP server integration.

### 3. FilePickerModal Integration
**File:** `onyx/web/src/app/chat/my-documents/components/FilePicker.tsx`

Enhanced the existing file picker modal to include:
- Local files dropdown at the top of the interface
- Seamless integration with existing Onyx file management
- Automatic refresh after adding local files
- Success/error notifications

## How It Works

### User Experience
1. User clicks the file upload button in chat interface
2. FilePickerModal opens with the new local files dropdown at the top
3. User can browse local files and folders using the dropdown
4. User selects a file or folder
5. System calls MCP server to add the file to Onyx
6. Success notification appears and file list refreshes
7. User can now use the file in their chat context

### Technical Flow
```
User Selection → LocalFilesDropdown → API Call → MCP Server → Onyx Integration → UI Refresh
```

## Features

### ✅ Implemented
- [x] Local files dropdown component
- [x] Search functionality
- [x] File and folder selection
- [x] Loading states and error handling
- [x] API endpoints for MCP integration
- [x] Integration with existing FilePickerModal
- [x] Success/error notifications
- [x] Responsive design
- [x] Dark mode support

### 🔄 Ready for MCP Integration
- [ ] Real MCP server connection (currently uses mock data)
- [ ] File content processing
- [ ] Progress tracking for large files
- [ ] Batch file operations

## Usage

### For Users
1. Open chat interface
2. Click the file upload button (📎 icon)
3. Use the "Browse local files..." dropdown at the top
4. Search and select files/folders
5. Files are automatically added to Onyx

### For Developers
```tsx
import { LocalFilesDropdown } from '@/components/LocalFilesDropdown';

<LocalFilesDropdown
  onFileSelect={(file) => console.log('File selected:', file)}
  onFolderSelect={(folder) => console.log('Folder selected:', folder)}
  placeholder="Select local files..."
/>
```

## API Reference

### GET /api/mcp/local-files
Returns list of local files and folders.

**Response:**
```json
{
  "success": true,
  "files": [
    {
      "name": "document.pdf",
      "path": "/Documents/document.pdf",
      "type": "file",
      "size": 1024000,
      "lastModified": "2024-01-01T00:00:00.000Z"
    }
  ]
}
```

### POST /api/mcp/local-files
Adds a local file or folder to Onyx.

**Request:**
```json
{
  "filePath": "/Documents/document.pdf",
  "fileName": "document.pdf",
  "fileType": "file"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully added document.pdf to Onyx",
  "fileId": "abc123def"
}
```

## Integration with MCP Server

The current implementation is ready for MCP server integration. To connect to a real MCP server:

1. Update the API endpoints to call the actual MCP server
2. Replace mock data with real file system access
3. Add proper error handling for MCP server responses
4. Implement file content processing

## Future Enhancements

- [ ] Drag and drop support
- [ ] File preview functionality
- [ ] Batch file selection
- [ ] File type filtering
- [ ] Recent files quick access
- [ ] File metadata display
- [ ] Progress bars for large file uploads

## Testing

To test the integration:

1. Start the development server: `npm run dev`
2. Navigate to the chat interface
3. Click the file upload button
4. Use the local files dropdown
5. Select files and verify they appear in the interface

## Notes

- The integration is non-breaking and doesn't affect existing functionality
- All components follow Onyx's design system and patterns
- Error handling is comprehensive with user-friendly messages
- The code is fully typed with TypeScript
- Components are responsive and work on all screen sizes
