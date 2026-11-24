from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from vxlib.packaging import (  # noqa: E402
    ImageBuildOptions,
    PackageRequest,
    default_mkisofs_path,
    default_windows_base_path,
    package_directory,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package a directory as a .vxapp.")
    parser.add_argument("target", help="Directory to package.")
    parser.add_argument("legacy_config", nargs="?", help="Optional legacy vxapp.config path.")
    parser.add_argument("--config", help="Path to a vxapp.config file.")
    parser.add_argument("--output-root", help="Directory that will receive the .vxapp staging folder.")
    parser.add_argument("--mkisofs", default=str(default_mkisofs_path()), help="Path to mkisofs.")
    parser.add_argument("--windows-base", default=str(default_windows_base_path()), help="Path to windows_base.zip.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve paths without writing package output.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    source_path = Path(args.target).resolve()
    config_path = Path(args.config or args.legacy_config).resolve() if args.config or args.legacy_config else None
    staging_root = Path(args.output_root).resolve() if args.output_root else source_path.parent / "__staging"

    request = PackageRequest(
        source_path=source_path,
        staging_root=staging_root,
        config_path=config_path,
        windows_base_path=Path(args.windows_base).resolve(),
        image_options=ImageBuildOptions(
            mkisofs_path=Path(args.mkisofs).resolve(),
            dry_run=args.dry_run,
        ),
    )
    package_path = package_directory(request)
    print(f"Prepared: {package_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
