import os


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
