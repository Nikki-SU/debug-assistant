"""存储层：Markdown 报告 + CSV 索引。"""
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

__all__ = [
    "append_resolution",
    "append_index_row",
    "generate_error_id",
    "load_index",
    "parse_error_id",
    "read_report",
    "render_report",
    "report_path",
    "search_index",
    "update_index_row",
    "write_new_report",
    "write_report",
]
