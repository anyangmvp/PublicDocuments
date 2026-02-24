"""
ShareTools Core Module
Provides core functionality for GitHub operations, compression, and extraction.
"""

import os
import json
import base64
import shutil
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

DEFAULT_PARENT = "repo-files"

EXCLUDE_PATTERNS = [
    ".git", ".svn", ".hg", ".gitignore", ".gitattributes",
    "node_modules", "bower_components", "vendor",
    "target", "build", "dist", "out",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".tox",
    "venv", ".venv", "env", ".env",
    "bin", "obj", "packages",
    "*.pyc", "*.pyo", "*.class", "*.o", "*.so", "*.dll", "*.dylib",
    "*.exe", "*.jar", "*.war", "*.ear",
    "*.log", "*.tmp", "*.temp",
    "Thumbs.db", ".DS_Store", "desktop.ini"
]


@dataclass
class Config:
    """Configuration dataclass"""
    parent_folder: str = DEFAULT_PARENT
    proxy_enabled: bool = False
    proxy_address: str = "127.0.0.1"
    proxy_port: int = 10808
    proxy_user: str = ""
    proxy_pass: str = ""
    download_proxy_enabled: bool = False
    download_proxy_address: str = "127.0.0.1"
    download_proxy_port: int = 10808
    download_proxy_user: str = ""
    download_proxy_pass: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


def load_config(config_file: str = "config.json") -> Config:
    """Load configuration from file"""
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Config.from_dict(data)
        except Exception:
            pass
    return Config()


def save_config(config: Config, config_file: str = "config.json") -> None:
    """Save configuration to file"""
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2)


def get_7z_path() -> str:
    """Get 7z executable path"""
    paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\77z.exe",
        "7z"
    ]
    for p in paths:
        if p == "7z" or os.path.exists(p):
            return p
    return "7z"


def get_folder(subfolder: str, config: Optional[Config] = None) -> str:
    """Get folder path"""
    if config is None:
        config = load_config()
    return os.path.join(config.parent_folder or DEFAULT_PARENT, subfolder)


def ensure_folders(config: Optional[Config] = None) -> None:
    """Ensure required folders exist"""
    if config is None:
        config = load_config()
    for folder in ["github", "compress", "extract", "download"]:
        dir_path = get_folder(folder, config)
        os.makedirs(dir_path, exist_ok=True)


def should_exclude(file_path: str) -> bool:
    """Check if file should be excluded"""
    name = os.path.basename(file_path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern or pattern in name:
            return True
    return False


def run_command(cmd: str, cwd: Optional[str] = None) -> Tuple[str, str]:
    """Run shell command"""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=True,
        encoding="utf-8",
        errors="ignore"
    )
    if result.returncode != 0:
        raise Exception(f"Command failed: {result.stderr}")
    return result.stdout, result.stderr


def generate_id() -> str:
    """Generate random ID"""
    import secrets
    return secrets.token_hex(8)


def build_git_clone_command(url: str, target_path: str, config: Config) -> str:
    """Build git clone command with proxy"""
    proxy_port = config.proxy_port or 10808
    proxy_address = config.proxy_address or "127.0.0.1"

    if not config.proxy_enabled:
        return f'git clone "{url}" "{target_path}"'

    if config.proxy_user and config.proxy_pass:
        proxy = f"http://{config.proxy_user}:{config.proxy_pass}@{proxy_address}:{proxy_port}"
    else:
        proxy = f"http://{proxy_address}:{proxy_port}"

    return f'git clone -c http.proxy={proxy} -c https.proxy={proxy} "{url}" "{target_path}"'


def build_curl_command(url: str, file_path: str, config: Config) -> str:
    """Build curl command with proxy"""
    proxy_port = config.download_proxy_port or 10808
    proxy_address = config.download_proxy_address or "127.0.0.1"

    if not config.download_proxy_enabled:
        return f'curl -L -o "{file_path}" "{url}"'

    if config.download_proxy_user and config.download_proxy_pass:
        proxy = f"http://{config.download_proxy_user}:{config.download_proxy_pass}@{proxy_address}:{proxy_port}"
    else:
        proxy = f"http://{proxy_address}:{proxy_port}"

    return f'curl -x {proxy} -L -o "{file_path}" "{url}"'


def walk_dir_for_merge(source_folder: str, write_file) -> Dict[str, int]:
    """Walk directory and merge files"""
    file_count = 0
    skip_count = 0

    def walk(dir_path: str):
        nonlocal file_count, skip_count
        try:
            items = os.listdir(dir_path)
        except PermissionError:
            return

        dirs = sorted([i for i in items if os.path.isdir(os.path.join(dir_path, i))])
        files = sorted([i for i in items if os.path.isfile(os.path.join(dir_path, i))])

        for d in dirs:
            if not should_exclude(d):
                walk(os.path.join(dir_path, d))

        for f in files:
            file_path = os.path.join(dir_path, f)
            if should_exclude(file_path):
                skip_count += 1
                continue

            rel_path = os.path.relpath(file_path, source_folder)
            write_file.write(f"\n===FILE:{rel_path}===\n")

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as rf:
                    write_file.write(rf.read())
            except Exception:
                write_file.write("[Binary file or read error]")

            write_file.write("\n===END===\n")
            file_count += 1

    walk(source_folder)
    return {"file_count": file_count, "skip_count": skip_count}


def extract_txt_to_folder(content: str, out_dir: str) -> Dict[str, int]:
    """Extract merged TXT to folder"""
    lines = content.split("\n")
    current_file = None
    current_content = []
    in_content = False
    file_count = 0

    for line in lines:
        if line.startswith("===MERGE_INFO:"):
            continue

        if line.startswith("===FILE:"):
            if current_file:
                full_path = os.path.join(out_dir, current_file.replace("\\", "/"))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(current_content))
                file_count += 1
            current_file = line[8:].replace("===", "").strip()
            current_content = []
            in_content = True
        elif line.strip() == "===END===":
            if current_file:
                full_path = os.path.join(out_dir, current_file.replace("\\", "/"))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(current_content))
                file_count += 1
                current_file = None
                current_content = []
                in_content = False
        elif in_content and current_file is not None:
            current_content.append(line)

    if current_file:
        full_path = os.path.join(out_dir, current_file.replace("\\", "/"))
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(current_content))
        file_count += 1

    return {"file_count": file_count}


class ShareToolsAPI:
    """ShareTools API class"""

    @staticmethod
    async def github_clone(url: str, config_file: str = "config.json") -> Dict[str, Any]:
        """Clone a GitHub repository"""
        if not url:
            raise ValueError("URL is required")

        config = load_config(config_file)
        target_dir = get_folder("github", config)
        os.makedirs(target_dir, exist_ok=True)

        repo_name = url.replace(".git", "").split("/")[-1]
        target_path = os.path.join(target_dir, repo_name)

        if os.path.exists(target_path):
            shutil.rmtree(target_path)

        # Only pass repo_name to git clone, not full path (git runs in target_dir)
        cmd = build_git_clone_command(url, repo_name, config)
        run_command(cmd, target_dir)

        return {"success": True, "path": target_path}

    @staticmethod
    async def github_download(url: str, config_file: str = "config.json") -> Dict[str, Any]:
        """Download a single file from GitHub"""
        if not url:
            raise ValueError("URL is required")

        config = load_config(config_file)

        # Convert GitHub URL to raw URL
        if "github.com" in url and "raw.githubusercontent.com" not in url:
            raw_url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        else:
            raw_url = url

        download_dir = get_folder("download", config)
        os.makedirs(download_dir, exist_ok=True)

        file_name = raw_url.split("/")[-1] or "download"
        file_path = os.path.join(download_dir, file_name)

        cmd = build_curl_command(raw_url, file_path, config)
        run_command(cmd)

        if not os.path.exists(file_path):
            raise Exception("Download failed")

        return {"success": True, "path": file_path}

    @staticmethod
    async def compress_zip(source_folder: str, output_folder: Optional[str] = None,
                           config_file: str = "config.json") -> Dict[str, Any]:
        """Compress folder to base64 ZIP"""
        if not source_folder or not os.path.exists(source_folder):
            raise ValueError("Invalid source folder")

        config = load_config(config_file)
        out_dir = output_folder or get_folder("compress", config)
        os.makedirs(out_dir, exist_ok=True)

        folder_name = os.path.basename(source_folder)
        temp_zip = os.path.join(tempfile.gettempdir(), f"{folder_name}_{generate_id()}.zip")

        # Build exclude arguments - use simpler wildcard patterns
        exclude_args = []
        for pattern in EXCLUDE_PATTERNS:
            if pattern.startswith("*"):
                # Extension patterns like *.pyc
                exclude_args.append(f'-x!{pattern}')
            else:
                # Directory/file patterns - just use the pattern with wildcard
                exclude_args.append(f'-x!{pattern}')

        cmd = f'"{get_7z_path()}" a -r -tzip "{temp_zip}" "{source_folder}\\*" {" ".join(exclude_args)}'
        run_command(cmd)

        if not os.path.exists(temp_zip):
            raise Exception("Failed to create ZIP")

        with open(temp_zip, "rb") as f:
            zip_content = f.read()

        base64_content = base64.b64encode(zip_content).decode("utf-8")
        size_kb = (len(zip_content) + 1023) // 1024

        output_path = os.path.join(out_dir, f"BS64_{size_kb}K_{folder_name}.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(base64_content)

        os.remove(temp_zip)

        return {"success": True, "outputPath": output_path}

    @staticmethod
    async def compress_txt(source_folder: str, output_folder: Optional[str] = None,
                           config_file: str = "config.json") -> Dict[str, Any]:
        """Merge folder to TXT"""
        if not source_folder or not os.path.exists(source_folder):
            raise ValueError("Invalid source folder")

        config = load_config(config_file)
        out_dir = output_folder or get_folder("compress", config)
        os.makedirs(out_dir, exist_ok=True)

        folder_name = os.path.basename(source_folder)
        output_path = os.path.join(out_dir, f"{folder_name}.txt")

        with open(output_path, "w", encoding="utf-8") as wf:
            wf.write(f"===MERGE_INFO:folder={folder_name}===\n")
            result = walk_dir_for_merge(source_folder, wf)

        stats = os.stat(output_path)
        size_kb = (stats.st_size + 1023) // 1024
        final_path = os.path.join(out_dir, f"MERGE_{size_kb}K_{folder_name}.txt")
        os.rename(output_path, final_path)

        return {
            "success": True,
            "outputPath": final_path,
            "fileCount": result["file_count"],
            "skipCount": result["skip_count"]
        }

    @staticmethod
    async def extract_zip(input_file: str, output_folder: Optional[str] = None,
                          config_file: str = "config.json") -> Dict[str, Any]:
        """Extract base64 ZIP"""
        if not input_file or not os.path.exists(input_file):
            raise ValueError("Invalid input file")

        config = load_config(config_file)
        base_out_dir = output_folder or get_folder("extract", config)
        os.makedirs(base_out_dir, exist_ok=True)

        out_dir = os.path.join(base_out_dir, os.path.splitext(os.path.basename(input_file))[0])
        os.makedirs(out_dir, exist_ok=True)

        with open(input_file, "rb") as f:
            raw_content = f.read()

        # Check if content is base64
        content_str = raw_content.decode("utf-8", errors="ignore").strip()
        is_base64 = bool(re.match(r'^[A-Za-z0-9+/=]+$', content_str)) and len(raw_content) % 4 == 0

        if is_base64:
            zip_buffer = base64.b64decode(content_str)
        else:
            zip_buffer = raw_content

        temp_zip = os.path.join(tempfile.gettempdir(), f"extract_{generate_id()}.zip")

        with open(temp_zip, "wb") as f:
            f.write(zip_buffer)

        cmd = f'"{get_7z_path()}" x -y -o"{out_dir}" "{temp_zip}"'
        run_command(cmd)
        os.remove(temp_zip)

        return {"success": True, "outputPath": out_dir}

    @staticmethod
    async def extract_txt(input_file: str, output_folder: Optional[str] = None,
                          config_file: str = "config.json") -> Dict[str, Any]:
        """Extract from merged TXT"""
        if not input_file or not os.path.exists(input_file):
            raise ValueError("Invalid input file")

        config = load_config(config_file)
        base_out_dir = output_folder or get_folder("extract", config)
        os.makedirs(base_out_dir, exist_ok=True)

        out_dir = os.path.join(base_out_dir, os.path.splitext(os.path.basename(input_file))[0])
        os.makedirs(out_dir, exist_ok=True)

        with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        result = extract_txt_to_folder(content, out_dir)

        return {"success": True, "outputPath": out_dir, "fileCount": result["file_count"]}

    @staticmethod
    def get_config(config_file: str = "config.json") -> Dict[str, Any]:
        """Get current configuration"""
        return load_config(config_file).to_dict()

    @staticmethod
    def set_config(params: Dict[str, Any], config_file: str = "config.json") -> Dict[str, Any]:
        """Set configuration"""
        config = Config.from_dict(params)
        save_config(config, config_file)
        ensure_folders(config)
        return {"success": True}

    @staticmethod
    async def browse_folder(target_path: Optional[str] = None) -> Dict[str, Any]:
        """Browse folder contents"""
        dir_path = target_path or os.path.expanduser("~")
        if not os.path.exists(dir_path):
            raise ValueError("Path not found")

        items = []
        try:
            for name in os.listdir(dir_path):
                full_path = os.path.join(dir_path, name)
                try:
                    stat = os.stat(full_path)
                    items.append({
                        "name": name,
                        "isDirectory": os.path.isdir(full_path),
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except (OSError, PermissionError):
                    continue
        except PermissionError:
            pass

        return {"path": dir_path, "items": items}

    @staticmethod
    async def browse_file(file_path: str, filter_ext: Optional[str] = None) -> Dict[str, Any]:
        """Browse file or folder"""
        if not file_path or not os.path.exists(file_path):
            raise ValueError("File not found")

        stat = os.stat(file_path)

        if os.path.isdir(file_path):
            items = []
            try:
                for name in os.listdir(file_path):
                    if filter_ext and not name.endswith(filter_ext):
                        continue
                    items.append({
                        "name": name,
                        "isDirectory": os.path.isdir(os.path.join(file_path, name))
                    })
            except PermissionError:
                pass
            return {"path": file_path, "items": items}
        else:
            with open(file_path, "rb") as f:
                content = f.read()
            return {
                "path": file_path,
                "size": stat.st_size,
                "base64": base64.b64encode(content).decode("utf-8")
            }

    @staticmethod
    def get_folders(config_file: str = "config.json") -> Dict[str, str]:
        """Get configured folder paths"""
        config = load_config(config_file)
        parent = config.parent_folder or DEFAULT_PARENT
        return {
            "github": os.path.join(parent, "github"),
            "compress": os.path.join(parent, "compress"),
            "extract": os.path.join(parent, "extract"),
            "download": os.path.join(parent, "download")
        }


# Create API instance for easy import
api = ShareToolsAPI()
