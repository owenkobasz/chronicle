#!/usr/bin/env python3
"""
Chronicle - Photo Organization and Cataloging Tool
A console-based application to organize and catalog photos using metadata.
"""

from pathlib import Path
from organize_photos import organize_photos
import settings
from ascii_art import print_title


def display_menu():
    """Display the main menu options."""
    print('')
    print_title()
    print("=" * 50)
    print("  Photo Organization Tool")
    print("=" * 50)
    print("1. Catalog new photos")
    print("2. Settings")
    print("3. Quit")
    print("=" * 50)


def get_user_choice() -> str:
    """Get user's menu choice."""
    while True:
        choice = input("\nEnter your choice (1-3): ").strip()
        if choice in ("1", "2", "3"):
            return choice
        print("Invalid choice. Please enter 1, 2, or 3.")


def get_source_directory(use_default: bool = True) -> Path:
    """Prompt user for source directory."""
    default_source = settings.get_default_source()
    
    while True:
        if use_default and default_source:
            prompt = f"\nEnter source directory path [{default_source}]: "
        else:
            prompt = "\nEnter source directory path: "
        
        source = input(prompt).strip()
        
        # Use default if user just presses Enter
        if not source and default_source:
            source = default_source
        
        if not source:
            print("Source directory cannot be empty.")
            continue
        
        source_path = Path(source).expanduser()
        if not source_path.exists():
            print(f"Error: Directory does not exist: {source_path}")
            continue
        if not source_path.is_dir():
            print(f"Error: Path is not a directory: {source_path}")
            continue
        
        return source_path


def get_destination_directory(use_default: bool = True) -> Path:
    """Prompt user for destination directory."""
    default_dest = settings.get_default_destination()
    
    while True:
        if use_default and default_dest:
            prompt = f"Enter destination directory path [{default_dest}]: "
        else:
            prompt = "Enter destination directory path: "
        
        dest = input(prompt).strip()
        
        # Use default if user just presses Enter
        if not dest and default_dest:
            dest = default_dest
        
        if not dest:
            print("Destination directory cannot be empty.")
            continue
        
        dest_path = Path(dest).expanduser()
        
        # Create directory if it doesn't exist
        if not dest_path.exists():
            create = input(f"Directory does not exist. Create it? (y/n): ").strip().lower()
            if create == 'y':
                try:
                    dest_path.mkdir(parents=True, exist_ok=True)
                    return dest_path
                except Exception as e:
                    print(f"Error creating directory: {e}")
                    continue
            else:
                continue
        
        if not dest_path.is_dir():
            print(f"Error: Path is not a directory: {dest_path}")
            continue
        
        return dest_path


def get_move_option(use_default: bool = True) -> bool:
    """Ask user if they want to move or copy files."""
    default_move = settings.get_default_move_files()
    
    while True:
        if use_default:
            default_str = "y" if default_move else "n"
            prompt = f"Move files instead of copying? (y/n) [{default_str}]: "
        else:
            prompt = "Move files instead of copying? (y/n): "
        
        move = input(prompt).strip().lower()
        
        # Use default if user just presses Enter
        if not move and use_default:
            return default_move
        
        if move == 'y':
            return True
        elif move == 'n':
            return False
        else:
            print("Please enter 'y' for yes or 'n' for no.")


def catalog_photos():
    """Handle the catalog photos workflow."""
    print("\n--- Catalog New Photos ---")
    
    source = get_source_directory()
    destination = get_destination_directory()
    move_files = get_move_option()
    
    print("\nStarting photo organization...")
    try:
        organize_photos(source, destination, move=move_files, interactive=True)
        print("\n✓ Photo cataloging completed successfully!")
    except Exception as e:
        print(f"\n✗ Error during cataloging: {e}")


def configure_settings():
    """Handle the settings configuration workflow."""
    print("\n--- Settings ---")
    
    current_settings = settings.load_settings()
    
    # Format organization scheme for display
    scheme = current_settings.get('organization_scheme', 'camera_year_month')
    scheme_display = {
        'camera_year_month': 'Camera/Year/Month',
        'year_month': 'Year/Month',
        'year_month_camera': 'Year/Month/Camera'
    }.get(scheme, scheme)
    
    month_format = current_settings.get('month_format', 'full')
    month_display = 'Full (01 - January)' if month_format == 'full' else 'Number (01)'
    
    separate_types = current_settings.get('separate_file_types', True)
    separate_display = 'Yes' if separate_types else 'No'
    
    print("\nCurrent settings:")
    print(f"  Default source: {current_settings.get('default_source', 'Not set')}")
    print(f"  Default destination: {current_settings.get('default_destination', 'Not set')}")
    print(f"  Default move files: {current_settings.get('default_move_files', False)}")
    print(f"  Organization scheme: {scheme_display}")
    print(f"  Month format: {month_display}")
    print(f"  Separate file types: {separate_display}")
    
    print("\nWhat would you like to configure?")
    print("1. Set default source directory")
    print("2. Set default destination directory")
    print("3. Set default move files preference")
    print("4. Set organization scheme")
    print("5. Set month format")
    print("6. Set file type separation")
    print("7. Clear all settings (reset to defaults)")
    print("8. Back to main menu")
    
    while True:
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            print("\nSetting default source directory...")
            source = input("Enter default source directory path (or press Enter to clear): ").strip()
            if source:
                source_path = Path(source).expanduser()
                if source_path.exists() and source_path.is_dir():
                    if settings.set_default_source(str(source_path)):
                        print(f"✓ Default source set to: {source_path}")
                    else:
                        print("✗ Failed to save setting.")
                else:
                    print(f"✗ Directory does not exist or is not a directory: {source_path}")
            else:
                if settings.set_default_source(""):
                    print("✓ Default source cleared.")
                else:
                    print("✗ Failed to save setting.")
            break
        
        elif choice == "2":
            print("\nSetting default destination directory...")
            dest = input("Enter default destination directory path (or press Enter to clear): ").strip()
            if dest:
                dest_path = Path(dest).expanduser()
                # Allow setting even if it doesn't exist (user might create it later)
                if settings.set_default_destination(str(dest_path)):
                    print(f"✓ Default destination set to: {dest_path}")
                else:
                    print("✗ Failed to save setting.")
            else:
                if settings.set_default_destination(""):
                    print("✓ Default destination cleared.")
                else:
                    print("✗ Failed to save setting.")
            break
        
        elif choice == "3":
            print("\nSetting default move files preference...")
            while True:
                move = input("Move files by default? (y/n): ").strip().lower()
                if move == 'y':
                    if settings.set_default_move_files(True):
                        print("✓ Default move files set to: Yes")
                    else:
                        print("✗ Failed to save setting.")
                    break
                elif move == 'n':
                    if settings.set_default_move_files(False):
                        print("✓ Default move files set to: No")
                    else:
                        print("✗ Failed to save setting.")
                    break
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
            break
        
        elif choice == "4":
            print("\nSetting organization scheme...")
            print("Available schemes:")
            print("  1. Camera/Year/Month (default)")
            print("  2. Year/Month")
            print("  3. Year/Month/Camera")
            while True:
                scheme_choice = input("Enter your choice (1-3): ").strip()
                if scheme_choice == "1":
                    if settings.set_organization_scheme("camera_year_month"):
                        print("✓ Organization scheme set to: Camera/Year/Month")
                    else:
                        print("✗ Failed to save setting.")
                    break
                elif scheme_choice == "2":
                    if settings.set_organization_scheme("year_month"):
                        print("✓ Organization scheme set to: Year/Month")
                    else:
                        print("✗ Failed to save setting.")
                    break
                elif scheme_choice == "3":
                    if settings.set_organization_scheme("year_month_camera"):
                        print("✓ Organization scheme set to: Year/Month/Camera")
                    else:
                        print("✗ Failed to save setting.")
                    break
                else:
                    print("Invalid choice. Please enter 1, 2, or 3.")
            break
        
        elif choice == "5":
            print("\nSetting month format...")
            print("  1. Full (01 - January)")
            print("  2. Number (01)")
            while True:
                format_choice = input("Enter your choice (1-2): ").strip()
                if format_choice == "1":
                    if settings.set_month_format("full"):
                        print("✓ Month format set to: Full (01 - January)")
                    else:
                        print("✗ Failed to save setting.")
                    break
                elif format_choice == "2":
                    if settings.set_month_format("number"):
                        print("✓ Month format set to: Number (01)")
                    else:
                        print("✗ Failed to save setting.")
                    break
                else:
                    print("Invalid choice. Please enter 1 or 2.")
            break
        
        elif choice == "6":
            print("\nSetting file type separation...")
            while True:
                separate = input("Separate JPG/RAW/VIDEO into subfolders? (y/n): ").strip().lower()
                if separate == 'y':
                    if settings.set_separate_file_types(True):
                        print("✓ File type separation enabled")
                    else:
                        print("✗ Failed to save setting.")
                    break
                elif separate == 'n':
                    if settings.set_separate_file_types(False):
                        print("✓ File type separation disabled")
                    else:
                        print("✗ Failed to save setting.")
                    break
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
            break
        
        elif choice == "7":
            confirm = input("\nAre you sure you want to reset all settings to defaults? (y/n): ").strip().lower()
            if confirm == 'y':
                if settings.reset_settings():
                    print("✓ All settings have been reset to defaults.")
                else:
                    print("✗ Failed to reset settings.")
            break
        
        elif choice == "8":
            return
        
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, 5, 6, 7, or 8.")


def main():
    """Main application loop."""
    #print("Welcome to Chronicle!")
    
    while True:
        display_menu()
        choice = get_user_choice()
        
        if choice == "1":
            catalog_photos()
        elif choice == "2":
            configure_settings()
        elif choice == "3":
            print("\nThank you for using Chronicle. Goodbye!")
            break


if __name__ == "__main__":
    main()
