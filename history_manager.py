import sqlite3
from typing import Optional

DB_PATH = "download_history.db"


def init_db(db_path: str = DB_PATH) -> None:
    """
    初始化数据库，创建表和索引如果不存在。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建history表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL
        )
    """)

    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel ON history(channel_id)")

    # 创建logs表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            download_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            file_path TEXT,
            is_first_for_channel TEXT DEFAULT 'false'
        )
    """)

    # 创建logs索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_channel_log ON logs(channel_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_time ON logs(download_time)")

    conn.commit()
    conn.close()


def has_records_for_channel(channel_id: str, db_path: str = DB_PATH) -> bool:
    """
    检查指定频道是否有下载记录。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM history WHERE channel_id = ?", (channel_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0


def is_downloaded(video_id: str, db_path: str = DB_PATH) -> bool:
    """
    检查视频ID是否已下载。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM history WHERE video_id = ?", (video_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def mark_downloaded(video_id: str, channel_id: str, db_path: str = DB_PATH) -> None:
    """
    标记视频为已下载（插入history）。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO history (video_id, channel_id) VALUES (?, ?)", (video_id, channel_id))
    conn.commit()
    conn.close()


def log_download(
    video_id: str,
    channel_id: str,
    status: str,
    file_path: Optional[str] = None,
    is_first_for_channel: str = "false",
    db_path: str = DB_PATH,
) -> None:
    """
    记录下载日志到logs表。
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO logs (video_id, channel_id, status, file_path, is_first_for_channel)
        VALUES (?, ?, ?, ?, ?)
    """,
        (video_id, channel_id, status, file_path, is_first_for_channel),
    )
    conn.commit()
    conn.close()
