import logging
import os
import signal
import sys

from src.config.config_reader import get_channel_ids, load_config
from src.core.history_manager import has_records_for_channel, init_db, is_downloaded, log_download, mark_downloaded
from src.core.scheduler import run_loop, setup_schedule
from src.downloader.channel_checker import get_videos
from src.downloader.video_downloader import download_video

# 设置日志
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def check_and_download(config):
    """
    检查并下载新视频的核心函数。
    """
    try:
        channel_ids = get_channel_ids()
        if not channel_ids:
            logger.warning("没有找到频道ID，请检查channels.txt")
            return

        logger.info(f"开始检查 {len(channel_ids)} 个频道的新视频")

        for channel_id in channel_ids:
            logger.info(f"处理频道: {channel_id}")

            is_first = not has_records_for_channel(channel_id)
            videos = get_videos(channel_id, is_first, config)

            if not videos:
                logger.warning(f"频道 {channel_id} 无视频数据")
                continue

            logger.info(f"从频道 {channel_id} 拉取 {len(videos)} 个视频")

            new_downloads = 0
            for video in videos:
                video_id = video["video_id"]
                if not is_downloaded(video_id):
                    logger.info(f"发现新视频: {video['title'][:50]}...")

                    file_path = download_video(video_id, video["channel_name"], video["upload_date"], video["title"], config)

                    if file_path:
                        mark_downloaded(video_id, channel_id)
                        log_download(video_id, channel_id, "success", file_path, str(is_first))
                        logger.info(f"下载成功: {file_path}")
                        new_downloads += 1
                    else:
                        log_download(video_id, channel_id, "failed", None, str(is_first))
                        logger.error(f"下载失败: {video_id}")
                else:
                    logger.debug(f"视频已下载: {video_id}")

            if new_downloads == 0:
                logger.info(f"频道 {channel_id} 本批次无新视频下载")

        logger.info("检查循环完成")
    except Exception as e:
        logger.error(f"检查循环错误: {e}", exc_info=True)


def signal_handler(sig, frame):
    logger.info("接收到停止信号，优雅关闭...")
    sys.exit(0)


def main():
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 加载配置
    config = load_config()

    # 初始化
    init_db()
    logger.info("YouTube订阅视频下载器启动")

    # 立即执行一次检查
    check_and_download(config)

    # 设置定时任务
    def wrapper():
        check_and_download(config)
    setup_schedule(wrapper, config)

    # 运行循环
    try:
        run_loop()
    except KeyboardInterrupt:
        logger.info("脚本停止")
    except Exception as e:
        logger.error(f"运行错误: {e}", exc_info=True)


if __name__ == "__main__":
    main()
