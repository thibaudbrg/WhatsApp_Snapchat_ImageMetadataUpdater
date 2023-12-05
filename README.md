# WhatsAppImageMetadataUpdater

WhatsAppImageMetadataUpdater is a Python script designed to update the EXIF metadata of images following the WhatsApp naming convention (e.g., `IMG-YYYYMMDD-WA####.jpg`). It includes features for creating backups of images, performing integrity checks, and handling images both in a specific directory and recursively in subdirectories.

## Features

- Update EXIF metadata (date) in WhatsApp images based on filenames.
- Create backups of original images before modification.
- Perform integrity checks (checksum and file size) post-backup.
- Process images in a specified directory or recursively in subdirectories.
- Handle images on different operating systems (Windows, Linux/WSL, macOS).

## Requirements

- Python 3
- Pillow (Python Imaging Library Fork)
- tqdm (for progress bar visualization)

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/WhatsAppImageMetadataUpdater.git
```
2. Navigate to the cloned directory:
```
cd WhatsAppImageMetadataUpdater
```
3. Install the required packages:
```
pip install -r requirements.txt
```

## Usage

Run the script from the command line, providing the necessary arguments:
```
python filename_date_to_metadata.py -d /path/to/images [-r] [--override]
```

- `-d`, `--directory` (required): Specify the directory of images.
- `-r`, `--recursive`: Process images in subdirectories recursively.
- `--override`: Override original images without creating a backup.

### Example

Updating images in a specific directory:

```
python filename_date_to_metadata.py -d ./my_images
```

Updating images recursively in a directory and its subdirectories:

```
python filename_date_to_metadata.py -d ./my_images -r
```

## Contributing

Contributions to improve the script or add new features are welcome. Please feel free to submit issues and pull requests.

## License

[MIT License]


