"""
verify_data_structure.py

Scan ./data for dataset folders and report valid vs suspicious/redundant files.

Safe by default: only prints a report. Use --clean to enable deletions (requires confirmation).

Compatible with Python 3.10+. Uses pathlib/os for file handling and pandas when available
for lightweight readability checks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except Exception:
    PANDAS_AVAILABLE = False

# Allowed "valid" extensions for structured data
VALID_EXTS = {
    ".csv",
    ".json",
    ".jsonl",
    ".ndjson",
    ".txt",
    ".parquet",
    ".feather",
    ".avro",
    ".xlsx",
}

# Suspicious / redundant extensions or file name patterns
SUSPICIOUS_EXTS = {
    ".zip",
    ".tar",
    ".tgz",
    ".gz",
    ".tar.gz",
    ".7z",
    ".rar",
    ".log",
    ".tmp",
    ".bak",
    ".DS_Store",
    ".db",
    ".sqlite",
    ".ckpt",
    ".pt",
    ".pth",
    ".model",
    ".h5",
}

# Filenames to ignore entirely for reporting as data (but we'll still detect them)
IGNORED_NAMES = {"README.md", "readme.md", "LICENSE", "license", "thumbs.db"}

# Default ignore rules for VCS and temporary files/folders
IGNORE_DIRS = {".git", "__pycache__"}
IGNORE_FILE_NAMES = {".gitignore", ".gitattributes", ".ds_store", "thumbs.db"}
IGNORE_SUFFIXES = {".part"}
IGNORE_ARCHIVE_SUFFIXES = {".zip", ".tar", ".tgz", ".gz", ".tar.gz", ".7z", ".rar"}

# Read a file in chunks for hashing
def file_md5(path: Path, chunk_size: int = 8192) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def human_readable_size(num_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} PB"


def is_structured_ext(path: Path) -> bool:
    s = path.suffix.lower()
    if s in VALID_EXTS:
        return True
    # handle .tar.gz / .tar.bz2 style
    name = path.name.lower()
    if name.endswith(".tar.gz") or name.endswith(".tar.bz2"):
        return False
    return False


def quick_readable_check(path: Path) -> Tuple[bool, str]:
    """Try to read a small sample of the file using pandas if possible.
    Returns (readable_bool, error_message_or_empty).
    This is a lightweight check (reads minimal rows) to detect obvious corruption.
    If pandas is not available, we do a basic size check and simple read for text files.
    """
    try:
        ext = path.suffix.lower()
        if ext == ".csv" and PANDAS_AVAILABLE:
            _ = pd.read_csv(path, nrows=5)
            return True, ""
        if ext in {".json", ".jsonl", ".ndjson"}:
            if PANDAS_AVAILABLE:
                # pandas can read many JSON variants
                try:
                    _ = pd.read_json(path, lines=True, nrows=5)
                    return True, ""
                except Exception:
                    # fallback to reading raw json
                    import json as _json

                    with path.open("r", encoding="utf-8", errors="ignore") as fh:
                        _ = fh.read(8192)
                    return True, ""
            else:
                # basic sanity: try to load a small prefix
                with path.open("r", encoding="utf-8", errors="ignore") as fh:
                    _ = fh.read(8192)
                return True, ""
        if ext in {".parquet", ".feather"} and PANDAS_AVAILABLE:
            try:
                _ = pd.read_parquet(path, columns=None)
                return True, ""
            except Exception as e:
                return False, str(e)
        if ext == ".txt" or ext == ".md" or path.name.lower().endswith("readme"):
            # confirm readable text
            with path.open("r", encoding="utf-8", errors="ignore") as fh:
                _ = fh.read(1024)
            return True, ""
        # For other extensions, just check size > 0
        if path.stat().st_size > 0:
            return True, ""
        return False, "empty file"
    except Exception as exc:
        return False, str(exc)


def analyze_dataset(dataset_path: Path) -> Dict[str, object]:
    """Analyze a single dataset folder.
    Returns a dictionary with lists of valid_files, suspicious_files, duplicates, empty_files, unreadable_files, suggested_cleanup_size
    """
    # Collect files but exclude VCS, temp and archive files by default
    def is_ignored_path(p: Path) -> bool:
        # any parent directory is in the ignore list
        parts = [part.lower() for part in p.parts]
        if any(d in parts for d in IGNORE_DIRS):
            return True
        lname = p.name.lower()
        if lname in IGNORE_FILE_NAMES:
            return True
        # suffix match (single suffixes like .part)
        if any(lname.endswith(suf) for suf in IGNORE_SUFFIXES):
            return True
        # archive-like suffixes (handle .tar.gz by name check)
        if any(lname.endswith(suf) for suf in IGNORE_ARCHIVE_SUFFIXES):
            return True
        return False

    files = [p for p in dataset_path.rglob("*") if p.is_file() and not is_ignored_path(p)]

    valid_files: List[Path] = []
    suspicious_files: List[Path] = []
    empty_files: List[Path] = []
    unreadable_files: List[Tuple[Path, str]] = []

    md5_map: Dict[str, List[Path]] = defaultdict(list)

    for f in files:
        lname = f.name
        if lname in IGNORED_NAMES:
            suspicious_files.append(f)
            continue

        size = f.stat().st_size
        if size == 0:
            empty_files.append(f)
            md5_map["EMPTY_" + str(size)].append(f)
            continue

        # Hash for duplicate detection
        try:
            h = file_md5(f)
            md5_map[h].append(f)
        except Exception:
            # hashing failed for some reason, continue without hash
            h = ""

        lower_name = f.name.lower()
        # Suspicious by extension
        if any(lower_name.endswith(s) for s in SUSPICIOUS_EXTS):
            suspicious_files.append(f)
            continue

        # Consider valid if extension matches
        if is_structured_ext(f):
            readable, err = quick_readable_check(f)
            if readable:
                valid_files.append(f)
            else:
                unreadable_files.append((f, err))
            continue

        # If file sits under raw/ or processed/ and has a common data ext, accept
        # Path.parts yields strings for each path component; lower-case them directly
        parent_names = {part.lower() for part in f.parts}
        if "raw" in parent_names or "processed" in parent_names:
            # accept common structured data extensions even if not in our list
            ext = f.suffix.lower()
            if ext in VALID_EXTS:
                readable, err = quick_readable_check(f)
                if readable:
                    valid_files.append(f)
                    continue
                else:
                    unreadable_files.append((f, err))
                    continue

        # Default: mark as suspicious (unknown binary / extra file)
        suspicious_files.append(f)

    # Duplicate detection
    duplicates: List[List[Path]] = [v for v in md5_map.values() if len(v) > 1]

    # Aggregate sizes for suggested cleanup: suspicious + empty + duplicates (excluding one copy each)
    suggested_paths = set()
    total_cleanup = 0

    # suspicious and empty
    for p in suspicious_files + empty_files:
        suggested_paths.add(p)
        try:
            total_cleanup += p.stat().st_size
        except Exception:
            pass

    # duplicates: keep one per hash, mark the rest
    for group in duplicates:
        # skip if group is only empty markers
        real_files = [p for p in group if p.exists() and p.stat().st_size > 0]
        if len(real_files) <= 1:
            continue
        # sort by path and keep first
        real_files_sorted = sorted(real_files)
        for dup in real_files_sorted[1:]:
            suggested_paths.add(dup)
            try:
                total_cleanup += dup.stat().st_size
            except Exception:
                pass

    result = {
        "dataset": dataset_path.name,
        "valid_files": sorted(valid_files),
        "suspicious_files": sorted(suspicious_files),
        "empty_files": sorted(empty_files),
        "unreadable_files": sorted(unreadable_files, key=lambda x: str(x[0])),
        "duplicates": duplicates,
        "suggested_cleanup_paths": sorted(suggested_paths),
        "suggested_cleanup_size": total_cleanup,
    }
    return result


def print_report(dataset_report: Dict[str, object]) -> None:
    ds = dataset_report["dataset"]
    valid: List[Path] = dataset_report["valid_files"]
    suspicious: List[Path] = dataset_report["suspicious_files"]
    empty: List[Path] = dataset_report["empty_files"]
    unreadable: List[Tuple[Path, str]] = dataset_report["unreadable_files"]
    duplicates: List[List[Path]] = dataset_report["duplicates"]
    suggested_paths: List[Path] = dataset_report["suggested_cleanup_paths"]
    cleanup_size: int = dataset_report["suggested_cleanup_size"]

    print(f"\nDataset: {ds}")
    if valid:
        valid_names = ", ".join(p.name for p in valid[:20])
        more = "" if len(valid) <= 20 else f" (+{len(valid)-20} more)"
        print(f"✅ {len(valid)} valid files found: {valid_names}{more}")
    else:
        print("⚠️ No valid structured data files found.")

    total_susp = len(suspicious) + len(empty) + len(unreadable) + sum(len(g)-1 for g in duplicates)
    if total_susp > 0:
        print(f"⚠️ {total_susp} suspicious or redundant files detected:")
        for p in suspicious[:50]:
            print(f"  - {p.name}  ({human_readable_size(p.stat().st_size)})")
        for p in empty[:50]:
            print(f"  - {p.name}  (EMPTY)")
        for p, err in unreadable[:50]:
            print(f"  - {p.name}  (UNREADABLE: {err})")
        if duplicates:
            print("  Duplicate groups detected (keeping first file in each group):")
            for group in duplicates[:10]:
                group_names = ", ".join(p.name for p in group)
                print(f"    - {group_names}")
    else:
        print("✅ No suspicious or redundant files detected.")

    if suggested_paths:
        print(f"\nSuggested cleanup size: {human_readable_size(cleanup_size)}")
        sample = ", ".join(p.name for p in suggested_paths[:10])
        more = "" if len(suggested_paths) <= 10 else f" (+{len(suggested_paths)-10} more)"
        print(f"Files that would be deleted if cleanup enabled: {sample}{more}")
    else:
        print("No files suggested for cleanup.")


def confirm_and_delete(paths: List[Path], yes: bool = False) -> None:
    if not paths:
        print("Nothing to delete.")
        return
    print('\nFiles to delete:')
    for p in paths:
        try:
            print(f"  - {p}  ({human_readable_size(p.stat().st_size)})")
        except Exception:
            print(f"  - {p}")
    if yes:
        ok = "y"
    else:
        ok = input("Proceed to delete these files? Type 'yes' to confirm: ")
    if ok.lower() in {"y", "yes"}:
        for p in paths:
            try:
                p.unlink()
                print(f"Deleted {p}")
            except Exception as exc:
                print(f"Failed to delete {p}: {exc}")
        print("Deletion complete.")
    else:
        print("Deletion cancelled by user.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify data directory structure and suggest cleanup (safe by default).")
    parser.add_argument("--data-dir", type=str, default="./data", help="Path to the data directory (default: ./data)")
    parser.add_argument("--clean", action="store_true", help="Enable deletion after confirmation")
    parser.add_argument("--yes", action="store_true", help="Assume yes for deletion confirmation (use with --clean)")

    args = parser.parse_args()

    data_root = Path(args.data_dir).resolve()
    if not data_root.exists() or not data_root.is_dir():
        print(f"Data directory not found: {data_root}")
        return

    print(f"Scanning data root: {data_root}")
    dataset_dirs = [p for p in sorted(data_root.iterdir()) if p.is_dir()]
    if not dataset_dirs:
        print("No dataset directories found under data root.")
        return

    all_reports = []
    overall_cleanup_paths: List[Path] = []

    for ds in dataset_dirs:
        # Only analyze top-level dataset folders (skip hidden/system)
        if ds.name.startswith("."):
            continue
        report = analyze_dataset(ds)
        print_report(report)
        all_reports.append(report)
        overall_cleanup_paths.extend(report["suggested_cleanup_paths"])

    # Global summary
    total_cleanup = sum(p.stat().st_size for p in overall_cleanup_paths if p.exists())
    print("\n==== SUMMARY ====")
    print(f"Datasets scanned: {len(all_reports)}")
    print(f"Total suggested cleanup size (all datasets): {human_readable_size(total_cleanup)}")

    if args.clean:
        print("\n--clean enabled: files will be deleted after confirmation.")
        confirm_and_delete(sorted(set(overall_cleanup_paths)), yes=args.yes)
    else:
        print("\nRun with --clean to actually remove suggested files (requires confirmation).")

    # Optionally write a JSON report to data root
    try:
        out = {
            "root": str(data_root),
            "datasets": {r['dataset']: {
                "valid_count": len(r['valid_files']),
                "suspicious_count": len(r['suspicious_files']) + len(r['empty_files']) + len(r['unreadable_files']),
                "suggested_cleanup_size": r['suggested_cleanup_size'],
            } for r in all_reports}
        }
        p = data_root / "verify_data_report.json"
        with p.open("w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        print(f"JSON summary written to {p}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
