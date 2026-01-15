# Chronicle

A console-based photo and video organization and cataloging tool that automatically organizes your media files using metadata (EXIF data) from your images and videos.

## Purpose

Chronicle is designed to help photographers and video creators organize their digital media collections by automatically sorting photos and videos into a structured folder hierarchy based on camera information and capture dates. The app reads metadata from your media files and organizes them into a logical, easy-to-navigate structure.

## Features

### 📁 Smart Organization
- **Automatic folder structure**: Organizes photos and videos by `CAMERA/YEAR/MONTH - MonthName/`
- **File type separation**: When multiple file types exist in the same time period, they are automatically separated into subfolders:
  - `JPG/` and `RAW/` subfolders when both exist
  - `VIDEO/` subfolder for video files
- **Comprehensive RAW support**: Supports all major RAW formats including:
  - Canon (.cr2, .cr3)
  - Nikon (.nef, .nrw)
  - Sony (.arw, .srf, .sr2)
  - Fujifilm (.raf)
  - Adobe DNG (.dng)
  - And many more
- **Video support**: Organizes video files alongside photos with support for:
  - Common formats: .mp4, .mov, .avi, .mkv, .m4v
  - Additional formats: .mpg, .mpeg, .wmv, .flv, .webm
  - Mobile formats: .3gp, .3g2
  - Professional formats: .mts, .m2ts (AVCHD), .vob (DVD)

### 📸 Metadata Extraction
- Reads EXIF data from photos to determine:
  - Camera make and model
  - Date and time the photo was taken
- **Camera name normalization**: Intelligently normalizes camera names for consistency:
  - Handles brand name variations (Sony, Canon, Nikon, DJI, etc.)
  - Normalizes model numbers (e.g., ILCE-7M3 → A7III)
  - Cleans up formatting for folder-friendly names
- For videos, uses file modification time when EXIF is unavailable
- Handles missing metadata gracefully with interactive prompts

### ⚙️ User Preferences
- **Settings management**: Save default source and destination directories
- **Persistent preferences**: Settings are saved between sessions
- **Quick workflow**: Use defaults or override as needed

### 🔄 Flexible Operations
- **Copy or move**: Choose to copy files (keeping originals) or move them
- **Interactive fallback**: When metadata is missing, the app prompts you to enter it manually
- **Non-destructive**: By default, copies files instead of moving them

### 📊 Processing Reports
- **Detailed statistics**: After processing, view a comprehensive report including:
  - Total files processed
  - Camera breakdown with file counts
  - Missing EXIF data count
  - RAW/JPG pairs matched
  - Processing duration
- Example report format:
  ```
  Processed: 8,240 files
  Cameras: Sony_A7III (6,010), DJI_Mavic3 (1,200), iPhone14 (1,030)
  Missing EXIF: 140 files
  RAW/JPG pairs matched: 500
  Duration: 00:12:41
  ```

### 🔐 Checksum Logging
- **File integrity verification**: Calculates SHA256 checksums for all processed files
- **Persistent logging**: Checksums are saved to `.checksums.json` in the destination directory
- **Incremental updates**: Checksum log is updated incrementally, preserving existing entries
- Use checksums to verify file integrity and detect corruption or changes

## Installation

### Prerequisites
- Python 3.8 or higher
- Poetry (recommended) or pip

### Setup with Poetry (Recommended)

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
   Or follow the [official Poetry installation guide](https://python-poetry.org/docs/#installation).

2. **Clone or download this repository**

3. **Install dependencies and create virtual environment**:
   ```bash
   poetry install
   ```
   This will automatically create a virtual environment and install all dependencies.

4. **Activate the virtual environment** (optional):
   ```bash
   # Option 1: Install shell plugin (recommended for Poetry 2.0+)
   poetry self add poetry-plugin-shell
   poetry shell
   
   # Option 2: Manually activate the virtual environment
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

### Setup with pip (Alternative)

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

**With Poetry:**
```bash
# After installing with 'poetry install', you can run from anywhere:
chronicle

# Or use Poetry to run it:
poetry run chronicle
```

**With pip:**
```bash
# Activate virtual environment (if using one)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the application
python -m chronicle.main
# Or from the project directory:
cd chronicle
python main.py
```

### Main Menu

When you start Chronicle, you'll see a menu with the following options:

1. **Catalog new photos** - Organize photos from a source directory
2. **Settings** - Configure default directories and preferences
3. **Quit** - Exit the application

### Cataloging Photos

1. Select option `1` from the main menu
2. Enter the source directory containing your photos (or press Enter to use default)
3. Enter the destination directory where organized photos should be placed (or press Enter to use default)
4. Choose whether to move or copy files (or press Enter to use default)
5. The app will process all photos and organize them automatically

### Organization Structure

Photos and videos are organized into the following structure:

```
Destination/
├── CameraName/
│   ├── YYYY/
│   │   ├── 01 - January/
│   │   │   ├── JPG/          (if JPG and RAW both exist)
│   │   │   │   └── photo1.jpg
│   │   │   ├── RAW/          (if JPG and RAW both exist)
│   │   │   │   └── photo1.cr2
│   │   │   └── VIDEO/        (if videos exist)
│   │   │       └── video1.mp4
│   │   ├── 02 - February/
│   │   │   └── photo2.jpg    (if only one file type)
│   │   └── ...
│   └── ...
└── .checksums.json           (checksum log file)
```

### Settings Configuration

1. Select option `2` from the main menu
2. Choose what to configure:
   - Set default source directory
   - Set default destination directory
   - Set default move files preference
   - Reset all settings to defaults

Settings are saved in `~/.chronicle_settings.json` and persist between sessions.

### Handling Missing Metadata

If a photo is missing EXIF metadata (camera info or date), Chronicle will:
- Prompt you interactively to enter the missing information
- Allow you to specify camera name, year, and month manually
- Use "UnknownCamera", "UnknownYear", or "UnknownMonth" if you skip the prompts

## Project Structure

```
chronicle/
├── chronicle/          # Main package
│   ├── __init__.py    # Package initialization
│   ├── main.py        # Main application entry point with menu system
│   ├── organize_photos.py  # Core photo organization logic
│   ├── settings.py    # Settings management module
│   └── ascii_art.py   # ASCII art for title display
├── pyproject.toml     # Poetry configuration and dependencies
├── poetry.lock        # Locked dependency versions
├── requirements.txt   # Python dependencies (legacy)
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## Technical Details

### Dependencies
- **Pillow** (PIL): For reading EXIF metadata from images

### Supported File Formats
- **Photo formats**: JPG, JPEG, PNG, HEIC, TIFF, BMP, GIF
- **RAW formats**: See comprehensive list in Features section above
- **Video formats**: MP4, MOV, AVI, MKV, M4V, MPG, MPEG, WMV, FLV, WEBM, 3GP, 3G2, MTS, M2TS, VOB, OGV

### Settings Storage
Settings are stored in JSON format at `~/.chronicle_settings.json`:
```json
{
  "default_source": "/path/to/source",
  "default_destination": "/path/to/destination",
  "default_move_files": false
}
```

## Command Line Usage (Advanced)

The `organize_photos` module can also be used directly from the command line:

```bash
# With Poetry (after installation):
poetry run python -m chronicle.organize_photos /path/to/source --dest /path/to/destination [--move] [--no-interactive]

# Or if you have the package installed:
python -m chronicle.organize_photos /path/to/source --dest /path/to/destination [--move] [--no-interactive]
```

Options:
- `src`: Source directory (required)
- `--dest`: Destination directory (optional, defaults to source)
- `--move`: Move files instead of copying
- `--no-interactive`: Disable interactive prompts for missing metadata

The command-line tool processes both photos and videos, generates a processing report, and creates a checksum log automatically.

## Notes

- The app processes photos and videos recursively from the source directory
- Duplicate filenames are automatically handled with numeric suffixes
- The app preserves file modification times when copying/moving
- Settings file location can be customized by modifying `settings.py`
- Checksum log file (`.checksums.json`) is stored in the destination directory and can be used for file integrity verification
- Video files without EXIF metadata will use file modification time for date organization

## License

This project is provided as-is for personal use.

## Contributing

This is a personal project, but suggestions and improvements are welcome!
