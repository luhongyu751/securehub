import os
import sys
import subprocess
import tempfile

def _subprocess_add(input_pdf_path, watermark_text, font_size, opacity):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    add_py = os.path.join(project_root, 'modules', 'add.py')
    if not os.path.exists(add_py):
        raise FileNotFoundError(f"add.py not found at {add_py}")

    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp_out.close()

    cmd = [sys.executable, add_py, input_pdf_path, tmp_out.name, watermark_text, str(font_size), str(opacity)]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        try:
            os.unlink(tmp_out.name)
        except Exception:
            pass
        raise RuntimeError(f"Watermark process failed: {proc.stderr}\nSTDOUT: {proc.stdout}")

    return tmp_out.name


def run_add_watermark(input_pdf_path, watermark_text, font_size=40, opacity=0.3):
    """优先尝试直接导入并调用 `modules.add.add_watermark`，若失败回退到子进程方式。

    返回带水印的临时文件路径。调用者负责删除该临时文件或交由后台任务清理。
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # 尝试直接导入模块以避免启动子进程（性能与可观测性更好）
    try:
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from modules.add import add_watermark as add_watermark_func

        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp_out.close()

        # 调用模块内部函数（同步）
        add_watermark_func(input_pdf_path, tmp_out.name, watermark_text, font_size=font_size, opacity=opacity)
        return tmp_out.name
    except Exception as exc:
        # 如果直接调用失败，回退到原有的子进程实现
        try:
            return _subprocess_add(input_pdf_path, watermark_text, font_size, opacity)
        except Exception:
            # 把原始异常与回退异常一起抛出，便于调试
            raise RuntimeError(f"Direct call failed: {exc}")


if __name__ == '__main__':
    # 简单 CLI 用法，便于本地测试
    if len(sys.argv) < 4:
        print("Usage: python watermark_wrapper.py input.pdf 'Watermark Text' [font_size] [opacity]")
        sys.exit(1)
    input_pdf = sys.argv[1]
    text = sys.argv[2]
    font_size = float(sys.argv[3]) if len(sys.argv) > 3 else 40
    opacity = float(sys.argv[4]) if len(sys.argv) > 4 else 0.3
    out = run_add_watermark(input_pdf, text, font_size, opacity)
    print(out)
