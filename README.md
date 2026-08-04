# Pinkuha

A little CLI to download Pinterest boards, clean up the duplicates, and sort the images into categories.

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

### `reorder`

Sort images into `PIXELART`, `DRAW`, `TUTORIAL`, or `CLOTHES` subfolders using a CLIP model — no training needed. The first run downloads the model (a few hundred MB).

```bash
uv run pinkuha reorder output/board
```

### `flatten`

Undo `reorder`, moving everything back out of the category subfolders.

```bash
uv run pinkuha flatten output/board
```

### `stats`

Show image count and total size for a folder, broken down by category.

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
