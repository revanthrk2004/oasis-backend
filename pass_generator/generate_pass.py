import os
import zipfile
import json
from pathlib import Path

PASS_FOLDER = Path(__file__).parent
PASS_FILES = ['pass.json', 'Oasis_Logo_Green_RGB.png', 'Oasis_Logo_Green_RGB.png']
OUTPUT_FILE = PASS_FOLDER / 'OasisCard.pkpass'

def create_fake_signature():
    # For real usage, use OpenSSL and your Apple certificate to sign the manifest
    return b'fake-signature'

def generate_pass():
    print("📦 Generating .pkpass...")

    # Load and check pass.json
    pass_json = PASS_FOLDER / 'pass.json'
    if not pass_json.exists():
        print("❌ pass.json not found")
        return

    with open(pass_json, 'r') as f:
        pass_data = json.load(f)
        print("✅ Loaded pass.json")

    # Create zip file
    with zipfile.ZipFile(OUTPUT_FILE, 'w') as pkpass:
        # Add required files
        for file_name in PASS_FILES:
            path = PASS_FOLDER / file_name
            if path.exists():
                pkpass.write(path, arcname=file_name)
                print(f"✅ Added {file_name}")
            else:
                print(f"⚠️ Skipped {file_name} (not found)")

        # Create fake signature (replace with real signing later)
        pkpass.writestr('signature', create_fake_signature())

    print(f"✅ .pkpass created at {OUTPUT_FILE}")

if __name__ == '__main__':
    generate_pass()
