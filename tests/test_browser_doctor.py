import importlib
import json
import unittest
from pathlib import Path

from typer.testing import CliRunner


def require(name):
    module_name, attr_name = name.rsplit(".", 1)
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        raise AssertionError(f"expected module {module_name} to exist") from exc
    try:
        return getattr(module, attr_name)
    except AttributeError as exc:
        raise AssertionError(f"expected {name} to exist") from exc


class BrowserDoctorTests(unittest.TestCase):
    def resolver(self, **kwargs):
        BrowserRuntimeResolver = require("scansci_pdf.browser_discovery.BrowserRuntimeResolver")
        return BrowserRuntimeResolver(**kwargs)

    def test_explicit_shared_browser_command_wins_and_never_requires_install(self):
        resolver = self.resolver(
            env={"SCANSCI_BROWSER_COMMAND": "scansci-browser serve --port 8765"},
            path_lookup=lambda name: None,
            import_exists=lambda name: False,
            path_exists=lambda path: False,
            http_available=lambda url: False,
            current_module_paths=[],
            default_system_browser_paths=[],
        )

        result = resolver.doctor()

        self.assertEqual(result["selected"], "configured_command")
        self.assertEqual(result["source"], "SCANSCI_BROWSER_COMMAND")
        self.assertEqual(result["command"], ["scansci-browser", "serve", "--port", "8765"])
        self.assertFalse(result["install_needed"])

    def test_path_scansci_browser_is_selected_before_local_pdf_modules_and_packages(self):
        resolver = self.resolver(
            env={},
            path_lookup=lambda name: f"C:/Tools/{name}.exe" if name == "scansci-browser" else None,
            import_exists=lambda name: name in {"cloakbrowser", "playwright"},
            path_exists=lambda path: True,
            http_available=lambda url: True,
            current_module_paths=["D:/scansci-pdf/src/scansci_pdf/browser_cookies.py"],
            default_system_browser_paths=["C:/Program Files/Google/Chrome/Application/chrome.exe"],
        )

        result = resolver.doctor()

        self.assertEqual(result["selected"], "scansci_browser_command")
        self.assertEqual(result["path"], "C:/Tools/scansci-browser.exe")
        self.assertFalse(result["install_needed"])

    def test_local_scansci_pdf_browser_modules_are_reusable_without_installing_browser(self):
        resolver = self.resolver(
            env={},
            path_lookup=lambda name: None,
            import_exists=lambda name: False,
            path_exists=lambda path: str(path).endswith("browser_cookies.py"),
            http_available=lambda url: False,
            current_module_paths=["D:/scansci-pdf/src/scansci_pdf/browser_cookies.py"],
            default_system_browser_paths=[],
        )

        result = resolver.doctor()

        self.assertEqual(result["selected"], "scansci_pdf_browser")
        self.assertEqual(result["source"], "current_scansci_pdf")
        self.assertFalse(result["install_needed"])

    def test_no_browser_runtime_reports_install_hint_without_installing(self):
        resolver = self.resolver(
            env={},
            path_lookup=lambda name: None,
            import_exists=lambda name: False,
            path_exists=lambda path: False,
            http_available=lambda url: False,
            current_module_paths=[],
            default_system_browser_paths=[],
        )

        result = resolver.doctor()

        self.assertEqual(result["selected"], "")
        self.assertTrue(result["install_needed"])
        self.assertIn("pip install cloakbrowser", result["install_hint"])

    def test_doctor_result_is_json_serializable_and_uses_shared_browser_dirs(self):
        resolver = self.resolver(
            env={"SCANSCI_BROWSER_COMMAND": "scansci-browser serve"},
            path_lookup=lambda name: None,
            import_exists=lambda name: False,
            path_exists=lambda path: False,
            http_available=lambda url: False,
            current_module_paths=[],
            default_system_browser_paths=[],
        )

        result = resolver.doctor()

        json.dumps(result)
        self.assertEqual(result["profile_dir"], "D:/Dev/browser-profiles/scansci")
        self.assertEqual(result["cache_dir"], "D:/Dev/cache/browser")

    def test_cli_browser_doctor_prints_json(self):
        app = require("scansci_pdf.main.app")
        runner = CliRunner()

        result = runner.invoke(app, ["browser-doctor"])

        self.assertEqual(result.exit_code, 0, result.output)
        payload = json.loads(result.output)
        self.assertEqual(payload["profile_dir"], "D:/Dev/browser-profiles/scansci")
        self.assertEqual(payload["cache_dir"], "D:/Dev/cache/browser")
        self.assertIn("install_needed", payload)

    def test_mcp_browser_doctor_tool_returns_json_string(self):
        tool = require("scansci_pdf.server.scansci_pdf_browser_doctor")

        payload = json.loads(tool())

        self.assertEqual(payload["profile_dir"], "D:/Dev/browser-profiles/scansci")
        self.assertEqual(payload["cache_dir"], "D:/Dev/cache/browser")
        self.assertIn("install_needed", payload)


if __name__ == "__main__":
    unittest.main()
