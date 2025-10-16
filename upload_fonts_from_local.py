import os
import frappe
from frappe.utils.file_manager import save_file

# ========= CONFIG ==========
FONTS_BASE_PATH = "/home/frappe/frappe-bench/Fonts"  # local folder where fonts are stored
DOCTYPE = "Font Library"                # your Doctype name
ATTACH_FIELD = "font_file"              # attach fieldname in Doctype
FONT_NAME_FIELD = "font_name"           # field for the font name
VALID_EXTENSIONS = (".ttf", ".otf", ".woff", ".woff2")  # supported font types
# ===========================


def upload_from_local_folder():
    """
    Uploads all font files from a local directory (and subdirectories)
    into the Font Library doctype in the current Frappe site.
    """

    if not frappe.db:
        frappe.connect()

    print(f"📁 Scanning folder: {FONTS_BASE_PATH}\n")

    # Recursively find font files
    font_files = []
    for root, dirs, files in os.walk(FONTS_BASE_PATH):
        for file in files:
            if file.lower().endswith(VALID_EXTENSIONS):
                font_files.append(os.path.join(root, file))

    print(f"✅ Found {len(font_files)} font files to process.\n")

    for file_path in font_files:
        try:
            filename = os.path.basename(file_path)
            font_name = os.path.splitext(filename)[0]

            # Skip if font already exists
            if frappe.db.exists(DOCTYPE, {FONT_NAME_FIELD: font_name}):
                print(f"⚠️  Skipping existing font: {font_name}")
                continue

            # Read file
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Create new record
            doc = frappe.new_doc(DOCTYPE)
            doc.set(FONT_NAME_FIELD, font_name)
            doc.insert(ignore_permissions=True)

            # Attach file
            file_doc = save_file(filename, file_content, DOCTYPE, doc.name, is_private=0)

            # Link to the attachment field
            doc.set(ATTACH_FIELD, file_doc.file_url)
            doc.save(ignore_permissions=True)
            frappe.db.commit()

            print(f"✅ Uploaded: {font_name}")

        except Exception as e:
            frappe.db.rollback()
            print(f"❌ Error processing {file_path}: {e}")

    frappe.destroy()
    print("\n🎉 All local fonts processed successfully (uploaded + skipped).")


if __name__ == "__main__":
    upload_from_local_folder()
