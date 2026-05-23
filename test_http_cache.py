"""Tests for the shared HTTP cache layer (http_cache.py).

These verify:
  - The cache is OFF by default (so existing provider tests keep working).
  - When CANLAND_HTTP_CACHE_PATH is set, requests_cache.install_cache is
    called with the expected arguments.
  - Only municipal-API hosts are cacheable; everything else passes through.
  - The install is idempotent (multiple calls don't re-install).
"""

import os
import tempfile
import unittest
from unittest.mock import patch

import http_cache


class HttpCacheInstallTests(unittest.TestCase):
    def setUp(self):
        http_cache.reset_for_testing()

    def tearDown(self):
        http_cache.reset_for_testing()

    def test_no_env_var_means_no_cache(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CANLAND_HTTP_CACHE_PATH", None)
            with patch("requests_cache.install_cache") as mock_install:
                installed = http_cache.install_http_cache_if_configured()
        self.assertFalse(installed)
        mock_install.assert_not_called()

    def test_empty_env_var_means_no_cache(self):
        with patch.dict(os.environ, {"CANLAND_HTTP_CACHE_PATH": "   "}):
            with patch("requests_cache.install_cache") as mock_install:
                installed = http_cache.install_http_cache_if_configured()
        self.assertFalse(installed)
        mock_install.assert_not_called()

    def test_set_env_var_installs_cache(self):
        with tempfile.TemporaryDirectory() as td:
            cache_path = os.path.join(td, "cache")
            with patch.dict(os.environ, {
                "CANLAND_HTTP_CACHE_PATH": cache_path,
                "CANLAND_HTTP_CACHE_TTL_SECONDS": "300",
            }):
                with patch("requests_cache.install_cache") as mock_install:
                    installed = http_cache.install_http_cache_if_configured()
        self.assertTrue(installed)
        mock_install.assert_called_once()
        kwargs = mock_install.call_args.kwargs
        self.assertEqual(kwargs["cache_name"], cache_path)
        self.assertEqual(kwargs["backend"], "sqlite")
        self.assertEqual(kwargs["allowable_methods"], ("GET",))
        self.assertEqual(kwargs["allowable_codes"], (200,))

    def test_cacheable_hosts_are_scoped_correctly(self):
        with tempfile.TemporaryDirectory() as td:
            cache_path = os.path.join(td, "cache")
            with patch.dict(os.environ, {"CANLAND_HTTP_CACHE_PATH": cache_path}):
                with patch("requests_cache.install_cache") as mock_install:
                    http_cache.install_http_cache_if_configured()

        urls_expire_after = mock_install.call_args.kwargs["urls_expire_after"]
        # Edmonton and Calgary should be cacheable
        self.assertIn("data.edmonton.ca/*", urls_expire_after)
        self.assertIn("data.calgary.ca/*", urls_expire_after)
        # Everything else should be DO_NOT_CACHE
        import requests_cache
        self.assertEqual(urls_expire_after["*"], requests_cache.DO_NOT_CACHE)

    def test_install_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            cache_path = os.path.join(td, "cache")
            with patch.dict(os.environ, {"CANLAND_HTTP_CACHE_PATH": cache_path}):
                with patch("requests_cache.install_cache") as mock_install:
                    http_cache.install_http_cache_if_configured()
                    http_cache.install_http_cache_if_configured()
                    http_cache.install_http_cache_if_configured()
        # Should only install once across three calls
        self.assertEqual(mock_install.call_count, 1)

    def test_invalid_ttl_falls_back_to_default(self):
        with tempfile.TemporaryDirectory() as td:
            cache_path = os.path.join(td, "cache")
            with patch.dict(os.environ, {
                "CANLAND_HTTP_CACHE_PATH": cache_path,
                "CANLAND_HTTP_CACHE_TTL_SECONDS": "not-a-number",
            }):
                with patch("requests_cache.install_cache") as mock_install:
                    installed = http_cache.install_http_cache_if_configured()
        self.assertTrue(installed)
        urls_expire_after = mock_install.call_args.kwargs["urls_expire_after"]
        # Default 600 seconds should apply to the municipal hosts
        self.assertEqual(urls_expire_after["data.edmonton.ca/*"], 600)

    def test_install_failure_is_graceful(self):
        """If install_cache raises, we log and continue rather than crashing
        the whole app at startup."""
        with tempfile.TemporaryDirectory() as td:
            cache_path = os.path.join(td, "cache")
            with patch.dict(os.environ, {"CANLAND_HTTP_CACHE_PATH": cache_path}):
                with patch("requests_cache.install_cache", side_effect=RuntimeError("boom")):
                    installed = http_cache.install_http_cache_if_configured()
        self.assertFalse(installed)


class HealthEndpointReportsCacheStatusTest(unittest.TestCase):
    """The /api/health endpoint should expose cache enablement so operators
    can see at a glance whether production has caching active."""

    def test_health_reports_cache_disabled_by_default(self):
        from app import app

        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CANLAND_HTTP_CACHE_PATH", None)
            resp = app.test_client().get("/api/health")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertFalse(body["http_cache_enabled"])

    def test_health_reports_cache_enabled_when_set(self):
        from app import app

        with patch.dict(os.environ, {"CANLAND_HTTP_CACHE_PATH": "/tmp/canland_cache"}):
            resp = app.test_client().get("/api/health")
        body = resp.get_json()
        self.assertTrue(body["http_cache_enabled"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
