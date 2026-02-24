# ShareTools

A comprehensive developer utilities suite with Web UI and MCP (Model Context Protocol) integration for AI-powered workflows.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-green?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/FastMCP-2.0%2B-orange?style=flat-square" alt="FastMCP">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License">
</p>

---

## ✨ Features

### GitHub Integration
- **Repository Clone** - Clone any GitHub repository with proxy support
- **File Download** - Download single files directly from GitHub

### Compression Tools
- **ZIP + Base64** - Compress folders to ZIP and encode as Base64 text
- **Merge to TXT** - Merge all files into a single structured TXT file

### Extraction Tools
- **Extract ZIP+Base64** - Decode Base64 and extract ZIP archives
- **Extract from TXT** - Restore original file structure from merged TXT

### File Management
- **Browse Folders** - Navigate and list directory contents
- **Browse Files** - View file contents with optional filtering

### Configuration
- **Proxy Support** - Separate proxy settings for Git and downloads
- **Custom Folders** - Configure parent directory for all operations

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start server (Web UI + MCP HTTP)
python server.py
```

The server will automatically open your browser to http://localhost:3000/ (Web UI) when it starts up.

---

## 📖 Architecture

```
PublicDocuments/
├── core.py              # ShareTools Core API (business logic)
├── server.py            # Web Server entry point (FastAPI) with auto browser open feature
├── public/
│   └── index.html       # Web UI
├── share-tools-skills/     # Claude/Trae Skill
│   ├── SKILL.md         # Skill definition
│   └── scripts/         # Skill scripts (use core.py)
├── config.json          # Runtime configuration
├── requirements.txt     # Python dependencies
    └── ...
```

### Module Design

| File | Description |
|------|-------------|
| `core.py` | Contains all business logic - reusable across projects |
| `server.py` | Web server + MCP protocol handlers - depends on core.py |

### ShareTools API Class

```python
from core import ShareToolsAPI

api = ShareToolsAPI()
```

---

## 🔌 Running Modes

| Command | Description | Ports | Browser Auto-Open |
|---------|-------------|-------|-------------------|
| `python server.py` | Web API + MCP HTTP (default) | 3000 | Yes, opens API docs at http://localhost:3000/docs |

---

## 🤖 MCP Integration

### Available Tools (ShareTools Prefix)

All MCP tools have the `sharetools_` prefix for easy AI recognition:

| Tool | Description | Parameters |
|------|-------------|------------|
| `sharetools_github_clone` | Clone a GitHub repository | `url` |
| `sharetools_github_download` | Download a file from GitHub | `url` |
| `sharetools_compress_zip` | Compress folder to Base64 ZIP | `source_folder`, `output_folder?` |
| `sharetools_compress_txt` | Merge folder to TXT | `source_folder`, `output_folder?` |
| `sharetools_extract_zip` | Extract Base64 ZIP | `input_file`, `output_folder?` |
| `sharetools_extract_txt` | Extract from merged TXT | `input_file`, `output_folder?` |
| `sharetools_get_config` | Get current configuration | - |
| `sharetools_set_config` | Set configuration | `parent_folder`, `proxy_*`, etc. |
| `sharetools_browse_folder` | Browse folder contents | `path?` |
| `sharetools_browse_file` | Browse file or folder | `path`, `filter?` |
| `sharetools_get_folders` | Get configured folder paths | - |

### MCP Configuration

**For Claude/Trae (Stdio):**
```json
{
  "mcpServers": {
    "command": "python",
    "args": ["server.py", "--mcp-stdio"]
    }
}
```

**For Claude/Trae (HTTP):**
```json
{
  "mcpServers": {
    "url": "http://localhost:3000/mcp/streamable-http"
    }
}
```

---

## 🛠️ API Usage (core.py)

Copy `core.py` to your project for direct API access:

```python
import asyncio
from core import api

# Clone repository
result = asyncio.run(api.github_clone('https://github.com/owner/repo'))

# Download file
result = asyncio.run(api.github_download('https://github.com/owner/repo/blob/main/file.txt'))

# Compress folder
result = asyncio.run(api.compress_zip('C:/path/to/folder'))

# Extract files
result = asyncio.run(api.extract_zip('C:/path/to/file.txt'))

# Get configuration
config = api.get_config()

# Set configuration
api.set_config({'parent_folder': 'my-files'})

# Browse folders
result = asyncio.run(api.browse_folder('C:/path'))

# Browse files
result = asyncio.run(api.browse_file('C:/path/to/file.txt'))
```

---

## 🌐 Web API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Get configuration |
| POST | `/api/config` | Set configuration |
| GET | `/api/folders` | Get folder paths |
| GET | `/api/system-info` | Get system information |
| POST | `/api/github/clone` | Clone repository |
| POST | `/api/github/download-file` | Download file |
| POST | `/api/compress/zip-base64` | Compress to ZIP+Base64 |
| POST | `/api/compress/txt` | Merge to TXT |
| POST | `/api/extract/zip-base64` | Extract ZIP+Base64 |
| POST | `/api/extract/txt` | Extract from TXT |
| GET | `/api/browse/folder` | Browse folder |
| GET | `/api/browse/file` | Browse file/folder |

---

## 🎓 Skill Usage

The `share-tools-skills` folder contains Python scripts that wrap `core.py`:

```bash
cd share-tools-skills/scripts

# Clone repository
python github_clone.py https://github.com/facebook/react

# Compress folder
python compress_zip.py "C:\Projects\myapp"

# Get configuration
python get_config.py
```

See [SKILL.md](share-tools-skills/SKILL.md) for detailed documentation.

---

## ⚙️ Configuration

### Default Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `parent_folder` | Base folder for all operations | `repo-files` |
| `proxy_enabled` | Enable proxy for git clone | `false` |
| `proxy_address` | Proxy server address | `127.0.0.1` |
| `proxy_port` | Proxy server port | `10808` |
| `download_proxy_enabled` | Enable proxy for downloads | `false` |
| `download_proxy_address` | Download proxy address | `127.0.0.1` |
| `download_proxy_port` | Download proxy port | `10808` |

### Default Folder Structure

```
repo-files/
├── github/     # Git clone destinations
├── compress/   # Compressed output
├── extract/    # Extracted files
└── download/   # Downloaded files
```

---

## 📦 Dependencies

```
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
fastmcp>=2.0.0
pydantic>=2.10.0
```

---

## 📝 License

MIT License - feel free to use in your projects.

---

## 🔗 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastMCP Documentation](https://fastmcp.wiki/)
- [MCP Protocol](https://modelcontextprotocol.io/)
