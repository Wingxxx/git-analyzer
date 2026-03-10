#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Analyzer Skill 构建脚本

一键同步最新文件到安装目录并打包。

使用方法:
    python build_skill.py              # 同步文件到安装目录
    python build_skill.py --zip        # 同步并打包为zip
    python build_skill.py --output ./dist  # 指定输出目录
    python build_skill.py --clean      # 清理安装目录后重新构建

WING
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_manifest(manifest_path: str) -> Dict:
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compare_files(source_path: str, dest_path: str) -> bool:
    if not os.path.exists(dest_path):
        return False
    return get_file_hash(source_path) == get_file_hash(dest_path)


def copy_file_if_changed(source_path: str, dest_path: str) -> Tuple[bool, str]:
    if compare_files(source_path, dest_path):
        return False, "unchanged"
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    shutil.copy2(source_path, dest_path)
    return True, "updated"


def sync_directory(
    source_dir: str,
    dest_dir: str,
    patterns: List[str],
    exclude_patterns: List[str]
) -> Dict[str, int]:
    stats = {"copied": 0, "skipped": 0, "unchanged": 0, "errors": 0}
    
    import fnmatch
    
    for pattern in patterns:
        if pattern.startswith("*"):
            for root, dirs, files in os.walk(source_dir):
                dirs[:] = [d for d in dirs if not any(
                    fnmatch.fnmatch(d, ex) for ex in exclude_patterns
                )]
                
                for file in files:
                    if fnmatch.fnmatch(file, pattern):
                        source_path = os.path.join(root, file)
                        rel_path = os.path.relpath(source_path, source_dir)
                        dest_path = os.path.join(dest_dir, rel_path)
                        
                        try:
                            copied, status = copy_file_if_changed(source_path, dest_path)
                            if copied:
                                stats["copied"] += 1
                                print(f"  ✓ 复制: {rel_path}")
                            else:
                                stats["unchanged"] += 1
                        except Exception as e:
                            stats["errors"] += 1
                            print(f"  ✗ 错误: {rel_path} - {e}")
        else:
            source_path = os.path.join(source_dir, pattern)
            if os.path.exists(source_path):
                dest_path = os.path.join(dest_dir, pattern)
                try:
                    copied, status = copy_file_if_changed(source_path, dest_path)
                    if copied:
                        stats["copied"] += 1
                        print(f"  ✓ 复制: {pattern}")
                    else:
                        stats["unchanged"] += 1
                except Exception as e:
                    stats["errors"] += 1
                    print(f"  ✗ 错误: {pattern} - {e}")
    
    return stats


def clean_output_dir(output_dir: str, preserve: List[str]):
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        if item in preserve:
            print(f"  保留: {item}")
            continue
        
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
            print(f"  删除目录: {item}/")
        else:
            os.remove(item_path)
            print(f"  删除文件: {item}")


def generate_version_info(output_dir: str, manifest: Dict):
    version_info = {
        "name": manifest["name"],
        "version": manifest["version"],
        "build_time": datetime.now().isoformat(),
        "author": manifest.get("author", "WING"),
        "files": []
    }
    
    for root, dirs, files in os.walk(output_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, output_dir)
            version_info["files"].append({
                "path": rel_path,
                "hash": get_file_hash(file_path),
                "size": os.path.getsize(file_path)
            })
    
    version_path = os.path.join(output_dir, "VERSION.json")
    with open(version_path, 'w', encoding='utf-8') as f:
        json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    print(f"  ✓ 生成版本信息: VERSION.json")
    return version_path


def create_zip_package(output_dir: str, zip_name: Optional[str] = None):
    if zip_name is None:
        zip_name = f"{os.path.basename(output_dir)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    zip_path = shutil.make_archive(zip_name, 'zip', output_dir)
    print(f"\n📦 打包完成: {zip_path}")
    print(f"   大小: {os.path.getsize(zip_path) / 1024:.2f} KB")
    return zip_path


def build_skill(
    manifest_path: str = "skill_manifest.json",
    output_dir: Optional[str] = None,
    create_zip: bool = False,
    clean: bool = False
):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    if not os.path.exists(manifest_path):
        print(f"❌ 错误: 找不到配置文件 {manifest_path}")
        return False
    
    manifest = load_manifest(manifest_path)
    
    source_dir = manifest["source_dir"]
    dest_dir = output_dir or manifest["output_dir"]
    preserve = manifest.get("preserve_output", [])
    
    print(f"\n{'='*60}")
    print(f"Git Analyzer Skill 构建工具")
    print(f"{'='*60}")
    print(f"源目录: {source_dir}")
    print(f"目标目录: {dest_dir}")
    print(f"版本: {manifest['version']}")
    print(f"{'='*60}\n")
    
    if not os.path.exists(source_dir):
        print(f"❌ 错误: 源目录不存在 {source_dir}")
        return False
    
    if clean and os.path.exists(dest_dir):
        print("🧹 清理目标目录...")
        clean_output_dir(dest_dir, preserve)
    
    os.makedirs(dest_dir, exist_ok=True)
    
    total_stats = {"copied": 0, "skipped": 0, "unchanged": 0, "errors": 0}
    
    include = manifest.get("include", {})
    exclude = manifest.get("exclude", [])
    
    if "root" in include:
        print("\n📁 同步根目录文件...")
        stats = sync_directory(source_dir, dest_dir, include["root"], exclude)
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)
    
    if "scripts" in include:
        print("\n📁 同步 scripts/ 目录...")
        scripts_dest = os.path.join(dest_dir, "scripts")
        scripts_source = os.path.join(source_dir, "scripts")
        os.makedirs(scripts_dest, exist_ok=True)
        stats = sync_directory(scripts_source, scripts_dest, include["scripts"], exclude)
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)
    
    if "references" in include:
        print("\n📁 同步 references/ 目录...")
        refs_dest = os.path.join(dest_dir, "references")
        refs_source = os.path.join(source_dir, "references")
        os.makedirs(refs_dest, exist_ok=True)
        stats = sync_directory(refs_source, refs_dest, include["references"], exclude)
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)
    
    print("\n📝 生成版本信息...")
    generate_version_info(dest_dir, manifest)
    
    print(f"\n{'='*60}")
    print("构建统计:")
    print(f"  复制文件: {total_stats['copied']}")
    print(f"  未变文件: {total_stats['unchanged']}")
    print(f"  错误数量: {total_stats['errors']}")
    print(f"{'='*60}")
    
    if create_zip:
        create_zip_package(dest_dir)
    
    print("\n✅ 构建完成!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Git Analyzer Skill 构建工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python build_skill.py              # 同步文件到安装目录
    python build_skill.py --zip        # 同步并打包为zip
    python build_skill.py --clean      # 清理后重新构建
    python build_skill.py --output ./dist/git-analyzer
        """
    )
    
    parser.add_argument(
        "--manifest", "-m",
        default="skill_manifest.json",
        help="配置文件路径 (默认: skill_manifest.json)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="输出目录 (默认使用配置文件中的设置)"
    )
    
    parser.add_argument(
        "--zip", "-z",
        action="store_true",
        help="打包为zip文件"
    )
    
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="清理目标目录后重新构建"
    )
    
    args = parser.parse_args()
    
    success = build_skill(
        manifest_path=args.manifest,
        output_dir=args.output,
        create_zip=args.zip,
        clean=args.clean
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
