import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add project root to sys.path for imports in tests
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_db_path():
    """临时数据库路径的fixture，用于history_manager测试。"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    try:
        os.unlink(db_path)
    except OSError:
        pass  # Ignore if file is locked, common on Windows with SQLite

@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run，用于channel_checker和video_downloader测试。"""
    with patch('subprocess.run') as mock:
        yield mock

@pytest.fixture
def mock_os_path_exists():
    """Mock os.path.exists，用于文件检查。"""
    with patch('os.path.exists') as mock:
        mock.return_value = True
        yield mock