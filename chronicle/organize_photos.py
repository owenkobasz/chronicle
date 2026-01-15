import argparse
import calendar
import hashlib
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from PIL import Image
from PIL.ExifTags import TAGS


# File types to treat as photos
PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".tif", ".tiff", ".bmp", ".gif"}

# RAW file extensions
RAW_EXTENSIONS = {
    ".cr2", ".cr3",  # Canon
    ".nef", ".nrw",  # Nikon
    ".arw", ".srf", ".sr2",  # Sony
    ".orf",  # Olympus
    ".raf",  # Fujifilm
    ".rw2",  # Panasonic
    ".dng",  # Adobe Digital Negative
    ".pef",  # Pentax
    ".x3f",  # Sigma
    ".3fr",  # Hasselblad
    ".mef",  # Mamiya
    ".erf",  # Epson
    ".kdc",  # Kodak
    ".dcr",  # Kodak
    ".mos",  # Leaf
    ".mrw",  # Minolta
    ".raw",  # Generic RAW
    ".rwl",  # Leica
    ".srw",  # Samsung
}

# JPG file extensions (subset of PHOTO_EXTENSIONS)
JPG_EXTENSIONS = {".jpg", ".jpeg"}

# Video file extensions
VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".m4v",  # Common formats
    ".mpg", ".mpeg", ".wmv", ".flv", ".webm",  # Additional formats
    ".3gp", ".3g2",  # Mobile formats
    ".mts", ".m2ts",  # AVCHD
    ".vob",  # DVD
    ".ogv",  # Ogg
}


def get_exif(path: Path) -> dict:
    """Return a dict of EXIF tags for an image, or {} if unavailable."""
    try:
        with Image.open(path) as img:
            exif_data = img._getexif()
    except Exception:
        return {}

    if not exif_data:
        return {}

    exif = {}
    for tag_id, value in exif_data.items():
        tag = TAGS.get(tag_id, tag_id)
        exif[tag] = value
    return exif


def get_date_taken(path: Path) -> Optional[datetime]:
    """
    Try to get the 'date taken' from EXIF (for images) or file metadata (for videos).
    Returns a datetime object or None if not found/parsable.
    """
    # For images, try EXIF first
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        exif = get_exif(path)
        date_str = exif.get("DateTimeOriginal") or exif.get("DateTime")
        if date_str:
            # EXIF datetime format is typically "YYYY:MM:DD HH:MM:SS"
            try:
                return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except Exception:
                pass
    
    # For videos or if EXIF failed, try file modification time
    try:
        mtime = os.path.getmtime(path)
        return datetime.fromtimestamp(mtime)
    except Exception:
        return None


def normalize_camera_name(raw_make: str | None, raw_model: str | None) -> str:
    """
    Clean up camera make/model into a folder-friendly name with improved normalization.
    Examples:
      Make='Apple', Model='iPhone 14 Pro' -> 'Apple_iPhone_14_Pro'
      Make=None, Model='NIKON D5300' -> 'Nikon_D5300'
      Make='SONY', Model='ILCE-7M3' -> 'Sony_A7III'
    """
    if not raw_make and not raw_model:
        return "UnknownCamera"

    def clean(s: str) -> str:
        s = s.strip()
        # Remove common prefixes/suffixes
        s = s.replace("Corporation", "").replace("Inc.", "").replace("Inc", "")
        s = s.replace("Company", "").replace("Ltd.", "").replace("Ltd", "")
        s = s.strip()
        # Basic capitalization polish - preserve existing capitalization for known brands
        parts = s.split()
        cleaned_parts = []
        for part in parts:
            # Preserve common brand names
            part_lower = part.lower()
            if part_lower in ["iphone", "ipad", "dji", "gopro", "sony", "canon", "nikon", "fujifilm", "olympus", "panasonic", "pentax", "leica", "hasselblad"]:
                cleaned_parts.append(part.capitalize())
            elif part_lower.startswith("ilce-") or part_lower.startswith("dsc-"):
                # Sony model numbers - preserve format
                cleaned_parts.append(part.upper())
            else:
                # Normal capitalization
                cleaned_parts.append(part.capitalize())
        s = " ".join(cleaned_parts)
        # Replace spaces and slashes with underscores
        for ch in (" ", "/", "\\", "-"):
            s = s.replace(ch, "_")
        # Remove multiple underscores
        while "__" in s:
            s = s.replace("__", "_")
        # Remove leading/trailing underscores
        s = s.strip("_")
        return s

    make = clean(raw_make) if raw_make else ""
    model = clean(raw_model) if raw_model else ""

    # Normalize common camera model names
    model_normalized = model
    # Sony ILCE-7M3 -> A7III, ILCE-7RM4 -> A7RIV, etc.
    if "ILCE_7M3" in model_normalized or "ILCE_7M3" in model_normalized:
        model_normalized = "A7III"
    elif "ILCE_7M4" in model_normalized:
        model_normalized = "A7IV"
    elif "ILCE_7RM3" in model_normalized or "ILCE_7RM3A" in model_normalized:
        model_normalized = "A7RIII"
    elif "ILCE_7RM4" in model_normalized:
        model_normalized = "A7RIV"
    elif "ILCE_7RM5" in model_normalized:
        model_normalized = "A7RV"
    elif "ILCE_9" in model_normalized:
        model_normalized = "A9"
    elif "ILCE_1" in model_normalized:
        model_normalized = "A1"
    # DJI normalization
    elif "MAVIC" in model_normalized.upper() and "3" in model_normalized:
        model_normalized = "Mavic3"
    elif "MAVIC" in model_normalized.upper() and "2" in model_normalized:
        model_normalized = "Mavic2"
    # iPhone normalization
    elif "IPHONE" in model_normalized.upper():
        # Extract model number if present
        parts = model_normalized.split("_")
        for part in parts:
            if "IPHONE" in part.upper() and any(c.isdigit() for c in part):
                model_normalized = part.replace("_", "")
                break

    # Avoid super-redundant names like "Nikon_Nikon_D5300"
    if make and model_normalized:
        if model_normalized.lower().startswith(make.lower()):
            return model_normalized
        return f"{make}_{model_normalized}"
    return make or model_normalized or "UnknownCamera"


def get_camera_name(path: Path) -> str:
    """
    Get camera name from EXIF Make/Model (for images) or return UnknownCamera (for videos).
    Returns a cleaned string suitable for use as a folder name.
    """
    # For videos, we can't easily extract camera info from EXIF
    # Could use file metadata in the future, but for now return UnknownCamera
    if path.suffix.lower() in VIDEO_EXTENSIONS:
        return "UnknownCamera"
    
    exif = get_exif(path)
    make = exif.get("Make")
    model = exif.get("Model")
    # Some EXIF fields can be bytes, convert to str if needed
    if isinstance(make, bytes):
        make = make.decode(errors="ignore")
    if isinstance(model, bytes):
        model = model.decode(errors="ignore")

    return normalize_camera_name(make, model)


def is_raw_file(path: Path) -> bool:
    """Check if file is a RAW format."""
    return path.suffix.lower() in RAW_EXTENSIONS


def is_jpg_file(path: Path) -> bool:
    """Check if file is a JPG format."""
    return path.suffix.lower() in JPG_EXTENSIONS


def get_file_type_category(path: Path) -> str:
    """
    Returns 'RAW', 'JPG', 'VIDEO', or 'OTHER' based on file extension.
    """
    ext = path.suffix.lower()
    if ext in RAW_EXTENSIONS:
        return "RAW"
    elif ext in JPG_EXTENSIONS:
        return "JPG"
    elif ext in VIDEO_EXTENSIONS:
        return "VIDEO"
    else:
        return "OTHER"


def format_month_name(month_number: int, format_type: str = "full") -> str:
    """
    Format month based on format_type.
    - 'full': 'MM - MonthName' (e.g., '01 - January')
    - 'number': 'MM' (e.g., '01')
    """
    if 1 <= month_number <= 12:
        if format_type == "number":
            return f"{month_number:02d}"
        else:
            month_name = calendar.month_name[month_number]
            return f"{month_number:02d} - {month_name}"
    return "UnknownMonth"


def prompt_for_metadata(file_path: Path, month_format: str = "full") -> Tuple[str, str, str]:
    """
    Interactive prompt for missing metadata.
    Returns (camera_name, year, month).
    """
    print(f"\n⚠️  Missing metadata for: {file_path.name}")
    print("Please provide the following information (press Enter to skip):")
    
    camera = input("Camera name (or press Enter for 'UnknownCamera'): ").strip()
    if not camera:
        camera = "UnknownCamera"
    else:
        # Normalize the camera name
        camera = normalize_camera_name(camera, None)
    
    year = input("Year (YYYY, or press Enter for 'UnknownYear'): ").strip()
    if not year:
        year = "UnknownYear"
    else:
        # Validate year format
        try:
            year_int = int(year)
            if 1900 <= year_int <= 2100:
                year = f"{year_int:04d}"
            else:
                print("Invalid year, using 'UnknownYear'")
                year = "UnknownYear"
        except ValueError:
            print("Invalid year format, using 'UnknownYear'")
            year = "UnknownYear"
    
    month = input("Month (MM, or press Enter for 'UnknownMonth'): ").strip()
    if not month:
        month = "UnknownMonth"
    else:
        # Validate month format
        try:
            month_int = int(month)
            if 1 <= month_int <= 12:
                month = format_month_name(month_int, month_format)
            else:
                print("Invalid month, using 'UnknownMonth'")
                month = "UnknownMonth"
        except ValueError:
            print("Invalid month format, using 'UnknownMonth'")
            month = "UnknownMonth"
    
    return camera, year, month


def get_unique_target(target: Path) -> Path:
    """
    If 'target' already exists, add _1, _2, ... to the filename stem.
    """
    if not target.exists():
        return target

    stem, suffix = target.stem, target.suffix
    i = 1
    while True:
        candidate = target.with_name(f"{stem}_{i}{suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return ""


def save_checksum_log(dest_dir: Path, checksum_log: Dict[str, str]) -> None:
    """
    Save checksum log to a JSON file in the destination directory.
    """
    log_file = dest_dir / ".checksums.json"
    try:
        # Load existing checksums if file exists
        existing_log = {}
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    existing_log = json.load(f)
            except Exception:
                pass
        
        # Merge with new checksums
        existing_log.update(checksum_log)
        
        # Save updated log
        with open(log_file, 'w') as f:
            json.dump(existing_log, f, indent=2)
    except Exception:
        pass


def organize_photos(src_dir: Path, dest_dir: Path, move: bool = False, interactive: bool = True, 
                    organization_scheme: str = None, month_format: str = None, separate_file_types: bool = None):
    """
    Organize photos and videos from src_dir into dest_dir based on organization scheme.
    
    Organization schemes:
    - 'camera_year_month': CAMERA/YEAR/MONTH (default)
    - 'year_month': YEAR/MONTH
    - 'year_month_camera': YEAR/MONTH/CAMERA
    
    Month format:
    - 'full': 'MM - MonthName' (e.g., '01 - January')
    - 'number': 'MM' (e.g., '01')
    
    File type separation (if enabled):
    - JPG/RAW/VIDEO subfolders when multiple types exist
    
    Files without EXIF date go under YYYY='UnknownYear', MM='UnknownMonth'.
    Files without camera info go under CameraName='UnknownCamera'.
    
    Args:
        src_dir: Source directory
        dest_dir: Destination directory
        move: Whether to move files (True) or copy them (False)
        interactive: Whether to prompt for missing metadata
        organization_scheme: Organization scheme ('camera_year_month', 'year_month', 'year_month_camera')
        month_format: Month format ('full' or 'number')
        separate_file_types: Whether to separate JPG/RAW/VIDEO into subfolders
    """
    import time
    from . import settings as settings_module
    
    # Load settings if not provided
    if organization_scheme is None:
        organization_scheme = settings_module.get_organization_scheme()
    if month_format is None:
        month_format = settings_module.get_month_format()
    if separate_file_types is None:
        separate_file_types = settings_module.get_separate_file_types()
    
    start_time = time.time()
    src_dir = src_dir.resolve()
    dest_dir = dest_dir.resolve()

    if not src_dir.exists() or not src_dir.is_dir():
        raise ValueError(f"Source directory does not exist or is not a directory: {src_dir}")

    print(f"Source: {src_dir}")
    print(f"Destination: {dest_dir}")
    print(f"Mode: {'MOVE' if move else 'COPY'}")
    print("-" * 40)

    # Statistics tracking
    stats = {
        "files_processed": 0,
        "files_no_date": 0,
        "files_no_camera": 0,
        "files_no_exif": 0,
        "raw_jpg_pairs": 0,
        "cameras": defaultdict(int),
        "checksum_log": {},
    }

    # First pass: collect all files and their metadata
    file_info_list = []
    all_file_extensions = PHOTO_EXTENSIONS | RAW_EXTENSIONS | VIDEO_EXTENSIONS

    for path in src_dir.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in all_file_extensions:
            continue

        # Get metadata
        camera_name = get_camera_name(path)
        date_taken = get_date_taken(path)
        
        # Track missing EXIF (for images only)
        if path.suffix.lower() not in VIDEO_EXTENSIONS:
            exif = get_exif(path)
            if not exif:
                stats["files_no_exif"] += 1
        
        # Handle missing metadata with interactive fallback
        needs_camera_prompt = (camera_name == "UnknownCamera")
        needs_date_prompt = (date_taken is None)
        
        if (needs_camera_prompt or needs_date_prompt) and interactive:
            # Interactive mode: prompt user for missing info
            prompt_camera, prompt_year, prompt_month = prompt_for_metadata(path, month_format)
            
            # Use prompted camera if original was unknown
            if needs_camera_prompt:
                camera_name = prompt_camera
            
            # Use prompted date if original was missing
            if needs_date_prompt:
                if prompt_year != "UnknownYear" and prompt_month != "UnknownMonth":
                    try:
                        # Extract month number from formatted string (e.g., "01 - January" -> 1)
                        month_num = int(prompt_month.split(" - ")[0])
                        date_taken = datetime(int(prompt_year), month_num, 1)
                    except (ValueError, IndexError):
                        date_taken = None
                        stats["files_no_date"] += 1
                else:
                    stats["files_no_date"] += 1
        else:
            # Non-interactive mode: track missing metadata
            if needs_camera_prompt:
                stats["files_no_camera"] += 1
            if needs_date_prompt:
                stats["files_no_date"] += 1
        
        # Determine year and month
        if date_taken:
            year = f"{date_taken.year:04d}"
            month = format_month_name(date_taken.month, month_format)
        else:
            year = "UnknownYear"
            month = "UnknownMonth"

        file_type = get_file_type_category(path)
        file_info_list.append({
            "path": path,
            "camera": camera_name,
            "year": year,
            "month": month,
            "type": file_type,
            "stem": path.stem,  # For matching RAW/JPG pairs
        })
        
        # Track camera usage
        stats["cameras"][camera_name] += 1

    # Match RAW/JPG pairs (same stem, same camera/year/month)
    raw_files = {info["stem"].lower(): info for info in file_info_list if info["type"] == "RAW"}
    jpg_files = {info["stem"].lower(): info for info in file_info_list if info["type"] == "JPG"}
    
    for stem in raw_files.keys():
        if stem in jpg_files:
            raw_info = raw_files[stem]
            jpg_info = jpg_files[stem]
            # Check if they're in the same camera/year/month group
            if (raw_info["camera"] == jpg_info["camera"] and 
                raw_info["year"] == jpg_info["year"] and 
                raw_info["month"] == jpg_info["month"]):
                stats["raw_jpg_pairs"] += 1

    # Group files by camera/year/month
    groups = defaultdict(list)
    for info in file_info_list:
        key = (info["camera"], info["year"], info["month"])
        groups[key].append(info)

    # Second pass: organize files
    for (camera, year, month), files in groups.items():
        # Check if this group has multiple file types that need separation
        has_jpg = any(f["type"] == "JPG" for f in files)
        has_raw = any(f["type"] == "RAW" for f in files)
        has_video = any(f["type"] == "VIDEO" for f in files)
        needs_separation = separate_file_types and ((has_jpg and has_raw) or has_video)

        for file_info in files:
            path = file_info["path"]
            file_type = file_info["type"]

            # Build folder path based on organization scheme
            if organization_scheme == "camera_year_month":
                # CAMERA/YEAR/MONTH
                base_path = dest_dir / camera / year / month
            elif organization_scheme == "year_month":
                # YEAR/MONTH
                base_path = dest_dir / year / month
            elif organization_scheme == "year_month_camera":
                # YEAR/MONTH/CAMERA
                base_path = dest_dir / year / month / camera
            else:
                # Default to camera_year_month
                base_path = dest_dir / camera / year / month

            # Add file type subfolder if separation is needed
            if needs_separation and file_type in ("JPG", "RAW", "VIDEO"):
                folder_path = base_path / file_type
            else:
                folder_path = base_path

            folder_path.mkdir(parents=True, exist_ok=True)

            target = folder_path / path.name
            target = get_unique_target(target)

            # Calculate checksum before moving/copying
            checksum = calculate_checksum(path)
            if checksum:
                # Store checksum with relative path from dest_dir
                rel_path = str(target.relative_to(dest_dir))
                stats["checksum_log"][rel_path] = checksum

            if move:
                shutil.move(str(path), str(target))
            else:
                shutil.copy2(str(path), str(target))

            stats["files_processed"] += 1
            if stats["files_processed"] % 100 == 0:
                print(f"{stats['files_processed']} files processed...")

    # Save checksum log
    if stats["checksum_log"]:
        save_checksum_log(dest_dir, stats["checksum_log"])

    # Calculate duration
    total_seconds = int(time.time() - start_time)
    duration_hours = total_seconds // 3600
    duration_minutes = (total_seconds % 3600) // 60
    duration_seconds = total_seconds % 60
    duration_str = f"{duration_hours:02d}:{duration_minutes:02d}:{duration_seconds:02d}"

    # Generate and display report
    generate_report(stats, duration_str)


def generate_report(stats: Dict[str, Any], duration: str) -> None:
    """
    Generate and display a processing report.
    """
    print("\n" + "=" * 50)
    print("PROCESSING REPORT")
    print("=" * 50)
    
    # Files processed
    print(f"Processed: {stats['files_processed']:,} files")
    
    # Cameras
    if stats["cameras"]:
        camera_list = []
        for camera, count in sorted(stats["cameras"].items(), key=lambda x: x[1], reverse=True):
            camera_list.append(f"{camera} ({count:,})")
        print(f"Cameras: {', '.join(camera_list)}")
    
    # Missing EXIF
    if stats["files_no_exif"] > 0:
        print(f"Missing EXIF: {stats['files_no_exif']:,} files")
    
    # RAW/JPG pairs
    if stats["raw_jpg_pairs"] > 0:
        print(f"RAW/JPG pairs matched: {stats['raw_jpg_pairs']:,}")
    
    # Duration
    print(f"Duration: {duration}")
    
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Organize photos and videos into folders based on camera and EXIF date taken. "
                    "Separates JPG, RAW, and VIDEO files into subfolders when multiple types exist."
    )
    parser.add_argument(
        "src",
        type=str,
        help="Source folder containing your photos",
    )
    parser.add_argument(
        "--dest",
        type=str,
        default=None,
        help="Destination folder (default: same as source)",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help="Move files instead of copying them",
    )
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Disable interactive prompts for missing metadata",
    )

    args = parser.parse_args()

    src_dir = Path(args.src).expanduser()
    dest_dir = Path(args.dest).expanduser() if args.dest else src_dir

    organize_photos(src_dir, dest_dir, move=args.move, interactive=not args.no_interactive)


if __name__ == "__main__":
    main()
