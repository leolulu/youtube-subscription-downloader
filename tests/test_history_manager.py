import os
import sqlite3

import pytest

from history_manager import has_records_for_channel, init_db, is_downloaded, log_download, mark_downloaded


class TestHistoryManager:
    def test_init_db_creates_tables(self, temp_db_path):
        """测试初始化DB创建表和索引。"""
        init_db(temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # 检查history表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='history'")
        assert cursor.fetchone() is not None
        
        # 检查logs表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logs'")
        assert cursor.fetchone() is not None
        
        # 检查索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='history' AND name='idx_channel'")
        assert cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='logs' AND name='idx_channel_log'")
        assert cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='logs' AND name='idx_time'")
        assert cursor.fetchone() is not None
        
        conn.close()

    def test_has_records_for_channel_no_records(self, temp_db_path):
        """测试频道无记录返回False。"""
        init_db(temp_db_path)
        assert not has_records_for_channel("test_channel", temp_db_path)

    def test_has_records_for_channel_with_records(self, temp_db_path):
        """测试频道有记录返回True。"""
        init_db(temp_db_path)
        mark_downloaded("video1", "test_channel", temp_db_path)
        assert has_records_for_channel("test_channel", temp_db_path)

    def test_is_downloaded_no_record(self, temp_db_path):
        """测试视频未下载返回False。"""
        init_db(temp_db_path)
        assert not is_downloaded("video1", temp_db_path)

    def test_is_downloaded_with_record(self, temp_db_path):
        """测试视频已下载返回True。"""
        init_db(temp_db_path)
        mark_downloaded("video1", "test_channel", temp_db_path)
        assert is_downloaded("video1", temp_db_path)

    def test_mark_downloaded_inserts_if_new(self, temp_db_path):
        """测试标记新视频插入记录。"""
        init_db(temp_db_path)
        mark_downloaded("video1", "test_channel", temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM history WHERE video_id = ?", ("video1",))
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == "video1"
        assert result[1] == "test_channel"
        conn.close()

    def test_mark_downloaded_ignore_if_exists(self, temp_db_path):
        """测试标记已存在视频不重复插入。"""
        init_db(temp_db_path)
        mark_downloaded("video1", "test_channel", temp_db_path)
        mark_downloaded("video1", "test_channel", temp_db_path)  # 重复
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM history WHERE video_id = ?", ("video1",))
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()

    def test_log_download_success(self, temp_db_path):
        """测试记录成功下载日志。"""
        init_db(temp_db_path)
        log_download("video1", "test_channel", "success", "/path/to/file.mp4", "true", temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs WHERE video_id = ?", ("video1",))
        result = cursor.fetchone()
        assert result is not None
        assert result[1] == "video1"
        assert result[2] == "test_channel"
        assert result[4] == "success"
        assert result[5] == "/path/to/file.mp4"
        assert result[6] == "true"
        conn.close()

    def test_log_download_failed(self, temp_db_path):
        """测试记录失败下载日志。"""
        init_db(temp_db_path)
        log_download("video1", "test_channel", "failed", None, "false", temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs WHERE video_id = ?", ("video1",))
        result = cursor.fetchone()
        assert result[4] == "failed"
        assert result[5] is None
        assert result[6] == "false"
        conn.close()

    def test_log_download_multiple(self, temp_db_path):
        """测试多次记录日志。"""
        init_db(temp_db_path)
        log_download("video1", "test_channel", "success", "/path1.mp4", "false", temp_db_path)
        log_download("video2", "test_channel", "failed", None, "false", temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        assert count == 2
        conn.close()