# GitHub 项目归档工具

GitHub 项目压缩和还原工具，支持双格式输出（纯文本 + 压缩格式），并自动发布到指定仓库。

## 功能特性

- 双格式输出：纯文本（`.txt`）+ 压缩格式（`.b64.txt`）
- 智能格式识别：自动识别并正确解压
- 代理支持：默认使用 `http://127.0.0.1:10808`
- 自动发布：一键发布到 Git 仓库
- 高效压缩：节省约 40-50% 存储空间

## 快速开始

### 克隆 GitHub 项目

```bash
# 使用默认代理
python github_archiver.py compress https://github.com/anthropics/skills -o skills

# 自定义代理
python github_archiver.py compress https://github.com/anthropics/skills -o skills --proxy http://127.0.0.1:7890

# 不使用代理
python github_archiver.py compress https://github.com/anthropics/skills -o skills --proxy ""
```

### 压缩本地项目

```bash
python github_archiver.py compress ./skills -o skills
```

### 解压归档

```bash
# 解压纯文本格式
python github_archiver.py extract archives/skills.txt -d ./restored

# 解压压缩格式
python github_archiver.py extract archives/skills.b64.txt -d ./restored
```

### 发布到仓库

```bash
# 发布到指定目录
python github_archiver.py compress https://github.com/anthropics/skills -o skills -p C:\Users\Steph\Desktop\test\PublicDocuments

# 指定提交消息
python github_archiver.py compress https://github.com/anthropics/skills -o skills -p C:\Users\Steph\Desktop\test\PublicDocuments -m "添加归档"
```

## 命令参数

### compress 命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `source` | 项目路径或 GitHub URL | - |
| `-o, --output` | 输出文件名 | 项目名称 |
| `-d, --output-dir` | 输出目录 | `./archives` |
| `-p, --publish-dir` | 发布目录 | - |
| `-m, --message` | 提交消息 | 自动生成 |
| `--proxy` | 代理地址 | `http://127.0.0.1:10808` |

### extract 命令

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `archive` | 归档文件路径 | - |
| `-d, --output-dir` | 输出目录 | `./archives` |

## 输出格式

### 纯文本格式（`.txt`）

- 优点：可直接预览和阅读
- 缺点：文件体积较大
- 适用：需要人工查看代码

### 压缩格式（`.b64.txt`）

- 优点：文件体积小（节省 40-50%）
- 缺点：Base64 编码，无法直接阅读
- 适用：高效存储和传输

## 文件大小对比

以 `anthropics/skills` 项目为例：

| 格式 | 大小 | 压缩率 |
|------|------|--------|
| `.txt` | 7.44 MB | - |
| `.b64.txt` | 4.27 MB | 42.6% ↓ |

## 常见问题

**Q: 如何禁用代理？**

A: 使用 `--proxy ""`

**Q: 如何只生成一种格式？**

A: 当前版本同时生成两种格式

**Q: 解压时如何识别格式？**

A: 自动检测文件名中的 `.b64`

**Q: 发布失败怎么办？**

A: 检查 Git 仓库权限、网络连接、代理设置

## 技术细节

### 纯文本格式

- 使用 `=== FILE: 路径 ===` 分隔文件
- UTF-8 编码
- 自动处理二进制文件

### 压缩格式

- ZIP 压缩（DEFLATED）
- Base64 编码
- 自动清理临时文件

### 代理设置

- 支持 HTTP/HTTPS 代理
- 兼容 Windows/Linux/macOS
