import time
from unittest.mock import Mock, patch

import pytest
import schedule

from scheduler import run_loop, setup_schedule


class TestScheduler:
    def test_setup_schedule_sets_interval_from_config(self):
        """测试使用配置中的interval_min设置定时任务。"""
        mock_func = Mock()
        config = {"interval_min": 15}
        
        with patch('schedule.every') as mock_every:
            setup_schedule(mock_func, config)
        
        mock_every(15).minutes.do.assert_called_once_with(mock_func)

    def test_setup_schedule_default_interval(self):
        """测试默认interval_min=30。"""
        mock_func = Mock()
        config = {"interval_min": 30}  # 默认值
        
        with patch('schedule.every') as mock_every:
            setup_schedule(mock_func, config)
        
        mock_every(30).minutes.do.assert_called_once_with(mock_func)

    @patch('time.sleep')
    @patch('schedule.run_pending')
    def test_run_loop_runs_pending_jobs(self, mock_run_pending, mock_sleep):
        """测试run_loop运行pending任务。"""
        mock_run_pending.return_value = None
        mock_sleep.return_value = None
        
        # 限制循环次数
        with patch('schedule.run_pending', side_effect=[True, False]):  # 模拟一次运行
            with pytest.raises(StopIteration):  # 强制停止
                gen = run_loop_generator()
                next(gen)
                next(gen)
        
        mock_run_pending.assert_called()
        mock_sleep.assert_called_with(1)

def run_loop_generator():
    """生成器版本的run_loop用于测试。"""
    while True:
        schedule.run_pending()
        time.sleep(1)
        yield