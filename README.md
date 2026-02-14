# DevToolkit

Developer Utilities Suite - A modern web-based tool for developer tasks.

## Features

### GitHub Clone
- Clone GitHub repositories to local folder
- Auto-detect proxy status (default port: 10808)
- Use proxy for clone if enabled
- **Hidden automatically** if Windows username is numeric (e.g., 10808)

### Download
- Download single files from GitHub
- Automatically converts GitHub URL to raw.githubusercontent.com URL
- Separate proxy settings for download (independent from clone proxy)
- Default proxy port: 10808

### Compress
- **ZIP + Base64**: Compress folder to ZIP, then encode as Base64
- **Merge to TXT**: Merge all files into a single TXT file
- Auto-exclude build artifacts: `.git`, `node_modules`, `target`, `build`, `__pycache__`, etc.

### Extract
- **Extract ZIP+Base64**: Decode Base64 and extract ZIP
- **Extract TXT**: Restore files from merged TXT

### Operation Logs
- Records all operations (clone, download, compress, extract)
- Displays operation details including file paths
- One-click path copying
- Persistent storage in localStorage
- Slide-out panel on the right side of the screen

## Quick Start

```bash
npm install
npm start
```

Then open http://localhost:3000

## Proxy Detection

### GitHub Clone
The app will automatically detect if a proxy is running on port 10808:

1. **Proxy available but not enabled**: Shows warning that proxy is available
2. **Proxy enabled but not running**: Shows error to start proxy
3. **Proxy enabled and running**: Uses proxy for git clone

### File Download
- Separate proxy setting for file download
- Configure in Settings - "Download Proxy" section
- Default port: 10808

## Settings

| Setting | Description | Default |
|---------|-------------|---------|
| Parent Folder | Base folder for all operations | ABC folder |
| Enable GitHub Clone | Show/hide clone tab | Auto (hidden if username is numeric) |
| Proxy (Clone) | Proxy for git clone | Port 10808 |
| Download Proxy | Proxy for file download | Port 10808 |

## Theme

Toggle between Dark/Light mode using the button in the top-right corner.

## Tech Stack

- **Frontend**: Pure HTML/CSS/JS with modern design
- **Backend**: Node.js + Express
- **Compression**: 7-Zip (via command line)
- **Download**: cURL

## Folder Structure

All operations use folders under the parent folder:

```
ABC folder/
├── github/     # Git clone destinations
├── compress/   # Compressed output
├── extract/    # Extracted files
└── download/   # Downloaded files
```
