"""Build standalone release bundles for the current platform."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
SPEC_PATH = ROOT / "filesearch.spec"
ICON_DIR = SRC_DIR / "filesearch" / "resources" / "icons"
MASTER_ICON = ICON_DIR / "app_icon.png"
WINDOWS_ICON = ICON_DIR / "app_icon.ico"
APP_NAME = "FileSearch"

PLATFORM_NAMES = {
    "Windows": "windows",
    "Darwin": "macos",
    "Linux": "linux",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "dist",
        help="Root directory for packaged bundles and archives.",
    )
    parser.add_argument(
        "--expected-version",
        help="Optional version string to validate against the app version.",
    )
    return parser.parse_args()


def read_version() -> str:
    """Read the package version from filesearch.__init__ without importing it."""
    init_file = SRC_DIR / "filesearch" / "__init__.py"

    for line in init_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__ = "):
            return line.split("=", 1)[1].strip().strip('"')

    raise RuntimeError(f"Could not determine version from {init_file}")


def validate_expected_version(expected_version: str | None) -> str:
    """Validate the current version against an optional expected value."""
    version = read_version()
    if expected_version and expected_version != version:
        raise RuntimeError(
            f"Version mismatch: expected {expected_version}, found {version}"
        )
    return version


def current_platform_name() -> str:
    """Return the normalized platform name used for artifact names."""
    system_name = platform.system()
    try:
        return PLATFORM_NAMES[system_name]
    except KeyError as exc:
        raise RuntimeError(f"Unsupported platform: {system_name}") from exc


def get_staging_base_dir(build_dir: Path) -> Path:
    """Return the base directory used for transient PyInstaller staging files."""
    override = os.environ.get("FILESEARCH_BUILD_STAGING_ROOT")
    if override:
        staging_dir = Path(override)
    elif current_platform_name() == "windows":
        staging_dir = Path(tempfile.gettempdir()) / "filesearch-pyinstaller"
    else:
        staging_dir = build_dir

    staging_dir.mkdir(parents=True, exist_ok=True)
    return staging_dir


def ensure_windows_icon() -> Path:
    """Regenerate the Windows ICO from the master PNG if needed."""
    if (
        WINDOWS_ICON.exists()
        and WINDOWS_ICON.stat().st_mtime >= MASTER_ICON.stat().st_mtime
    ):
        return WINDOWS_ICON

    from PIL import Image

    with Image.open(MASTER_ICON) as image:
        rgba = image.convert("RGBA")
        rgba.save(
            WINDOWS_ICON,
            format="ICO",
            sizes=[
                (16, 16),
                (24, 24),
                (32, 32),
                (48, 48),
                (64, 64),
                (128, 128),
                (256, 256),
            ],
        )

    return WINDOWS_ICON


def create_icns(icon_dir: Path) -> Path:
    """Generate a macOS ICNS file from the master PNG."""
    from PIL import Image

    iconset_dir = icon_dir / "app_icon.iconset"
    if iconset_dir.exists():
        shutil.rmtree(iconset_dir)
    iconset_dir.mkdir(parents=True)

    size_map = [
        (16, "icon_16x16.png"),
        (32, "icon_16x16@2x.png"),
        (32, "icon_32x32.png"),
        (64, "icon_32x32@2x.png"),
        (128, "icon_128x128.png"),
        (256, "icon_128x128@2x.png"),
        (256, "icon_256x256.png"),
        (512, "icon_256x256@2x.png"),
        (512, "icon_512x512.png"),
        (1024, "icon_512x512@2x.png"),
    ]

    with Image.open(MASTER_ICON) as image:
        rgba = image.convert("RGBA")
        for size, name in size_map:
            rgba.resize((size, size), Image.Resampling.LANCZOS).save(
                iconset_dir / name,
                format="PNG",
            )

    icns_path = icon_dir / "app_icon.icns"
    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
        check=True,
    )
    return icns_path


def platform_icon(build_dir: Path) -> Path | None:
    """Return the platform-specific icon for PyInstaller."""
    platform_name = current_platform_name()
    if platform_name == "windows":
        return ensure_windows_icon()
    if platform_name == "macos":
        return create_icns(build_dir / "icons")
    return MASTER_ICON


def run_pyinstaller(output_dir: Path, build_dir: Path) -> Path:
    """Run PyInstaller and return the packaged bundle path."""
    build_dir.mkdir(parents=True, exist_ok=True)
    run_root = get_staging_base_dir(build_dir) / f"run-{uuid.uuid4().hex}"
    run_root.mkdir(parents=True, exist_ok=False)
    dist_dir = run_root / "dist"
    work_dir = run_root / "work"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + env.get("PYTHONPATH", "")
    icon_path = platform_icon(run_root)
    if icon_path is not None:
        env["FILESEARCH_PYINSTALLER_ICON"] = str(icon_path)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(SPEC_PATH),
            "--noconfirm",
            "--clean",
            "--distpath",
            str(dist_dir),
            "--workpath",
            str(work_dir),
        ],
        cwd=ROOT,
        check=True,
        env=env,
    )

    if current_platform_name() == "macos":
        bundle_path = dist_dir / f"{APP_NAME}.app"
    else:
        bundle_path = dist_dir / APP_NAME

    if not bundle_path.exists():
        raise RuntimeError(f"Expected packaged bundle at {bundle_path}")

    return bundle_path


def smoke_check(bundle_path: Path) -> None:
    """Validate that the packaged bundle exists and includes the icon asset."""
    if not bundle_path.exists():
        raise RuntimeError(f"Missing packaged bundle: {bundle_path}")

    icon_matches = list(bundle_path.rglob("app_icon.png"))
    if not icon_matches:
        raise RuntimeError(f"Bundled icon asset not found inside {bundle_path}")


def archive_bundle(bundle_path: Path, archive_root: Path) -> Path:
    """Archive the packaged bundle into a GitHub-release-friendly artifact."""
    archive_root.mkdir(parents=True, exist_ok=True)
    platform_name = current_platform_name()
    archive_stem = archive_root / f"{APP_NAME}-{platform_name}"

    if platform_name in {"windows", "macos"}:
        archive_file = shutil.make_archive(
            str(archive_stem),
            "zip",
            root_dir=bundle_path.parent,
            base_dir=bundle_path.name,
        )
    else:
        archive_file = shutil.make_archive(
            str(archive_stem),
            "gztar",
            root_dir=bundle_path.parent,
            base_dir=bundle_path.name,
        )

    return Path(archive_file)


def main() -> int:
    """Build and archive a release bundle for the current platform."""
    args = parse_args()

    expected_version = args.expected_version
    if (
        expected_version is None
        and os.environ.get("GITHUB_REF_NAME", "").startswith("v")
    ):
        expected_version = os.environ["GITHUB_REF_NAME"][1:]

    version = validate_expected_version(expected_version)
    build_dir = ROOT / "build" / "release" / current_platform_name()
    bundle_path = run_pyinstaller(args.output_dir, build_dir)
    smoke_check(bundle_path)
    archive_path = archive_bundle(bundle_path, args.output_dir)

    print(f"Built FileSearch {version} for {current_platform_name()}")
    print(f"Bundle: {bundle_path}")
    print(f"Archive: {archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
