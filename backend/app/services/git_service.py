from __future__ import annotations

import subprocess
from pathlib import Path

from app.config import project_root


def git_available() -> bool:
    return (project_root() / ".git").exists()


def status_short() -> str:
    if not git_available():
        return "not a git repository"
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={project_root().as_posix()}", "status", "--short"],
        cwd=project_root(),
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def path_is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(project_root().resolve())
        return True
    except ValueError:
        return False


def commit_paths(paths: list[Path], message: str) -> bool:
    if not git_available():
        return False
    safe_paths = [path for path in paths if path_is_inside_repo(path)]
    if not safe_paths:
        return False
    root = project_root()
    subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "add", *[str(path) for path in safe_paths]],
        cwd=root,
        check=True,
    )
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "commit", "-m", message],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0
