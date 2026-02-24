"""
ShareTools FastAPI Web Server
Provides HTTP API endpoints and MCP integration for ShareTools operations.
"""

import os
import sys
import getpass
import re
import asyncio
import warnings
import webbrowser
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

# Filter websockets deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn")

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from core import api, ensure_folders, load_config

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

    @staticmethod
    def colorize(text: str, *colors: str) -> str:
        """Apply colors to text"""
        return ''.join(colors) + text + Colors.END

WEB_PORT = 3000


# Request/Response Models
class GithubCloneRequest(BaseModel):
    url: str = Field(..., description="GitHub repository URL")


class GithubDownloadRequest(BaseModel):
    url: str = Field(..., description="GitHub file URL")


class CompressRequest(BaseModel):
    sourceFolder: str = Field(..., description="Source folder path")
    outputFolder: Optional[str] = Field(None, description="Output folder path")


class ExtractRequest(BaseModel):
    inputFile: str = Field(..., description="Input file path")
    outputFolder: Optional[str] = Field(None, description="Output folder path")


class ConfigRequest(BaseModel):
    parent_folder: Optional[str] = None
    proxy_enabled: Optional[bool] = None
    proxy_address: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_user: Optional[str] = None
    proxy_pass: Optional[str] = None
    download_proxy_enabled: Optional[bool] = None
    download_proxy_address: Optional[str] = None
    download_proxy_port: Optional[int] = None
    download_proxy_user: Optional[str] = None
    download_proxy_pass: Optional[str] = None


class BrowseFileRequest(BaseModel):
    path: str = Field(..., description="File or folder path")
    filter: Optional[str] = Field(None, description="File filter extension")


def create_mcp_server():
    """Create MCP server with ShareTools tools"""
    from fastmcp import FastMCP
    
    mcp = FastMCP("ShareTools")
    
    @mcp.tool()
    async def sharetools_github_clone(url: str) -> str:
        """ShareTools: Clone a GitHub repository"""
        result = await api.github_clone(url)
        return f"Successfully cloned to: {result['path']}"

    @mcp.tool()
    async def sharetools_github_download(url: str) -> str:
        """ShareTools: Download a single file from GitHub"""
        result = await api.github_download(url)
        return f"Successfully downloaded to: {result['path']}"

    @mcp.tool()
    async def sharetools_compress_zip(source_folder: str, output_folder: Optional[str] = None) -> str:
        """ShareTools: Compress folder to base64 ZIP"""
        result = await api.compress_zip(source_folder, output_folder)
        return f"Successfully compressed to: {result['outputPath']}"

    @mcp.tool()
    async def sharetools_compress_txt(source_folder: str, output_folder: Optional[str] = None) -> str:
        """ShareTools: Merge folder contents to a single TXT file"""
        result = await api.compress_txt(source_folder, output_folder)
        return f"Successfully merged {result.get('fileCount', 0)} files to: {result['outputPath']}"

    @mcp.tool()
    async def sharetools_extract_zip(input_file: str, output_folder: Optional[str] = None) -> str:
        """ShareTools: Extract base64 ZIP file"""
        result = await api.extract_zip(input_file, output_folder)
        return f"Successfully extracted to: {result['outputPath']}"

    @mcp.tool()
    async def sharetools_extract_txt(input_file: str, output_folder: Optional[str] = None) -> str:
        """ShareTools: Extract from merged TXT file"""
        result = await api.extract_txt(input_file, output_folder)
        return f"Successfully extracted {result.get('fileCount', 0)} files to: {result['outputPath']}"

    @mcp.tool()
    def sharetools_get_config() -> str:
        """ShareTools: Get current configuration"""
        import json
        config = api.get_config()
        return json.dumps(config, indent=2)

    @mcp.tool()
    def sharetools_set_config(
        parent_folder: Optional[str] = None,
        proxy_enabled: Optional[bool] = None,
        proxy_address: Optional[str] = None,
        proxy_port: Optional[int] = None,
        proxy_user: Optional[str] = None,
        proxy_pass: Optional[str] = None,
        download_proxy_enabled: Optional[bool] = None,
        download_proxy_address: Optional[str] = None,
        download_proxy_port: Optional[int] = None,
        download_proxy_user: Optional[str] = None,
        download_proxy_pass: Optional[str] = None
    ) -> str:
        """ShareTools: Set configuration"""
        params = {
            k: v for k, v in locals().items()
            if v is not None and k != "config_file"
        }
        api.set_config(params)
        return "Configuration updated successfully"

    @mcp.tool()
    async def sharetools_browse_folder(path: Optional[str] = None) -> str:
        """ShareTools: Browse folder contents"""
        result = await api.browse_folder(path)
        items_str = "\n".join([
            f"  {'[DIR]' if item['isDirectory'] else '[FILE]'} {item['name']}"
            for item in result['items'][:50]
        ])
        return f"Contents of {result['path']}:\n{items_str}"

    @mcp.tool()
    async def sharetools_browse_file(path: str, filter_ext: Optional[str] = None) -> str:
        """ShareTools: Browse file or folder"""
        result = await api.browse_file(path, filter_ext)
        if "items" in result:
            items_str = "\n".join([
                f"  {'[DIR]' if item['isDirectory'] else '[FILE]'} {item['name']}"
                for item in result['items'][:50]
            ])
            return f"Contents of {result['path']}:\n{items_str}"
        else:
            return f"File: {result['path']}\nSize: {result['size']} bytes\nBase64: {result['base64'][:100]}..."

    @mcp.tool()
    def sharetools_get_folders() -> str:
        """ShareTools: Get configured folder paths"""
        import json
        folders = api.get_folders()
        return json.dumps(folders, indent=2)
    
    return mcp


# Create MCP server and get HTTP app
mcp = create_mcp_server()
mcp_app = mcp.http_app(transport='http', path='/streamable-http')


# Create FastAPI application with MCP lifespan
app = FastAPI(
    title="ShareTools API",
    version="1.0.0",
    lifespan=mcp_app.lifespan
)


# API Routes
@app.get("/api/system-info")
async def system_info() -> Dict[str, Any]:
    """Get system information"""
    config = load_config()
    return {
        "platform": sys.platform,
        "user": getpass.getuser(),
        "parentFolder": config.parent_folder,
        "proxyEnabled": config.proxy_enabled,
        "downloadProxyEnabled": config.download_proxy_enabled
    }


@app.post("/api/github/clone")
async def github_clone(request: GithubCloneRequest) -> Dict[str, Any]:
    """Clone a GitHub repository"""
    try:
        return await api.github_clone(request.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/github/download-file")
async def github_download(request: GithubDownloadRequest) -> Dict[str, Any]:
    """Download a single file from GitHub"""
    try:
        return await api.github_download(request.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compress/zip-base64")
async def compress_zip(request: CompressRequest) -> Dict[str, Any]:
    """Compress folder to base64 ZIP"""
    try:
        return await api.compress_zip(request.sourceFolder, request.outputFolder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/compress/txt")
async def compress_txt(request: CompressRequest) -> Dict[str, Any]:
    """Merge folder to TXT"""
    try:
        return await api.compress_txt(request.sourceFolder, request.outputFolder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract/zip-base64")
async def extract_zip(request: ExtractRequest) -> Dict[str, Any]:
    """Extract base64 ZIP"""
    try:
        return await api.extract_zip(request.inputFile, request.outputFolder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract/txt")
async def extract_txt(request: ExtractRequest) -> Dict[str, Any]:
    """Extract from merged TXT"""
    try:
        return await api.extract_txt(request.inputFile, request.outputFolder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config() -> Dict[str, Any]:
    """Get current configuration"""
    return api.get_config()


@app.post("/api/config")
async def set_config(request: ConfigRequest) -> Dict[str, Any]:
    """Set configuration"""
    try:
        params = {k: v for k, v in request.dict().items() if v is not None}
        return api.set_config(params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/browse/folder")
async def browse_folder(
    path: Optional[str] = Query(None, description="Folder path")
) -> Dict[str, Any]:
    """Browse folder contents"""
    try:
        return await api.browse_folder(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/browse/file")
async def browse_file(
    path: str = Query(..., description="File or folder path"),
    filter: Optional[str] = Query(None, description="File extension filter")
) -> Dict[str, Any]:
    """Browse file or folder"""
    try:
        return await api.browse_file(path, filter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount MCP app at /mcp endpoint
app.mount("/mcp", mcp_app)

# Serve static files (if public folder exists)
if os.path.exists("public"):
    app.mount("/", StaticFiles(directory="public", html=True), name="static")


async def start_server():
    """Start combined Web API + MCP HTTP server on single port"""
    print()
    print(Colors.colorize("=" * 50, Colors.CYAN, Colors.BOLD))
    print(Colors.colorize("  ShareTools Server", Colors.CYAN, Colors.BOLD))
    print(Colors.colorize("=" * 50, Colors.CYAN, Colors.BOLD))
    print()
    print(Colors.colorize("Mode:", Colors.YELLOW), Colors.colorize("Web API + MCP HTTP (Single Port)", Colors.GREEN, Colors.BOLD))
    print()
    print(Colors.colorize("🌐 Web API:", Colors.BLUE), f"http://localhost:{WEB_PORT}")
    print(Colors.colorize("📚 API Docs:", Colors.MAGENTA), f"http://localhost:{WEB_PORT}/docs")
    print(Colors.colorize("🔌 MCP endpoint:", Colors.GREEN), f"http://localhost:{WEB_PORT}/mcp/streamable-http")
    print()
    
    # 在后台启动服务器
    config = uvicorn.Config(app, host="0.0.0.0", port=WEB_PORT, log_level="info")
    server = uvicorn.Server(config)
    
    # 创建一个任务在服务器启动后打开浏览器
    async def open_browser_after_delay():
        # 等待服务器启动（延迟几秒）
        await asyncio.sleep(2)
        # 尝试打开浏览器到API文档页面
        webbrowser.open(f"http://localhost:{WEB_PORT}")
        
    # 启动浏览器打开任务
    asyncio.create_task(open_browser_after_delay())
    
    await server.serve()


async def start_mcp_stdio():
    """Start MCP server in stdio mode"""
    print()
    print(Colors.colorize("=" * 50, Colors.CYAN, Colors.BOLD))
    print(Colors.colorize("  ShareTools Server", Colors.CYAN, Colors.BOLD))
    print(Colors.colorize("=" * 50, Colors.CYAN, Colors.BOLD))
    print()
    print(Colors.colorize("Mode:", Colors.YELLOW), Colors.colorize("MCP Stdio Only", Colors.GREEN, Colors.BOLD))
    print()
    ensure_folders()
    await mcp.run_stdio_async()


async def main():
    """Main entry point"""
    args = sys.argv[1:]
    mode = args[0] if args else ""

    ensure_folders()

    if mode == "--mcp-stdio":
        await start_mcp_stdio()
    else:
        # Default: Combined mode (Web API + MCP on same port)
        await start_server()


if __name__ == "__main__":
    asyncio.run(main())
