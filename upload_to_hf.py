#!/usr/bin/env python3
"""
Upload the current project folder directly to a Hugging Face Space using the Python Hub API.
"""

import json
import os
from getpass import getpass
from pathlib import Path
from huggingface_hub import HfApi

SPACE_REPO_ID = "niahr/Opspilot"
SPACE_REPO_TYPE = "space"
EXCLUDE_DIRS = {
    ".git",
    "OOpspilot_hf",
    "Opspilot_hf",
    "env",
    "node_modules",
    ".venv",
    "venv",
}

EXCLUDE_PATTERNS = [
    "*.pyc",
    "__pycache__/**",
    ".DS_Store",
    "*.log",
    "*.sqlite3",
    "*.db",
    "*.env",
    "*.tmp",
    "*.cache",
    "push_to_hf.py",
    "upload_to_hf.py",
]


def get_token():
    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    if token:
        return token.strip()

    home = Path.home()
    token_paths = [
        home / ".huggingface" / "token",
        home / ".huggingface" / "token.txt",
        home / ".huggingface" / "config.json",
    ]
    for token_path in token_paths:
        if token_path.exists():
            try:
                content = token_path.read_text(encoding="utf-8").strip()
                if not content:
                    continue
                if token_path.name == "config.json":
                    data = json.loads(content)
                    for key in ["token", "hf_token", "access_token"]:
                        if key in data and data[key]:
                            return str(data[key]).strip()
                else:
                    return content.splitlines()[0].strip()
            except Exception:
                continue

    return None


def build_ignore_patterns(root: Path):
    patterns = []
    for exclude_dir in EXCLUDE_DIRS:
        patterns.append(f"{exclude_dir}")
        patterns.append(f"{exclude_dir}/**")
    patterns.extend(EXCLUDE_PATTERNS)
    return patterns


def main():
    token = get_token()
    if not token:
        print("No Hugging Face token found in environment or local config.")
        token = getpass("Enter your Hugging Face token: ").strip()
        if not token:
            print("ERROR: Hugging Face token is required to upload.")
            return 1

    root = Path(__file__).resolve().parent
    api = HfApi(token=token)

    print(f"Uploading project files from {root} to Hugging Face space {SPACE_REPO_ID}...")

    # Check if space exists, if not create it
    try:
        api.repo_info(repo_id=SPACE_REPO_ID, repo_type=SPACE_REPO_TYPE)
        print(f"Space {SPACE_REPO_ID} exists.")
    except Exception:
        print(f"Space {SPACE_REPO_ID} does not exist. Creating it...")
        try:
            api.create_repo(
                repo_id=SPACE_REPO_ID,
                repo_type=SPACE_REPO_TYPE,
                space_sdk="docker",
                private=False,
            )
            print(f"Space {SPACE_REPO_ID} created successfully.")
        except Exception as exc:
            print(f"Failed to create space: {exc}")
            return 1

    ignore_patterns = build_ignore_patterns(root)
    try:
        commit_info = api.upload_large_folder(
            repo_id=SPACE_REPO_ID,
            folder_path=str(root),
            path_in_repo="",
            commit_message="Upload project files to Hugging Face Space",
            repo_type=SPACE_REPO_TYPE,
            ignore_patterns=ignore_patterns,
            create_pr=True,
        )
        print("Upload completed successfully.")
        if hasattr(commit_info, 'commit_id'):
            print(f"Commit URL: https://huggingface.co/{SPACE_REPO_ID}/commit/{commit_info.commit_id}")
        return 0
    except Exception as exc:
        print("Upload failed:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
