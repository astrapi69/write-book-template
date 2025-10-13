# tests/test_generate_images_deepai.py
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any, List
import requests

import scripts.generate_images_deepai as mod


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text="", content=b"IMG"):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self.content = content

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(self.text)


class FakeSession:
    def __init__(self, post_resp: FakeResponse, get_resp: FakeResponse):
        self._post_resp = post_resp
        self._get_resp = get_resp
        self.post_calls: List[Any] = []
        self.get_calls: List[Any] = []

    def post(self, url, data=None, headers=None, timeout=None):
        self.post_calls.append(
            {"url": url, "data": data, "headers": headers, "timeout": timeout}
        )
        return self._post_resp

    def get(self, url, timeout=None):
        self.get_calls.append({"url": url, "timeout": timeout})
        return self._get_resp


def test_load_character_profiles_missing_returns_empty(tmp_path, caplog):
    path = tmp_path / "missing.json"
    profiles = mod.load_character_profiles(path)
    assert profiles == {}


def test_build_prompt_single_character_and_style():
    profiles = {"Timmy": "Timmy, a brave boy"}
    final = mod.build_prompt("finds a key", "Timmy", profiles, "moody lighting")
    assert final == "Timmy, a brave boy, finds a key, moody lighting"


def test_build_prompt_multiple_characters_and_missing():
    profiles = {"Timmy": "Timmy brave", "Boronius": "Boronius wise"}
    final = mod.build_prompt(
        "in a cave", ["Timmy", "Unknown", "Boronius"], profiles, None
    )
    # Unknown is omitted; order preserved
    assert final == "Timmy brave, Boronius wise, in a cave"


def test_generate_image_skips_if_exists(tmp_path, caplog):
    caplog.set_level("INFO")
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "a.png").write_bytes(b"OLD")
    session = FakeSession(FakeResponse(), FakeResponse())
    ok = mod.generate_image(
        session=session,
        prompt="p",
        filename="a.png",
        output_dir=out_dir,
        api_key="k",
    )
    assert ok is True
    assert "Skipped (exists)" in caplog.text


def test_generate_image_handles_api_error(tmp_path, caplog):
    caplog.set_level("ERROR")
    out_dir = tmp_path / "out"
    session = FakeSession(FakeResponse(status_code=500, text="boom"), FakeResponse())
    ok = mod.generate_image(
        session=session,
        prompt="p",
        filename="b.png",
        output_dir=out_dir,
        api_key="k",
    )
    assert ok is False
    assert "DeepAI error 500" in caplog.text


def test_generate_image_success_writes_file(tmp_path):
    out_dir = tmp_path / "out"
    post_resp = FakeResponse(json_data={"output_url": "http://x/y.png"})
    get_resp = FakeResponse(status_code=200, content=b"PNGDATA")
    session = FakeSession(post_resp, get_resp)

    ok = mod.generate_image(
        session=session,
        prompt="p",
        filename="c.png",
        output_dir=out_dir,
        api_key="k",
    )
    assert ok is True
    assert (out_dir / "c.png").read_bytes() == b"PNGDATA"
    # Ensure our fake was exercised
    assert session.post_calls and session.get_calls


def test_generate_image_missing_output_url(tmp_path, caplog):
    caplog.set_level("ERROR")
    out_dir = tmp_path / "out"
    session = FakeSession(FakeResponse(json_data={}), FakeResponse())
    ok = mod.generate_image(
        session=session,
        prompt="p",
        filename="d.png",
        output_dir=out_dir,
        api_key="k",
    )
    assert ok is False
    assert "missing output_url" in caplog.text


def test_make_config_requires_api_key(monkeypatch, tmp_path, caplog):
    caplog.set_level("ERROR")

    # ensure no env var
    monkeypatch.delenv("DEEPAI_API_KEY", raising=False)
    # block getenv to avoid leaking a real key from environment
    monkeypatch.setattr(mod.os, "getenv", lambda *a, **k: None)

    args = SimpleNamespace(
        prompt_file=str(tmp_path / "prompts.json"),
        output_dir=str(tmp_path / "out"),
        api_key=None,
        character_profile=str(tmp_path / "chars.json"),
        overwrite=False,
    )

    cfg = mod.make_config(args)
    assert cfg is None
    assert "No API key provided" in caplog.text


def test_main_happy_path(monkeypatch, tmp_path):
    # Arrange prompt file
    prompts = {
        "style": "cinematic",
        "chapters": [
            {
                "prompts": [
                    {
                        "prompt": "scene one",
                        "character": "Timmy",
                        "filename": "img1.png",
                    },
                    {
                        "prompt": "scene two",
                        "character": ["Timmy", "Boronius"],
                        "filename": "img2.png",
                    },
                ]
            }
        ],
    }
    prompt_file = tmp_path / "prompts.json"
    prompt_file.write_text(json.dumps(prompts), encoding="utf-8")

    # character profiles
    chars = {"Timmy": "Timmy brave", "Boronius": "Boronius wise"}
    char_file = tmp_path / "characters.json"
    char_file.write_text(json.dumps(chars), encoding="utf-8")

    # Fake generate_image to avoid network/files
    called = []

    def fake_generate_image(**kwargs):
        called.append(kwargs)
        # simulate success
        return True

    monkeypatch.setattr(mod, "generate_image", fake_generate_image)
    monkeypatch.setenv("DEEPAI_API_KEY", "abc123")

    rc = mod.main(
        [
            "--prompt-file",
            str(prompt_file),
            "--output-dir",
            str(tmp_path / "out"),
            "--character-profile",
            str(char_file),
        ]
    )

    assert rc == 0
    assert len(called) == 2
    # Assert prompt composition happened
    prompts_sent = [k["prompt"] for k in called]
    assert "Timmy brave, scene one, cinematic" in prompts_sent[0]
    assert "Timmy brave, Boronius wise, scene two, cinematic" in prompts_sent[1]


def test_overwrite_true_will_not_skip(tmp_path, monkeypatch):
    # existing file
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "x.png").write_bytes(b"OLD")

    post_resp = FakeResponse(json_data={"output_url": "http://x/y.png"})
    get_resp = FakeResponse(status_code=200, content=b"NEW")
    session = FakeSession(post_resp, get_resp)

    ok = mod.generate_image(
        session=session,
        prompt="p",
        filename="x.png",
        output_dir=out_dir,
        api_key="k",
        overwrite=True,
    )
    assert ok is True
    assert (out_dir / "x.png").read_bytes() == b"NEW"


def test_download_raises_http_error(tmp_path, caplog):
    caplog.set_level("ERROR")
    post_resp = FakeResponse(json_data={"output_url": "http://x/y.png"})
    bad_get = FakeResponse(status_code=404, text="not found")
    session = FakeSession(post_resp, bad_get)

    ok = mod.generate_image(
        session=session,
        prompt="p",
        filename="e.png",
        output_dir=tmp_path / "out",
        api_key="k",
    )
    assert ok is False
    assert "Failed to save image" in caplog.text


def test_invalid_json_logged(tmp_path, caplog):
    caplog.set_level("ERROR")
    bad = tmp_path / "bad.json"
    bad.write_text("{ invalid json", encoding="utf-8")
    data = mod.load_json(bad)
    assert data == {}
    assert "Invalid JSON" in caplog.text


def test_make_config_missing_prompt_file(tmp_path, monkeypatch, caplog):
    caplog.set_level("ERROR")
    monkeypatch.setenv("DEEPAI_API_KEY", "abc")
    args = type(
        "A",
        (),
        {
            "prompt_file": str(tmp_path / "nope.json"),
            "output_dir": tmp_path / "out",
            "api_key": None,
            "character_profile": str(tmp_path / "chars.json"),
            "overwrite": False,
        },
    )()
    cfg = mod.make_config(args)
    assert cfg is None
    assert "Prompt file does not exist" in caplog.text


def test_api_key_flag_overrides_env(tmp_path, monkeypatch):
    # prepare prompt file
    pf = tmp_path / "p.json"
    pf.write_text('{"chapters":[]}', encoding="utf-8")
    monkeypatch.setenv("DEEPAI_API_KEY", "ENVKEY")
    args = ["--prompt-file", str(pf), "--api-key", "FLAGKEY"]
    cfg = mod.make_config(mod.parse_args(args))
    assert cfg is not None
    assert cfg.api_key == "FLAGKEY"


def test_prompt_building_edge_cases():
    profiles = {"T": "Tall hero"}
    # empty base prompt + style only
    p = mod.build_prompt("", "T", profiles, "noir")
    assert p == "Tall hero, noir"
    # None character, just base + style
    p2 = mod.build_prompt("walks", None, profiles, "noir")
    assert p2 == "walks, noir"
    # tuple character key
    p3 = mod.build_prompt("enters", ("T",), profiles, None)
    assert p3 == "Tall hero, enters"


def test_main_returns_failure_if_any_generation_fails(tmp_path, monkeypatch):
    # prompt file
    pf = tmp_path / "p.json"
    pf.write_text(
        json.dumps(
            {
                "chapters": [
                    {
                        "prompts": [
                            {"prompt": "a", "filename": "a.png"},
                            {"prompt": "b", "filename": "b.png"},
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    # chars
    cf = tmp_path / "c.json"
    cf.write_text("{}", encoding="utf-8")
    # fake generator: first ok, second fails
    calls = []

    def fake_gen(**kw):
        calls.append(kw)
        return len(calls) == 1

    monkeypatch.setattr(mod, "generate_image", fake_gen)
    monkeypatch.setenv("DEEPAI_API_KEY", "K")

    rc = mod.main(
        [
            "--prompt-file",
            str(pf),
            "--character-profile",
            str(cf),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    )
    assert rc == 1
