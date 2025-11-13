import os
import zipfile
import shutil
import subprocess

# === CONFIG ===
FUNCTIONS = ["generate_upload", "pdf_extractor", "text_translator", "status_checker"]
OUTPUT_DIR = "artifacts"

# === HELPER FUNCTION ===
def zip_directory(source_dir, zip_path):
    """Compresses source_dir into a zip file located at zip_path."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, source_dir)
                zipf.write(abs_path, rel_path)

# === MAIN SCRIPT ===
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

for func in FUNCTIONS:
    func_path = os.path.join(os.getcwd(), "app", func)
    temp_dir = os.path.join(func_path, "build")

    # 1 Build klasörünü sıfırla
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    print(f"\n Bundling Lambda: {func}")

    # 2 Fonksiyon dosyasını kopyala
    shutil.copy(os.path.join(func_path, "lambda_function.py"), temp_dir)

    # 3 Gereksinimleri yükle
    req_path = os.path.join(func_path, "requirements.txt")
    if os.path.exists(req_path):
        print(f" Installing dependencies for {func}...")
        subprocess.run(
            ["pip3", "install", "-r", req_path, "-t", temp_dir],
            check=True
        )

    # 4 __pycache__ klasörlerini temizle
    for root, dirs, _ in os.walk(temp_dir):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d))

    # 5 ZIP oluştur
    zip_name = f"{func}.zip"
    zip_path = os.path.join(OUTPUT_DIR, zip_name)
    zip_directory(temp_dir, zip_path)

    print(f" Created {zip_name} → {zip_path}")

    # 6 Build klasörünü temizle
    shutil.rmtree(temp_dir)

print("\n All Lambda functions bundled successfully!")

