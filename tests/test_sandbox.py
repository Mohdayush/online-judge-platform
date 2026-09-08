from pathlib import Path

from app.services.sandbox import DockerSandbox, outputs_match


def test_sandbox_command_has_security_controls(tmp_path: Path):
    command = DockerSandbox().build_command("python", tmp_path, 1000, 128)
    assert "--network" in command and "none" in command
    assert "--read-only" in command
    assert "--pids-limit" in command
    assert "--memory" in command


def test_output_matching_ignores_insignificant_whitespace():
    assert outputs_match("1  2\n", "1 2")
    assert not outputs_match("1 3", "1 2")
