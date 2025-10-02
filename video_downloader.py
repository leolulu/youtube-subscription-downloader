import os
import subprocess
import time
from typing import Optional


def download_video(video_id: str, channel_name: str, upload_date: str, title: str, max_retries: int = 1) -> Optional[str]:
    """
    下载单个视频到downloads/文件夹。
    返回文件路径如果成功，否则None。
    """
    if not os.path.exists("downloads"):
        os.makedirs("downloads")

    # 清理标题用于文件名
    safe_title = (
        title.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )
    safe_channel = (
        channel_name.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )

    output_template = f"downloads/{safe_channel}_{upload_date}_{safe_title}.%(ext)s"
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        "yt-dlp",
        "--proxy",
        "socks5://127.0.0.1:10808",
        "-f",
        "bestvideo*[filesize<100M][ext=mp4]+bestaudio",
        "--remux-video",
        "mp4",
        "-o",
        output_template,
        url,
    ]

    for attempt in range(max_retries):
        try:
            result = subprocess.run(cmd, check=True)
            if result.returncode == 0:
                # 构建文件路径 (假设ext=mp4)
                file_path = f"downloads/{safe_channel}_{upload_date}_{safe_title}.mp4"
                if os.path.exists(file_path):
                    return file_path
                else:
                    print(f"下载成功但文件未找到: {file_path}")
                    return None
        except subprocess.CalledProcessError as e:
            if attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            else:
                print(f"下载视频 {video_id} 失败: {e}")
                return None

    return None
