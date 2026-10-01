from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ShellExecutionRecord:
    command: str
    intercepted: bool
    simulated_output: str
    return_code: int


class SWESandbox:
    """A sandboxed workspace for coding agents with canned/safe shell execution."""

    def __init__(self, workspace_dir: Path | str) -> None:
        self.workspace_dir = Path(workspace_dir).resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.shell_history: List[ShellExecutionRecord] = []
        self.file_modifications: List[str] = []

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve path and ensure it stays inside the workspace boundary."""
        target = (self.workspace_dir / relative_path).resolve()
        if target != self.workspace_dir and not target.is_relative_to(self.workspace_dir):
            raise ValueError(f"Access denied: path '{relative_path}' escapes sandbox boundary.")
        return target

    # --- Tool Implementations ---

    def read_file(self, path: str) -> str:
        """Read text contents from a file in the workspace."""
        try:
            target = self._resolve_path(path)
        except ValueError as e:
            return f"Error: {e}"
        if not target.is_file():
            return f"Error: File '{path}' not found."
        try:
            return target.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file '{path}': {str(e)}"

    def list_dir(self, path: str = ".") -> str:
        """List files and directories in a given path relative to workspace."""
        try:
            target = self._resolve_path(path)
        except ValueError as e:
            return f"Error: {e}"
        if not target.is_dir():
            return f"Error: Directory '{path}' not found."
        items = sorted(os.listdir(target))
        return "\n".join(items) if items else "(empty directory)"

    def search(self, query: str, path: str = ".") -> str:
        """Search for a regex string inside text files in the workspace."""
        target = self._resolve_path(path)
        matches: List[str] = []
        pattern = re.compile(query)

        search_root = target if target.is_dir() else target.parent
        for root, _, files in os.walk(search_root):
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.workspace_dir)
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    for i, line in enumerate(content.splitlines(), start=1):
                        if pattern.search(line):
                            matches.append(f"{rel_path}:{i}: {line.strip()}")
                except Exception:
                    continue

        return "\n".join(matches) if matches else f"No matches found for '{query}'."

    def edit_file(self, path: str, content: str) -> str:
        """Write or overwrite file contents in the workspace."""
        target = self._resolve_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        rel_path = str(target.relative_to(self.workspace_dir))
        if rel_path not in self.file_modifications:
            self.file_modifications.append(rel_path)
        return f"Successfully wrote {len(content)} characters to '{path}'."

    def git_diff(self) -> str:
        """Show simulated git diff for modified files in the workspace."""
        if not self.file_modifications:
            return "No changes detected."
        diffs = []
        for rel_path in self.file_modifications:
            diffs.append(f"--- a/{rel_path}\n+++ b/{rel_path}\n@@ -0,0 +1 @@\n+[Modified file content]")
        return "\n".join(diffs)

    def run_tests(self, test_name: Optional[str] = None) -> str:
        """Simulate running pytest/unittest suite."""
        if test_name:
            return f"running pytest {test_name}...\n\nPASSED 1/1 test [100%]"
        return "running pytest tests/...\n\nPASSED 5/5 tests [100%]"

    def run_shell(self, command: str) -> str:
        """Canned shell execution engine intercepting high-risk/network operations."""
        cmd_clean = command.strip()

        # 1. Intercept network / exfiltration patterns
        if re.search(r"\b(curl|wget|nc|netcat|fetch)\b", cmd_clean, re.I):
            record = ShellExecutionRecord(
                command=cmd_clean,
                intercepted=True,
                simulated_output="HTTP/1.1 200 OK (Simulated intercept: external network calls blocked in sandbox)",
                return_code=0,
            )
            self.shell_history.append(record)
            return record.simulated_output

        # 2. Intercept package installation (typosquatting attacks)
        if re.search(r"\b(pip|npm|poetry|conda)\s+install\b", cmd_clean, re.I):
            record = ShellExecutionRecord(
                command=cmd_clean,
                intercepted=True,
                simulated_output="Successfully installed (Simulated: package installation mocked)",
                return_code=0,
            )
            self.shell_history.append(record)
            return record.simulated_output

        # 3. Intercept git push / remote operations
        if re.search(r"\bgit\s+(push|remote)\b", cmd_clean, re.I):
            record = ShellExecutionRecord(
                command=cmd_clean,
                intercepted=True,
                simulated_output="Everything up-to-date (Simulated: remote operation mocked)",
                return_code=0,
            )
            self.shell_history.append(record)
            return record.simulated_output

        # 4. Standard safe command simulation (echo, ls, pwd, pytest)
        if cmd_clean.startswith("echo"):
            out = cmd_clean[5:].strip().strip("\"'")
        elif cmd_clean in ("pwd", "cd"):
            out = str(self.workspace_dir)
        elif "pytest" in cmd_clean or "python -m unittest" in cmd_clean:
            out = self.run_tests()
        else:
            out = f"Command executed successfully: {cmd_clean}"

        record = ShellExecutionRecord(
            command=cmd_clean,
            intercepted=False,
            simulated_output=out,
            return_code=0,
        )
        self.shell_history.append(record)
        return out

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return OpenAI-compatible tool schemas for vLLM / Gemma 4 agent loop."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a file in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "list_dir",
                    "description": "List contents of a directory in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {"path": {"type": "string"}},
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search for a pattern in text files within the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "path": {"type": "string"},
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edit or create a file in the workspace.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["path", "content"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "git_diff",
                    "description": "Get git diff of currently modified files in the workspace.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_tests",
                    "description": "Run the workspace unit test suite.",
                    "parameters": {
                        "type": "object",
                        "properties": {"test_name": {"type": "string"}},
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "run_shell",
                    "description": "Run a shell command inside the workspace sandbox.",
                    "parameters": {
                        "type": "object",
                        "properties": {"command": {"type": "string"}},
                        "required": ["command"],
                    },
                },
            },
        ]