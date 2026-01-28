import os
import json
import time

# Change this to your project root if running from elsewhere
PROJECT_ROOT = os.getcwd()  
OUTPUT_FILE = "project_contents.json"

# Define file extensions you want to include (text/code files)
TEXT_FILE_EXTENSIONS = {
    ".py", ".html", ".css", ".js", ".txt", ".json", ".md", ".csv", ".yml", ".yaml"
}

# Folders to skip
SKIP_FOLDERS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'staticfiles', '.pytest_cache', 'db.sqlite3'}

project_data = {}
files_processed = 0
errors = 0

for root, dirs, files in os.walk(PROJECT_ROOT):
    # Skip hidden folders and problematic ones
    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_FOLDERS]
    
    for file in files:
        file_path = os.path.join(root, file)
        _, ext = os.path.splitext(file)
        
        if ext.lower() in TEXT_FILE_EXTENSIONS:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    relative_path = os.path.relpath(file_path, PROJECT_ROOT)
                    project_data[relative_path] = content
                    files_processed += 1
                    print(f"✓ {relative_path}")
            except UnicodeDecodeError:
                print(f"⊘ Skipped (encoding): {os.path.relpath(file_path, PROJECT_ROOT)}")
                errors += 1
            except Exception as e:
                print(f"⊘ Error: {os.path.relpath(file_path, PROJECT_ROOT)} - {str(e)[:50]}")
                errors += 1

# Write all collected contents to JSON
with open(OUTPUT_FILE, "w", encoding="utf-8") as out_file:
    json.dump(project_data, out_file, indent=2)

print(f"\n✅ Project contents saved to {OUTPUT_FILE}")
print(f"📊 Files processed: {files_processed}, Errors: {errors}")
