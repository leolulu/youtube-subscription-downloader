import schedule
import time
from typing import Callable

def setup_schedule(check_func: Callable, interval_min: int = 30) -> None:
    """
    设置定时任务，每interval_min分钟执行check_func。
    """
    schedule.every(interval_min).minutes.do(check_func)

def run_loop() -> None:
    """
    运行调度循环。
    """
    while True:
        schedule.run_pending()
        time.sleep(1)