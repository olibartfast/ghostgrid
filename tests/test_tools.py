"""Tests for built-in ReAct tools (filesystem, shell, and vision stubs)."""

from ghostgrid.models import Agent, InferenceConfig
from ghostgrid.tools import BUILTIN_TOOLS
from ghostgrid.tools.builtin import (
    _tool_list_directory,
    _tool_neuriplo_detect,
    _tool_read_file,
    _tool_run_bash,
    _tool_search_files,
    _tool_write_file,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _agent() -> Agent:
    return Agent(
        model="test-model",
        endpoint="http://localhost/v1/chat/completions",
        api_key="EMPTY",
        provider="openai",
    )


def _cfg() -> InferenceConfig:
    return InferenceConfig(image_paths=[], detail="low", max_tokens=256, resize=False, target_size=(512, 512))


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------


def test_builtin_tools_contains_filesystem_tools():
    for name in ("read_file", "write_file", "list_directory", "run_bash", "search_files"):
        assert name in BUILTIN_TOOLS, f"'{name}' missing from BUILTIN_TOOLS"


def test_builtin_tools_contains_vision_tools():
    for name in ("describe", "detect_objects", "read_text", "analyze_region", "count_objects"):
        assert name in BUILTIN_TOOLS, f"'{name}' missing from BUILTIN_TOOLS"


# ---------------------------------------------------------------------------
# read_file
# ---------------------------------------------------------------------------


def test_read_file_returns_content(tmp_path):
    f = tmp_path / "hello.txt"
    f.write_text("hello world")
    result = _tool_read_file(_agent(), _cfg(), path=str(f))
    assert result == "hello world"


def test_read_file_missing_path_param():
    result = _tool_read_file(_agent(), _cfg())
    assert result.startswith("ERROR:")


def test_read_file_nonexistent_file():
    result = _tool_read_file(_agent(), _cfg(), path="/no/such/file.txt")
    assert result.startswith("ERROR:")


# ---------------------------------------------------------------------------
# write_file
# ---------------------------------------------------------------------------


def test_write_file_creates_file(tmp_path):
    dest = tmp_path / "out.txt"
    result = _tool_write_file(_agent(), _cfg(), path=str(dest), content="new content")
    assert "Written" in result
    assert dest.read_text() == "new content"


def test_write_file_creates_parent_directories(tmp_path):
    dest = tmp_path / "a" / "b" / "c.txt"
    _tool_write_file(_agent(), _cfg(), path=str(dest), content="deep")
    assert dest.read_text() == "deep"


def test_write_file_overwrites_existing(tmp_path):
    dest = tmp_path / "f.txt"
    dest.write_text("old")
    _tool_write_file(_agent(), _cfg(), path=str(dest), content="new")
    assert dest.read_text() == "new"


def test_write_file_missing_path_param():
    result = _tool_write_file(_agent(), _cfg())
    assert result.startswith("ERROR:")


# ---------------------------------------------------------------------------
# list_directory
# ---------------------------------------------------------------------------


def test_list_directory_shows_files_and_dirs(tmp_path):
    (tmp_path / "file.txt").write_text("x")
    (tmp_path / "subdir").mkdir()
    result = _tool_list_directory(_agent(), _cfg(), path=str(tmp_path))
    assert "file.txt" in result
    assert "subdir/" in result


def test_list_directory_empty_dir(tmp_path):
    result = _tool_list_directory(_agent(), _cfg(), path=str(tmp_path))
    assert result == "(empty directory)"


def test_list_directory_nonexistent_path():
    result = _tool_list_directory(_agent(), _cfg(), path="/no/such/dir")
    assert result.startswith("ERROR:")


def test_list_directory_defaults_to_cwd():
    result = _tool_list_directory(_agent(), _cfg())
    # Just verify it returns something without crashing
    assert isinstance(result, str)
    assert not result.startswith("ERROR:")


# ---------------------------------------------------------------------------
# run_bash
# ---------------------------------------------------------------------------


def test_run_bash_blocked_without_allow_shell():
    result = _tool_run_bash(_agent(), _cfg(), command="echo hi", allow_shell=False)
    assert "disabled" in result.lower() or "--allow-shell" in result


def test_run_bash_blocked_by_default():
    result = _tool_run_bash(_agent(), _cfg(), command="echo hi")
    assert "--allow-shell" in result


def test_run_bash_executes_with_allow_shell():
    result = _tool_run_bash(_agent(), _cfg(), command="echo hello-world", allow_shell=True)
    assert "hello-world" in result


def test_run_bash_captures_stderr_with_allow_shell():
    result = _tool_run_bash(_agent(), _cfg(), command="echo err >&2", allow_shell=True)
    assert "err" in result


def test_run_bash_missing_command_param():
    result = _tool_run_bash(_agent(), _cfg(), allow_shell=True)
    assert result.startswith("ERROR:")


# ---------------------------------------------------------------------------
# search_files
# ---------------------------------------------------------------------------


def test_search_files_finds_pattern(tmp_path):
    (tmp_path / "a.txt").write_text("hello world\nfoo bar\n")
    (tmp_path / "b.txt").write_text("nothing here\n")
    result = _tool_search_files(_agent(), _cfg(), pattern="hello", path=str(tmp_path))
    assert "hello" in result
    assert "a.txt" in result


def test_search_files_no_match(tmp_path):
    (tmp_path / "x.txt").write_text("irrelevant")
    result = _tool_search_files(_agent(), _cfg(), pattern="zzznotfound", path=str(tmp_path))
    assert "No matches" in result


def test_search_files_missing_pattern_param():
    result = _tool_search_files(_agent(), _cfg(), path=".")
    assert result.startswith("ERROR:")


def test_search_files_truncates_large_output(tmp_path, monkeypatch):
    """Output exceeding 50 lines should be truncated with a notice."""
    import subprocess

    fake_output = "\n".join(f"file.txt:{i}:match" for i in range(100))

    def fake_run(cmd, **kwargs):
        class R:
            stdout = fake_output
            stderr = ""

        return R()

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = _tool_search_files(_agent(), _cfg(), pattern="match", path=str(tmp_path))
    assert "truncated" in result


# ---------------------------------------------------------------------------
# neuriplo_detect
# ---------------------------------------------------------------------------


def _detect_cfg(tmp_path) -> InferenceConfig:
    """Config with one real (tiny) image file so encode_image succeeds."""
    from PIL import Image

    img = tmp_path / "frame.jpg"
    Image.new("RGB", (8, 8), color=(255, 0, 0)).save(img)
    return InferenceConfig(image_paths=[str(img)], detail="low", max_tokens=256, resize=False, target_size=(512, 512))


def test_neuriplo_detect_requires_endpoint_env(monkeypatch):
    monkeypatch.delenv("NEURIPLO_DETECT_URL", raising=False)
    result = _tool_neuriplo_detect(_agent(), _cfg())
    assert result.startswith("ERROR:")
    assert "NEURIPLO_DETECT_URL" in result


def test_neuriplo_detect_requires_image(monkeypatch):
    monkeypatch.setenv("NEURIPLO_DETECT_URL", "http://localhost:9000/detect")
    result = _tool_neuriplo_detect(_agent(), _cfg())
    assert result.startswith("ERROR:")
    assert "image" in result


def test_neuriplo_detect_returns_contract_detections(tmp_path, monkeypatch):
    monkeypatch.setenv("NEURIPLO_DETECT_URL", "http://localhost:9000/detect")
    contract_body = {
        "task": "object_detection",
        "model": "yolov8n",
        "image": {"width": 8, "height": 8},
        "detections": [
            {
                "class_id": 0,
                "label": "person",
                "class_confidence": 0.93,
                "bbox": {"x": 1, "y": 2, "width": 3, "height": 4},
            }
        ],
    }
    captured = {}

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return contract_body

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["payload"] = json
        return FakeResponse()

    import ghostgrid.tools.builtin as builtin

    monkeypatch.setattr(builtin.requests, "post", fake_post)
    result = _tool_neuriplo_detect(_agent(), _detect_cfg(tmp_path), labels="person, dog", confidence="0.5")
    assert result.startswith("1 detection(s) from yolov8n")
    assert '"label": "person"' in result
    assert captured["url"] == "http://localhost:9000/detect"
    assert captured["payload"]["labels"] == ["person", "dog"]
    assert captured["payload"]["confidence_threshold"] == 0.5
    assert "image" in captured["payload"]


def test_neuriplo_detect_rejects_bad_confidence(tmp_path, monkeypatch):
    monkeypatch.setenv("NEURIPLO_DETECT_URL", "http://localhost:9000/detect")
    result = _tool_neuriplo_detect(_agent(), _detect_cfg(tmp_path), confidence="high")
    assert result.startswith("ERROR:")
    assert "confidence" in result


def test_neuriplo_detect_http_error(tmp_path, monkeypatch):
    monkeypatch.setenv("NEURIPLO_DETECT_URL", "http://localhost:9000/detect")

    class FakeResponse:
        status_code = 503
        text = "model not loaded"

    import ghostgrid.tools.builtin as builtin

    monkeypatch.setattr(builtin.requests, "post", lambda *a, **k: FakeResponse())
    result = _tool_neuriplo_detect(_agent(), _detect_cfg(tmp_path))
    assert result.startswith("ERROR:")
    assert "503" in result


def test_neuriplo_detect_missing_detections_key(tmp_path, monkeypatch):
    monkeypatch.setenv("NEURIPLO_DETECT_URL", "http://localhost:9000/detect")

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {"unexpected": True}

    import ghostgrid.tools.builtin as builtin

    monkeypatch.setattr(builtin.requests, "post", lambda *a, **k: FakeResponse())
    result = _tool_neuriplo_detect(_agent(), _detect_cfg(tmp_path))
    assert result.startswith("ERROR:")
    assert "detections" in result


def test_builtin_tools_contains_neuriplo_detect():
    assert "neuriplo_detect" in BUILTIN_TOOLS
