import os
from unittest.mock import Mock, patch

import pytest

from src.downloader.video_downloader import download_video


class TestVideoDownloader:
    @patch("shutil.move")
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_download_success(self, mock_run, mock_exists, mock_makedirs, mock_move):
        """测试成功下载返回文件路径。"""
        mock_run.return_value = Mock(returncode=0)
        mock_exists.return_value = True
        mock_makedirs.return_value = None
        mock_move.return_value = None

        config = {
            "download_format": "best[format]",
            "max_retries": 1,
            "proxy": "test_proxy",
            "download_dir": "downloads",
        }
        file_path = download_video(
            "video1", "Test Channel", "20250101", "Test / Title \\", config
        )

        assert file_path == os.path.join(
            "downloads", "Test_Channel_20250101_Test___Title__.mp4"
        )

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "yt-dlp"
        assert args[1] == "--js-runtimes"
        assert args[2] == "node"
        assert args[3] == "--proxy"
        assert args[4] == "test_proxy"
        assert args[5] == "-f"
        assert args[6] == "best[format]"
        assert args[7] == "--remux-video"
        assert args[8] == "mp4"
        assert args[9] == "--no-playlist"
        assert args[10] == "--mark-watched"
        assert args[11] == "-o"
        assert args[12] == os.path.join(
            "temp", "Test_Channel_20250101_Test___Title__.%(ext)s"
        )
        assert args[13] == "https://www.youtube.com/watch?v=video1"

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_download_file_not_found(self, mock_run, mock_exists, mock_makedirs):
        """测试下载成功但文件不存在返回None。"""
        mock_run.return_value = Mock(returncode=0)
        mock_exists.return_value = False  # 文件不存在

        config = {
            "download_format": "best[format]",
            "max_retries": 1,
            "proxy": "test_proxy",
            "download_dir": "downloads",
        }
        file_path = download_video(
            "video1", "Test Channel", "20250101", "Test Title", config
        )

        assert file_path is None

    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_download_failure_no_retry(self, mock_run, mock_exists, mock_makedirs):
        """测试失败无重试返回None。"""
        mock_run.return_value = Mock(returncode=1)
        mock_exists.return_value = True

        config = {
            "download_format": "best[format]",
            "max_retries": 1,
            "proxy": "test_proxy",
            "download_dir": "downloads",
        }
        file_path = download_video(
            "video1", "Test Channel", "20250101", "Test Title", config
        )

        assert file_path is None

    @patch("shutil.move")
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_download_with_retry_success(
        self, mock_run, mock_exists, mock_makedirs, mock_move
    ):
        """测试失败后重试成功。"""
        mock_run.side_effect = [
            Mock(returncode=1),  # 第一次失败
            Mock(returncode=0),  # 第二次成功
        ]
        mock_exists.return_value = True
        mock_move.return_value = None

        config = {
            "download_format": "best[format]",
            "max_retries": 2,
            "proxy": "test_proxy",
            "download_dir": "downloads",
        }
        file_path = download_video(
            "video1", "Test Channel", "20250101", "Test Title", config
        )

        assert file_path == os.path.join(
            "downloads", "Test_Channel_20250101_Test_Title.mp4"
        )
        assert mock_run.call_count == 2

    @patch("shutil.move")
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_title_and_channel_cleanup(
        self, mock_run, mock_exists, mock_makedirs, mock_move
    ):
        """测试标题和频道名清理（替换无效字符）。"""
        mock_run.return_value = Mock(returncode=0)
        mock_exists.return_value = True
        mock_move.return_value = None

        config = {
            "download_format": "best[format]",
            "max_retries": 1,
            "proxy": "test_proxy",
            "download_dir": "downloads",
        }
        file_path = download_video(
            "video1", "Channel: Name*", "20250101", 'Title? <With> |Chars"', config
        )

        assert file_path == os.path.join(
            "downloads", "Channel__Name__20250101_Title___With___Chars_.mp4"
        )

    @patch("shutil.move")
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_downloads_dir_created_if_not_exists(
        self, mock_run, mock_exists, mock_makedirs, mock_move
    ):
        """测试downloads目录不存在时创建。"""
        mock_run.return_value = Mock(returncode=0)
        mock_exists.side_effect = [True, False]  # 临时文件存在，下载目录不存在
        mock_move.return_value = None

        config = {
            "download_format": "best[format]",
            "max_retries": 1,
            "proxy": "test_proxy",
            "download_dir": "downloads",
        }
        download_video("video1", "Test Channel", "20250101", "Test Title", config)

        mock_makedirs.assert_any_call("temp", exist_ok=True)
        mock_makedirs.assert_any_call("downloads", exist_ok=True)

    @patch("shutil.move")
    @patch("os.makedirs")
    @patch("os.path.exists")
    @patch("subprocess.run")
    def test_proxy_from_config(self, mock_run, mock_exists, mock_makedirs, mock_move):
        """测试代理从配置使用。"""
        mock_run.return_value = Mock(returncode=0)
        mock_exists.return_value = True
        mock_move.return_value = None

        config = {
            "download_format": "best[format]",
            "max_retries": 1,
            "proxy": "custom://proxy:8080",
            "download_dir": "downloads",
        }
        download_video("video1", "Test Channel", "20250101", "Test Title", config)

        args = mock_run.call_args[0][0]
        assert args[1] == "--js-runtimes"
        assert args[2] == "node"
        assert args[3] == "--proxy"
        assert args[4] == "custom://proxy:8080"
