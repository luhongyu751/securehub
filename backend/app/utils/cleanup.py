import os
import time
import tempfile
from typing import List


def list_temp_pdf_files(temp_dir: str = None) -> List[str]:
    d = temp_dir or tempfile.gettempdir()
    files = []
    for name in os.listdir(d):
        if name.lower().endswith('.pdf') and name.startswith('tmp'):
            files.append(os.path.join(d, name))
    return files


def cleanup_expired_files(temp_dir: str = None, older_than_seconds: int = 300) -> List[str]:
    """删除在临时目录中比指定秒数更旧的 PDF 文件，返回被删除的文件列表。"""
    d = temp_dir or tempfile.gettempdir()
    now = time.time()
    removed = []
    for path in list_temp_pdf_files(d):
        try:
            mtime = os.path.getmtime(path)
            if now - mtime > older_than_seconds:
                os.remove(path)
                removed.append(path)
        except Exception:
            continue
    return removed
