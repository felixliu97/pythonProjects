import tempfile
import time
from pathlib import Path

import requests

try:
    from utils import get_root_dir
except ImportError:
    from scripts.utils import get_root_dir

_CACHE_DIR = get_root_dir() / ".pdf_cache"
_CACHE_DIR.mkdir(exist_ok=True)


def get_cache_dir() -> Path:
    return _CACHE_DIR


def _build_download_session(base_session) -> requests.Session:
    download_session = requests.Session()
    download_session.headers.update(getattr(base_session, "headers", {}))
    adapter = requests.adapters.HTTPAdapter(max_retries=0)
    download_session.mount("http://", adapter)
    download_session.mount("https://", adapter)
    return download_session


def download_pdf(
    session,
    url: str,
    filename: str,
    *,
    cache_dir: Path | None = None,
    timeout=(10, 20),
    chunk_size: int = 65536,
    logger=None,
    max_elapsed_seconds: float | None = None,
    disable_retries: bool = False,
) -> Path | None:
    if not url:
        return None

    resolved_cache_dir = cache_dir or _CACHE_DIR
    resolved_cache_dir.mkdir(exist_ok=True)
    local_path = resolved_cache_dir / filename
    if local_path.exists():
        return local_path

    tmp_path = None
    request_session = (
        _build_download_session(session) if disable_retries and isinstance(session, requests.Session) else session
    )
    start_time = time.monotonic()
    try:
        if logger:
            logger.info(f"Downloading PDF: {filename}...")
        with request_session.get(url, timeout=timeout, stream=True) as response:
            response.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, dir=resolved_cache_dir, suffix=".part") as tmp_file:
                tmp_path = Path(tmp_file.name)
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if max_elapsed_seconds is not None and (time.monotonic() - start_time) > max_elapsed_seconds:
                        raise TimeoutError(f"download exceeded {max_elapsed_seconds:.1f}s")
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
            elif isinstance(e, TimeoutError):
                logger.error(f"PDF download timed out fast for {filename}: {e}")
            else:
                logger.error(f"Failed to download PDF {filename}: {e}")
        return None
    finally:
        if disable_retries and request_session is not session:
            request_session.close()
