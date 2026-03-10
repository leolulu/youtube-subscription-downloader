from collections.abc import Callable
import time

import schedule

from src.types import ScheduleConfig


def setup_schedule(check_func: Callable[[], None], config: ScheduleConfig) -> None:
    """
    设置定时任务，每config['interval_min']分钟执行check_func。
    """
    interval_min = config['interval_min']
    schedule.every(interval_min).minutes.do(check_func)

def run_loop() -> None:
    """
    运行调度循环。
    """
    while True:
        schedule.run_pending()
        time.sleep(1)
