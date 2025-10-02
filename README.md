# YouTube 订阅视频下载器

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/Tests-Pytest-green)](https://pytest.org/)

这是一个简单的 Python 脚本，用于自动监控 YouTube 订阅频道的新视频，并下载到本地文件夹。使用 `yt-dlp` 查询和下载视频，通过 SQLite 数据库避免重复下载，支持定时运行和代理配置。适合个人订阅管理，避免海量历史视频下载。

## 特性
- **订阅管理**：通过 `channels.txt` 配置频道 handle（e.g., `@MoneyXYZ`），支持注释。
- **定时下载**：每隔指定分钟（默认 1440 分钟，即 24 小时）检查新视频。
- **智能限制**：首次运行每个频道限 5 个视频，后续检查最近 10 个中的新视频。
- **下载格式**：默认高质量 MP4（文件大小 <100MB），支持自定义格式和代理（SOCKS5 等）。
- **历史记录**：SQLite 数据库跟踪已下载视频，日志记录成功/失败详情。
- **错误处理**：自动重试（默认 3 次），优雅停止（Ctrl+C）。
- **测试覆盖**：使用 Pytest 单元测试核心模块。
- **配置化**：TOML 配置文件，支持本地/SMB 下载路径。

**注意**：仅限个人非商业使用，遵守 YouTube 服务条款。`yt-dlp` 需自行安装并更新。

## 先决条件
- Python 3.8+
- `yt-dlp`（命令行工具）：[安装指南](https://github.com/yt-dlp/yt-dlp#installation)
- 可选：代理工具（如 Shadowsocks）用于绕过网络限制。

## 安装
1. 克隆仓库：
   ```
   git clone https://github.com/yourusername/youtube-subscription-downloader.git
   cd youtube-subscription-downloader
   ```

2. 安装 Python 依赖（推荐使用 `uv` 或 `pip`）：
   ```
   uv pip install -r requirements.txt
   # 或
   pip install -r requirements.txt
   ```

3. 更新 `yt-dlp`：
   ```
   yt-dlp -U
   ```

## 配置
1. **频道订阅** (`channels.txt`)：
   - 编辑根目录 `channels.txt`，每行一个频道 handle（带 `@` 或不带自动添加）。
   - 支持 `#` 注释和空行。
   - 示例：
     ```
     # YouTube 订阅频道列表
     # 可以使用#进行行级注释
     # 每行添加一个频道handle (e.g., MoneyXYZ)
     # 示例:
     # MoneyXYZ
     # @EXSIREMUSIC
     ```
   - 如果文件不存在，首次运行会创建示例并提示编辑。

2. **运行参数** (`config.toml`)：
   - 首次运行 `main.py` 会生成默认 `config.toml`，编辑后重启。
   - 必需参数（默认值）：
     - `query_limit = 10`：查询视频上限
     - `first_run_limit = 5`：首次运行限制
     - `interval_min = 1440`：检查间隔分钟（24 小时）
     - `download_format = "bestvideo*[filesize<100M][ext=mp4]+bestaudio"`：yt-dlp 格式
     - `max_retries = 3`：重试次数
     - `proxy = "socks5://127.0.0.1:10808"`：代理 URL（空字符串禁用）
     - `download_dir = "downloads"`：下载路径（支持 UNC 如 `"\\\\server\\share"`）
   - 示例：
     ```
     query_limit = 10
     first_run_limit = 5
     interval_min = 1440
     download_format = "bestvideo*[filesize<100M][ext=mp4]+bestaudio"
     max_retries = 3
     proxy = "socks5://127.0.0.1:10808"
     download_dir = "downloads"
     ```
   - **隐私提示**：`config.toml`、`channels.txt`、`download_history.db`、`logs/app.log` 已添加至 `.gitignore`，上传 GitHub 前确保不包含敏感信息（如真实代理/路径）。

## 使用
1. 确保配置完成（编辑 `channels.txt` 和 `config.toml`）。
2. 运行脚本：
   ```
   uv run main.py
   # 或
   python main.py
   ```
   - 首次：初始化数据库，下载每个频道的前 `first_run_limit` 个视频。
   - 后续：定时检查新视频，下载到 `download_dir`。
   - 文件名格式：`{频道名}_{YYYYMMDD}_{标题}.mp4`（非法字符替换为 `_`）。
   - 日志：`logs/app.log`（事件记录）和控制台输出。

3. 停止：按 `Ctrl+C`，脚本优雅退出。

4. 监控：
   - 查看日志：`tail -f logs/app.log`
   - 查询数据库：使用 SQLite 工具打开 `download_history.db`，查看 `logs` 表历史。

**示例输出**：
```
2025-10-02 16:48:57,547 - INFO - 开始检查 1 个频道的新视频
2025-10-02 16:48:57,548 - INFO - 处理频道: @EXSIREMUSIC
2025-10-02 16:49:08,936 - INFO - 从频道 @EXSIREMUSIC 拉取 2 个视频
2025-10-02 16:49:08,937 - INFO - 发现新视频: 示例视频标题...
2025-10-02 16:49:08,937 - INFO - 下载成功: downloads/EXSIREMUSIC_20251002_标题.mp4
```

## 测试
运行单元测试（覆盖核心逻辑，如配置解析、数据库操作、mock 下载）：
```
pytest -v --cov=. --cov-report=term-missing
```
- 测试使用 mock（subprocess, sqlite3 in-memory），无需真实 YouTube 访问。
- 覆盖率报告显示缺失行，便于维护。

## 故障排除
- **yt-dlp 错误**：确保 `yt-dlp` 在 PATH 中，更新版本。检查代理/网络。
- **下载失败**：查看 `app.log`，常见原因：视频私有/地区限制、格式不支持（调整 `download_format`）。
- **数据库锁定**：SQLite 单用户，避免并发编辑。
- **Windows UNC 路径**：确保 SMB 共享权限，yt-dlp 支持但需测试。
- **无新视频**：检查频道 handle 正确，代理有效。

## 贡献
1. Fork 仓库。
2. 创建分支：`git checkout -b feature/xxx`。
3. 提交变更：`git commit -m "添加 xxx"`。
4. Push 并 PR。
- 遵循 PEP 8，添加测试，更新 specs.md。

欢迎 issue/PR：新特性（如 API 支持）、bug 修复、文档改进。

## 许可证
MIT License - 详见 [LICENSE](LICENSE)（若无，添加标准 MIT）。

## 更多文档
- [详细规格](doc/specs.md)：架构、流程图、模块设计。
- 灵感来源：yt-dlp、schedule、tomlkit。

**免责**：本工具仅用于合法订阅内容下载。作者不对 YouTube 政策变更或下载问题负责。