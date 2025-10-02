def sanitize_filename(name: str) -> str:
    return (
        name.replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
    )


def add_cookies_to_cmd(cmd: list):
    """
    检查项目根目录下以 .cookie 结尾的文件，如果存在，使用第一个添加到 cmd 中（--cookies 参数）。
    位置插入在 cmd[1] 前（通常在 --proxy 之前）。
    如果找到，打印日志。
    """
    import os

    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    cookie_files = [f for f in os.listdir(root_dir) if f.endswith(".cookie")]
    if cookie_files:
        cookie_file = os.path.join(root_dir, cookie_files[0])
        cmd.insert(1, "--cookies")
        cmd.insert(2, cookie_file)
        print(f"使用 cookie 文件: {cookie_file}")
