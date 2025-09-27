#!/usr/bin/env python3
"""
Start the Real MCP Server for Local File Access

This script starts the MCP server with proper configuration for real file access.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start the MCP server with real file access configuration."""
    
    # Get the script directory
    script_dir = Path(__file__).parent
    
    # Set environment variables for real file access
    os.environ["ALLOWED_DIRECTORIES"] = "/Users,/home,/Documents,/Desktop,/Downloads"
    os.environ["MAX_FILE_SIZE"] = "50000000"  # 50MB
    os.environ["ALLOWED_EXTENSIONS"] = ".txt,.md,.py,.js,.ts,.json,.yaml,.yml,.xml,.csv,.pdf,.docx,.doc,.html,.htm,.rtf,.odt"
    os.environ["ONYX_SERVER_URL"] = "http://localhost:3001"
    
    print("🚀 Starting Real MCP Server for Local File Access")
    print("=" * 50)
    print(f"Allowed Directories: {os.environ['ALLOWED_DIRECTORIES']}")
    print(f"Max File Size: {os.environ['MAX_FILE_SIZE']} bytes")
    print(f"Allowed Extensions: {os.environ['ALLOWED_EXTENSIONS']}")
    print(f"Onyx Server URL: {os.environ['ONYX_SERVER_URL']}")
    print("=" * 50)
    
    # Start the MCP server
    try:
        subprocess.run([
            sys.executable, 
            "mcp_server.py",
            "--transport", "http",
            "--host", "127.0.0.1",
            "--port", "8001",
            "--path", "/mcp",
            "--allowed-dirs", os.environ["ALLOWED_DIRECTORIES"],
            "--max-file-size", os.environ["MAX_FILE_SIZE"],
            "--allowed-extensions", os.environ["ALLOWED_EXTENSIONS"],
            "--onyx-server-url", os.environ["ONYX_SERVER_URL"]
        ], cwd=script_dir)
    except KeyboardInterrupt:
        print("\n🛑 MCP Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
