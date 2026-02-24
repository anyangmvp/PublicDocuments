---
name: share-tools
description: |
  ShareTools - A comprehensive developer utilities suite with GitHub integration, file compression/extraction, and file management capabilities.
  
  Use this skill when users need to:
  - Clone GitHub repositories or download files from GitHub
  - Compress folders to ZIP+Base64 or merge files to TXT
  - Extract ZIP archives or restore files from merged TXT
  - Browse folders and manage files
  - Configure proxy settings for network operations
  
  All operations are performed through the ShareToolsAPI class in core.py.
---

# ShareTools Skill

ShareTools provides developer utilities for file operations, GitHub integration, and data compression/extraction.

## Core API

All functionality is exposed through the `ShareToolsAPI` class in `core.py`:

```python
from core import ShareToolsAPI

# All methods are static, no instantiation needed
result = await ShareToolsAPI.github_clone(url: str)
```
## Available Operations

### GitHub Operations

#### Clone Repository
```python
result = await ShareToolsAPI.github_clone(url: str)
# Returns: {"success": True, "path": "repo-files/github/repo-name"}
```

#### Download File
```python
result = await ShareToolsAPI.github_download(url: str)
# Returns: {"success": True, "path": "repo-files/download/filename"}
```

### Compression Operations

#### ZIP + Base64
```python
result = await ShareToolsAPI.compress_zip(
    source_folder: str,
    output_folder: Optional[str] = None
)
# Returns: {"success": True, "outputPath": "path/to/BS64_sizeK_foldername.txt"}
```

#### Merge to TXT
```python
result = await ShareToolsAPI.compress_txt(
    source_folder: str,
    output_folder: Optional[str] = None
)
# Returns: {"success": True, "outputPath": "path/to/MERGE_sizeK_foldername.txt", "fileCount": N, "skipCount": M}
```

### Extraction Operations

#### Extract ZIP+Base64
```python
result = await ShareToolsAPI.extract_zip(
    input_file: str,
    output_folder: Optional[str] = None
)
# Returns: {"success": True, "outputPath": "path/to/extracted"}
```

#### Extract from TXT
```python
result = await ShareToolsAPI.extract_txt(
    input_file: str,
    output_folder: Optional[str] = None
)
# Returns: {"success": True, "outputPath": "path/to/extracted", "fileCount": N}
```

### File Management

#### Browse Folder
```python
result = await ShareToolsAPI.browse_folder(path: Optional[str] = None)
# Returns: {"path": "/full/path", "items": [{"name": "...", "isDirectory": bool, "size": N, "modified": "..."}]}
```

#### Browse File
```python
result = await ShareToolsAPI.browse_file(path: str, filter_ext: Optional[str] = None)
# Returns folder contents or file details with base64 content
```

### Configuration

#### Get Config
```python
config = ShareToolsAPI.get_config()
# Returns current configuration dict
```

#### Set Config
```python
ShareToolsAPI.set_config({
    "parent_folder": "repo-files",
    "proxy_enabled": True,
    "proxy_address": "127.0.0.1",
    "proxy_port": 10808,
    # ... other options
})
```

## Folder Structure

All operations use the configured parent folder (default: `repo-files`):

```
repo-files/
├── github/       # Cloned repositories
├── download/     # Downloaded files
├── compress/     # Compressed outputs
└── extract/      # Extracted outputs
```

## Proxy Configuration

Two separate proxy settings:
- **Git Proxy**: For `github_clone` operations
- **Download Proxy**: For `github_download` operations

## Usage Examples

### Clone and Compress
```python
# Clone a repository
result = await ShareToolsAPI.github_clone("https://github.com/user/repo")
repo_path = result["path"]

# Compress the cloned repository
result = await ShareToolsAPI.compress_zip(repo_path)
print(f"Compressed to: {result['outputPath']}")
```

### Extract and Browse
```python
# Extract an archive
result = await ShareToolsAPI.extract_zip("path/to/archive.txt")
extract_path = result["outputPath"]

# Browse extracted contents
result = await ShareToolsAPI.browse_folder(extract_path)
for item in result["items"]:
    print(f"{'[DIR]' if item['isDirectory'] else '[FILE]'} {item['name']}")
```

## Error Handling

All methods raise exceptions on failure. Wrap calls in try-except:

```python
try:
    result = await ShareToolsAPI.github_clone(url)
except Exception as e:
    print(f"Error: {e}")
```

## Dependencies

- fastapi
- uvicorn
- fastmcp
- pydantic

Install with: `pip install -r requirements.txt`
