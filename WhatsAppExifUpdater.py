import os
import subprocess
import platform
import argparse
from PIL import Image
import piexif
from datetime import datetime
import re
import shutil
from tqdm import tqdm
import hashlib

# Regex pattern to identify WhatsApp image filenames
WHATSAPP_IMAGE_PATTERN = r"^IMG-\d{8}-WA\d{4}\.jpg$"

def is_whatsapp_image(filename):
    return re.match(WHATSAPP_IMAGE_PATTERN, filename) is not None

def extract_date_from_filename(filename):
    # Extracting the date part from the filename
    date_str = filename[4:12]  # Assuming the format IMG-YYYYMMDD-WA####
    return datetime.strptime(date_str, '%Y%m%d')

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
                print(f"File missing in backup: {dst_file}")
                continue

            src_checksum = file_checksum(src_file)
            dst_checksum = file_checksum(dst_file)

            if src_checksum != dst_checksum or os.path.getsize(src_file) != os.path.getsize(dst_file):
                print(f"File mismatch found: {file}")

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

def update_image_metadata(file_path):
    try:
        img = Image.open(file_path)
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
            if piexif.ExifIFD.DateTimeOriginal in exif_dict['Exif']:
                return 'exists'
        else:
            exif_dict = {'Exif': {}, '0th': {}, '1st': {}, 'thumbnail': None, 'GPS': {}}

        date = extract_date_from_filename(os.path.basename(file_path))
        formatted_date = date.strftime("%Y:%m:%d %H:%M:%S")

        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = formatted_date.encode('utf-8')
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = formatted_date.encode('utf-8')
        exif_dict['0th'][piexif.ImageIFD.DateTime] = formatted_date.encode('utf-8')

        exif_bytes = piexif.dump(exif_dict)
        img.save(file_path, "jpeg", exif=exif_bytes)

        return 'updated'
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 'failed'

def process_directory(directory, override, recursive):
    total_images = 0
    whatsapp_images = 0
    non_whatsapp_images = 0
    metadata_exists = 0
    metadata_updated = 0
    update_failed = 0

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.endswith((".jpg", ".jpeg", ".png", ".heic")):
                total_images += 1
                if is_whatsapp_image(filename):
                    whatsapp_images += 1
                    result = update_image_metadata(os.path.join(root, filename))
                    if result == 'exists':
                        metadata_exists += 1
                    elif result == 'updated':
                        metadata_updated += 1
                    elif result == 'failed':
                        update_failed += 1
                else:
                    non_whatsapp_images += 1
        if not recursive:
            break

    return total_images, whatsapp_images, non_whatsapp_images, metadata_exists, metadata_updated, update_failed

def main(directory, override, recursive):
    if not override:
        print(f"Creating backup of the directory '{directory}'...")
        backup_dir = backup_directory(directory)
        print(f"Backup created successfully.")

        print("Verifying backup integrity...")
        verify_backup(directory, backup_dir)
        print("Verification completed.")

    stats = process_directory(directory, override, recursive)

    print(f"Total images encountered: {stats[0]}")
    print(f"WhatsApp images: {stats[1]}")
    print(f"Non-WhatsApp images: {stats[2]}")
    print(f"Images with existing metadata: {stats[3]}")
    print(f"Images whose metadata was updated: {stats[4]}")
    print(f"Images that failed to update: {stats[5]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update image metadata with date from filename for WhatsApp images only if the date created metadata does not already exist.")
    parser.add_argument('-d', '--directory', type=str, required=True, help='Directory of images')
    parser.add_argument('-r', '--recursive', action='store_true', help="Recursively process images in subdirectories.")
    parser.add_argument('--override', action='store_true', help="Override original images without creating a backup.")

    args = parser.parse_args()
    main(args.directory, args.override, args.recursive)
