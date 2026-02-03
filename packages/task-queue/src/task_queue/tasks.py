from __future__ import annotations

from celery.result import AsyncResult
from typing import Any, Generic, TypeVar
import inspect
import subprocess

from pathlib import Path

from celery import Task

from task_queue.celery import app

T = TypeVar("T")

class TypedTask(Task, Generic[T]):
    def delay(self, *args: Any, **kwargs: Any) -> AsyncResult[T]:
        return super().delay(*args, **kwargs)

    def apply_async(self, *args: Any, **kwargs: Any) -> AsyncResult[T]:
        return super().apply_async(*args, **kwargs)


class SubprocessTask(Task):
    """
    A custom Celery Task that wraps execution to catch and format subprocess errors.
    """

    def __call__(self, *args, **kwargs):
        try:
            # We call super().__call__ to ensure Celery sets up the request context
            # (self.request) correctly before running the task body.
            return super().__call__(*args, **kwargs)

        except FileNotFoundError as exc:
            # This catches cases where the executable itself is missing from PATH
            # or a file argument is missing (if not handled inside the task).
            raise FileNotFoundError(
                f"Task failed because a required file or executable was not found. "
                f"Original error: {exc}"
            ) from exc

        except subprocess.CalledProcessError as exc:
            # This catches commands that ran but failed (returned non-zero exit code)
            # provided check=True was used in subprocess.run.
            cmd_str = (
                " ".join(exc.cmd) if isinstance(exc.cmd, list) else exc.cmd
            )
            error_msg = f"Command '{cmd_str}' failed with exit code {exc.returncode}."

            if exc.stderr:
                error_msg += f"\nSTDERR: {exc.stderr}"

            raise RuntimeError(error_msg) from exc


class PathValidationTask(Task):
    """
    A custom Celery Task that automatically validates file path arguments
    before the task is executed.

    Usage:
        @app.task(base=PathValidationTask, files_to_validate={"query_path": "Query file"})
        def my_task(query_path):
            ...
    """

    # Dictionary mapping argument names to descriptions.
    # This is populated by passing `files_to_validate` to the @app.task decorator.
    files_to_validate = {}

    def __call__(self, *args, **kwargs):
        if self.files_to_validate:
            # Inspect the task function's signature to map positional/keyword args to names
            sig = inspect.signature(self.run)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            for arg_name, description in self.files_to_validate.items():
                if arg_name in bound.arguments:
                    path_val = bound.arguments[arg_name]

                    # Skip validation if the value is None (useful for optional arguments)
                    if path_val is None:
                        continue

                    try:
                        Path(path_val).resolve(strict=True)
                    except FileNotFoundError as exc:
                        raise FileNotFoundError(
                            f"{description} not found at {path_val}"
                        ) from exc

        return super().__call__(*args, **kwargs)


@app.task
def add(x, y):
    return x + y


class SubprocessPathValidationTask(SubprocessTask, PathValidationTask):
    """
    A custom Celery Task that combines path validation and subprocess error handling.
    """

    pass
