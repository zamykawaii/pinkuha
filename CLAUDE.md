# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Pinkuha (`pinkuha` on PyPI) is a Typer-based CLI to download Pinterest boards with `gallery-dl`, deduplicate the resulting images, and sort them into categories with a CLIP zero-shot model. The entire CLI lives in one file: `src/pinkuha/cli.py`. There is no test suite and no linter/formatter configured.

## Commands

```bash
uv sync                          # install/update the environment from pyproject.toml + uv.lock
uv run pinkuha --help            # list all commands
uv run pinkuha <command> --help  # see a specific command's arguments/options
uv build                         # build the sdist/wheel (used to check PyPI metadata renders correctly)
```

There is no `pinkuha` installed globally — always invoke it through `uv run` from the repo root.

## Architecture

Every command is a `@app.command()` function in `src/pinkuha/cli.py`, grouped by what they operate on:

- **Board commands** (`download`, `sync`, `info`, `metadata`) all shell out to `gallery-dl` via `subprocess` (`python -m gallery_dl`) rather than using it as a library. Two shared helpers wrap this: `run_gallery_dl()` streams output straight to the console (used for real downloads), and `run_gallery_dl_capture()` captures stdout to parse/save it (used by `info`'s file count and `metadata`'s JSON dump). `sync` is just `download` plus `--download-archive`, pointing at a per-board `.sync-archive.sqlite3` file — note that `gallery-dl` always stores this archive as SQLite regardless of the extension you give it.
- **`resolve_target(url)`** is the single place that turns a board URL into `(actual_url_to_pass_to_gallery_dl, destination_folder_name)`. It has one special case worth knowing: Pinterest's "all pins" profile URL (`/{user}/_pins/`) isn't recognized by `gallery-dl`, which only understands `/{user}/pins/` (no underscore). `resolve_target` rewrites the URL and always routes that case to a folder named `general`, regardless of which profile it came from — this is intentional, not a bug: an earlier revision scoped this folder per-username and it was deliberately reverted to the simpler flat `general` name.
- **Image maintenance commands** (`remove-duplicates`, `stats`, `compress`) and the **classification commands** (`reorder`, `flatten`) all share `list_images(directory, recursive, extensions=IMAGE_EXTENSIONS)` for listing files by extension. `compress` passes a narrower `COMPRESSIBLE_EXTENSIONS` (no `.gif`/`.bmp`) since re-encoding those would break animations or isn't useful.
- **`CATEGORY_PROMPTS`** (a dict of category name → natural-language CLIP prompt) is the single source of truth for the four fixed categories (`PIXELART`, `DRAW`, `TUTORIAL`, `CLOTHES`). `reorder`, `flatten`, and `stats` all iterate over its keys instead of hardcoding the category list anywhere else.
- **`classify_images()`** lazy-imports `torch`/`open_clip`/`PIL` inside the function body (not at module level) so that every other command stays fast and doesn't pay the cost of importing torch. It loads `ViT-B-32-quickgelu` with OpenAI weights (the "quickgelu" variant matters — the plain `ViT-B-32` tag mismatches OpenAI's activation function and logs a warning). Model download failures are caught and re-raised as `ConnectionError` with a short message, which `reorder` catches to print a clean error instead of a stack trace.
- `torch` is pinned to the CPU-only wheel through a dedicated `[tool.uv.index]`/`[tool.uv.sources]` entry in `pyproject.toml` pointing at `download.pytorch.org/whl/cpu` — adding other torch-related dependencies later should go through the same index or they may pull the much larger CUDA build.

## Conventions specific to this repo

- No comments in the code, anywhere. Docstrings are kept only because Typer surfaces them as `--help` text for each command — they are functional, not explanatory.
- Everything (code, CLI output, docs) is in English.
- Prefer extending the existing shared helpers (`list_images`, `run_gallery_dl`/`run_gallery_dl_capture`, `CATEGORY_PROMPTS`) over introducing parallel logic when adding a new command.
