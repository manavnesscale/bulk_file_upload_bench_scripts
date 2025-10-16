import os
import tempfile
import frappe
import gdown
from frappe.utils.file_manager import save_file

# ========= CONFIG ==========
SITE_NAME = "ecom-dev.nesscale.com"   # your frappe site
DOCTYPE = "Font Library"             # your Doctype name
DRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1le2Zw4uQx1_Kx5Lp8BPpX3v-15DOSTji"  # your Google Drive folder link
ATTACH_FIELD = "font_file"   # attach fieldname in Font Doctype
FONT_NAME_FIELD = "font_name"  # field for the font name
# ===========================


def download_drive_folder(folder_url):
    """
    Downloads all files from a Google Drive folder to a temporary directory.
    Skips problematic files automatically.
    """
    temp_dir = tempfile.mkdtemp(prefix="drive_download_")
    print(f"📂 Downloading files from Google Drive folder into: {temp_dir}")

    try:
        # gdown 5.x+ has retry support for missing files
        gdown.download_folder(url=folder_url, output=temp_dir, quiet=False, use_cookies=False)
    except Exception as e:
        print(f"⚠️  Folder-level error during download: {e}")
        print("Continuing with whatever files were successfully downloaded...")

    return temp_dir


def upload_to_frappe(folder_path):
    """
    Uploads all files in folder_path to Frappe, creating new Font records
    with the attached file in the `font_file` field.
    """
    frappe.init(site=SITE_NAME)
    frappe.connect()

    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    print(f"✅ Found {len(files)} files to upload.\n")

    for filename in files:
        try:
            file_path = os.path.join(folder_path, filename)
            name_without_ext = os.path.splitext(filename)[0]

            existing = frappe.db.exists(DOCTYPE, {FONT_NAME_FIELD: name_without_ext})
            if existing:
                print(f"⚠️ Skipping {filename} — record already exists ({existing})")
                continue

            with open(file_path, "rb") as f:
                file_content = f.read()

            # Create new Font record
            doc = frappe.new_doc(DOCTYPE)
            doc.set(FONT_NAME_FIELD, name_without_ext)
            doc.insert(ignore_permissions=True)

            # ✅ Correct way to attach file
            file_doc = save_file(filename, file_content, DOCTYPE, doc.name, is_private=0)

            # Link file to field
            doc.set(ATTACH_FIELD, file_doc.file_url)
            doc.save(ignore_permissions=True)

            frappe.db.commit()
            print(f"✅ Uploaded and linked: {filename}")

        except Exception as e:
            frappe.db.rollback()
            print(f"❌ Error processing {filename}: {e}")
            continue  # Skip this file and move to the next one

    frappe.destroy()
    print("\n🎉 All files processed! (successful uploads + skipped errors)\n")


def upload_from_drive():
    folder_path = download_drive_folder(DRIVE_FOLDER_URL)
    if folder_path:
        upload_to_frappe(folder_path)
    else:
        print("❌ No files downloaded. Please check Drive link or permissions.")


if __name__ == "__main__":
    upload_from_drive()
