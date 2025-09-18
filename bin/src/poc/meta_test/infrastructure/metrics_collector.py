"""Runtime metrics collector for operational data."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class MetricsCollector:
    """Collects runtime metrics for learning."""

    def __init__(self, data_dir: str):
        """Initialize collector with data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.data_dir / "runtime_metrics.json"
        self._ensure_metrics_file()

    def _ensure_metrics_file(self) -> None:
        """Ensure metrics file exists."""
        if not self.metrics_file.exists():
            self.metrics_file.write_text(json.dumps({
                "test_executions": [],
                "operational_metrics": {},
                "business_metrics": {},
                "incidents": []
            }))

    def _load_metrics(self) -> dict[str, Any]:
        """Load metrics from file."""
        return json.loads(self.metrics_file.read_text())

    def _save_metrics(self, metrics: dict[str, Any]) -> None:
        """Save metrics to file."""
        self.metrics_file.write_text(json.dumps(metrics, indent=2, default=str))

    def record_test_execution(self,
                            requirement_id: str,
                            test_id: str,
                            passed: bool,
                            duration_ms: float) -> None:
        """Record test execution result."""
        metrics = self._load_metrics()

        execution = {
            "timestamp": datetime.now().isoformat(),
            "requirement_id": requirement_id,
            "test_id": test_id,
            "passed": passed,
            "duration_ms": duration_ms
        }

        metrics["test_executions"].append(execution)
        self._save_metrics(metrics)

    def record_operational_metric(self,
                                metric_name: str,
                                value: float,
                                timestamp: datetime | None = None) -> None:
        """Record operational metric value."""
        metrics = self._load_metrics()

        if metric_name not in metrics["operational_metrics"]:
            metrics["operational_metrics"][metric_name] = []

        record = {
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "value": value
        }

        metrics["operational_metrics"][metric_name].append(record)
        self._save_metrics(metrics)

    def record_business_metric(self,
                             metric_name: str,
                             value: float,
                             timestamp: datetime | None = None) -> None:
        """Record business metric value."""
        metrics = self._load_metrics()

        if metric_name not in metrics["business_metrics"]:
            metrics["business_metrics"][metric_name] = []

        record = {
            "timestamp": (timestamp or datetime.now()).isoformat(),
            "value": value
        }

        metrics["business_metrics"][metric_name].append(record)
        self._save_metrics(metrics)

    def record_incident(self,
                       incident_id: str,
                       severity: str,
                       description: str,
                       related_requirements: list[str]) -> None:
        """Record production incident."""
        metrics = self._load_metrics()

        incident = {
            "timestamp": datetime.now().isoformat(),
            "incident_id": incident_id,
            "severity": severity,
            "description": description,
            "related_requirements": related_requirements
        }

        metrics["incidents"].append(incident)
        self._save_metrics(metrics)

    def get_test_history(self, requirement_id: str) -> list[dict[str, Any]]:
        """Get test execution history for requirement."""
        metrics = self._load_metrics()

        return [
            execution for execution in metrics["test_executions"]
            if execution["requirement_id"] == requirement_id
        ]

    def get_operational_metrics(self,
                              metric_names: list[str] | None = None) -> dict[str, list[float]]:
        """Get operational metrics values."""
        metrics = self._load_metrics()
        result = {}

        for name, records in metrics["operational_metrics"].items():
            if metric_names is None or name in metric_names:
                result[name] = [record["value"] for record in records]

        return result

    def get_business_metrics(self,
                           metric_names: list[str] | None = None) -> dict[str, list[float]]:
        """Get business metrics values."""
        metrics = self._load_metrics()
        result = {}

        for name, records in metrics["business_metrics"].items():
            if metric_names is None or name in metric_names:
                result[name] = [record["value"] for record in records]

        return result

    def get_incidents(self, requirement_id: str | None = None) -> list[dict[str, Any]]:
        """Get incidents, optionally filtered by requirement."""
        metrics = self._load_metrics()

        if requirement_id:
            return [
                incident for incident in metrics["incidents"]
                if requirement_id in incident.get("related_requirements", [])
            ]

        return metrics["incidents"]
