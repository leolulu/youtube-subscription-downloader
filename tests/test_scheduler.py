from unittest.mock import Mock, patch

import pytest

from src.core.scheduler import run_loop, setup_schedule


class TestScheduler:
    def test_setup_schedule_sets_interval_from_config(self):
        """测试使用配置中的interval_min设置定时任务。"""
        mock_func = Mock()
        config = {"interval_min": 15}

        with patch("schedule.every") as mock_every:
            setup_schedule(mock_func, config)

        mock_every(15).minutes.do.assert_called_once_with(mock_func)

    def test_setup_schedule_default_interval(self):
        """测试默认interval_min=30。"""
        mock_func = Mock()
        config = {"interval_min": 30}  # 默认值

        with patch("schedule.every") as mock_every:
            setup_schedule(mock_func, config)

        mock_every(30).minutes.do.assert_called_once_with(mock_func)

    @patch("time.sleep")
    @patch("schedule.run_pending")
    def test_run_loop_runs_pending_jobs(self, mock_run_pending, mock_sleep):
        """测试run_loop运行pending任务。"""
        mock_run_pending.side_effect = [None, StopIteration]

        with pytest.raises(StopIteration):
            run_loop()

        assert mock_run_pending.call_count == 2
        mock_sleep.assert_called_with(1)
