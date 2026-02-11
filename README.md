# 📦 GitHub 项目归档工具

> 一个强大的 GitHub 项目压缩和还原工具，支持双格式输出（纯文本 + 压缩格式），并自动发布到指定仓库。

---

## ✨ 功能特性

- 🎯 **双格式输出**：纯文本（`.txt`）+ 压缩格式（`.b64.txt`）
- 🧠 **智能格式识别**：自动识别并正确解压
- 🌐 **代理支持**：默认使用 `http://127.0.0.1:10808`
- 🚀 **自动发布**：一键发布到 Git 仓库
- 📉 **高效压缩**：节省约 40-70% 存储空间
- 🔧 **7z 支持**：使用 7-Zip 获得最高压缩率

---

## 🚀 快速开始

### 1️⃣ 克隆 GitHub 项目

```bash
# 使用默认代理
python github_archiver.py compress https://github.com/anthropics/skills -o skills

# 自定义代理
python github_archiver.py compress https://github.com/anthropics/skills -o skills --proxy http://127.0.0.1:10808

# 不使用代理
python github_archiver.py compress https://github.com/anthropics/skills -o skills --proxy ""
```

### 2️⃣ 压缩本地项目

```bash
python github_archiver.py compress ./my-project -o my-project
```

### 3️⃣ 解压归档

```bash
# 解压纯文本格式
python github_archiver.py extract archives/my-project.txt -d ./restored

# 解压压缩格式
python github_archiver.py extract archives/my-project.b64.txt -d ./restored
```

### 4️⃣ 发布到仓库

```bash
# 发布到指定目录
python github_archiver.py compress https://github.com/anthropics/skills -o skills -p C:\Users\Steph\Desktop\PublicDocuments

# 指定提交消息
python github_archiver.py compress https://github.com/anthropics/skills -o skills -p C:\Users\Steph\Desktop\PublicDocuments -m "添加归档"
```

---

## 📋 命令参数

### compress 命令

| 参数 | 说明 | 默认值 |
|:-----|:-----|:--------|
| `source` | 项目路径或 GitHub URL | - |
| `-o, --output` | 输出文件名 | 项目名称 |
| `-d, --output-dir` | 输出目录 | `./archives` |
| `-p, --publish-dir` | 发布目录 | - |
| `-m, --message` | 提交消息 | 自动生成 |
| `--proxy` | 代理地址 | `http://127.0.0.1:10808` |

### extract 命令

| 参数 | 说明 | 默认值 |
|:-----|:-----|:--------|
| `archive` | 归档文件路径 | - |
| `-d, --output-dir` | 输出目录 | `./archives` |

---

## 📊 输出格式

### 📄 纯文本格式（`.txt`）

| 特性 | 说明 |
|:-----|:-----|
| ✅ 优点 | 可直接预览和阅读 |
| ❌ 缺点 | 文件体积较大 |
| 🎯 适用 | 需要人工查看代码 |

### 🗜️ 压缩格式（`.b64.txt`）

| 特性 | 说明 |
|:-----|:-----|
| ✅ 优点 | 文件体积小（节省 40-70%） |
| ❌ 缺点 | Base64 编码，无法直接阅读 |
| 🎯 适用 | 高效存储和传输 |

---

## 📈 文件大小对比

以 `anthropics/skills` 项目为例：

| 格式 | 大小 | 压缩率 |
|:-----|:-----|:--------|
| `.txt` | 7.44 MB | - |
| `.zip` + Base64 | 4.27 MB | 42.6% ↓ |
| `.7z` + Base64 | ~2.5 MB | ~66% ↓ |

> 💡 **提示**：安装 7-Zip 可获得更高的压缩率

---

## ❓ 常见问题

### Q: 如何禁用代理？

**A:** 使用 `--proxy ""`

```bash
python github_archiver.py compress https://github.com/xxx/repo -o repo --proxy ""
```

---

### Q: 如何只生成一种格式？

**A:** 当前版本会同时生成两种格式，如需修改请编辑源代码。

---

### Q: 解压时如何识别格式？

**A:** 工具会自动检测文件名中是否包含 `.b64`，包含则使用压缩格式解压，否则使用纯文本格式。

---

### Q: 发布失败怎么办？

**A:** 检查以下几点：

1. ✅ 发布目录是否是有效的 Git 仓库
2. ✅ 是否有 Git 推送权限
3. ✅ 网络连接是否正常
4. ✅ 代理设置是否正确

---

### Q: 如何安装 7-Zip？

**A:** 根据操作系统选择安装方式：

**Windows:**
```bash
# 使用 Chocolatey
choco install 7zip

# 或手动下载安装
# https://www.7-zip.org/download.html
```

**Linux:**
```bash
sudo apt install p7zip-full
```

**macOS:**
```bash
brew install p7zip
```

---

## 🔧 技术细节

### 📄 纯文本格式

- 使用 `=== FILE: 路径 ===` 作为文件分隔符
- UTF-8 编码
- 自动处理二进制文件，显示文件大小

### 🗜️ 压缩格式

- **7z 压缩**：使用 LZMA2 算法，最高压缩级别（-mx9）
- **ZIP 压缩**：使用 DEFLATED 算法（7z 不可用时降级）
- Base64 编码确保文本可存储
- 自动清理临时文件

### 🌐 代理设置

- 支持 HTTP/HTTPS 代理
- 同时设置环境变量 `HTTP_PROXY` 和 `HTTPS_PROXY`
- 兼容 Windows、Linux 和 macOS

### 📂 发布目录结构

归档文件会发布到 `{发布目录}/share/{项目名称}/` 目录下。

---

## 📝 示例场景

### 场景 1：备份开源项目

```bash
# 备份多个开源项目
python github_archiver.py compress https://github.com/anthropics/skills -o skills
python github_archiver.py compress https://github.com/microsoft/vscode -o vscode
python github_archiver.py compress https://github.com/python/cpython -o python
```

### 场景 2：团队代码归档

```bash
# 压缩团队项目并发布到内部仓库
python github_archiver.py compress ./team-project -o team-project-v1.0 -p ./internal-repo -m "团队项目 v1.0 归档"
```

### 场景 3：快速代码审查

```bash
# 生成纯文本格式供快速查看
python github_archiver.py compress https://github.com/xxx/repo -o repo
# 使用文本编辑器打开 archives/repo.txt 查看代码
```

---

## 📄 许可证

本项目遵循 MIT 许可证。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

<div align="center">

**Made with ❤️ by GitHub Archiver Tool**

</div>
