import os
from typing import Any, Dict, Optional

from src.telemetry.logger import logger


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


class _NoopSpan:
    """No-op span so LangSmith can be disabled without changing call sites."""

    def start_child(
        self,
        name: str,
        run_type: str,
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "_NoopSpan":
        return self

    def end(
        self,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        return None


class _LangSmithSpan:
    def __init__(self, run_tree: Any):
        self._run_tree = run_tree

    def start_child(
        self,
        name: str,
        run_type: str,
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "_LangSmithSpan":
        try:
            child = self._run_tree.create_child(
                name=name,
                run_type=run_type,
                inputs=inputs or {},
                extra={"metadata": metadata or {}},
            )
            child.post()
            return _LangSmithSpan(child)
        except Exception as exc:
            logger.log_event("LANGSMITH_CHILD_ERROR", {"name": name, "error": str(exc)})
            return _NoopSpan()

    def end(
        self,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        try:
            if error:
                self._run_tree.end(outputs=outputs or {}, error=error)
            else:
                self._run_tree.end(outputs=outputs or {})
            self._run_tree.patch()
        except Exception as exc:
            logger.log_event("LANGSMITH_PATCH_ERROR", {"error": str(exc)})


class LangSmithTracer:
    """Optional LangSmith tracer that records each ReAct step and tool call."""

    def __init__(self):
        self.enabled = False
        self.project = "day3-react-agent"
        self._run_tree_cls = None
        self._init_error_logged = False

    def _refresh_config(self) -> None:
        self.enabled = _to_bool(os.getenv("LANGSMITH_TRACING", "false"))
        self.project = os.getenv("LANGSMITH_PROJECT", "day3-react-agent")

    def _ensure_ready(self) -> bool:
        self._refresh_config()

        if not self.enabled:
            return False

        if self._run_tree_cls is not None:
            return True

        try:
            from langsmith.run_trees import RunTree

            self._run_tree_cls = RunTree
            self._init_error_logged = False
            return True
        except Exception as exc:
            if not self._init_error_logged:
                logger.log_event("LANGSMITH_DISABLED", {"reason": str(exc)})
                self._init_error_logged = True
            return False

    def start_agent_run(
        self,
        user_input: str,
        model_name: str,
        max_steps: int,
    ) -> Any:
        if not self._ensure_ready() or self._run_tree_cls is None:
            return _NoopSpan()

        try:
            run = self._run_tree_cls(
                name="ReActAgent.run",
                run_type="chain",
                project_name=self.project,
                inputs={
                    "input": user_input,
                    "model": model_name,
                    "max_steps": max_steps,
                },
                extra={"metadata": {"component": "react-agent"}},
            )
            run.post()
            return _LangSmithSpan(run)
        except Exception as exc:
            logger.log_event("LANGSMITH_START_ERROR", {"error": str(exc)})
            return _NoopSpan()


langsmith_tracer = LangSmithTracer()