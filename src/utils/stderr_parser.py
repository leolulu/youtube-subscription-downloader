"""
yt-dlp stderr 输出解析工具

将 yt-dlp 的 stderr 输出分类，区分"可忽略的警告"和"关键错误"
"""

import re
from typing import Dict, List


# 可忽略的错误模式（格式检查相关，不影响视频元数据获取）
IGNORABLE_PATTERNS = [
    # JS 挑战求解失败
    r"n challenge solving failed",
    # 格式不可用
    r"Unable to download format .+\. Skipping",
    # 直播格式检查失败
    r"fragment \d+ not found",
    # 请求的格式不可用
    r"Requested format is not available",
    # HTTP 403 针对格式检查
    r"\[download\] Got error: HTTP Error 403",
    # 格式下载错误
    r"ERROR:\s*$",  # 空的 ERROR 行
    r"ERROR:\s*\[download\]",
    # HLS 直播流相关
    r"Unable to download format \d+-\d+",
    # 重试信息
    r"Retrying \(\d+/\d+\)",
]

# 关键错误模式（真正的问题，需要用户关注）
CRITICAL_PATTERNS = [
    # 视频不可用
    (r"Video unavailable", "视频不可用"),
    # 私有视频
    (r"Private video", "私有视频"),
    # 视频不可用（通用）
    (r"This video is not available", "视频不可用"),
    (r"This video has been removed", "视频已被删除"),
    # 频道不存在
    (r"Channel not found", "频道不存在"),
    (r"404.*Not Found", "资源不存在"),
    # 地区限制
    (r"not available in your country", "地区限制"),
    (r"geo.?restricted", "地区限制"),
    # 年龄限制
    (r"Sign in to confirm your age", "需要登录确认年龄"),
    # 认证问题
    (r"Please sign in", "需要登录"),
    # 网络问题（非格式相关）
    (r"Unable to download webpage", "无法下载网页"),
    # SSL 问题
    (r"SSL.*UNEXPECTED_EOF", "SSL连接异常"),
    # 会员视频
    (r"members.only", "会员专属视频"),
    (r"available to this channel's members", "会员专属视频"),
    # 直播未开始
    (r"Premieres in", "视频尚未发布"),
    (r"This live event will begin", "直播尚未开始"),
]


def parse_ytdlp_stderr(stderr: str) -> Dict:
    """
    解析 yt-dlp 的 stderr 输出，分类错误类型

    Args:
        stderr: yt-dlp 命令的 stderr 输出

    Returns:
        {
            "critical_errors": [...],      # 关键错误列表（需要显示给用户）
            "ignorable_warnings": [...],   # 可忽略的警告列表（只记录到日志文件）
            "summary": "...",              # 一行简短的摘要信息
            "has_critical": bool,          # 是否有关键错误
            "raw": stderr                  # 原始内容
        }
    """
    critical_errors: List[str] = []
    ignorable_warnings: List[str] = []

    lines = stderr.split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检查是否匹配可忽略模式
        is_ignorable = False
        for pattern in IGNORABLE_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                is_ignorable = True
                ignorable_warnings.append(line)
                break

        if is_ignorable:
            continue

        # 检查是否匹配关键错误模式
        is_critical = False
        for pattern, description in CRITICAL_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                is_critical = True
                # 避免重复添加相同类型的错误
                if description not in critical_errors:
                    critical_errors.append(description)
                break

        # 未匹配任何模式的 WARNING/ERROR 行
        if not is_critical and (line.startswith("WARNING:") or line.startswith("ERROR:")):
            # 作为可忽略警告处理，但仍记录
            ignorable_warnings.append(line)

    # 生成摘要
    summary = _generate_summary(critical_errors, ignorable_warnings)

    return {
        "critical_errors": critical_errors,
        "ignorable_warnings": ignorable_warnings,
        "summary": summary,
        "has_critical": len(critical_errors) > 0,
        "raw": stderr,
    }


def _generate_summary(critical_errors: List[str], ignorable_warnings: List[str]) -> str:
    """
    生成一行简短的摘要信息
    """
    if critical_errors:
        # 有关键错误，显示第一个
        return critical_errors[0]
    elif ignorable_warnings:
        # 只有可忽略警告
        return "部分格式检查失败"
    else:
        return ""
