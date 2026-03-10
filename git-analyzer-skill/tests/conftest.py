#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pytest配置文件

提供测试fixtures和共享配置。

WING
"""

import os
import sys
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta

# 添加scripts目录到Python路径
scripts_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
sys.path.insert(0, scripts_dir)


# ==================== Git仓库Fixtures ====================

@pytest.fixture
def temp_git_repo():
    """
    创建临时Git仓库用于测试。
    
    Yields:
        str: 临时Git仓库路径
    """
    temp_dir = tempfile.mkdtemp()
    repo_path = os.path.join(temp_dir, 'test_repo')
    os.makedirs(repo_path)
    
    try:
        # 初始化Git仓库
        os.system(f'cd "{repo_path}" && git init > /dev/null 2>&1')
        os.system(f'cd "{repo_path}" && git config user.email "test@test.com"')
        os.system(f'cd "{repo_path}" && git config user.name "Test User"')
        
        yield repo_path
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def git_repo_with_commits(temp_git_repo):
    """
    创建包含多个提交的Git仓库。
    
    Args:
        temp_git_repo: 临时Git仓库fixture
        
    Yields:
        tuple: (仓库路径, 提交列表)
    """
    repo_path = temp_git_repo
    commits = []
    
    # 创建多个提交
    for i in range(5):
        # 创建测试文件
        test_file = os.path.join(repo_path, f'test_{i}.py')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(f'"""测试文件 {i}"""\n\ndef test_{i}():\n    pass\n')
        
        # 提交
        os.system(f'cd "{repo_path}" && git add . > /dev/null 2>&1')
        os.system(f'cd "{repo_path}" && git commit -m "Add test file {i}" > /dev/null 2>&1')
        
        commits.append({
            'index': i,
            'file': test_file,
            'message': f'Add test file {i}'
        })
    
    yield repo_path, commits


@pytest.fixture
def git_repo_with_branches(temp_git_repo):
    """
    创建包含多个分支的Git仓库。
    
    Args:
        temp_git_repo: 临时Git仓库fixture
        
    Yields:
        tuple: (仓库路径, 分支列表)
    """
    repo_path = temp_git_repo
    branches = ['main']
    
    # 创建初始提交
    test_file = os.path.join(repo_path, 'initial.py')
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write('# Initial file\n')
    
    os.system(f'cd "{repo_path}" && git add . > /dev/null 2>&1')
    os.system(f'cd "{repo_path}" && git commit -m "Initial commit" > /dev/null 2>&1')
    
    # 创建多个分支
    for branch_name in ['feature-1', 'feature-2', 'bugfix-1']:
        os.system(f'cd "{repo_path}" && git checkout -b {branch_name} > /dev/null 2>&1')
        branches.append(branch_name)
    
    # 切回main分支
    os.system(f'cd "{repo_path}" && git checkout main > /dev/null 2>&1')
    
    yield repo_path, branches


# ==================== 代码文件Fixtures ====================

@pytest.fixture
def sample_python_file():
    """
    创建示例Python代码文件。
    
    Yields:
        str: Python文件路径
    """
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, 'sample.py')
    
    code_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例Python文件

用于测试代码质量评估功能。
"""

import os
import sys
from typing import List, Dict, Optional


class SampleClass:
    """示例类。"""
    
    def __init__(self, name: str):
        """初始化方法。
        
        Args:
            name: 名称。
        """
        self.name = name
        self.data = []
    
    def add_data(self, item: str) -> None:
        """添加数据。
        
        Args:
            item: 数据项。
        """
        if item:
            self.data.append(item)
    
    def get_data(self) -> List[str]:
        """获取数据。
        
        Returns:
            数据列表。
        """
        return self.data


def calculate_sum(numbers: List[int]) -> int:
    """计算数字列表的和。
    
    Args:
        numbers: 数字列表。
    
    Returns:
        总和。
    """
    total = 0
    for num in numbers:
        total += num
    return total


def main():
    """主函数。"""
    sample = SampleClass("test")
    sample.add_data("item1")
    sample.add_data("item2")
    
    numbers = [1, 2, 3, 4, 5]
    total = calculate_sum(numbers)
    
    print(f"Total: {total}")


if __name__ == '__main__':
    main()
'''
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        yield file_path
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_bad_python_file():
    """
    创建质量较差的Python代码文件。
    
    Yields:
        str: Python文件路径
    """
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, 'bad_sample.py')
    
    # 故意编写质量较差的代码
    code_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os,sys
from typing import *

class a:
    def __init__(s,n):
        s.n=n
        s.d=[]
    def ad(s,i):
        if i:
            s.d.append(i)
    def gd(s):
        return s.d

def cs(n):
    t=0
    for x in n:
        t+=x
    return t

def main():
    o=a("test")
    o.ad("i1")
    o.ad("i2")
    n=[1,2,3,4,5]
    t=cs(n)
    print(t)

if __name__=='__main__':
    main()
'''
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        yield file_path
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def syntax_error_file():
    """
    创建有语法错误的Python文件。
    
    Yields:
        str: Python文件路径
    """
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, 'syntax_error.py')
    
    # 故意编写有语法错误的代码
    code_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def test(:
    pass

if __name__ == '__main__':
    test()
'''
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code_content)
        
        yield file_path
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def large_python_file():
    """
    创建大型Python文件（用于性能测试）。
    
    Yields:
        str: Python文件路径
    """
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, 'large_file.py')
    
    # 生成大型文件
    lines = ['#!/usr/bin/env python3', '# -*- coding: utf-8 -*-', '']
    lines.append('"""大型测试文件。"""')
    lines.append('')
    
    # 生成大量函数
    for i in range(100):
        lines.append(f'def function_{i}():')
        lines.append(f'    """函数 {i}。"""')
        lines.append(f'    result = 0')
        for j in range(10):
            lines.append(f'    result += {j}')
        lines.append(f'    return result')
        lines.append('')
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        yield file_path
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ==================== 配置Fixtures ====================

@pytest.fixture
def test_config():
    """
    测试配置。
    
    Returns:
        dict: 测试配置字典
    """
    return {
        'test_author': 'Test User',
        'test_email': 'test@test.com',
        'test_repo_name': 'test_repo',
        'test_branch': 'main',
        'test_commit_message': 'Test commit',
        'timeout': 30,
        'max_file_size': 10 * 1024 * 1024,  # 10MB
    }


@pytest.fixture
def date_range():
    """
    测试日期范围。
    
    Returns:
        tuple: (开始日期, 结束日期)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    return start_date, end_date


# ==================== 性能测试Fixtures ====================

@pytest.fixture
def performance_test_repo():
    """
    创建用于性能测试的大型Git仓库。
    
    Yields:
        str: 仓库路径
    """
    temp_dir = tempfile.mkdtemp()
    repo_path = os.path.join(temp_dir, 'perf_repo')
    os.makedirs(repo_path)
    
    try:
        # 初始化Git仓库
        os.system(f'cd "{repo_path}" && git init > /dev/null 2>&1')
        os.system(f'cd "{repo_path}" && git config user.email "perf@test.com"')
        os.system(f'cd "{repo_path}" && git config user.name "Perf User"')
        
        # 创建大量提交
        for i in range(50):
            # 创建Python文件
            py_file = os.path.join(repo_path, f'module_{i}.py')
            with open(py_file, 'w', encoding='utf-8') as f:
                f.write(f'"""模块 {i}"""\n\n')
                for j in range(20):
                    f.write(f'def func_{j}():\n    pass\n\n')
            
            # 创建文档文件
            if i % 5 == 0:
                doc_file = os.path.join(repo_path, f'doc_{i}.md')
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write(f'# 文档 {i}\n\n内容描述...\n')
            
            # 提交
            os.system(f'cd "{repo_path}" && git add . > /dev/null 2>&1')
            os.system(f'cd "{repo_path}" && git commit -m "Add module {i}" > /dev/null 2>&1')
        
        yield repo_path
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ==================== Pytest配置 ====================

def pytest_configure(config):
    """pytest配置钩子。"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )
    config.addinivalue_line(
        "markers", "requires_git: 需要Git环境的测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试集合。"""
    # 为需要Git的测试添加标记
    for item in items:
        if "temp_git_repo" in item.fixturenames or "git_repo_with_commits" in item.fixturenames:
            item.add_marker(pytest.mark.requires_git)
