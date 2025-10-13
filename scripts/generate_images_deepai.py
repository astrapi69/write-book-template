# scripts/generate_images_deepai.py
from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Union, Sequence

import requests
from dotenv import load_dotenv

DEEPAI_ENDPOINT = "https://api.deepai.org/api/text2img"

# Configure root logger; tests can override with caplog
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Config:
    prompt_file: Path
    output_dir: Path
    api_key: str
    character_profile_path: Path
    endpoint: str = DEEPAI_ENDPOINT
    timeout: int = 30
    overwrite: bool = False  # keeps current behavior (skip if exists)


def load_json(path: Path) -> Dict[str, Any]:
    """Safe JSON loader with informative errors."""
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("File not found: %s", path)
        return {}
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in %s: %s", path, e)
        return {}


def load_character_profiles(
    path: Union[str, Path] = "scripts/data/character_profiles.json",
) -> Dict[str, str]:
    """Load character profiles; return {} on failure (backward-compatible)."""
    path = Path(path)
    data = load_json(path)
    # Ensure keys -> str, values -> str for robustness
    return {str(k): str(v) for k, v in data.items()} if data else {}


def _character_desc_from_key(
    character_key: Optional[Union[str, Iterable[str]]],
    profiles: Dict[str, str],
) -> str:
    if not character_key:
        return ""
    if isinstance(character_key, (list, tuple, set)):
        parts = [profiles.get(str(name), "") for name in character_key]
        return ", ".join([p for p in parts if p])  # drop empties
    return profiles.get(str(character_key), "")


def build_prompt(
    base_prompt: str,
    character_key: Optional[Union[str, Iterable[str]]],
    profiles: Dict[str, str],
    global_style: Optional[str],
) -> str:
    """Combine character description, base prompt, and optional global style."""
    base_prompt = (base_prompt or "").strip()
    desc = _character_desc_from_key(character_key, profiles).strip()
    combined = f"{desc}, {base_prompt}" if desc else base_prompt
    combined = combined.strip(" ,")
    if global_style:
        combined = f"{combined}, {global_style}".strip(" ,")
    return combined


def generate_image(
    *,
    session: requests.Session,
    prompt: str,
    filename: str,
    output_dir: Path,
    api_key: str,
    endpoint: str = DEEPAI_ENDPOINT,
    timeout: int = 30,
    overwrite: bool = False,
) -> bool:
    """
    Generate a single image. Returns True on success, False otherwise.
    - Skips if file exists (unless overwrite=True).
    """
    output_path = output_dir / filename
    if output_path.exists() and not overwrite:
        logger.info("Skipped (exists): %s", filename)
        return True

    logger.info("Generating: %s", filename)
    try:
        resp = session.post(
            endpoint,
            data={"text": prompt},
            headers={"api-key": api_key},
            timeout=timeout,
        )
    except requests.RequestException as e:
        logger.error("DeepAI request failed for %s: %s", filename, e)
        return False

    if resp.status_code != 200:
        logger.error(
            "DeepAI error %s for %s: %s", resp.status_code, filename, resp.text
        )
        return False

    try:
        image_url = resp.json().get("output_url")
        if not image_url:
            logger.error(
                "DeepAI response missing output_url for %s: %s", filename, resp.text
            )
            return False

        img = session.get(image_url, timeout=timeout)
        img.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(img.content)
        logger.info("Saved: %s", output_path)
        return True
    except (ValueError, requests.RequestException, OSError) as e:
        logger.error("Failed to save image for %s: %s", filename, e)
        return False


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate images from prompts using DeepAI text2img"
    )
    parser.add_argument(
        "--prompt-file",
        default="scripts/data/image_prompts.json",
        help="Path to the prompt JSON file (default: scripts/data/image_prompts.json)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("assets/illustrations"),
        help="Directory to save generated images (default: assets/illustrations)",
    )
    parser.add_argument(
        "--api-key",
        required=False,
        help="DeepAI API key (optional, overrides .env)",
    )
    parser.add_argument(
        "--character-profile",
        default="scripts/data/character_profiles.json",
        help="Path to character profile JSON file",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files instead of skipping",
    )
    return parser.parse_args(argv)


def make_config(args: argparse.Namespace) -> Optional[Config]:
    # Load env only here so imports are fast in tests / scripts
    load_dotenv()

    api_key = args.api_key or os.getenv("DEEPAI_API_KEY")
    if not api_key:
        logger.error(
            "No API key provided. Set --api-key or define DEEPAI_API_KEY in .env"
        )
        return None

    prompt_file = Path(args.prompt_file)
    if not prompt_file.exists():
        logger.error("Prompt file does not exist: %s", prompt_file)
        return None

    return Config(
        prompt_file=prompt_file,
        output_dir=Path(args.output_dir),
        api_key=api_key,
        character_profile_path=Path(args.character_profile),
        overwrite=bool(args.overwrite),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(list(argv) if argv is not None else None)
    cfg = make_config(args)
    if not cfg:
        return 2  # configuration issue

    data = load_json(cfg.prompt_file)
    global_style = data.get("style")
    character_profiles = load_character_profiles(cfg.character_profile_path)
    chapters = data.get("chapters", [])

    session = requests.Session()

    any_failed = False
    for chapter in chapters:
        for item in chapter.get("prompts", []):
            base_prompt = item.get("prompt", "") or ""
            character_key = item.get("character")
            final_prompt = build_prompt(
                base_prompt, character_key, character_profiles, global_style
            )
            filename = item.get("filename", "output.png")
            ok = generate_image(
                session=session,
                prompt=final_prompt,
                filename=filename,
                output_dir=cfg.output_dir,
                api_key=cfg.api_key,
                endpoint=cfg.endpoint,
                timeout=cfg.timeout,
                overwrite=cfg.overwrite,
            )
            any_failed = any_failed or (not ok)

    return 1 if any_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
