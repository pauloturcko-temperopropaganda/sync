"""Estado compartilhado de uma execução de sincronização em segundo
plano — em memória, um processo só. Se o processo do dashboard
reiniciar, o histórico do console reinicia junto (o que importa de
verdade, `data_sync_runs`, continua no banco)."""

from __future__ import annotations

import io
import threading
from datetime import datetime, timezone


class _TeeStream(io.TextIOBase):
    """Redireciona print() tanto pro console real (log do processo)
    quanto pro buffer de linhas que o dashboard exibe."""

    def __init__(self, target: "SyncRunState", real_stream):
        self._state = target
        self._real_stream = real_stream

    def write(self, text: str) -> int:
        self._real_stream.write(text)
        self._state._append(text)
        return len(text)

    def flush(self) -> None:
        self._real_stream.flush()


class SyncRunState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.running = False
        self.lines: list[str] = []
        self.started_at: datetime | None = None
        self.finished_at: datetime | None = None
        self.ok: bool | None = None
        self._partial_line = ""

    def _append(self, text: str) -> None:
        with self._lock:
            self._partial_line += text
            while "\n" in self._partial_line:
                line, self._partial_line = self._partial_line.split("\n", 1)
                self.lines.append(line)

    def start(self) -> _TeeStream:
        import sys

        with self._lock:
            self.running = True
            self.lines = []
            self._partial_line = ""
            self.started_at = datetime.now(timezone.utc)
            self.finished_at = None
            self.ok = None
        return _TeeStream(self, sys.stdout)

    def finish(self, ok: bool) -> None:
        with self._lock:
            if self._partial_line:
                self.lines.append(self._partial_line)
                self._partial_line = ""
            self.running = False
            self.finished_at = datetime.now(timezone.utc)
            self.ok = ok

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "running": self.running,
                "lines": list(self.lines),
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "finished_at": self.finished_at.isoformat() if self.finished_at else None,
                "ok": self.ok,
            }


sync_run_state = SyncRunState()
