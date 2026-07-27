from __future__ import annotations

"""Testes para o gerenciador de ciclo de vida do OmniRoute.

Testa OmniRouteManager: descoberta do Node.js, npm install,
subprocesso, healthcheck, stop e atexit.
"""

import atexit as atexit_module
from unittest import mock

import httpx

from spark_eda.adapters.omniroute.manager import OmniRouteManager


_BUILTINS_IMPORT: object = __import__


def _raise(exc: Exception) -> None:
    raise exc


class TestOmniRouteManager:
    """Testes unitários para OmniRouteManager."""

    def test_port_in_use_returns_true_when_omniroute_already_running(self) -> None:
        """ensure_running deve retornar True se a porta já estiver
        ocupada por um OmniRoute saudável."""
        with mock.patch("spark_eda.adapters.omniroute.manager._port_in_use", return_value=True):
            manager = OmniRouteManager()
            result = manager.ensure_running()
            assert result is True

    def test_ensure_running_when_node_found_returns_true(self) -> None:
        """ensure_running deve retornar True quando Node.js é
        encontrado, npm install succeede e healthcheck passa."""
        with (
            mock.patch("spark_eda.adapters.omniroute.manager._port_in_use", return_value=False),
            mock.patch("spark_eda.adapters.omniroute.manager._find_node", return_value="/usr/bin/node"),
            mock.patch("spark_eda.adapters.omniroute.manager._npm_install", return_value=True),
            mock.patch("spark_eda.adapters.omniroute.manager.subprocess.Popen") as mock_popen,
            mock.patch("spark_eda.adapters.omniroute.manager._healthcheck", return_value=True),
        ):
            manager = OmniRouteManager()
            result = manager.ensure_running()

            assert result is True
            mock_popen.assert_called_once()

    def test_ensure_running_when_node_not_found_returns_false(self) -> None:
        """ensure_running deve retornar False quando Node.js não
        é encontrado."""
        with (
            mock.patch("spark_eda.adapters.omniroute.manager._port_in_use", return_value=False),
            mock.patch("spark_eda.adapters.omniroute.manager._find_node", return_value=None),
            mock.patch("spark_eda.adapters.omniroute.manager._npm_install") as mock_install,
        ):
            manager = OmniRouteManager()
            result = manager.ensure_running()

            assert result is False
            mock_install.assert_not_called()

    def test_ensure_running_when_npm_install_fails_returns_false(self) -> None:
        """ensure_running deve retornar False quando npm install falha."""
        with (
            mock.patch("spark_eda.adapters.omniroute.manager._port_in_use", return_value=False),
            mock.patch("spark_eda.adapters.omniroute.manager._find_node", return_value="/usr/bin/node"),
            mock.patch("spark_eda.adapters.omniroute.manager._npm_install", return_value=False),
        ):
            manager = OmniRouteManager()
            result = manager.ensure_running()

            assert result is False

    def test_ensure_running_when_healthcheck_times_out_returns_false(self) -> None:
        """ensure_running deve retornar False quando healthcheck
        não responde após todas as tentativas."""
        with (
            mock.patch("spark_eda.adapters.omniroute.manager._port_in_use", return_value=False),
            mock.patch("spark_eda.adapters.omniroute.manager._find_node", return_value="/usr/bin/node"),
            mock.patch("spark_eda.adapters.omniroute.manager._npm_install", return_value=True),
            mock.patch("spark_eda.adapters.omniroute.manager.subprocess.Popen"),
            mock.patch("spark_eda.adapters.omniroute.manager._healthcheck", return_value=False),
            mock.patch("spark_eda.adapters.omniroute.manager.time.sleep"),
        ):
            manager = OmniRouteManager()
            result = manager.ensure_running()

            assert result is False

    def test_stop_kills_subprocess_gracefully(self) -> None:
        """stop deve encerrar o subprocesso graciosamente."""
        with (
            mock.patch("spark_eda.adapters.omniroute.manager._port_in_use", return_value=False),
            mock.patch("spark_eda.adapters.omniroute.manager._find_node", return_value="/usr/bin/node"),
            mock.patch("spark_eda.adapters.omniroute.manager._npm_install", return_value=True),
            mock.patch("spark_eda.adapters.omniroute.manager._healthcheck", return_value=True),
        ):
            manager = OmniRouteManager()
            manager.ensure_running()

            with mock.patch.object(manager, "_stop_process") as mock_stop:
                manager.stop()
                mock_stop.assert_called_once()

    def test_stop_when_no_process_does_nothing(self) -> None:
        """stop não deve falhar quando nenhum processo foi iniciado."""
        manager = OmniRouteManager()
        manager.stop()  # Should not raise

    def test_atexit_registered_on_init(self) -> None:
        """atexit.register deve ser chamado para stop no __init__."""
        # Capture original before patching to avoid recursion
        original_register = atexit_module.register
        registered_funcs: list = []

        def tracking_register(func, *args, **kwargs):
            registered_funcs.append(func)
            return original_register(func, *args, **kwargs)

        with mock.patch("atexit.register", side_effect=tracking_register):
            manager = OmniRouteManager()
            # Compare by function name and qualname since bound method
            # objects are different on each access
            stop_qualname = f"{type(manager).__name__}.stop"
            assert any(
                getattr(f, "__qualname__", None) == stop_qualname or getattr(f, "__name__", None) == "stop"
                for f in registered_funcs
            )

    def test_ensure_running_is_idempotent_on_subsequent_calls(self) -> None:
        """Chamadas subsequentes a ensure_running não devem
        reiniciar o subprocesso se ele já está saudável."""
        with (
            mock.patch("spark_eda.adapters.omniroute.manager._port_in_use", return_value=False),
            mock.patch("spark_eda.adapters.omniroute.manager._find_node", return_value="/usr/bin/node"),
            mock.patch("spark_eda.adapters.omniroute.manager._npm_install", return_value=True),
            mock.patch("spark_eda.adapters.omniroute.manager.subprocess.Popen") as mock_popen,
        ):
            manager = OmniRouteManager()

            # First call — healthcheck passes
            with mock.patch("spark_eda.adapters.omniroute.manager._healthcheck", return_value=True):
                first_result = manager.ensure_running()

            # Second call — _healthcheck alone must return True (process already exists)
            # This time _healthcheck is called, but _find_node / _npm_install / Popen are not
            with mock.patch("spark_eda.adapters.omniroute.manager._healthcheck", return_value=True):
                second_result = manager.ensure_running()

            assert first_result is True
            assert second_result is True
            # Popen should be called only once (first call)
            assert mock_popen.call_count == 1

    def test_ensure_running_restarts_when_process_died(self) -> None:
        """ensure_running deve reiniciar o subprocesso se o healthcheck
        falhar em uma chamada subsequente."""
        with (
            mock.patch("spark_eda.adapters.omniroute.manager._port_in_use", return_value=False),
            mock.patch("spark_eda.adapters.omniroute.manager._find_node", return_value="/usr/bin/node"),
            mock.patch("spark_eda.adapters.omniroute.manager._npm_install", return_value=True),
            mock.patch("spark_eda.adapters.omniroute.manager.subprocess.Popen") as mock_popen,
            mock.patch("spark_eda.adapters.omniroute.manager.time.sleep"),
        ):
            manager = OmniRouteManager()

            # First call — healthcheck passes
            with mock.patch("spark_eda.adapters.omniroute.manager._healthcheck", return_value=True):
                manager.ensure_running()

            # Second call — healthcheck fails once, then passes after restart
            healthcheck_results = iter([False, True])
            with mock.patch(
                "spark_eda.adapters.omniroute.manager._healthcheck",
                side_effect=lambda: next(healthcheck_results),
            ):
                result = manager.ensure_running()

            assert result is True
            # Popen should be called twice (initial + restart)
            assert mock_popen.call_count == 2

    def test_ensure_running_with_popen_oserror_returns_false(self) -> None:
        """ensure_running deve retornar False quando subprocess.Popen
        levanta OSError."""
        with (
            mock.patch("spark_eda.adapters.omniroute.manager._port_in_use", return_value=False),
            mock.patch("spark_eda.adapters.omniroute.manager._find_node", return_value="/usr/bin/node"),
            mock.patch("spark_eda.adapters.omniroute.manager._npm_install", return_value=True),
            mock.patch("spark_eda.adapters.omniroute.manager.subprocess.Popen", side_effect=OSError),
            mock.patch("spark_eda.adapters.omniroute.manager.time.sleep"),
        ):
            manager = OmniRouteManager()
            result = manager.ensure_running()

            assert result is False

    # ------------------------------------------------------------------
    # Testes diretos para _stop_process (exception handler — kill fallback)
    # ------------------------------------------------------------------

    def test_stop_process_terminate_exception_triggers_kill(self) -> None:
        """_stop_process deve chamar kill quando terminate levanta
        exceção, e não propagar o erro."""
        fake_proc = mock.MagicMock()
        fake_proc.terminate.side_effect = Exception("terminate failed")
        fake_proc.kill.return_value = None
        fake_proc.wait.return_value = None

        manager = OmniRouteManager()
        manager._process = fake_proc
        manager._stop_process()

        fake_proc.terminate.assert_called_once()
        fake_proc.kill.assert_called_once()
        assert manager._process is None

    def test_stop_process_kill_also_fails_does_not_propagate(self) -> None:
        """_stop_process não deve propagar exceção mesmo quando
        tanto terminate quanto kill falham."""
        fake_proc = mock.MagicMock()
        fake_proc.terminate.side_effect = Exception("terminate failed")
        fake_proc.kill.side_effect = Exception("kill also failed")
        fake_proc.wait.return_value = None

        manager = OmniRouteManager()
        manager._process = fake_proc
        manager._stop_process()

        fake_proc.terminate.assert_called_once()
        fake_proc.kill.assert_called_once()
        assert manager._process is None

    # ------------------------------------------------------------------
    # Testes diretos para _port_in_use  (linhas 52-56)
    # ------------------------------------------------------------------

    def test_port_in_use_returns_true_when_http_ok(self) -> None:
        from spark_eda.adapters.omniroute.manager import _port_in_use

        with mock.patch("spark_eda.adapters.omniroute.manager.httpx.get") as mock_get:
            mock_response = mock.MagicMock()
            mock_response.is_success = True
            mock_get.return_value = mock_response

            result = _port_in_use()
            assert result is True

    def test_port_in_use_returns_false_on_http_error(self) -> None:
        from spark_eda.adapters.omniroute.manager import _port_in_use

        with mock.patch(
            "spark_eda.adapters.omniroute.manager.httpx.get",
            side_effect=httpx.HTTPError("connection refused"),
        ):
            result = _port_in_use()
            assert result is False

    # ------------------------------------------------------------------
    # Testes diretos para _healthcheck  (linhas 60-64)
    # ------------------------------------------------------------------

    def test_healthcheck_returns_true_when_http_ok(self) -> None:
        from spark_eda.adapters.omniroute.manager import _healthcheck

        with mock.patch("spark_eda.adapters.omniroute.manager.httpx.get") as mock_get:
            mock_response = mock.MagicMock()
            mock_response.is_success = True
            mock_get.return_value = mock_response

            result = _healthcheck()
            assert result is True

    def test_healthcheck_returns_false_on_http_error(self) -> None:
        from spark_eda.adapters.omniroute.manager import _healthcheck

        with mock.patch(
            "spark_eda.adapters.omniroute.manager.httpx.get",
            side_effect=httpx.HTTPError("connection refused"),
        ):
            result = _healthcheck()
            assert result is False

    # ------------------------------------------------------------------
    # Testes diretos para _find_node (linhas 22-33)
    # ------------------------------------------------------------------

    def test_find_node_with_nodejs_package_and_valid_path(self) -> None:
        from spark_eda.adapters.omniroute.manager import _find_node

        fake_nodejs = mock.MagicMock()
        fake_nodejs.path = "/fake/nodejs/bin/node"

        with (
            mock.patch.dict("sys.modules", {"nodejs": fake_nodejs}),
            mock.patch("pathlib.Path.is_file", return_value=True),
        ):
            result = _find_node()
            assert result == "/fake/nodejs/bin/node"

    def test_find_node_with_nodejs_path_is_none_falls_back(self) -> None:
        from spark_eda.adapters.omniroute.manager import _find_node

        fake_nodejs = mock.MagicMock()
        fake_nodejs.path = None

        with (
            mock.patch.dict("sys.modules", {"nodejs": fake_nodejs}),
            mock.patch("shutil.which", return_value="/usr/bin/node"),
        ):
            result = _find_node()
            assert result == "/usr/bin/node"

    def test_find_node_with_nodejs_path_not_a_file_falls_back(self) -> None:
        from spark_eda.adapters.omniroute.manager import _find_node

        fake_nodejs = mock.MagicMock()
        fake_nodejs.path = "/nonexistent/node"

        with (
            mock.patch.dict("sys.modules", {"nodejs": fake_nodejs}),
            mock.patch("pathlib.Path.is_file", return_value=False),
            mock.patch("shutil.which", return_value="/usr/bin/node"),
        ):
            result = _find_node()
            assert result == "/usr/bin/node"

    def test_find_node_import_error_falls_back_to_shutil(self) -> None:
        from spark_eda.adapters.omniroute.manager import _find_node

        orig_import = _BUILTINS_IMPORT

        def _mock_import(name, *args, **kwargs):
            if name == "nodejs":
                raise ImportError(f"No module named '{name}'")
            return orig_import(name, *args, **kwargs)

        with (
            mock.patch("builtins.__import__", side_effect=_mock_import),
            mock.patch("shutil.which", return_value="/usr/bin/node"),
        ):
            result = _find_node()
            assert result == "/usr/bin/node"

    def test_find_node_not_found_anywhere_returns_none(self) -> None:
        from spark_eda.adapters.omniroute.manager import _find_node

        orig_import = _BUILTINS_IMPORT

        def _mock_import(name, *args, **kwargs):
            if name == "nodejs":
                raise ImportError(f"No module named '{name}'")
            return orig_import(name, *args, **kwargs)

        with (
            mock.patch("builtins.__import__", side_effect=_mock_import),
            mock.patch("shutil.which", return_value=None),
        ):
            result = _find_node()
            assert result is None

    # ------------------------------------------------------------------
    # Testes diretos para _npm_install (linhas 37-48)
    # ------------------------------------------------------------------

    def test_npm_install_success(self) -> None:
        from spark_eda.adapters.omniroute.manager import _npm_install

        fake_nodejs = mock.MagicMock()
        fake_npm = mock.MagicMock()
        fake_result = mock.MagicMock()
        fake_result.returncode = 0
        fake_npm.run.return_value = fake_result
        fake_nodejs.npm = fake_npm

        with mock.patch.dict("sys.modules", {"nodejs": fake_nodejs}):
            result = _npm_install("/tmp/cache")
            assert result is True

    def test_npm_install_failure(self) -> None:
        from spark_eda.adapters.omniroute.manager import _npm_install

        fake_nodejs = mock.MagicMock()
        fake_npm = mock.MagicMock()
        fake_result = mock.MagicMock()
        fake_result.returncode = 1
        fake_npm.run.return_value = fake_result
        fake_nodejs.npm = fake_npm

        with mock.patch.dict("sys.modules", {"nodejs": fake_nodejs}):
            result = _npm_install("/tmp/cache")
            assert result is False

    def test_npm_install_exception_returns_false(self) -> None:
        from spark_eda.adapters.omniroute.manager import _npm_install

        fake_nodejs = mock.MagicMock()
        fake_npm = mock.MagicMock()
        fake_npm.run.side_effect = RuntimeError("npm failed")
        fake_nodejs.npm = fake_npm

        with mock.patch.dict("sys.modules", {"nodejs": fake_nodejs}):
            result = _npm_install("/tmp/cache")
            assert result is False

    def test_npm_install_import_error_returns_false(self) -> None:
        from spark_eda.adapters.omniroute.manager import _npm_install

        orig_import = _BUILTINS_IMPORT

        def _mock_import(name, *args, **kwargs):
            if name == "nodejs":
                raise ImportError(f"No module named '{name}'")
            return orig_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=_mock_import):
            result = _npm_install("/tmp/cache")
            assert result is False
