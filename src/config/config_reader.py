import os
import sys

import tomlkit


def get_channel_ids(file_path: str = "channels.txt") -> list[str]:
    """
    读取配置文件，解析频道ID列表。
    忽略空行和#注释行。
    如果文件不存在，自动创建placeholder文件。
    """
    if not os.path.exists(file_path):
        placeholder_content = """# YouTube订阅频道列表
# 可以使用#进行行级注释
# 每行添加一个频道handle (e.g., MoneyXYZ) 或 UC_ ID
# 示例:
# MoneyXYZ
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(placeholder_content)
        print(f"已创建示例配置文件 {file_path}。请编辑添加您的频道ID，然后重新运行。")
        return []

    channel_ids = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                channel_ids.append(line)

    return channel_ids


def load_config(file_path: str = "config.toml") -> dict:
    """
    加载TOML配置文件，返回配置字典。
    如果文件不存在，创建默认配置TOML，提示用户修改，然后中断程序。
    如果文件存在但缺少必需键，提示错误并中断程序。
    所有配置必须源于TOML文件，无硬编码默认值。
    """
    required_keys = {
        "query_limit": "整数，查询视频上限 (e.g., 50)",
        "first_run_limit": "整数，首次运行限制 (e.g., 10)",
        "interval_min": "整数，定时间隔分钟 (e.g., 30)",
        "download_format": "字符串，yt-dlp格式 (e.g., 'bestvideo*[filesize<100M][ext=mp4]+bestaudio')",
        "max_retries": "整数，重试次数 (e.g., 3)",
        "proxy": "字符串，代理设置 (e.g., 'socks5://127.0.0.1:10808')",
    }

    default_config = {
        "query_limit": 10,
        "first_run_limit": 5,
        "interval_min": 1440,
        "download_format": "bestvideo*[filesize<100M][ext=mp4]+bestaudio",
        "max_retries": 3,
        "proxy": "socks5://127.0.0.1:10808",
    }

    if not os.path.exists(file_path):
        # 创建默认配置文件
        with open(file_path, "w", encoding="utf-8") as f:
            tomlkit.dump(default_config, f)
        print(f"已创建默认配置文件 {file_path}。")
        print("请编辑 config.toml 文件，设置您的配置参数，然后重新运行程序。")
        print("必需参数: " + ", ".join(required_keys.keys()))
        sys.exit(1)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            config = tomlkit.parse(f.read())

        # 验证所有必需键是否存在
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            print(f"错误: config.toml 缺少以下必需参数: {', '.join(missing_keys)}")
            print("请添加缺失参数并重新运行。示例:")
            for key, desc in required_keys.items():
                if key in missing_keys:
                    print(f"  {key} = {default_config[key]}  # {desc}")
            sys.exit(1)

        # 类型验证（简单检查）
        for key, value in config.items():
            if key in ["query_limit", "first_run_limit", "interval_min", "max_retries"]:
                if not isinstance(value, int) or value <= 0:
                    print(f"错误: {key} 必须是正整数，当前值: {value}")
                    sys.exit(1)
            elif key == "download_format":
                if not isinstance(value, str):
                    print(f"错误: {key} 必须是字符串，当前值: {value}")
                    sys.exit(1)
            elif key == "proxy":
                if not isinstance(value, str):
                    print(f"错误: {key} 必须是字符串，当前值: {value}")
                    sys.exit(1)

        return dict(config)  # 转换为普通dict
    except Exception as e:
        print(f"加载配置错误: {e}")
        print("请检查 config.toml 文件格式是否正确 (TOML 格式)。")
        sys.exit(1)
