import tempfile
from pathlib import Path

try:
    from utils import get_root_dir
except ImportError:
    from scripts.utils import get_root_dir

_CACHE_DIR = get_root_dir() / ".pdf_cache"
_CACHE_DIR.mkdir(exist_ok=True)


def get_cache_dir() -> Path:
    return _CACHE_DIR


def download_pdf(
    session,
    url: str,
    filename: str,
    *,
    cache_dir: Path | None = None,
    timeout=(10, 20),
    chunk_size: int = 65536,
    logger=None,
) -> Path | None:
    if not url:
        return None

    resolved_cache_dir = cache_dir or _CACHE_DIR
    resolved_cache_dir.mkdir(exist_ok=True)
    local_path = resolved_cache_dir / filename
    if local_path.exists():
        return local_path

    tmp_path = None
    try:
        if logger:
            logger.info(f"Downloading PDF: {filename}...")
        with session.get(url, timeout=timeout, stream=True) as response:
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, dir=resolved_cache_dir, suffix=".part") as tmp_file:
                tmp_path = Path(tmp_file.name)
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        tmp_file.write(chunk)
        tmp_path.replace(local_path)
        return local_path
    except Exception as e:
        try:
            if tmp_path and tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        if logger:
            if hasattr(e, "response") and e.response is not None and e.response.status_code == 404:
                logger.warning(f"PDF not available (404): {filename}")
            else:
                logger.error(f"Failed to download PDF {filename}: {e}")
        return None
