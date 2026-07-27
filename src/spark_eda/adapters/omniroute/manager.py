from __future__ import annotations

import atexit
import logging
import subprocess
import time
from pathlib import Path

import httpx

_LOGGER = logging.getLogger(__name__)

_DEFAULT_CACHE_DIR: str = str(Path("~/.cache/spark_eda/omniroute/").expanduser())
_HEALTHCHECK_URL: str = "http://localhost:20128/health"
_HEALTHCHECK_RETRIES: int = 6
_HEALTHCHECK_INTERVAL: float = 5.0
_SUBPROCESS_TIMEOUT: int = 10
_OMNIROUTE_VERSION: str = "3.8.48"


def _find_node() -> str | None:
    try:
        import nodejs  # noqa: PLC0415  # type: ignore[import-untyped]

        node_path: str | None = getattr(nodejs, "path", None)
        if node_path is not None and Path(node_path).is_file():
            return node_path
    except ImportError:
        pass

    import shutil  # noqa: PLC0415

    return shutil.which("node")


def _npm_install(cache_dir: str) -> bool:
    try:
        from nodejs import npm  # noqa: PLC0415  # type: ignore[import-untyped]

        result = npm.run(
            ["install", f"omniroute@{_OMNIROUTE_VERSION}"],
            cwd=cache_dir,
            capture_output=True,
            timeout=120,
        )
        rc: int = getattr(result, "returncode", 1)
        return rc == 0
    except Exception:
        return False


def _port_in_use() -> bool:
    try:
        response: httpx.Response = httpx.get(_HEALTHCHECK_URL, timeout=2.0)
        return response.is_success
    except httpx.HTTPError:
        return False


def _healthcheck() -> bool:
    try:
        response: httpx.Response = httpx.get(_HEALTHCHECK_URL, timeout=5.0)
        return response.is_success
    except httpx.HTTPError:
        return False


class OmniRouteManager:
    def __init__(self, cache_dir: str | None = None) -> None:
        self.cache_dir: str = cache_dir or _DEFAULT_CACHE_DIR
        self._process: subprocess.Popen[bytes] | None = None
        self._installed: bool = False
        atexit.register(self.stop)

    def ensure_running(self) -> bool:  # noqa: PLR0911
        if _port_in_use():
            return True

        if self._process is not None:
            if _healthcheck():
                return True
            self._stop_process()

        node_path: str | None = _find_node()
        if node_path is None:
            _LOGGER.warning("Node.js não encontrado — comentários IA desabilitados")
            return False

        if not self._installed:
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
            if not _npm_install(self.cache_dir):
                _LOGGER.warning("npm install omniroute falhou — comentários IA desabilitados")
                return False
            self._installed = True

        node_modules_bin: str = str(Path(self.cache_dir) / "node_modules" / ".bin" / "omniroute")
        try:
            self._process = subprocess.Popen(
                [node_path, node_modules_bin],
                cwd=self.cache_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            _LOGGER.warning("Falha ao iniciar subprocesso OmniRoute", exc_info=True)
            return False

        for _ in range(_HEALTHCHECK_RETRIES):
            if _healthcheck():
                return True
            time.sleep(_HEALTHCHECK_INTERVAL)

        total_wait: float = _HEALTHCHECK_RETRIES * _HEALTHCHECK_INTERVAL
        _LOGGER.warning("OmniRoute não respondeu após %ds", total_wait)
        self._stop_process()
        return False

    def stop(self) -> None:
        self._stop_process()

    def _stop_process(self) -> None:
        process: subprocess.Popen[bytes] | None = self._process
        if process is None:
            return
        self._process = None
        try:
            process.terminate()
            process.wait(timeout=_SUBPROCESS_TIMEOUT)
        except Exception:
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception:
                pass
