"""transport.py unit tests — mock subprocess, no real SSH."""
import subprocess
from unittest.mock import patch, MagicMock
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.claude/skills/jetson-verify/scripts"))
from transport import detect_target_env, build_target_command, exec_on_target


class TestDetectTargetEnv:
    @patch("os.path.exists", return_value=True)
    def test_local_jetson_when_tegra_exists(self, mock_exists):
        assert detect_target_env() == "local_jetson"
        mock_exists.assert_called_with("/etc/nv_tegra_release")

    @patch("os.path.exists", return_value=False)
    def test_remote_jetson_when_not_tegra(self, mock_exists):
        assert detect_target_env() == "remote_jetson"


class TestBuildTargetCommand:
    def test_local_returns_bash_lc(self):
        argv = build_target_command("echo hello", "local_jetson")
        assert argv == ["bash", "-lc", "echo hello"]

    def test_remote_returns_ssh_argv(self):
        argv = build_target_command("echo hello", "remote_jetson")
        assert argv[0] == "ssh"
        assert "jetson-nano" in argv
        joined = " ".join(argv)
        assert "echo hello" in joined
        assert "bash -lc" in joined

    def test_remote_handles_special_chars(self):
        cmd = "awk '/MemAvailable:/ {print $2}' /proc/meminfo"
        argv = build_target_command(cmd, "remote_jetson")
        assert argv[0] == "ssh"
        assert argv[:2] == ["ssh", "jetson-nano"]


class TestExecOnTarget:
    @patch("subprocess.run")
    def test_success_returns_stdout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="42\n", stderr="")
        rc, out, err = exec_on_target("echo 42", "local_jetson", timeout_sec=5)
        assert rc == 0
        assert out == "42\n"

    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="x", timeout=5))
    def test_timeout_returns_minus2(self, mock_run):
        rc, out, err = exec_on_target("sleep 999", "local_jetson", timeout_sec=5)
        assert rc == -2
        assert "timeout" in err.lower()

    @patch("subprocess.run", side_effect=OSError("No such file"))
    def test_transport_failure_returns_minus1(self, mock_run):
        rc, out, err = exec_on_target("echo x", "remote_jetson", timeout_sec=5)
        assert rc == -1
        assert "No such file" in err

    @patch("subprocess.run")
    def test_nonzero_exit_code_passed_through(self, mock_run):
        mock_run.return_value = MagicMock(returncode=127, stdout="", stderr="not found")
        rc, out, err = exec_on_target("badcmd", "local_jetson", timeout_sec=5)
        assert rc == 127
