import hashlib

import pytest
import typer
from PIL import Image

from pinkuha.cli import (
    compress_image,
    file_hash,
    list_images,
    require_pinterest_url,
    resolve_target,
)


def test_resolve_target_normal():
    url = "https://www.pinterest.com/user/my-board/"
    target, slug = resolve_target(url)
    assert target == url
    assert slug == "my-board"


def test_resolve_target_sanitizes_slug():
    url = "https://www.pinterest.com/user/My Board!/"
    _, slug = resolve_target(url)
    assert slug == "My_Board"


def test_resolve_target_all_pins():
    url = "https://www.pinterest.com/user/_pins/"
    target, slug = resolve_target(url)
    assert target == "https://www.pinterest.com/user/pins/"
    assert slug == "general"


def test_resolve_target_empty_path_raises():
    with pytest.raises(ValueError):
        resolve_target("https://www.pinterest.com/")


def test_require_pinterest_url_accepts_pinterest():
    require_pinterest_url("https://www.pinterest.com/user/board/")


def test_require_pinterest_url_rejects_other_domains():
    with pytest.raises(typer.Exit):
        require_pinterest_url("https://example.com/user/board/")


def test_list_images_filters_by_extension_non_recursive(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "b.txt").write_bytes(b"x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.png").write_bytes(b"x")

    result = list_images(tmp_path, recursive=False)

    assert result == [tmp_path / "a.jpg"]


def test_list_images_recursive_includes_subdirs(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.png").write_bytes(b"x")

    result = sorted(list_images(tmp_path, recursive=True))

    assert result == sorted([tmp_path / "a.jpg", sub / "c.png"])


def test_file_hash_matches_sha256(tmp_path):
    path = tmp_path / "f.bin"
    content = b"hello world"
    path.write_bytes(content)

    assert file_hash(path) == hashlib.sha256(content).hexdigest()


def test_compress_image_downscales_oversized_image(tmp_path):
    path = tmp_path / "img.png"
    Image.new("RGB", (100, 50)).save(path)

    compress_image(path, quality=80, max_dimension=40)

    with Image.open(path) as result:
        assert max(result.size) <= 40
