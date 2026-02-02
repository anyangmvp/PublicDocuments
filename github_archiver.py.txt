#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import shutil
import base64
from pathlib import Path
from typing import Optional, List
import argparse


class GitHubProjectArchiver:
    """GitHub 项目压缩和还原工具"""

    def __init__(self, output_dir: str = "./archives", publish_dir: Optional[str] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.publish_dir = Path(publish_dir) if publish_dir else None

    def clone_github_repo(self, repo_url: str, target_dir: Optional[Path] = None, proxy: str = None) -> Path:
        """克隆 GitHub 仓库"""
        if target_dir is None:
            repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
            target_dir = self.output_dir / repo_name

        if target_dir.exists():
            print(f"删除已存在的目录: {target_dir}")
            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                print(f"删除失败，尝试使用系统命令: {e}")
                try:
                    if os.name == 'nt':
                        subprocess.run(['cmd', '/c', 'rmdir', '/s', '/q', str(target_dir)], 
                                     check=True, capture_output=True)
                    else:
                        subprocess.run(['rm', '-rf', str(target_dir)], 
                                     check=True, capture_output=True)
                except Exception as e2:
                    print(f"删除目录失败: {e2}")
                    raise

        print(f"正在克隆仓库: {repo_url}")
        
        # 设置代理
        env = os.environ.copy()
        if proxy:
            env['HTTP_PROXY'] = proxy
            env['HTTPS_PROXY'] = proxy
            env['http_proxy'] = proxy
            env['https_proxy'] = proxy
            print(f"使用代理: {proxy}")
        
        try:
            subprocess.run(
                ["git", "clone", repo_url, str(target_dir)],
                check=True,
                capture_output=True,
                text=True,
                env=env
            )
            print(f"克隆完成: {target_dir}")
            return target_dir
        except subprocess.CalledProcessError as e:
            print(f"克隆失败: {e}")
            print(f"错误输出: {e.stderr}")
            raise

    def compress_project(self, project_path: str, archive_name: Optional[str] = None) -> List[Path]:
        """压缩项目到文件（同时生成纯文本和压缩格式）"""
        project_path = Path(project_path)
        if not project_path.exists():
            raise FileNotFoundError(f"项目路径不存在: {project_path}")

        if archive_name is None:
            archive_name = f"{project_path.name}"

        txt_archive_path = self.output_dir / f"{archive_name}.txt"
        b64_archive_path = self.output_dir / f"{archive_name}.b64.txt"

        print(f"正在压缩项目: {project_path}")

        # 生成纯文本格式
        print(f"生成纯文本格式: {txt_archive_path}")
        with open(txt_archive_path, 'w', encoding='utf-8') as f:
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if d != '.git']
                for file in files:
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(project_path.parent)
                    
                    f.write(f"=== FILE: {relative_path} ===\n")
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as source_file:
                            content = source_file.read()
                            f.write(content)
                    except UnicodeDecodeError:
                        with open(file_path, 'rb') as source_file:
                            content = source_file.read()
                            f.write(f"[二进制文件: {len(content)} 字节]")
                    f.write("\n\n")

        print(f"纯文本格式完成: {txt_archive_path}")

        # 生成 7z+Base64 格式
        print(f"生成压缩格式: {b64_archive_path}")
        sevenz_temp_path = self.output_dir / f"{archive_name}.7z"
        
        # 检查 7z 是否可用
        try:
            subprocess.run(['7z'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("警告: 未找到 7z，使用 ZIP 压缩")
            import zipfile
            sevenz_temp_path = self.output_dir / f"{archive_name}.zip"
            with zipfile.ZipFile(sevenz_temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_path):
                    dirs[:] = [d for d in dirs if d != '.git']
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(project_path.parent)
                        zipf.write(file_path, arcname)
        else:
            # 使用 7z 压缩（最高压缩率）
            subprocess.run(
                ['7z', 'a', '-t7z', '-mx9', '-m0=lzma2', str(sevenz_temp_path), str(project_path) + '/*'],
                check=True,
                capture_output=True,
                text=True
            )

        # 转换为 base64
        with open(sevenz_temp_path, 'rb') as f:
            compressed_data = f.read()
        
        base64_data = base64.b64encode(compressed_data).decode('utf-8')
        with open(b64_archive_path, 'w', encoding='utf-8') as f:
            f.write(base64_data)

        # 删除临时压缩文件
        sevenz_temp_path.unlink()

        print(f"压缩格式完成: {b64_archive_path}")

        return [txt_archive_path, b64_archive_path]

    def archive_github_repo(self, repo_url: str, archive_name: Optional[str] = None, proxy: str = None) -> List[Path]:
        """直接从 GitHub URL 压缩项目"""
        repo_dir = self.clone_github_repo(repo_url, proxy=proxy)
        try:
            return self.compress_project(repo_dir, archive_name)
        finally:
            shutil.rmtree(repo_dir, ignore_errors=True)

    def extract_archive(self, archive_path: str, target_dir: Optional[str] = None) -> Path:
        """解压归档文件（支持纯文本和压缩格式）"""
        archive_path = Path(archive_path)
        if not archive_path.exists():
            raise FileNotFoundError(f"归档文件不存在: {archive_path}")

        if target_dir is None:
            target_dir = self.output_dir

        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"正在解压归档: {archive_path}")
        print(f"目标目录: {target_dir}")

        # 判断格式
        if '.b64' in archive_path.name:
            # Base64 格式
            print("检测到 Base64 压缩格式")
            with open(archive_path, 'r', encoding='utf-8') as f:
                base64_data = f.read()
            
            compressed_data = base64.b64decode(base64_data)
            compressed_temp_path = self.output_dir / f"{archive_path.stem}_temp.7z"
            
            # 检查压缩格式并解压
            try:
                # 尝试使用 7z 解压
                with open(compressed_temp_path, 'wb') as f:
                    f.write(compressed_data)
                
                subprocess.run(
                    ['7z', 'x', str(compressed_temp_path), f'-o{target_dir}', '-y'],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # 7z 不可用，尝试使用 ZIP
                print("7z 不可用，使用 ZIP 解压")
                import zipfile
                compressed_temp_path = self.output_dir / f"{archive_path.stem}_temp.zip"
                with open(compressed_temp_path, 'wb') as f:
                    f.write(compressed_data)
                
                with zipfile.ZipFile(compressed_temp_path, 'r') as zipf:
                    zipf.extractall(target_dir)
            
            compressed_temp_path.unlink()
        else:
            # 纯文本格式
            print("检测到纯文本格式")
            with open(archive_path, 'r', encoding='utf-8') as f:
                content = f.read()

            current_file = None
            current_content = []
            file_marker = "=== FILE: "

            for line in content.split('\n'):
                if line.startswith(file_marker):
                    if current_file:
                        file_path = target_dir / current_file
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(file_path, 'w', encoding='utf-8') as out_file:
                            out_file.write('\n'.join(current_content))
                    
                    current_file = line[len(file_marker):-3]
                    current_content = []
                elif current_file is not None:
                    current_content.append(line)

            if current_file:
                file_path = target_dir / current_file
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as out_file:
                    out_file.write('\n'.join(current_content))

        print(f"解压完成: {target_dir}")
        return target_dir

    def restore_project(self, archive_path: str, project_name: Optional[str] = None) -> Path:
        """还原项目（支持纯文本和压缩格式）"""
        archive_path = Path(archive_path)
        if not archive_path.exists():
            raise FileNotFoundError(f"归档文件不存在: {archive_path}")

        if project_name is None:
            project_name = archive_path.stem

        target_dir = self.output_dir / project_name
        target_dir.mkdir(parents=True, exist_ok=True)

        print(f"正在还原项目: {archive_path}")
        print(f"目标目录: {target_dir}")

        # 判断格式
        if '.b64' in archive_path.name:
            # Base64 格式
            print("检测到 Base64 压缩格式")
            with open(archive_path, 'r', encoding='utf-8') as f:
                base64_data = f.read()
            
            compressed_data = base64.b64decode(base64_data)
            compressed_temp_path = self.output_dir / f"{archive_path.stem}_temp.7z"
            
            # 检查压缩格式并解压
            try:
                # 尝试使用 7z 解压
                with open(compressed_temp_path, 'wb') as f:
                    f.write(compressed_data)
                
                subprocess.run(
                    ['7z', 'x', str(compressed_temp_path), f'-o{self.output_dir}', '-y'],
                    check=True,
                    capture_output=True,
                    text=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # 7z 不可用，尝试使用 ZIP
                print("7z 不可用，使用 ZIP 解压")
                import zipfile
                compressed_temp_path = self.output_dir / f"{archive_path.stem}_temp.zip"
                with open(compressed_temp_path, 'wb') as f:
                    f.write(compressed_data)
                
                with zipfile.ZipFile(compressed_temp_path, 'r') as zipf:
                    for member in zipf.namelist():
                        if member.startswith(project_name + '/') or '/' not in member:
                            zipf.extract(member, self.output_dir)
            
            compressed_temp_path.unlink()
        else:
            # 纯文本格式
            print("检测到纯文本格式")
            with open(archive_path, 'r', encoding='utf-8') as f:
                content = f.read()

            current_file = None
            current_content = []
            file_marker = "=== FILE: "

            for line in content.split('\n'):
                if line.startswith(file_marker):
                    if current_file:
                        if current_file.startswith(project_name + '/') or '/' not in current_file:
                            relative_path = current_file.split('/', 1)[1] if '/' in current_file else current_file
                            file_path = target_dir / relative_path
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(file_path, 'w', encoding='utf-8') as out_file:
                                out_file.write('\n'.join(current_content))
                    
                    current_file = line[len(file_marker):-3]
                    current_content = []
                elif current_file is not None:
                    current_content.append(line)

            if current_file:
                if current_file.startswith(project_name + '/') or '/' not in current_file:
                    relative_path = current_file.split('/', 1)[1] if '/' in current_file else current_file
                    file_path = target_dir / relative_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(file_path, 'w', encoding='utf-8') as out_file:
                        out_file.write('\n'.join(current_content))

        print(f"还原完成: {target_dir}")
        return target_dir

    def publish_archive(self, archive_paths: List[Path], commit_message: Optional[str] = None) -> bool:
        """将归档文件复制到发布目录并执行 git 操作"""
        if not self.publish_dir:
            print("未设置发布目录，跳过发布步骤")
            return False

        if not self.publish_dir.exists():
            raise FileNotFoundError(f"发布目录不存在: {self.publish_dir}")

        print(f"\n正在发布归档文件...")
        print(f"发布目录: {self.publish_dir}")

        project_name = archive_paths[0].stem
        target_dir = self.publish_dir / 'share' / project_name

        try:
            print(f"创建目标目录: {target_dir}")
            target_dir.mkdir(parents=True, exist_ok=True)

            # 复制所有归档文件
            for archive_path in archive_paths:
                print(f"复制归档文件到: {target_dir / archive_path.name}")
                shutil.copy2(archive_path, target_dir / archive_path.name)

            if commit_message is None:
                file_names = ', '.join([ap.name for ap in archive_paths])
                commit_message = f"添加归档文件: {file_names}"

            print(f"执行 git 操作...")
            for archive_path in archive_paths:
                subprocess.run(["git", "add", str(target_dir / archive_path.name)], 
                             cwd=self.publish_dir, check=True, capture_output=True, text=True)
            
            subprocess.run(["git", "commit", "-m", commit_message], 
                         cwd=self.publish_dir, check=True, capture_output=True, text=True)
            
            print(f"执行 git push...")
            subprocess.run(["git", "push"], 
                         cwd=self.publish_dir, check=True, capture_output=True, text=True)

            print(f"\n✓ 发布成功: {target_dir}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Git 操作失败: {e}")
            if e.stderr:
                print(f"错误输出: {e.stderr}")
            return False
        except Exception as e:
            print(f"✗ 发布失败: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="GitHub 项目压缩和还原工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 压缩命令
    compress_parser = subparsers.add_parser('compress', help='压缩项目')
    compress_parser.add_argument('source', help='项目路径或 GitHub URL')
    compress_parser.add_argument('-o', '--output', help='输出归档文件名')
    compress_parser.add_argument('-d', '--output-dir', default='./archives', help='输出目录')
    compress_parser.add_argument('-p', '--publish-dir', help='发布目录（GitHub 仓库路径）')
    compress_parser.add_argument('-m', '--message', help='Git 提交消息')
    compress_parser.add_argument('--proxy', default='http://127.0.0.1:10808', help='代理地址（默认: http://127.0.0.1:10808）')

    # 解压命令
    extract_parser = subparsers.add_parser('extract', help='解压归档')
    extract_parser.add_argument('archive', help='归档文件路径')
    extract_parser.add_argument('-d', '--output-dir', help='输出目录')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    publish_dir = getattr(args, 'publish_dir', None)
    archiver = GitHubProjectArchiver(output_dir=args.output_dir if hasattr(args, 'output_dir') else './archives', 
                                     publish_dir=publish_dir)

    try:
        if args.command == 'compress':
            if args.source.startswith('http'):
                proxy = getattr(args, 'proxy', None)
                archive_paths = archiver.archive_github_repo(args.source, args.output, proxy)
            else:
                archive_paths = archiver.compress_project(args.source, args.output)
            
            for archive_path in archive_paths:
                print(f"\n✓ 归档创建成功: {archive_path}")
                file_size = archive_path.stat().st_size
                print(f"  文件大小: {file_size:,} 字节 ({file_size / 1024 / 1024:.2f} MB)")
            
            if publish_dir:
                commit_message = getattr(args, 'message', None)
                archiver.publish_archive(archive_paths, commit_message)

        elif args.command == 'extract':
            output_dir = args.output_dir if args.output_dir else archiver.output_dir
            target_dir = archiver.extract_archive(args.archive, output_dir)
            print(f"\n✓ 归档解压成功: {target_dir}")

    except Exception as e:
        print(f"\n✗ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
