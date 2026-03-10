from typing import Literal, TypedDict


class QueryConfig(TypedDict):
    query_limit: int
    first_run_limit: int
    max_retries: int
    proxy: str


class DownloadConfig(TypedDict):
    download_format: str
    max_retries: int
    proxy: str
    download_dir: str


class ScheduleConfig(TypedDict):
    interval_min: int


class AppConfig(QueryConfig, DownloadConfig, ScheduleConfig):
    pass


class VideoInfo(TypedDict):
    video_id: str
    title: str
    upload_date: str
    channel_name: str


DownloadStatus = Literal["success", "failed"]
