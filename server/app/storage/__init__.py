"""存储层：Markdown 报告 + CSV 索引 + 项目注册表。"""
from .markdown_writer import (
    append_resolution,
    generate_error_id,
    parse_error_id,
    read_report,
    render_report,
    report_path,
    write_new_report,
    write_report,
)
from .csv_index import (
    append_index_row,
    load_index,
    search_index,
    update_index_row,
)
from .registry import (
    delete as delete_registry,
    get_one as get_registry,
    load_registry,
    upsert as upsert_registry,
)

__all__ = [
    "append_resolution",
    "append_index_row",
    "delete_registry",
    "generate_error_id",
    "get_registry",
    "load_index",
    "load_registry",
    "parse_error_id",
    "read_report",
    "render_report",
    "report_path",
    "search_index",
    "update_index_row",
    "upsert_registry",
    "write_new_report",
    "write_report",
]
