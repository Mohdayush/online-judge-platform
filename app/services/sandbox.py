"""Narrow Docker execution boundary for untrusted contestant programs."""
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
    memory_used_kb: int | None = None


class DockerSandbox:
    LANGUAGE_CONFIG = {
        "python": {"image": "python:3.12-alpine", "filename": "main.py", "command": "python /work/main.py"},
        "cpp": {"image": "gcc:14", "filename": "main.cpp", "command": "g++ -O2 /work/main.cpp -o /work/main && /work/main"},
    }

    def build_command(self, language: str, source_directory: Path, time_limit_ms: int, memory_limit_mb: int) -> list[str]:
        if language not in self.LANGUAGE_CONFIG:
            raise ValueError("Unsupported language")
        config = self.LANGUAGE_CONFIG[language]
        return [
            "docker", "run", "--rm", "--init", "--network", "none", "--read-only",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
            "--pids-limit", "64", "--cpus", "0.5", "--memory", f"{memory_limit_mb}m",
            "--memory-swap", f"{memory_limit_mb}m", "--ulimit", "nofile=256:256", "--ulimit", "fsize=32768:32768",
            "--tmpfs", "/work:rw,nosuid,nodev,noexec,size=32m", "--tmpfs", "/tmp:rw,nosuid,nodev,size=16m",
            "-v", f"{source_directory}:/source:ro", config["image"], "sh", "-c",
            f"cp /source/{config['filename']} /work/{config['filename']} && {config['command']}",
        ]

    def execute(self, language: str, source_code: str, stdin: str, time_limit_ms: int, memory_limit_mb: int) -> ExecutionResult:
        if language not in self.LANGUAGE_CONFIG:
            return ExecutionResult(verdict="SYSTEM_ERROR", stderr="Unsupported language")
        if len(source_code.encode("utf-8")) > 50000:
            return ExecutionResult(verdict="SYSTEM_ERROR", stderr="Source code exceeds the maximum size")
        with tempfile.TemporaryDirectory(prefix="judge-") as directory:
            source_directory = Path(directory)
            filename = self.LANGUAGE_CONFIG[language]["filename"]
            (source_directory / filename).write_text(source_code, encoding="utf-8")
            command = self.build_command(language, source_directory, time_limit_ms, memory_limit_mb)
            started = time.perf_counter()
            try:
                process = subprocess.run(command, input=stdin, text=True, capture_output=True, timeout=max(1.0, time_limit_ms / 1000 + 1.0))
            except subprocess.TimeoutExpired:
                return ExecutionResult(verdict="TIME_LIMIT_EXCEEDED", execution_time_ms=time_limit_ms)
            except (OSError, subprocess.SubprocessError) as error:
                return ExecutionResult(verdict="SYSTEM_ERROR", stderr=str(error)[-4000:])
            elapsed = int((time.perf_counter() - started) * 1000)
            stdout, stderr = process.stdout[-100000:], process.stderr[-4000:]
            if process.returncode != 0:
                if language == "cpp" and ("error:" in stderr or "fatal error:" in stderr or "compilation terminated" in stderr): verdict = "COMPILATION_ERROR"
                elif process.returncode in (-9, 137): verdict = "MEMORY_LIMIT_EXCEEDED"
                else: verdict = "RUNTIME_ERROR"
                return ExecutionResult(verdict=verdict, stdout=stdout, stderr=stderr, execution_time_ms=elapsed)
            return ExecutionResult(verdict="OK", stdout=stdout, stderr=stderr, execution_time_ms=elapsed)


def outputs_match(actual: str, expected: str) -> bool:
    """Token comparison ignores insignificant whitespace differences."""
    return actual.split() == expected.split()
