import json
import subprocess
import time
from typing import Dict, List


def get_videos(channel_id: str, is_first: bool = False, max_retries: int = 3) -> List[Dict[str, str]]:
    """
    使用yt-dlp查询频道最近视频元数据。
    查询最近50个视频，如果is_first则返回前10个。
    返回列表，按上传日期降序（最新在前）。
    """
    if channel_id.startswith("@"):
        url = f"https://www.youtube.com/{channel_id}/videos"
    elif channel_id.startswith("UC_"):
        url = f"https://www.youtube.com/channel/{channel_id}/videos"
    else:
        # 纯handle名，自动添加@
        url = f"https://www.youtube.com/@{channel_id}/videos"
    cmd = [
        "yt-dlp",
        "--playlist-end",
        "5",  # TODO: change back to 50
        "--proxy",
        "socks5://127.0.0.1:10808",
        "--dump-json",
        url,
    ]

    videos = []
    for attempt in range(max_retries):
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stdout.strip()
        if result.returncode != 0:
            print(f"查询频道 {channel_id} 尝试 {attempt + 1} returncode {result.returncode}: {result.stderr}")
            # 即使returncode != 0，也尝试解析stdout (可能有有效JSON)
            if "This video is available to this channel's members" in result.stderr:
                print(f"频道 {channel_id} 存在会员视频，但继续解析可用视频。")
                attempt = max_retries  # 不再重试
            if attempt < max_retries - 1:
                time.sleep(2**attempt)  # 指数退避
                continue
            else:  # 最终失败，但仍解析当前output
                pass
        else:  # 成功
            if not output:
                break

        for line in output.split("\n"):
            if line.strip():
                try:
                    video_info = json.loads(line)
                    if video_info.get("_type") == "video":
                        video = {
                            "video_id": video_info.get("id", ""),
                            "title": video_info.get("title", "").replace("/", "_").replace("\\", "_"),  # 清理文件名
                            "upload_date": video_info.get("upload_date", ""),  # YYYYMMDD
                            "channel_name": video_info.get("uploader", "").replace("/", "_").replace("\\", "_"),
                        }
                        videos.append(video)
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误 for 频道 {channel_id}: {e}")
                    continue

        # 应用首次限制
        if is_first:
            videos = videos[:10]

        return videos

    return []
