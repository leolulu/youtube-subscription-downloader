import logging
import os
import subprocess
import time
from typing import Optional

from src.utils.utils import add_cookies_to_cmd, sanitize_filename

logger = logging.getLogger(__name__)


def download_video(video_id: str, channel_name: str, upload_date: str, title: str, config: dict) -> Optional[str]:
    """
    下载单个视频到配置的download_dir文件夹。
    支持本地路径和SMB UNC路径 (e.g., \\\\192.168.1.100\\share)。
    返回文件路径如果成功，否则None。
    """
    download_dir = config["download_dir"]

    # 只为本地路径创建目录，SMB路径由yt-dlp处理
    if not download_dir.startswith("\\\\") and not os.path.exists(download_dir):
        os.makedirs(download_dir, exist_ok=True)

    # 清理标题用于文件名
    safe_title = sanitize_filename(title)
    safe_channel = sanitize_filename(channel_name)

    output_template = os.path.join(download_dir, f"{safe_channel}_{upload_date}_{safe_title}.%(ext)s")
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "--proxy",
        config["proxy"],
        "-f",
        config["download_format"],
        "--remux-video",
        "mp4",
        "--no-playlist",
        "-o",
        output_template,
        url,
    ]

    add_cookies_to_cmd(cmd)

    max_retries = config["max_retries"]
    for attempt in range(max_retries):
        try:
            result = subprocess.run(cmd, check=True)
            if result.returncode == 0:
                # 构建文件路径 (假设ext=mp4)
                file_path = os.path.join(download_dir, f"{safe_channel}_{upload_date}_{safe_title}.mp4")
                if os.path.exists(file_path):
                    return file_path
                else:
                    logger.warning(f"下载成功但文件未找到: {file_path}")
                    return None
        except subprocess.CalledProcessError as e:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            else:
                logger.error(f"下载视频 {video_id} 失败: {e}\n此错误可能由于 yt-dlp 未更新导致，请运行 'yt-dlp -U' 更新版本。")
                return None

    return None
