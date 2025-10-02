# YouTube订阅视频下载器 - 规格说明文档 (Specs)

## 1. 项目概述

### 1.1 项目目的
本项目是一个Python脚本，用于自动下载YouTube订阅频道的视频文件。核心功能是通过配置文件管理订阅频道ID，定时检查新视频，使用yt-dlp下载，并通过SQLite维护下载历史避免重复。设计强调模块化、简单性和个人使用，避免批量下载历史视频。

### 1.2 关键特性
- **订阅管理**：纯文本配置文件（channels.txt），每行一个频道ID，支持#注释。
- **定时检查**：使用schedule库，每30分钟检查一次新视频。
- **视频查询**：使用yt-dlp获取频道最近视频元数据（不下载）。
- **下载控制**：yt-dlp下载mp4格式（bestvideo*[filesize<100M][ext=mp4]+bestaudio），文件名格式：{频道名}_{上传日期}_{标题}.mp4，保存到downloads/文件夹。
- **历史管理**：SQLite数据库（download_history.db），记录已下载视频ID避免重复，日志表记录下载详情。
- **首次抓取限制**：每个频道首次运行时，只下载最近10个视频；后续运行处理最近50个中的新视频，避免海量下载（包括新添加频道）。
- **错误处理**：基本try-except，重试机制，日志记录（app.log）。
- **运行方式**：python main.py，后台循环运行（Ctrl+C停止）。

### 1.3 假设与约束
- 个人使用，不考虑商用/法律条款。
- yt-dlp需预安装并定期更新。
- 无并发下载、无通知、无测试代码（原型阶段），但模块设计便于未来扩展。
- 网络依赖YouTube可用性。

## 2. 需求规格

### 2.1 功能需求
- **F1**：读取配置文件，解析ID列表（忽略注释、空行）。
- **F2**：定时（30min）逐频道查询最近视频（元数据：ID、标题、上传日期、频道名）。
  - 查询上限：50个视频。
  - 首次（该频道history为空）：限10个。
- **F3**：检查视频ID是否已下载（SQLite history表）。
- **F4**：下载新视频，成功后记录history和logs。
- **F5**：失败时记录logs，不记录history。
- **F6**：创建downloads/文件夹，自动管理。

### 2.2 非功能需求
- **性能**：查询/下载高效，适合定时运行（<1min/循环）。
- **可靠性**：错误重试3次，日志追踪。
- **可维护性**：模块化设计，纯函数，便于测试/替换（e.g., yt-dlp → API）。
- **扩展性**：未来支持配置化参数、日期锚点过滤、测试。

### 2.3 用户场景
- **初始运行**：创建DB，读取channels.txt，首次每个频道下载10个最新视频。
- **正常运行**：定时检查，新视频下载。
- **添加频道**：编辑channels.txt，重启脚本，新频道限10个。
- **查询历史**：手动查看DB/logs（未来可加查询脚本）。

## 3. 配置文件设计

### 3.1 channels.txt
- **格式**：纯文本，每行一个YouTube频道ID（e.g., UC_x5XG1OV2P6uZZ5FSM9Ttw）。
- **解析规则**：
  - 有效行：非空、非#开头，trim空白，返回ID列表。
  - 注释行：#开头（e.g., # 作者A的频道），忽略。
  - 空行：忽略。
- **示例**：
  ```
  # 订阅频道列表 - YouTube下载器
  # 科技频道 - 作者A
  UC_x5XG1OV2P6uZZ5FSM9Ttw
  # 音乐频道 - 作者B
  UC1234567890abcdef
  ```
- **位置**：项目根目录。
- **模块**：config_reader.py 负责读取。

### 3.2 config.toml
- **格式**：TOML文件，定义运行参数。
- **必需参数**：
  - query_limit: 整数，查询视频上限 (默认50)。
  - first_run_limit: 整数，首次运行限制 (默认10)。
  - interval_min: 整数，定时间隔分钟 (默认30)。
  - download_format: 字符串，yt-dlp格式 (默认"bestvideo*[filesize<100M][ext=mp4]+bestaudio")。
  - max_retries: 整数，重试次数 (默认3)。
  - proxy: 字符串，代理设置 (默认"socks5://127.0.0.1:10808")。
- **示例**：
  ```
  query_limit = 50
  first_run_limit = 10
  interval_min = 30
  download_format = "bestvideo*[filesize<100M][ext=mp4]+bestaudio"
  max_retries = 3
  proxy = "socks5://127.0.0.1:10808"
  ```
- **位置**：项目根目录。
- **模块**：config_reader.py 负责加载和验证。
- **行为**：首次运行生成默认文件，提示用户编辑后重启；缺少参数或无效值时中断并提示。

## 4. 数据库设计 (SQLite: download_history.db)

### 4.1 表结构
- **history表**（排重核心）：
  ```sql
  CREATE TABLE IF NOT EXISTS history (
      video_id TEXT PRIMARY KEY,
      channel_id TEXT NOT NULL
  );
  CREATE INDEX IF NOT EXISTS idx_channel ON history(channel_id);
  ```
  - 用途：检查video_id是否存在，避免重复下载。
  - 插入：下载成功后。

- **logs表**（下载日志，不影响流程）：
  ```sql
  CREATE TABLE IF NOT EXISTS logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      video_id TEXT NOT NULL,
      channel_id TEXT NOT NULL,
      download_time DATETIME DEFAULT CURRENT_TIMESTAMP,
      status TEXT NOT NULL,  -- 'success' or 'failed'
      file_path TEXT,  -- e.g., 'downloads/频道名_2025-10-01_标题.mp4'
      is_first_for_channel TEXT DEFAULT 'false'  -- 'true' if first run for channel
  );
  CREATE INDEX IF NOT EXISTS idx_channel_log ON logs(channel_id);
  CREATE INDEX IF NOT EXISTS idx_time ON logs(download_time);
  ```
  - 用途：查询历史下载详情。
  - 插入：每次下载尝试（成功/失败）。

### 4.2 操作
- **has_records_for_channel(channel_id)**：SELECT COUNT(*) FROM history WHERE channel_id = ? > 0 → bool（判断首次）。
- **is_downloaded(video_id)**：SELECT 1 FROM history WHERE video_id = ?。
- **mark_downloaded(video_id, channel_id)**：INSERT OR IGNORE INTO history。
- **log_download(video_id, channel_id, status, file_path, is_first)**：INSERT INTO logs。
- **事务**：下载成功时原子插入history + logs。
- **位置**：项目根目录。

### 4.3 模块
- history_manager.py：使用sqlite3，提供以上方法，自动初始化表。

## 5. 模块设计

项目结构：
```
project/
├── main.py          # 入口，整合+调度
├── config_reader.py # F1
├── channel_checker.py # F2
├── history_manager.py # F3, F4部分
├── video_downloader.py # F4
├── scheduler.py     # F2-F4循环
├── requirements.txt # 依赖
├── channels.txt     # 配置
├── download_history.db # 生成
├── downloads/       # 生成，视频文件
└── app.log          # 生成，日志
```

### 5.1 config_reader.py
- **职责**：读取channels.txt返回ID列表；加载config.toml返回参数字典。
- **函数**：
  - get_channel_ids(file_path='channels.txt') → list[str]
  - load_config(file_path='config.toml') → dict
- **实现**：
  - get_channel_ids: open(file), for line in lines: if not line.strip() or line.startswith('#'): continue; ids.append(line.strip())
  - load_config: 使用tomlkit解析TOML；验证必需键和类型；文件不存在生成默认并中断；无效配置中断。
- **异常**：FileNotFoundError → 提示创建文件；TOML错误 → 中断提示。

### 5.2 channel_checker.py
- **职责**：查询频道视频元数据。
- **函数**：get_videos(channel_id: str, is_first: bool) → list[dict] {'video_id': str, 'title': str, 'upload_date': str (YYYYMMDD), 'channel_name': str}
- **实现**：
  - URL = f"https://www.youtube.com/channel/{channel_id}/videos"
  - cmd = ['yt-dlp', '--flat-playlist', '--playlist-end', '50', '--dump-json', URL]
  - output = subprocess.check_output(cmd).decode().strip().split('\n')
  - 解析每个JSON：if '_type' == 'video': extract fields
  - 如果is_first: return videos[:10] else: return videos
- **异常**：subprocess.CalledProcessError → 重试3次，日志错误，返回[]。
- **依赖**：yt-dlp, json, subprocess。

### 5.3 history_manager.py
- **职责**：DB操作。
- **类/函数**：init_db() 创建表；has_records_for_channel(channel_id) → bool；is_downloaded(video_id) → bool；mark_downloaded(video_id, channel_id)；log_download(video_id, channel_id, status, file_path, is_first='false')
- **实现**：import sqlite3；conn = sqlite3.connect('download_history.db')；参数化查询。
- **异常**：sqlite3.Error → 回滚，日志。

### 5.4 video_downloader.py
- **职责**：下载单个视频。
- **函数**：download_video(video_url: str, channel_name: str, upload_date: str, title: str) → str or None (file_path or None if failed)
- **实现**：
  - URL = f"https://www.youtube.com/watch?v={video_id}"
  - output_template = f"downloads/%(channel)s_%(upload_date)s_%(title)s.%(ext)s"
  - cmd = ['yt-dlp', '-f', 'bestvideo*[filesize<100M][ext=mp4]+bestaudio', '-o', output_template, URL]
  - subprocess.run(cmd)；if success: return os.path.join('downloads', f"{channel_name}_{upload_date}_{title}.mp4")
- **异常**：失败重试1次，返回None。
- **依赖**：yt-dlp, subprocess, os (创建downloads/)。

### 5.5 scheduler.py
- **职责**：定时执行。
- **函数**：setup_schedule(check_func, interval_min=30)；run_loop()
- **实现**：import schedule, time；schedule.every(interval_min).minutes.do(check_func)；while True: schedule.run_pending(); time.sleep(1)
- **集成**：main中调用。

### 5.6 main.py
- **职责**：入口，协调。
- **流程**：
  - import logging: setup 'app.log' (INFO)
  - config = get_channel_ids()
  - init_db()
  - def check_and_download():
    - for channel_id in config:
      - is_first = not has_records_for_channel(channel_id)
      - videos = get_videos(channel_id, is_first)
      - for video in videos:
        - if not is_downloaded(video['video_id']):
          - file_path = download_video(video['video_id'], video['channel_name'], video['upload_date'], video['title'])
          - if file_path:
            - mark_downloaded(video['video_id'], channel_id)
            - log_download(..., 'success', file_path, str(is_first))
          - else:
            - log_download(..., 'failed', None, str(is_first))
  - setup_schedule(check_and_download)
  - run_loop()
- **异常**：全局try-except，日志，继续运行。
- **依赖**：所有模块, logging。

## 6. 整体流程图

使用Mermaid描述主循环：

```mermaid
flowchart TD
    A[启动 main.py] --> B[config_reader: 读取 channels.txt 获取ID列表]
    B --> C[history_manager: 初始化DB, 创建表和索引]
    C --> D[scheduler: 启动定时循环 每30min执行一次]
    D --> E[逐频道: channel_id in ID列表]
    E --> F[history_manager: has_records_for_channel(channel_id)?]
    F -->|否 首次| G[channel_checker: 获取最近50视频, 过滤前10个]
    F -->|是 已抓取| H[channel_checker: 获取最近50视频, 全处理]
    G --> I[逐视频: history_manager.is_downloaded(video_id)?]
    H --> I
    I --> J{新视频?}
    J -->|否| K[继续下一个视频]
    J -->|是| L[video_downloader: 下载到 downloads/ 文件名: channel_date_title.mp4]
    L --> M[history_manager: 记录到history和logs, 包括is_first_for_channel]
    M -->|成功| N[日志: 成功下载]
    M -->|失败| O[日志: 失败, 不记录history]
    N --> K
    O --> K
    K --> P[继续下一个频道/循环结束, 等待下次调度]
    P --> E
```

## 7. 依赖与安装

### 7.1 requirements.txt
```
yt-dlp
schedule
tomlkit
```

### 7.2 安装
- `uv pip install -r requirements.txt`
- yt-dlp更新：`yt-dlp -U`
- Python 3.8+，sqlite3内置。

### 7.3 运行
- 创建channels.txt（至少一个ID）。
- 编辑config.toml（首次运行会生成默认，修改后重启）。
- `uv run main.py`
- 输出：app.log；视频在downloads/；DB自动生成。

## 8. 未来优化点
- **日期锚点**：history添加last_check_date，按日期过滤新视频。
- **测试**：单元测试（unittest/pytest），mock subprocess。
- **增强**：并发下载（threading）、通知（email）、字幕、API集成（YouTube Data API）。
- **监控**：查询DB日志，添加CLI查询工具。

## 9. 版本历史
- v1.0 (2025-10-01)：初始原型设计，基于讨论。
- v1.1 (2025-10-02)：添加TOML配置系统（config.toml），参数配置化；更新文档。

此文档作为蓝图，确保实现不偏离。若有变更，更新文档。