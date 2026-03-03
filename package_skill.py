#!/usr/bin/env python3
import os
import zipfile

SKILL_NAME = "git-analyzer"
SKILL_DIR = "git-analyzer-skill"
OUTPUT_FILE = f"{SKILL_NAME}.skill"

with zipfile.ZipFile(OUTPUT_FILE, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(SKILL_DIR):
        for file in files:
            if file.startswith('.') or file.endswith('~'):
                continue
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, SKILL_DIR)
            zf.write(file_path, relative_path)

print(f"打包完成！输出文件: {OUTPUT_FILE}")