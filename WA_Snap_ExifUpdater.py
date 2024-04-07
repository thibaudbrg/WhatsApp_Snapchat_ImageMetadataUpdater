import os
import subprocess
import platform
from PIL import Image, UnidentifiedImageError
import piexif
from datetime import datetime
import re
import shutil
from tqdm import tqdm
import hashlib
import logging
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger()

# Regex patterns for file identification
WHATSAPP_IMAGE_PATTERN = r"^IMG-\d{8}-WA\d{4}\.jpg$"
SNAPCHAT_FILE_PATTERN = r"^Snapchat-\d+\.(jpg|mp4)$"


def is_whatsapp_image(filename):
    return re.match(WHATSAPP_IMAGE_PATTERN, filename) is not None


def is_snapchat_file(filename):
    return re.match(SNAPCHAT_FILE_PATTERN, filename) is not None


def extract_date_from_whatsapp_filename(filename):
    date_str = filename[4:12]  # Assuming the format IMG-YYYYMMDD-WA####
    return datetime.strptime(date_str, '%Y%m%d')


def prompt_for_input(prompt_message, valid_options=None, error_message="Invalid input. Please try again."):
    while True:
        user_input = input(prompt_message).strip().lower()
        if valid_options:
            if user_input in valid_options:
                return user_input
            else:
                logger.error(Fore.RED + error_message)
        else:
            return user_input


def prompt_for_date(prompt_message):
    while True:
        date_str = input(prompt_message).strip()
        try:
            return datetime.strptime(date_str, '%Y:%m:%d')
        except ValueError:
            logger.error(Fore.RED + "Invalid date format. Please use YYYY:MM:DD.")


def get_file_count(directory):
    return sum([len(files) for r, d, files in os.walk(directory)])


def file_checksum(file_path):
    hash_func = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def verify_backup(source_dir, backup_dir):
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(backup_dir, os.path.relpath(src_file, source_dir))

            if not os.path.exists(dst_file):
                logger.error(Fore.RED + f"File missing in backup: {dst_file}")
                continue

            src_checksum = file_checksum(src_file)
            dst_checksum = file_checksum(dst_file)

            if src_checksum != dst_checksum or os.path.getsize(src_file) != os.path.getsize(dst_file):
                logger.error(Fore.RED + f"File mismatch found: {file}")


def backup_directory_for_windows(source_dir, destination_dir):
    result = subprocess.run(["robocopy", source_dir, destination_dir, "/E", "/COPY:DAT"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.STDOUT,
                            check=False)
    if result.returncode > 1:
        raise subprocess.CalledProcessError(result.returncode, result.args)


def backup_directory_for_unix(source_dir, destination_dir):
    file_count = get_file_count(source_dir)
    progress = tqdm(total=file_count, unit='file', desc='Backing up')

    for root, dirs, files in os.walk(source_dir):
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(destination_dir, os.path.relpath(src_file, source_dir))
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            shutil.copy2(src_file, dst_file)
            progress.update(1)

    progress.close()


def backup_directory(source_dir):
    backup_dir_base = f"{source_dir}_backup"
    backup_dir_name = backup_dir_base
    counter = 1

    while os.path.exists(backup_dir_name):
        backup_dir_name = f"{backup_dir_base}({counter})"
        counter += 1

    os_type = platform.system()

    if os_type == 'Windows':
        backup_directory_for_windows(source_dir, backup_dir_name)
    elif os_type in ['Linux', 'Darwin']:
        backup_directory_for_unix(source_dir, backup_dir_name)
    else:
        raise OSError("Unsupported operating system")
    return backup_dir_name


def update_video_metadata(file_path, date):
    """Update the metadata for MP4 files using ffmpeg."""
    temp_file = file_path + '_temp.mp4'
    formatted_date = date.strftime("%Y-%m-%dT%H:%M:%S")
    command = [
        'ffmpeg',
        '-i', file_path,
        '-c', 'copy',
        '-metadata', f"creation_time={formatted_date}",
        temp_file
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.replace(temp_file, file_path)  # Replace the original file with the updated one
        logger.info(Fore.GREEN + f"Metadata updated for {file_path}")
        return 'updated'
    except subprocess.CalledProcessError as e:
        logger.error(Fore.RED + f"Failed to update metadata for {file_path}: {e.stderr.decode()}")
        if os.path.exists(temp_file):
            os.remove(temp_file)  # Cleanup the temporary file on failure
        return 'failed'


def update_image_metadata(file_path, date=None):
    try:
        img = Image.open(file_path)
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
            if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                return 'exists'
        else:
            exif_dict = {'Exif': {}, '0th': {}, '1st': {}, 'thumbnail': None, 'GPS': {}}

        if date is None:
            date = extract_date_from_whatsapp_filename(os.path.basename(file_path))
        formatted_date = date.strftime("%Y:%m:%d %H:%M:%S")

        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = formatted_date.encode('utf-8')
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = formatted_date.encode('utf-8')
        exif_dict['0th'][piexif.ImageIFD.DateTime] = formatted_date.encode('utf-8')

        exif_bytes = piexif.dump(exif_dict)
        img.save(file_path, "jpeg", exif=exif_bytes)

        return 'updated'
    except UnidentifiedImageError as e:
        logger.error(Fore.RED + f"Cannot identify image file {file_path}: {e}")
        return 'failed'
    except Exception as e:
        logger.error(Fore.RED + f"Error processing {file_path}: {e}")
        return 'failed'


def process_directory(directory, override, recursive, mode, snapchat_date=None):
    total_files = 0
    whatsapp_images = 0
    snapchat_files = 0
    metadata_exists = 0
    metadata_updated = 0
    update_failed = 0

    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            total_files += 1

            if mode == "whatsapp" and is_whatsapp_image(filename):
                whatsapp_images += 1
                result = update_image_metadata(file_path)
                if result == 'exists':
                    metadata_exists += 1
                elif result == 'updated':
                    metadata_updated += 1
                elif result == 'failed':
                    update_failed += 1

            elif mode == "snapchat" and is_snapchat_file(filename):
                snapchat_files += 1
                if filename.lower().endswith('.mp4'):
                    result = update_video_metadata(file_path, snapchat_date)
                else:
                    result = update_image_metadata(file_path, snapchat_date)
                if result == 'exists':
                    metadata_exists += 1
                elif result == 'updated':
                    metadata_updated += 1
                elif result == 'failed':
                    update_failed += 1

        if not recursive:
            break

    return total_files, (whatsapp_images if mode == "whatsapp" else snapchat_files), metadata_exists, metadata_updated, update_failed


def main():
    logger.info(Fore.CYAN + "Welcome to the Image Metadata Updater!")
    mode = prompt_for_input("Select mode (whatsapp/snapchat): ", ["whatsapp", "snapchat"])
    directory = prompt_for_input("Enter the directory of images/videos: ")

    # Check if the directory exists
    if not os.path.isdir(directory):
        logger.error(Fore.RED + f"The directory '{directory}' does not exist. Please check the path and try again.")
        return

    override = prompt_for_input("Override original files without creating a backup? (yes/no): ", ["yes", "no"]) == "yes"
    recursive = prompt_for_input("Recursively process images in subdirectories? (yes/no): ", ["yes", "no"]) == "yes"
    snapchat_date = None

    if mode == "snapchat":
        snapchat_date = prompt_for_date("Enter the date for Snapchat images (YYYY:MM:DD): ")

    if not override:
        backup_dir = backup_directory(directory)
        logger.info(Fore.GREEN + f"Backup created successfully at '{backup_dir}'.")
        verify_backup(directory, backup_dir)

    stats = process_directory(directory, override, recursive, mode, snapchat_date)

    # Log the summary of the operation
    total_files, processed_files, metadata_exists, metadata_updated, update_failed = stats
    logger.info(Fore.GREEN + "Operation completed.")
    logger.info(Fore.GREEN + f"Total files encountered: {total_files}")

    if mode == "whatsapp":
        logger.info(Fore.GREEN + f"WhatsApp images processed: {processed_files}")
    elif mode == "snapchat":
        logger.info(Fore.GREEN + f"Snapchat files processed: {processed_files}")

    logger.info(Fore.GREEN + f"Files with existing metadata: {metadata_exists}")
    logger.info(Fore.GREEN + f"Files whose metadata was updated: {metadata_updated}")
    if update_failed > 0:
        logger.error(Fore.RED + f"Files that failed to update: {update_failed}")


if __name__ == "__main__":
    main()
