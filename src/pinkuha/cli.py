import hashlib
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import typer

app = typer.Typer(add_completion=False, help="Download, deduplicate, and organize Pinterest boards.")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


def resolve_target(url: str) -> tuple[str, str]:
    path = urlparse(url).path.strip("/")
    segments = path.split("/") if path else []
    if not segments:
        raise ValueError(f"Could not determine the board name from the URL: {url}")

    if segments[-1] == "_pins":
        return url.replace("/_pins", "/pins", 1), "general"

    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", segments[-1]).strip("_") or "board"
    return url, slug


def require_pinterest_url(url: str) -> None:
    if "pinterest." not in urlparse(url).netloc:
        typer.secho(f"This doesn't look like a Pinterest URL: {url}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


def run_gallery_dl(target_url: str, dest: Path, extra_args: list[str] | None = None) -> int:
    return subprocess.run(
        [sys.executable, "-m", "gallery_dl", target_url, "-D", str(dest), *(extra_args or [])]
    ).returncode


def run_gallery_dl_capture(target_url: str, flag: str) -> str | None:
    result = subprocess.run(
        [sys.executable, "-m", "gallery_dl", target_url, "-s", flag],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.stdout if result.returncode == 0 else None


def prepare_destination(board_url: str, output: Path) -> tuple[str, str, Path]:
    require_pinterest_url(board_url)
    target_url, board_name = resolve_target(board_url)
    dest = output / board_name
    dest.mkdir(parents=True, exist_ok=True)
    return target_url, board_name, dest


OUTPUT_OPTION = typer.Option(Path("output"), "--output", "-o", help="Root folder where each board's folder is created.")


@app.command()
def download(
    board_url: str = typer.Argument(..., help="URL of the Pinterest board to download."),
    output: Path = OUTPUT_OPTION,
):
    """Download all pins from a Pinterest board into output/{board_name}."""
    target_url, board_name, dest = prepare_destination(board_url, output)

    typer.secho(f"Downloading board '{board_name}' to {dest}...", fg=typer.colors.CYAN)

    if run_gallery_dl(target_url, dest) != 0:
        typer.secho("The download finished with errors.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Board downloaded successfully to {dest}", fg=typer.colors.GREEN)


@app.command()
def sync(
    board_url: str = typer.Argument(..., help="URL of the Pinterest board to sync."),
    output: Path = OUTPUT_OPTION,
):
    """Download only the pins added since the last download or sync of a board."""
    target_url, board_name, dest = prepare_destination(board_url, output)
    archive = dest / ".sync-archive.sqlite3"

    typer.secho(f"Syncing board '{board_name}' into {dest}...", fg=typer.colors.CYAN)

    if run_gallery_dl(target_url, dest, ["--download-archive", str(archive)]) != 0:
        typer.secho("The sync finished with errors.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    typer.secho(f"Board synced successfully to {dest}", fg=typer.colors.GREEN)


@app.command()
def info(
    board_url: str = typer.Argument(..., help="URL of the Pinterest board to inspect."),
):
    """Show how many files a Pinterest board would download, without downloading them."""
    require_pinterest_url(board_url)

    target_url, board_name = resolve_target(board_url)
    stdout = run_gallery_dl_capture(target_url, "-g")

    if stdout is None:
        typer.secho("Could not fetch information for this board.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    file_count = len([line for line in stdout.splitlines() if line.strip()])
    typer.secho(f"Board '{board_name}' has {file_count} file(s) to download.", fg=typer.colors.CYAN)


@app.command()
def metadata(
    board_url: str = typer.Argument(..., help="URL of the Pinterest board to export metadata for."),
    output: Path = OUTPUT_OPTION,
):
    """Export each pin's metadata (description, source, tags) as JSON, without downloading the images."""
    target_url, board_name, dest = prepare_destination(board_url, output)
    metadata_file = dest / "metadata.json"

    typer.secho(f"Exporting metadata for board '{board_name}'...", fg=typer.colors.CYAN)
    stdout = run_gallery_dl_capture(target_url, "-j")

    if stdout is None:
        typer.secho("Could not export metadata for this board.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    metadata_file.write_text(stdout, encoding="utf-8")
    typer.secho(f"Metadata exported to {metadata_file}", fg=typer.colors.GREEN)


def list_images(directory: Path, recursive: bool, extensions: set[str] = IMAGE_EXTENSIONS) -> list[Path]:
    paths = directory.rglob("*") if recursive else directory.iterdir()
    return [path for path in paths if path.is_file() and path.suffix.lower() in extensions]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@app.command(name="remove-duplicates")
def remove_duplicates(
    directory: Path = typer.Argument(..., exists=True, file_okay=False, help="Directory to scan for duplicate images."),
):
    """Find byte-identical duplicate images under a directory and delete the extras."""
    images = list_images(directory, recursive=True)

    groups = defaultdict(list)
    for path in images:
        groups[file_hash(path)].append(path)

    duplicates = [duplicate for paths in groups.values() for duplicate in sorted(paths)[1:]]

    if not duplicates:
        typer.secho("No duplicate images found.", fg=typer.colors.GREEN)
        return

    for duplicate in duplicates:
        typer.secho(str(duplicate), fg=typer.colors.RED)
    typer.secho(f"{len(duplicates)} duplicate image(s) found.", fg=typer.colors.RED)

    if not typer.confirm("Are you sure you want to delete them?"):
        typer.echo("Aborted, no files were deleted.")
        raise typer.Exit()

    for duplicate in duplicates:
        duplicate.unlink()

    typer.secho(f"Removed {len(duplicates)} duplicate image(s).", fg=typer.colors.GREEN)


@app.command()
def stats(
    directory: Path = typer.Argument(..., exists=True, file_okay=False, help="Directory to summarize."),
):
    """Show how many images are in a directory and their total size."""
    images = list_images(directory, recursive=True)
    total_size = sum(path.stat().st_size for path in images)

    typer.secho(f"{len(images)} image(s), {total_size / (1024 * 1024):.1f} MB total", fg=typer.colors.CYAN)


COMPRESSIBLE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def compress_image(path: Path, quality: int, max_dimension: int) -> None:
    from PIL import Image

    image = Image.open(path)
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.LANCZOS)
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        image = image.convert("RGB")
    image.save(path, quality=quality, optimize=True)


@app.command()
def compress(
    directory: Path = typer.Argument(..., exists=True, file_okay=False, help="Directory whose images will be compressed in place."),
    quality: int = typer.Option(85, help="JPEG/WEBP quality to re-encode with, from 1 to 95."),
    max_dimension: int = typer.Option(2048, help="Downscale images wider or taller than this, in pixels."),
):
    """Shrink image file sizes in place by re-encoding and downscaling oversized images."""
    paths = list_images(directory, recursive=True, extensions=COMPRESSIBLE_EXTENSIONS)

    if not paths:
        typer.secho("No images found to compress.", fg=typer.colors.GREEN)
        return

    before = sum(path.stat().st_size for path in paths)
    for path in paths:
        compress_image(path, quality, max_dimension)
    after = sum(path.stat().st_size for path in paths)

    typer.secho(f"Compressed {len(paths)} image(s), saved {(before - after) / (1024 * 1024):.1f} MB.", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
