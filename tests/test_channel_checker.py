import json
from unittest.mock import Mock, patch

import pytest

from src.downloader.channel_checker import get_videos


class TestChannelChecker:

    @patch('subprocess.run')
    def test_get_videos_at_channel(self, mock_run, mock_subprocess):
        """测试@频道handle格式。"""
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps({
            "_type": "video",
            "id": "video2",
            "title": "Another Video",
            "upload_date": "20250102",
            "uploader": "Another Channel"
        }))

        config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test_proxy"}
        videos = get_videos("@handle", False, config)
        
        assert len(videos) == 1
        assert videos[0]["video_id"] == "video2"
        
        args = mock_run.call_args[0][0]
        assert args[-1] == "https://www.youtube.com/@handle/videos"

    @patch('subprocess.run')
    def test_get_videos_plain_handle(self, mock_run, mock_subprocess):
        """测试纯handle名自动添加@。"""
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps({
            "_type": "video",
            "id": "video3",
            "title": "Plain Handle Video",
            "upload_date": "20250103",
            "uploader": "Plain Channel"
        }))

        config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test_proxy"}
        videos = get_videos("plainhandle", False, config)
        
        assert len(videos) == 1
        assert videos[0]["video_id"] == "video3"
        
        args = mock_run.call_args[0][0]
        assert args[-1] == "https://www.youtube.com/@plainhandle/videos"

    @patch('subprocess.run')
    def test_first_run_limit_applied(self, mock_run, mock_subprocess):
        """测试首次运行限制返回前10个视频。"""
        # 模拟50个视频，但只返回前10个
        stdout = ""
        for i in range(15):  # 超过10个
            stdout += json.dumps({
                "_type": "video",
                "id": f"video{i}",
                "title": f"Video {i}",
                "upload_date": "20250101",
                "uploader": "Test Channel"
            }) + "\n"
        
        mock_run.return_value = Mock(returncode=0, stdout=stdout)

        config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test_proxy"}
        videos = get_videos("testchannel", True, config)  # is_first=True
        
        assert len(videos) == 10  # 限制为10

    @patch('subprocess.run')
    def test_no_videos_returns_empty(self, mock_run, mock_subprocess):
        """测试无视频返回空列表。"""
        mock_run.return_value = Mock(returncode=0, stdout="")

        config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test_proxy"}
        videos = get_videos("testchannel", False, config)
        
        assert videos == []

    @patch('subprocess.run')
    def test_parse_non_video_skipped(self, mock_run, mock_subprocess):
        """测试跳过非视频类型JSON。"""
        stdout = json.dumps({"_type": "playlist"}) + "\n" + json.dumps({
            "_type": "video",
            "id": "video1",
            "title": "Valid Video",
            "upload_date": "20250101",
            "uploader": "Test Channel"
        })

        mock_run.return_value = Mock(returncode=0, stdout=stdout)

        config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test_proxy"}
        videos = get_videos("testchannel", False, config)
        
        assert len(videos) == 1

    @patch('subprocess.run')
    def test_json_decode_error_skipped(self, mock_run, mock_subprocess):
        """测试JSON解析错误跳过该行。"""
        stdout = "invalid json\n" + json.dumps({
            "_type": "video",
            "id": "video1",
            "title": "Valid Video",
            "upload_date": "20250101",
            "uploader": "Test Channel"
        })

        mock_run.return_value = Mock(returncode=0, stdout=stdout)

        config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test_proxy"}
        videos = get_videos("testchannel", False, config)
        
        assert len(videos) == 1  # 只解析有效行

    @patch('subprocess.run')
    def test_retries_on_failure(self, mock_run, mock_subprocess):
        """测试失败时重试。"""
        # 第一次失败，第二次成功
        mock_run.side_effect = [
            Mock(returncode=1, stdout="", stderr="Error"),
            Mock(returncode=0, stdout=json.dumps({
                "_type": "video",
                "id": "video1",
                "title": "Retry Video",
                "upload_date": "20250101",
                "uploader": "Test Channel"
            }))
        ]

        config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 2, "proxy": "test_proxy"}
        videos = get_videos("testchannel", False, config)
        
        assert len(videos) == 1
        assert mock_run.call_count == 2  # 重试一次

    @patch('subprocess.run')
    def test_member_video_error_continues(self, mock_run, mock_subprocess):
        """测试会员视频错误继续解析。"""
        mock_run.return_value = Mock(returncode=1, stdout=json.dumps({
            "_type": "video",
            "id": "video1",
            "title": "Public Video",
            "upload_date": "20250101",
            "uploader": "Test Channel"
        }), stderr="This video is available to this channel's members")

        config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test_proxy"}
        videos = get_videos("testchannel", False, config)
        
        assert len(videos) == 1  # 仍解析stdout

    @patch('subprocess.run')
    def test_title_cleanup(self, mock_run, mock_subprocess):
        """测试标题清理（替换/和\）。"""
        mock_run.return_value = Mock(returncode=0, stdout=json.dumps({
            "_type": "video",
            "id": "video1",
            "title": "Test / Video \\ with slashes",
            "upload_date": "20250101",
            "uploader": "Channel / Name"
        }))

        config = {"query_limit": 50, "first_run_limit": 10, "max_retries": 3, "proxy": "test_proxy"}
        videos = get_videos("testchannel", False, config)
        
        assert videos[0]["title"] == "Test _ Video _ with slashes"
        assert videos[0]["channel_name"] == "Channel _ Name"