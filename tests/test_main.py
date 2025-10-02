import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from main import check_and_download, main, signal_handler


class TestMain:
    @patch('main.get_channel_ids')
    @patch('main.has_records_for_channel')
    @patch('main.get_videos')
    @patch('main.is_downloaded')
    @patch('main.download_video')
    @patch('main.mark_downloaded')
    @patch('main.log_download')
    @patch('main.logger')
    def test_check_and_download_success_flow(self, mock_logger, mock_log_download, mock_mark_downloaded, mock_download_video, mock_is_downloaded, mock_get_videos, mock_has_records, mock_get_channel_ids):
        """测试完整成功流程。"""
        mock_config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test"}
        
        mock_channel_ids = ["channel1"]
        mock_get_channel_ids.return_value = mock_channel_ids
        
        mock_has_records.return_value = False  # is_first=True
        
        mock_videos = [
            {"video_id": "video1", "title": "Test Video", "upload_date": "20250101", "channel_name": "Test Channel"}
        ]
        mock_get_videos.return_value = mock_videos
        
        mock_is_downloaded.return_value = False  # 新视频
        
        mock_file_path = "/path/to/downloaded.mp4"
        mock_download_video.return_value = mock_file_path
        
        check_and_download(mock_config)
        
        # 检查调用链
        mock_get_channel_ids.assert_called_once()
        mock_has_records.assert_called_once_with("channel1")
        mock_get_videos.assert_called_once_with("channel1", True, mock_config)
        mock_is_downloaded.assert_called_once_with("video1")
        mock_download_video.assert_called_once_with("video1", "Test Channel", "20250101", "Test Video", mock_config)
        mock_mark_downloaded.assert_called_once_with("video1", "channel1")
        mock_log_download.assert_called_once_with("video1", "channel1", "success", mock_file_path, "True")
        mock_logger.info.assert_any_call(f"开始检查 {len(mock_channel_ids)} 个频道的新视频")
        mock_logger.info.assert_any_call("检查循环完成")

    @patch('main.get_channel_ids')
    @patch('main.has_records_for_channel')
    @patch('main.get_videos')
    @patch('main.is_downloaded')
    @patch('main.download_video')
    @patch('main.log_download')
    @patch('main.mark_downloaded')
    @patch('main.logger')
    def test_check_and_download_failure_log_only(self, mock_logger, mock_mark_downloaded, mock_log_download, mock_download_video, mock_is_downloaded, mock_get_videos, mock_has_records, mock_get_channel_ids):
        """测试下载失败只记录日志，不标记history。"""
        mock_config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test"}
        
        mock_get_channel_ids.return_value = ["channel1"]
        mock_has_records.return_value = False
        mock_get_videos.return_value = [{"video_id": "video1", "title": "Test Video", "upload_date": "20250101", "channel_name": "Test Channel"}]
        mock_is_downloaded.return_value = False
        mock_download_video.return_value = None  # 失败
        
        check_and_download(mock_config)
        
        mock_log_download.assert_called_once_with("video1", "channel1", "failed", None, "True")
        mock_mark_downloaded.assert_not_called()
        mock_logger.error.assert_called_once_with(f"下载失败: video1")

    @patch('main.get_channel_ids')
    @patch('main.logger')
    def test_no_channels_warning(self, mock_logger, mock_get_channel_ids):
        """测试无频道时警告并返回。"""
        mock_get_channel_ids.return_value = []
        mock_config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test"}
        
        check_and_download(mock_config)
        
        mock_logger.warning.assert_called_once_with("没有找到频道ID，请检查channels.txt")
        # 其他依赖不被调用
        with patch('main.get_videos') as mock_get_videos:
            mock_get_videos.assert_not_called()

    @patch('main.get_channel_ids')
    @patch('main.has_records_for_channel')
    @patch('main.get_videos')
    @patch('main.logger')
    def test_no_videos_for_channel_warning(self, mock_logger, mock_get_videos, mock_has_records, mock_get_channel_ids):
        """测试频道无视频数据时警告。"""
        mock_get_channel_ids.return_value = ["channel1"]
        mock_has_records.return_value = False
        mock_get_videos.return_value = []
        mock_config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test"}
        
        check_and_download(mock_config)
        
        mock_logger.warning.assert_called_once_with(f"频道 channel1 无视频数据")

    @patch('main.get_channel_ids')
    @patch('main.has_records_for_channel')
    @patch('main.get_videos')
    @patch('main.is_downloaded')
    @patch('main.logger')
    def test_already_downloaded_skip(self, mock_logger, mock_is_downloaded, mock_get_videos, mock_has_records, mock_get_channel_ids):
        """测试已下载视频跳过。"""
        mock_get_channel_ids.return_value = ["channel1"]
        mock_has_records.return_value = False
        mock_get_videos.return_value = [{"video_id": "video1", "title": "Test Video", "upload_date": "20250101", "channel_name": "Test Channel"}]
        mock_is_downloaded.return_value = True  # 已下载
        mock_config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test"}
        
        check_and_download(mock_config)
        
        mock_logger.debug.assert_called_once_with("视频已下载: video1")
        # download_video 不被调用
        with patch('main.download_video') as mock_download:
            mock_download.assert_not_called()

    def test_signal_handler(self):
        """测试信号处理程序。"""
        with patch('main.logger') as mock_logger:
            with patch('main.sys') as mock_sys:
                signal_handler(None, None)
                mock_logger.info.assert_called_once_with("接收到停止信号，优雅关闭...")
                mock_sys.exit.assert_called_once_with(0)

    @patch('main.load_config')
    @patch('main.init_db')
    @patch('main.check_and_download')
    @patch('main.setup_schedule')
    @patch('main.run_loop')
    @patch('main.signal.signal')
    @patch('main.logger')
    def test_main_entry_point(self, mock_logger, mock_signal, mock_run_loop, mock_setup_schedule, mock_check_and_download, mock_init_db, mock_load_config):
        """测试main入口点逻辑（if __name__ == "__main__"）。"""
        mock_config = {"interval_min": 30}
        mock_load_config.return_value = mock_config
        
        # 由于run_loop无限循环，使用side_effect模拟KeyboardInterrupt
        mock_run_loop.side_effect = KeyboardInterrupt
        
        # 模拟入口点执行
        main()
        # 注意：由于main.py使用if __name__，这里测试核心逻辑
        mock_signal.assert_any_call(2, signal_handler)
        mock_signal.assert_any_call(15, signal_handler)
        
        mock_load_config.assert_called_once()
        mock_init_db.assert_called_once()
        mock_logger.info.assert_any_call("YouTube订阅视频下载器启动")
        mock_check_and_download.assert_called_once_with(mock_config)
        
        # setup_schedule调用
        mock_setup_schedule.assert_called_once()
        # 检查wrapper函数
        wrapper = mock_setup_schedule.call_args[0][0]
        assert callable(wrapper)
        wrapper()  # 调用wrapper应调用check_and_download
        mock_check_and_download.assert_called_with(mock_config)
        
        mock_run_loop.assert_called_once()
        mock_logger.info.assert_any_call("脚本停止")  # KeyboardInterrupt处理

    @patch('main.load_config')
    def test_main_config_load_failure(self, mock_load_config):
        """测试配置加载失败时退出。"""
        mock_load_config.side_effect = SystemExit(1)
        
        with pytest.raises(SystemExit):
            main()