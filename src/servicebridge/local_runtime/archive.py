from __future__ import annotations

from pathlib import Path
import zipfile


def safe_extract_zip(zf: zipfile.ZipFile, destination: str | Path) -> None:
    """Extract a ZIP without allowing absolute paths or ../ traversal."""
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)

    for member in zf.infolist():
        name = member.filename.replace("\\", "/")
        if not name or name.endswith("/"):
            continue
        target = (root / name).resolve()
        try:
            target.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Unsafe ZIP member path: {member.filename}") from exc
        target.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member, "r") as src, open(target, "wb") as dst:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
