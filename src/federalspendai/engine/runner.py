"""Background scheduler for automatic ingest and analysis."""

from __future__ import annotations

import logging
import threading
from typing import Any

from federalspendai.config import Settings, get_settings
from federalspendai.engine.pipeline import run_cycle
from federalspendai.engine.state import mark_cycle_failed, mark_cycle_finished, mark_cycle_started
from federalspendai.plugins.base import EnginePlugin
from federalspendai.plugins.registry import load_plugins

logger = logging.getLogger(__name__)


class EngineRunner:
    """Runs ingest/analyze cycles on an interval and notifies MCP plugins."""

    def __init__(self, settings: Settings | None = None, plugins: list[EnginePlugin] | None = None) -> None:
        self.settings = settings or get_settings()
        self.plugins = plugins if plugins is not None else load_plugins(self.settings)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._running_cycle = False

    def run_cycle_once(self) -> dict[str, Any]:
        with self._lock:
            if self._running_cycle:
                return {"skipped": True, "reason": "cycle already running"}
            self._running_cycle = True

        mark_cycle_started(self.settings)
        try:
            summary = run_cycle(
                settings=self.settings,
                incremental=True,
                emit_events=True,
            )
            for plugin in self.plugins:
                try:
                    plugin.on_cycle_complete(summary)
                except Exception:
                    logger.exception("Plugin %s failed on_cycle_complete", plugin.name)
            mark_cycle_finished(summary, self.settings)
            return summary
        except Exception as exc:
            mark_cycle_failed(str(exc), self.settings)
            logger.exception("Engine cycle failed")
            raise
        finally:
            with self._lock:
                self._running_cycle = False

    def _loop(self) -> None:
        if self.settings.engine_run_on_start:
            try:
                self.run_cycle_once()
            except Exception:
                logger.exception("Initial engine cycle failed")

        interval = max(60, self.settings.engine_poll_interval_seconds)
        while not self._stop.wait(interval):
            try:
                self.run_cycle_once()
            except Exception:
                logger.exception("Scheduled engine cycle failed")

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="federalspend-engine", daemon=True)
        self._thread.start()
        logger.info(
            "Engine scheduler started (interval=%ss, plugins=%s)",
            self.settings.engine_poll_interval_seconds,
            [plugin.name for plugin in self.plugins],
        )

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        for plugin in self.plugins:
            try:
                plugin.shutdown()
            except Exception:
                logger.exception("Plugin %s failed shutdown", plugin.name)

    def status(self) -> dict[str, Any]:
        from federalspendai.engine.state import read_state

        state = read_state(self.settings)
        return {
            "enabled": self.settings.engine_enabled,
            "poll_interval_seconds": self.settings.engine_poll_interval_seconds,
            "datasets": self.settings.engine_datasets_list(),
            "plugins": [
                {"name": plugin.name, "type": plugin.plugin_type}
                for plugin in self.plugins
            ],
            "scheduler_running": bool(self._thread and self._thread.is_alive()),
            "cycle_in_progress": self._running_cycle,
            **state,
        }
