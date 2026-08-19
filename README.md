# Pinkuha

A little CLI to download Pinterest boards and clean up the duplicates.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Install

```bash
uv sync
```

Then run any command with `uv run pinkuha ...`.

## Commands

### `download`

Download every pin from a board.

```bash
uv run pinkuha download "https://www.pinterest.com/user/board/"
```

Saves to `output/board/` by default. Use `--output` to change the root folder.

### `sync`

Like `download`, but only fetches pins added since the last run.

```bash
uv run pinkuha sync "https://www.pinterest.com/user/board/"
```

### `info`

Check how many files a board has before downloading it.

```bash
uv run pinkuha info "https://www.pinterest.com/user/board/"
```

### `metadata`

Export each pin's description, source, and tags as JSON, without downloading images.

```bash
uv run pinkuha metadata "https://www.pinterest.com/user/board/"
```

### `remove-duplicates`

Delete byte-identical duplicate images from a folder (handy since the same pin often gets re-saved across boards).

```bash
uv run pinkuha remove-duplicates output/board
```

### `stats`

Show image count and total size for a folder.

```bash
uv run pinkuha stats output/board
```

### `compress`

Shrink image files in place by re-encoding and downscaling anything larger than 2048px.

```bash
uv run pinkuha compress output/board
```

Run `uv run pinkuha <command> --help` for the full list of options on any command.

## License

[MIT](LICENSE)
