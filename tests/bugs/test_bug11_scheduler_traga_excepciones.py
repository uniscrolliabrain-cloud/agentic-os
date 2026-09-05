"""Bug 11 - Scheduler traga excepciones auditoría: orchestration/scheduler.py loguea pero no falla"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile

from agentic_os.orchestration.scheduler import Scheduler
from agentic_os.kernel.world.events import Event


def test_scheduler_fire_audits_on_failure():
    """El scheduler debe auditar en EventLog cuando un job falla."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_log = MagicMock()
        scheduler = Scheduler(data_dir=tmpdir, event_log=mock_log)

        # Simular un fire que lanza excepción
        scheduler._fire("tenant-1", "pipeline-1", "schedule-1")

        # Debe haber auditado el fallo
        assert mock_log.append.called, \
            "Scheduler no auditó el fallo en EventLog"


def test_scheduler_emits_event_on_trigger():
    """El scheduler debe emitir un Event cuando se dispara un schedule."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_log = MagicMock()
        scheduler = Scheduler(data_dir=tmpdir, event_log=mock_log)

        # Programar un schedule diario
        scheduler.schedule_daily("tenant-1", "pipeline-1", hour=10)

        # Forzar el fire
        scheduler._fire("tenant-1", "pipeline-1", "schedule-1")

        # Debe haber emitido un evento
        assert mock_log.append.called, \
            "Scheduler no emitió Event al disparar un schedule"


def test_scheduler_handles_fire_exception_gracefully():
    """Si _fire falla, el scheduler debe manejar la excepción sin crash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_log = MagicMock()
        mock_log.append.side_effect = Exception("EventLog full")
        scheduler = Scheduler(data_dir=tmpdir, event_log=mock_log)

        # No debe lanzar excepción no manejada
        try:
            scheduler._fire("tenant-1", "pipeline-1", "schedule-1")
        except Exception:
            pytest.fail("Scheduler no debe lanzar excepciones no manejadas desde _fire")
