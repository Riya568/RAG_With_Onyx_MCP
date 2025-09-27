import React, { useState, useRef, useEffect } from "react";
import { FolderIcon, FileIcon, ChevronDownIcon, SearchIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface LocalFile {
  name: string;
  path: string;
  type: 'file' | 'folder';
  size?: number;
  lastModified?: Date;
}

interface LocalFilesDropdownProps {
  onFileSelect: (file: LocalFile) => void;
  onFolderSelect: (folder: LocalFile) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const LocalFilesDropdown: React.FC<LocalFilesDropdownProps> = ({
  onFileSelect,
  onFolderSelect,
  disabled = false,
  placeholder = "Select local files..."
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [localFiles, setLocalFiles] = useState<LocalFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Enhanced mock data with more realistic structure
  const mockLocalFiles: LocalFile[] = [
    { name: "Documents", path: "/Documents", type: "folder", lastModified: new Date() },
    { name: "Downloads", path: "/Downloads", type: "folder", lastModified: new Date() },
    { name: "Desktop", path: "/Desktop", type: "folder", lastModified: new Date() },
    { name: "Pictures", path: "/Pictures", type: "folder", lastModified: new Date() },
    { name: "report.pdf", path: "/Documents/report.pdf", type: "file", size: 1024000, lastModified: new Date() },
    { name: "presentation.pptx", path: "/Documents/presentation.pptx", type: "file", size: 2048000, lastModified: new Date() },
    { name: "notes.txt", path: "/Desktop/notes.txt", type: "file", size: 512, lastModified: new Date() },
    { name: "config.json", path: "/Desktop/config.json", type: "file", size: 1024, lastModified: new Date() },
    { name: "photo1.jpg", path: "/Pictures/photo1.jpg", type: "file", size: 1536000, lastModified: new Date() },
    { name: "photo2.png", path: "/Pictures/photo2.png", type: "file", size: 2560000, lastModified: new Date() },
  ];

  // Load local files from MCP server
  const loadLocalFiles = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/mcp/local-files');
      const data = await response.json();
      
      if (data.success) {
        setLocalFiles(data.files);
      } else {
        throw new Error(data.error || 'Failed to load files');
      }
    } catch (err) {
      setError("Failed to load local files");
      console.error("Error loading local files:", err);
      // Fallback to mock data for demo
      setLocalFiles(mockLocalFiles);
    } finally {
      setIsLoading(false);
    }
  };

  // Filter files based on search query
  const filteredFiles = localFiles.filter(file =>
    file.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Handle file/folder selection
  const handleItemClick = (item: LocalFile) => {
    if (item.type === 'folder') {
      onFolderSelect(item);
    } else {
      onFileSelect(item);
    }
    setIsOpen(false);
    setSearchQuery("");
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Load files when dropdown opens
  useEffect(() => {
    if (isOpen && localFiles.length === 0) {
      loadLocalFiles();
    }
  }, [isOpen, localFiles.length]);

  return (
    <div className="relative" ref={dropdownRef}>
      <Button
        variant="outline"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className="w-full justify-between"
      >
        <span className="flex items-center gap-2">
          <FolderIcon size={16} />
          {placeholder}
        </span>
        <ChevronDownIcon 
          size={16} 
          className={`transition-transform ${isOpen ? 'rotate-180' : ''}`}
        />
      </Button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-700 rounded-md shadow-lg max-h-[300px] overflow-hidden">
          {/* Search input */}
          <div className="p-2 border-b border-neutral-200 dark:border-neutral-700">
            <div className="relative">
              <SearchIcon 
                size={16} 
                className="absolute left-2 top-1/2 transform -translate-y-1/2 text-neutral-400"
              />
              <Input
                ref={inputRef}
                placeholder="Search files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8"
                autoFocus
              />
            </div>
          </div>

          {/* Files list */}
          <div className="max-h-[200px] overflow-y-auto">
            {isLoading ? (
              <div className="p-4 text-center text-sm text-neutral-500">
                Loading local files...
              </div>
            ) : error ? (
              <div className="p-4 text-center text-sm text-red-500">
                {error}
              </div>
            ) : filteredFiles.length === 0 ? (
              <div className="p-4 text-center text-sm text-neutral-500">
                {searchQuery ? "No files found" : "No local files available"}
              </div>
            ) : (
              filteredFiles.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-2 p-2 hover:bg-neutral-100 dark:hover:bg-neutral-800 cursor-pointer"
                  onClick={() => handleItemClick(file)}
                >
                  {file.type === 'folder' ? (
                    <FolderIcon size={16} className="text-blue-500" />
                  ) : (
                    <FileIcon size={16} className="text-neutral-500" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">
                      {file.name}
                    </div>
                    <div className="text-xs text-neutral-500 truncate">
                      {file.path}
                    </div>
                  </div>
                  {file.size && (
                    <div className="text-xs text-neutral-400">
                      {(file.size / 1024).toFixed(1)} KB
                    </div>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Footer with refresh button */}
          <div className="p-2 border-t border-neutral-200 dark:border-neutral-700">
            <Button
              variant="ghost"
              size="sm"
              onClick={loadLocalFiles}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? "Refreshing..." : "Refresh Files"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
