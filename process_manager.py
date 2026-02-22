import os
import pathlib
import shlex
import subprocess
import time
import logging

LOG_DIR = pathlib.Path(
    os.getenv("XDG_STATE_HOME", os.path.expanduser("~/.local/state"))
) / "linux-wallpaperengine-gui" / "logs"
LOG_FILE = LOG_DIR / "wallpaperengine.log"

class WallpaperProcessManager:
    def __init__(self):
        self._proc = None
        self._log_path = None
        self._log_handle = None
        self._expected_stop = False

    def start(self, cmd):
        self._expected_stop = False
        self._proc, self._log_path, self._log_handle = start_wallpaper_process(cmd)
        return self._proc

    def stop(self, timeout=1):
        self._expected_stop = True
        stopped = stop_process(self._proc, self._log_handle, timeout=timeout)
        self._proc = None
        self._log_handle = None
        self._log_path = None
        return stopped

    def is_running(self):
        return self._proc is not None

    def log_path(self):
        return self._log_path or LOG_FILE

    def check(self):
        if self._proc is None:
            return None
        returncode = self._proc.poll()
        if returncode is None:
            return None
        close_log_handle(self._log_handle)
        log_path = self._log_path
        expected = self._expected_stop
        self._proc = None
        self._log_handle = None
        self._log_path = None
        self._expected_stop = False
        return {
            "returncode": returncode,
            "log_path": log_path,
            "expected": expected,
        }

    def kill_external(self, process_name):
        return kill_external_wallpapers(process_name, ignore_pid=os.getpid())


def ensure_log_dir():
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error("Failed to create log directory: %s", e)
    return LOG_DIR


def open_wallpaper_log(cmd):
    ensure_log_dir()
    log_handle = open(LOG_FILE, "a", encoding="utf-8")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_handle.write(f"\n[{timestamp}] command: {shlex.join(cmd)}\n")
    log_handle.flush()
    return LOG_FILE, log_handle


def close_log_handle(log_handle):
    if log_handle is None:
        return
    try:
        log_handle.flush()
        log_handle.close()
    except Exception:
        pass


def start_wallpaper_process(cmd):
    log_path, log_handle = open_wallpaper_log(cmd)
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return proc, log_path, log_handle
    except Exception:
        close_log_handle(log_handle)
        raise


def stop_process(proc, log_handle=None, timeout=1):
    if proc is None:
        close_log_handle(log_handle)
        return False
    stopped = False
    try:
        proc.terminate()
        proc.wait(timeout=timeout)
        stopped = True
    except Exception:
        try:
            proc.kill()
            proc.wait(timeout=timeout)
            stopped = True
        except Exception:
            stopped = False
    close_log_handle(log_handle)
    return stopped


def kill_external_wallpapers(process_name, ignore_pid=None):
    try:
        cmd = ["pgrep", "-f", process_name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return 0
        killed = 0
        for pid_str in result.stdout.splitlines():
            try:
                pid = int(pid_str)
                if ignore_pid is not None and pid == ignore_pid:
                    continue
                os.kill(pid, 15)
                killed += 1
            except (ValueError, ProcessLookupError):
                continue
        return killed
    except Exception as e:
        logging.error("Failed to kill external wallpapers: %s", e)
        return 0
