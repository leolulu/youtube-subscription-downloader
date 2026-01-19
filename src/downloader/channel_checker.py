import json
import logging
import subprocess
import time
from typing import Dict, List

from src.utils.stderr_parser import parse_ytdlp_stderr
from src.utils.utils import add_cookies_to_cmd

logger = logging.getLogger(__name__)


def get_videos(channel_id: str, is_first: bool, config: dict) -> List[Dict[str, str]]:
    """
    使用yt-dlp查询频道最近视频元数据。
    查询最近config['query_limit']个视频，如果is_first则返回前config['first_run_limit']个。
    返回列表，按上传日期降序（最新在前）。
    """
    if channel_id.startswith("@"):
        url = f"https://www.youtube.com/{channel_id}/videos"
    else:
        # 纯handle名，自动添加@
        url = f"https://www.youtube.com/@{channel_id}/videos"
    cmd = [
        "yt-dlp",
        "--playlist-end",
        str(config["query_limit"]),
        "--proxy",
        config["proxy"],
        "--dump-json",
        url,
    ]

    add_cookies_to_cmd(cmd)

    videos = []
    max_retries = config["max_retries"]
    last_stderr_info = None  # 保存最后一次的 stderr 解析结果

    for attempt in range(max_retries):
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stdout.strip()

        if result.returncode != 0:
            # 解析 stderr
            stderr_info = parse_ytdlp_stderr(result.stderr)
            last_stderr_info = stderr_info

            # 详细的 stderr 内容只记录到日志文件（DEBUG 级别）
            logger.debug(f"查询频道 {channel_id} 尝试 {attempt + 1} yt-dlp stderr:\n{result.stderr}")

            # 会员视频特殊处理
            if "会员专属视频" in stderr_info["critical_errors"]:
                logger.info(f"频道 {channel_id} 存在会员视频，继续解析可用视频")
                # 不再重试，直接解析当前 output
                break

            # 判断是否需要重试
            if attempt < max_retries - 1:
                # 还有重试机会，输出简短的重试信息
                if stderr_info["has_critical"]:
                    logger.warning(f"查询频道 {channel_id} 尝试 {attempt + 1} 失败: {stderr_info['summary']}，重试中...")
                else:
                    logger.warning(f"查询频道 {channel_id} 尝试 {attempt + 1} 有警告，重试中...")
                time.sleep(2**attempt)  # 指数退避
                continue
            # else: 最后一次尝试，继续往下解析 output

        else:  # returncode == 0，成功
            last_stderr_info = None  # 清除错误信息
            if not output:
                break

        # 解析 stdout 中的 JSON
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
                    logger.warning(f"JSON解析错误 for 频道 {channel_id}: {e}")
                    continue

        # 根据实际结果输出最终状态
        if last_stderr_info:
            # 有 stderr 错误/警告
            if videos:
                # 有警告但成功获取了视频
                if last_stderr_info["has_critical"]:
                    logger.warning(
                        f"查询频道 {channel_id} 有警告 ({last_stderr_info['summary']})，但成功获取 {len(videos)} 个视频"
                    )
                else:
                    logger.info(
                        f"查询频道 {channel_id} 成功获取 {len(videos)} 个视频（{last_stderr_info['summary']}，详见日志）"
                    )
            else:
                # 真正的失败：没有获取到任何视频
                logger.error(f"查询频道 {channel_id} 失败: {last_stderr_info['summary']}")

        # 应用首次限制
        if is_first:
            videos = videos[: config["first_run_limit"]]

        return videos

    return []
