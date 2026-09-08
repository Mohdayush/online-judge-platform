"""A deliberately narrow Docker sandbox for untrusted contestant programs."""
from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
import time


@dataclass
class ExecutionResult:
    verdict: str
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: int | None = None


class DockerSandbox:
    LANGUAGE_CONFIG = {
        "python": {"image": "python:3.12-alpine", "filename": "main.py", "command": "python /work/main.py"},
        "cpp": {"image": "gcc:14", "filename": "main.cpp", "command": "g++ -O2 /work/main.cpp -o /work/main && /work/main"},
    }

    def build_command(self, language: str, source_directory: Path, time_limit_ms: int, memory_limit_mb: int) -> list[str]:
        config = self.LANGUAGE_CONFIG[language]
        return [
            "docker", "run", "--rm", "--network", "none", "--read-only",
            "--pids-limit", "64", "--cpus", "0.5", "--memory", f"{memory_limit_mb}m",
            "--tmpfs", "/work:rw,nosuid,size=32m",
            "-v", f"{source_directory}:/source:ro", config["image"],
            "sh", "-c", f"cp /source/{config['filename']} /work/{config['filename']} && {config['command']}",
        ]

    def execute(self, language: str, source_code: str, stdin: str, time_limit_ms: int, memory_limit_mb: int) -> ExecutionResult:
        if language not in self.LANGUAGE_CONFIG:
            return ExecutionResult(verdict="SYSTEM_ERROR", stderr="Unsupported language")
        with tempfile.TemporaryDirectory(prefix="judge-") as directory:
            source_directory = Path(directory)
            filename = self.LANGUAGE_CONFIG[language]["filename"]
            (source_directory / filename).write_text(source_code, encoding="utf-8")
            command = self.build_command(language, source_directory, time_limit_ms, memory_limit_mb)
            started = time.perf_counter()
            try:
                process = subprocess.run(command, input=stdin, text=True, capture_output=True, timeout=time_limit_ms / 1000 + 1)
            except subprocess.TimeoutExpired:
                return ExecutionResult(verdict="TIME_LIMIT_EXCEEDED", execution_time_ms=time_limit_ms)
            elapsed = int((time.perf_counter() - started) * 1000)
            if process.returncode != 0:
                verdict = "COMPILATION_ERROR" if language == "cpp" and "error:" in process.stderr else "RUNTIME_ERROR"
                return ExecutionResult(verdict=verdict, stdout=process.stdout, stderr=process.stderr[-4000:], execution_time_ms=elapsed)
            return ExecutionResult(verdict="OK", stdout=process.stdout, stderr=process.stderr, execution_time_ms=elapsed)


def outputs_match(actual: str, expected: str) -> bool:
    """Token comparison tolerates insignificant trailing whitespace."""
    return actual.split() == expected.split()
