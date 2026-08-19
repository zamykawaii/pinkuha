# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `pyright` as a dev dependency, configured in strict mode (`[tool.pyright]` in `pyproject.toml`).

## [0.1.0] - 2026-08-19

### Added

- Initial `pinkuha` CLI with Typer.
- `download`: download all pins from a Pinterest board.
- `sync`: download only the pins added since the last download or sync, using a per-board archive file.
- `info`: show how many files a board would download, without downloading them.
- `metadata`: export each pin's metadata (description, source, tags) as JSON.
- `remove-duplicates`: find and delete byte-identical duplicate images in a directory.
- `stats`: show image count and total size for a directory.
- `compress`: shrink image file sizes in place by re-encoding and downscaling oversized images.

[Unreleased]: https://github.com/zamykawaii/pinkuha/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/zamykawaii/pinkuha/releases/tag/v0.1.0
