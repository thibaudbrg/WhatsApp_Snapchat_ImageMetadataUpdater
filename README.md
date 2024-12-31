# WhatsApp, Snapchat & Instagram Image Metadata Updater 

## Overview 

The WhatsApp, Snapchat & Instagram Image Metadata Updater is a Python utility designed to update the metadata of images and videos received from WhatsApp, Snapchat, and Instagram. This tool is particularly useful for organizing your media files by correcting or adding the original creation date in the metadata, which might have been stripped or altered during the transfer process.

## Features 
 
- **Metadata Updating:**  Updates the creation date metadata of images and videos from WhatsApp, Snapchat, and Instagram.
 
- **Backup Creation:**  Offers an option to create a backup of the original files before modifying them.
 
- **Recursive Processing:**  Can process files in the specified directory and optionally in its subdirectories.
 
- **Cross-Platform Compatibility:**  Works on Windows, Linux, and macOS.

## Prerequisites 

Before you begin, ensure you have the following installed on your system:

- Python 3.6 or later

- Pip (Python package manager)

## Installation 
 
1. Clone this repository to your local machine or download the ZIP file:


```bash
git clone https://github.com/thibaudbrg/WhatsApp_Snapchat_ImageMetadataUpdater.git
```
 
2. Navigate to the project directory:


```bash
cd WhatsApp_Snapchat_ImageMetadataUpdater
```
 
3. Install the required Python packages:


```bash
pip install -r requirements.txt
```

## Usage 

To use the WhatsApp, Snapchat & Instagram Image Metadata Updater, follow these steps:
 
1. Open your terminal or command prompt.
 
2. Navigate to the project directory.
 
3. Run the script with the following command:


```bash
python WA_Snap_ExifUpdater.py
```
 
4. Follow the on-screen prompts to select the operation mode (WhatsApp, Snapchat, or Instagram), specify the directory of images/videos to process, and other options as prompted.

### Options 
 
- **Mode Selection:**  Choose whether to process WhatsApp images, Snapchat files, or Instagram files.
 
- **Directory Selection:**  Specify the path to the directory containing the media files to be processed.
 
- **Backup Creation:**  Decide whether to create a backup of the original files before making changes.
 
- **Recursive Processing:**  Choose whether to recursively process files in subdirectories.

## Contributing 

Contributions to the WhatsApp, Snapchat & Instagram Image Metadata Updater are welcome! If you have a feature request, bug report, or a pull request, please feel free to contribute.

## License 

This project is licensed under the MIT License.
