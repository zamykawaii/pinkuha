# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Pinkuha (`pinkuha` on PyPI) is a Typer-based CLI to download Pinterest boards with `gallery-dl` and deduplicate the resulting images. The entire CLI lives in one file: `src/pinkuha/cli.py`. There is no test suite and no linter/formatter configured.

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
- **Image maintenance commands** (`remove-duplicates`, `stats`, `compress`) all share `list_images(directory, recursive, extensions=IMAGE_EXTENSIONS)` for listing files by extension. `compress` passes a narrower `COMPRESSIBLE_EXTENSIONS` (no `.gif`/`.bmp`) since re-encoding those would break animations or isn't useful.
- There used to be CLIP-based classification commands (`reorder`/`flatten`) that sorted images into categories; they were removed to keep the library lightweight (no `torch`/`open-clip-torch` dependency). `pillow` remains a direct dependency for `compress`.

## Conventions specific to this repo

- No comments in the code, anywhere. Docstrings are kept only because Typer surfaces them as `--help` text for each command — they are functional, not explanatory.
- Everything (code, CLI output, docs) is in English.
- Prefer extending the existing shared helpers (`list_images`, `run_gallery_dl`/`run_gallery_dl_capture`, `CATEGORY_PROMPTS`) over introducing parallel logic when adding a new command.
