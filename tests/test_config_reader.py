import os
import sys
import tempfile
from unittest.mock import patch

import pytest

from config_reader import get_channel_ids, load_config


class TestGetChannelIds:
    def test_file_not_exists_creates_placeholder(self, tmp_path):
        """测试文件不存在时创建placeholder并返回空列表。"""
        file_path = tmp_path / "channels.txt"
        assert not file_path.exists()
        
        channel_ids = get_channel_ids(str(file_path))
        assert channel_ids == []
        assert file_path.exists()
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "# YouTube订阅频道列表" in content
        assert "# MoneyXYZ" in content  # 示例中有注释ID

    def test_parse_valid_channels(self, tmp_path):
        """测试解析有效频道ID，忽略注释和空行。"""
        file_path = tmp_path / "channels.txt"
        content = """# 注释行
UC1234567890
@handle
  trimmed_id

# 另一个注释
"""
        file_path.write_text(content, encoding="utf-8")
        
        channel_ids = get_channel_ids(str(file_path))
        assert channel_ids == ["UC1234567890", "@handle", "trimmed_id"]

    def test_ignore_comments_and_empty(self, tmp_path):
        """测试忽略注释和空行。"""
        file_path = tmp_path / "channels.txt"
        content = """
# 空行测试

# 注释
# 多行注释

有效ID
"""
        file_path.write_text(content, encoding="utf-8")
        
        channel_ids = get_channel_ids(str(file_path))
        assert channel_ids == ["有效ID"]

class TestLoadConfig:
    def test_file_not_exists_creates_default_and_exit(self, tmp_path, capsys):
        """测试文件不存在时创建默认TOML并退出。"""
        file_path = tmp_path / "config.toml"
        assert not file_path.exists()
        
        with patch('sys.exit') as mock_exit:
            config = load_config(str(file_path))
            mock_exit.assert_called_once_with(1)
        
        # 检查文件创建
        assert file_path.exists()
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "query_limit = 50" in content
        assert "proxy = \"socks5://127.0.0.1:10808\"" in content
        
        # 检查输出
        captured = capsys.readouterr()
        assert "已创建默认配置文件" in captured.out
        assert "请编辑 config.toml" in captured.out

    def test_missing_keys_exits_with_message(self, tmp_path, capsys):
        """测试缺少必需键时退出并提示。"""
        file_path = tmp_path / "config.toml"
        content = """
interval_min = 30
download_format = "test"
"""
        file_path.write_text(content, encoding="utf-8")
        
        with patch('sys.exit') as mock_exit:
            config = load_config(str(file_path))
            mock_exit.assert_called_once_with(1)
        
        captured = capsys.readouterr()
        assert "缺少以下必需参数: query_limit, first_run_limit, max_retries, proxy" in captured.out

    def test_invalid_type_exits(self, tmp_path, capsys):
        """测试类型无效时退出。"""
        file_path = tmp_path / "config.toml"
        content = """
query_limit = "invalid"  # 应为int
interval_min = 30
download_format = "test"
max_retries = 3
proxy = "test"
first_run_limit = 10
"""
        file_path.write_text(content, encoding="utf-8")
        
        with patch('sys.exit') as mock_exit:
            config = load_config(str(file_path))
            mock_exit.assert_called_once_with(1)
        
        captured = capsys.readouterr()
        assert "query_limit 必须是正整数" in captured.out

    def test_valid_config_loads(self, tmp_path):
        """测试有效配置加载返回dict。"""
        file_path = tmp_path / "config.toml"
        content = """
query_limit = 50
first_run_limit = 10
interval_min = 30
download_format = "bestvideo*[filesize<100M][ext=mp4]+bestaudio"
max_retries = 3
proxy = "socks5://127.0.0.1:10808"
"""
        file_path.write_text(content, encoding="utf-8")
        
        with patch('sys.exit') as mock_exit:
            config = load_config(str(file_path))
            mock_exit.assert_not_called()
        
        assert isinstance(config, dict)
        assert config['query_limit'] == 50
        assert config['proxy'] == "socks5://127.0.0.1:10808"

    def test_toml_parse_error_exits(self, tmp_path, capsys):
        """测试TOML解析错误时退出。"""
        file_path = tmp_path / "config.toml"
        content = "invalid_toml = ["  # 无效TOML
        file_path.write_text(content, encoding="utf-8")
        
        with patch('sys.exit') as mock_exit:
            config = load_config(str(file_path))
            mock_exit.assert_called_once_with(1)
        
        captured = capsys.readouterr()
        assert "加载配置错误" in captured.out
        assert "请检查 config.toml 文件格式是否正确" in captured.out