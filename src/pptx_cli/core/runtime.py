from __future__ import annotations

import os
import sys
import time
import uuid
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class RuntimeContext:
    request_id: str
    started_at: float
    llm_mode: bool

    @property
    def duration_ms(self) -> int:
        return int((time.perf_counter() - self.started_at) * 1000)


def build_runtime_context() -> RuntimeContext:
    return RuntimeContext(
        request_id=f"req_{uuid.uuid4().hex[:12]}",
        started_at=time.perf_counter(),
        llm_mode=os.getenv("LLM", "").lower() == "true",
    )


def stdout_is_tty() -> bool:
    return sys.stdout.isatty()
