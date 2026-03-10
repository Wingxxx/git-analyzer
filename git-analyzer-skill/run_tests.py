#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本

提供便捷的测试运行命令。

WING
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type='all', verbose=False, coverage=True, markers=None):
    """
    运行测试。
    
    Args:
        test_type: 测试类型 ('all', 'unit', 'integration', 'performance')
        verbose: 是否详细输出
        coverage: 是否生成覆盖率报告
        markers: 额外的标记
    """
    # 切换到项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 构建pytest命令
    cmd = ['python', '-m', 'pytest']
    
    # 添加测试类型过滤
    if test_type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
    elif test_type == 'performance':
        cmd.extend(['-m', 'performance'])
    
    # 添加额外标记
    if markers:
        cmd.extend(['-m', markers])
    
    # 添加详细输出
    if verbose:
        cmd.append('-v')
    
    # 添加覆盖率
    if coverage:
        cmd.extend([
            '--cov=scripts',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov'
        ])
    
    # 运行测试
    print(f"运行命令: {' '.join(cmd)}")
    print("=" * 80)
    
    result = subprocess.run(cmd)
    
    return result.returncode


def run_quick_tests():
    """运行快速测试（跳过慢速测试）。"""
    cmd = [
        'python', '-m', 'pytest',
        '-v',
        '-m', 'not slow',
        '--cov=scripts',
        '--cov-report=term-missing'
    ]
    
    print("运行快速测试...")
    print("=" * 80)
    
    result = subprocess.run(cmd)
    return result.returncode


def run_coverage_report():
    """生成覆盖率报告。"""
    cmd = [
        'python', '-m', 'pytest',
        '--cov=scripts',
        '--cov-report=html:htmlcov',
        '--cov-report=term'
    ]
    
    print("生成覆盖率报告...")
    print("=" * 80)
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n覆盖率报告已生成: htmlcov/index.html")
    
    return result.returncode


def clean_test_artifacts():
    """清理测试产物。"""
    import shutil
    
    artifacts = [
        'htmlcov',
        '.coverage',
        '.pytest_cache',
        '__pycache__',
        'tests/__pycache__'
    ]
    
    for artifact in artifacts:
        path = Path(artifact)
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"已删除: {artifact}")


def main():
    """主函数。"""
    parser = argparse.ArgumentParser(
        description='Git Analyzer 测试运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行所有测试
  python run_tests.py
  
  # 运行单元测试
  python run_tests.py --type unit
  
  # 运行集成测试
  python run_tests.py --type integration
  
  # 运行性能测试
  python run_tests.py --type performance
  
  # 运行快速测试（跳过慢速测试）
  python run_tests.py --quick
  
  # 生成覆盖率报告
  python run_tests.py --coverage
  
  # 清理测试产物
  python run_tests.py --clean
        """
    )
    
    parser.add_argument(
        '--type',
        choices=['all', 'unit', 'integration', 'performance'],
        default='all',
        help='测试类型'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出'
    )
    
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='不生成覆盖率报告'
    )
    
    parser.add_argument(
        '-m', '--markers',
        help='额外的pytest标记'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='运行快速测试（跳过慢速测试）'
    )
    
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='仅生成覆盖率报告'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='清理测试产物'
    )
    
    args = parser.parse_args()
    
    # 处理特殊命令
    if args.clean:
        clean_test_artifacts()
        return 0
    
    if args.coverage:
        return run_coverage_report()
    
    if args.quick:
        return run_quick_tests()
    
    # 运行常规测试
    return run_tests(
        test_type=args.type,
        verbose=args.verbose,
        coverage=not args.no_coverage,
        markers=args.markers
    )


if __name__ == '__main__':
    sys.exit(main())
