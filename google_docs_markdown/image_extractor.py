"""
Extract or inline image data in Markdown files.

Commands:
  extract: Extract base64-encoded data URI images from markdown into ./imgs/
  inline:  Inline image files referenced in markdown as data URIs at end
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import mimetypes
import pathlib
import re
import sys
from typing import Dict, Iterable, Tuple


DATA_URI_RE = re.compile(
    r"data:(?P<mime>image/[-\w.+]+);base64,(?P<b64>[A-Za-z0-9+/=\s]+)"
)

# Matches image references like [image1]: <imgs/img-24ed8.png>
IMAGE_REF_RE = re.compile(
    r"^\[(?P<label>image\d+)\]:\s*<(?P<path>[^>]+)>$", re.MULTILINE
)

HASH_LENGTH = 5


def _iter_data_uri_images(markdown_text: str) -> Iterable[Tuple[str, bytes]]:
    """
    Yield (mime_type, decoded_bytes) for each base64 image data URI found.
    """
    for m in DATA_URI_RE.finditer(markdown_text):
        mime = m.group("mime")
        b64 = re.sub(r"\s+", "", m.group("b64"))
        try:
            yield mime, base64.b64decode(b64, validate=True)
        except Exception as e:  # noqa: BLE001 - CLI tool: keep error context
            msg = f"Failed to decode base64 for mime={mime}: {e}"
            raise ValueError(msg) from e


def _ext_for_mime(mime: str) -> str:
    # Prefer common extensions; fall back to the `image/*` subtype.
    ext = mimetypes.guess_extension(mime) or ""
    if ext:
        return ext
    if "/" in mime:
        return "." + mime.split("/", 1)[1]
    return ""


def _rel_img_path(md_path: pathlib.Path, out_path: pathlib.Path) -> str:
    # Prefer a nice relative path like "imgs/img-abcde.png"
    try:
        rel = out_path.relative_to(md_path.parent)
        return rel.as_posix()
    except Exception:
        return out_path.as_posix()


def _choose_out_path(
    out_dir: pathlib.Path, *, mime: str, data: bytes, hash_length: int
) -> pathlib.Path:
    """
    Choose an output filename for the image bytes.

    If a short-hash collision occurs (same prefix, different bytes), we extend
    the hash length until it's unique, then fall back to a numeric suffix.
    """
    full_hex = hashlib.sha256(data).hexdigest()
    ext = _ext_for_mime(mime)

    # Try extending the hash prefix to avoid collisions.
    for n in range(max(1, hash_length), len(full_hex) + 1):
        h = full_hex[:n]
        candidate = out_dir / f"img-{h}{ext}"
        if not candidate.exists():
            return candidate
        if candidate.read_bytes() == data:
            return candidate

    # Extremely unlikely: full SHA-256 collision or repeated collisions due to
    # different extensions; append a numeric suffix.
    base = out_dir / f"img-{full_hex}{ext}"
    for i in range(2, 10_000):
        candidate = out_dir / f"{base.stem}-{i}{base.suffix}"
        if not candidate.exists():
            return candidate
        if candidate.read_bytes() == data:
            return candidate

    raise RuntimeError("Unable to choose a unique output filename")


def extract_images(
    md_path: pathlib.Path, *, rewrite_markdown: bool = True
) -> int:
    if not md_path.exists():
        raise FileNotFoundError(str(md_path))
    if not md_path.is_file():
        raise ValueError(f"Not a file: {md_path}")

    text = md_path.read_text(encoding="utf-8", errors="ignore")

    out_dir = md_path.parent / "imgs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Map full sha256 hex -> relative img path. This keeps replacements stable
    # within the same run and dedupes repeated data URIs.
    replacements: Dict[str, str] = {}

    def repl(m: re.Match[str]) -> str:
        mime = m.group("mime")
        b64 = re.sub(r"\s+", "", m.group("b64"))
        data = base64.b64decode(b64, validate=True)

        full_hex = hashlib.sha256(data).hexdigest()
        if full_hex in replacements:
            return replacements[full_hex]

        out_path = _choose_out_path(
            out_dir, mime=mime, data=data, hash_length=HASH_LENGTH
        )
        if not out_path.exists():
            out_path.write_bytes(data)

        rel = _rel_img_path(md_path, out_path)
        replacements[full_hex] = rel
        return rel

    # Rewrite markdown by replacing each data URI with a relative file path.
    # This effectively removes the base64 blobs from the markdown.
    new_text, num_subs = DATA_URI_RE.subn(repl, text)

    if rewrite_markdown and num_subs > 0 and new_text != text:
        md_path.write_text(new_text, encoding="utf-8")

    msg = (
        f"Found {num_subs} embedded image(s). "
        f"Exported {len(replacements)} unique image(s) to {out_dir}."
    )
    if rewrite_markdown and num_subs > 0:
        msg += " Updated markdown references in-place."
    print(msg)
    # Keep prior behavior: non-zero when no images found.
    return 0 if num_subs > 0 else 1


def inline_images(
    md_path: pathlib.Path, *, rewrite_markdown: bool = True
) -> int:
    """
    Inline image files referenced in markdown as base64 data URIs at end.

    Looks for lines like:
      [image1]: <imgs/img-24ed8.png>

    Reads the image files, converts them to base64 data URIs, and replaces
    the file references with data URI references at the end of the file.
    """
    if not md_path.exists():
        raise FileNotFoundError(str(md_path))
    if not md_path.is_file():
        raise ValueError(f"Not a file: {md_path}")

    text = md_path.read_text(encoding="utf-8", errors="ignore")
    md_dir = md_path.parent

    # Find all image references
    # (label, original_line, file_path)
    image_refs: list[tuple[str, str, pathlib.Path]] = []

    for m in IMAGE_REF_RE.finditer(text):
        label = m.group("label")
        img_path_str = m.group("path")
        original_line = m.group(0)

        # Resolve the image path relative to the markdown file's directory
        img_path = md_dir / img_path_str
        if not img_path.exists():
            msg = f"Warning: Image file not found: {img_path}"
            print(msg, file=sys.stderr)
            continue

        image_refs.append((label, original_line, img_path))

    if not image_refs:
        print("No image references found to inline.")
        return 1

    # Sort by label to maintain consistent order (image1, image2, etc.)
    image_refs.sort(key=lambda x: x[0])

    # Read images and convert to data URIs
    # label -> data URI reference line
    data_uri_refs: Dict[str, str] = {}

    for label, original_line, img_path in image_refs:
        try:
            img_data = img_path.read_bytes()

            # Determine MIME type from file extension
            mime_type, _ = mimetypes.guess_type(str(img_path))
            if not mime_type or not mime_type.startswith("image/"):
                # Fallback: try to infer from extension
                ext = img_path.suffix.lower()
                mime_map = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                    ".svg": "image/svg+xml",
                }
                mime_type = mime_map.get(ext, "image/png")

            # Encode as base64 data URI
            b64_data = base64.b64encode(img_data).decode("ascii")
            data_uri_ref = (
                f"[{label}]: <data:{mime_type};base64,{b64_data}>"
            )
            data_uri_refs[label] = data_uri_ref

        except Exception as e:  # noqa: BLE001
            msg = f"Warning: Failed to process {img_path}: {e}"
            print(msg, file=sys.stderr)
            continue

    if not data_uri_refs:
        print("No images were successfully converted.")
        return 1

    # Remove all old image reference lines
    new_text = text
    for _, original_line, _ in image_refs:
        # Remove the line, including any trailing newline
        new_text = re.sub(re.escape(original_line) + r"\n?", "", new_text)

    # Append all data URI references at the end
    if new_text and not new_text.endswith("\n"):
        new_text += "\n"

    # Append data URI references in sorted order (image1, image2, etc.)
    def label_sort_key(label: str) -> int:
        match = re.search(r"\d+", label)
        return int(match.group()) if match else 0

    for label in sorted(data_uri_refs.keys(), key=label_sort_key):
        new_text += data_uri_refs[label] + "\n"

    if rewrite_markdown and new_text != text:
        md_path.write_text(new_text, encoding="utf-8")

    msg = f"Inlined {len(data_uri_refs)} image(s) as data URIs."
    if rewrite_markdown:
        msg += " Updated markdown file in-place."
    print(msg)
    return 0


def main() -> int:
    """CLI entry point for image extraction/inlining."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract or inline image data in Markdown files. "
            "Use 'extract' to extract data URIs to files, "
            "or 'inline' to convert file references to data URIs."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Extract command
    extract_parser = subparsers.add_parser(
        "extract",
        help=(
            "Extract base64-encoded image data URIs from markdown "
            "into ./imgs/"
        ),
    )
    extract_parser.add_argument(
        "markdown_path",
        type=pathlib.Path,
        help="Path to the markdown file containing embedded data URI images",
    )
    extract_parser.add_argument(
        "--no-rewrite",
        action="store_true",
        help=(
            "Do not rewrite the markdown file; "
            "only export images to ./imgs/"
        ),
    )

    # Inline command
    inline_parser = subparsers.add_parser(
        "inline",
        help=(
            "Inline image files referenced in markdown "
            "as data URIs at end of file"
        ),
    )
    inline_parser.add_argument(
        "markdown_path",
        type=pathlib.Path,
        help="Path to the markdown file containing image file references",
    )
    inline_parser.add_argument(
        "--no-rewrite",
        action="store_true",
        help=(
            "Do not rewrite the markdown file; "
            "only show what would be done"
        ),
    )

    args = parser.parse_args()

    try:
        if args.command == "extract":
            return extract_images(
                args.markdown_path, rewrite_markdown=not args.no_rewrite
            )
        elif args.command == "inline":
            return inline_images(
                args.markdown_path, rewrite_markdown=not args.no_rewrite
            )
        else:
            parser.error(f"Unknown command: {args.command}")
            return 2
    except Exception as e:  # noqa: BLE001
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

