"""The monitoring endpoints are now wired in (were defined but never called)."""
import pytest
from fastapi.testclient import TestClient

from api_fastapi import DeCoinAPI
from node import DeCoinNode


def _client():
    return TestClient(DeCoinAPI(DeCoinNode()).app)


class TestMonitoringEndpoints:
    def test_health_is_served(self):
        r = _client().get("/monitoring/health")
        assert r.status_code == 200

    def test_metrics_is_served(self):
        r = _client().get("/monitoring/metrics")
        assert r.status_code == 200

    def test_dashboard_is_served(self):
        r = _client().get("/monitoring/dashboard")
        assert r.status_code == 200
