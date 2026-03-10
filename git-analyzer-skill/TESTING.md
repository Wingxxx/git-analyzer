# Git Analyzer 测试文档

## 测试概述

本文档描述了git-analyzer项目的自动化测试体系，包括单元测试、集成测试和性能测试。

**作者**: WING

## 测试结构

```
git-analyzer-skill/
├── tests/                          # 测试目录
│   ├── __init__.py                # 测试包初始化
│   ├── conftest.py                # pytest配置和fixtures
│   ├── test_exceptions.py         # 异常类单元测试
│   ├── test_validators.py         # 验证器单元测试
│   ├── test_performance_optimizer.py  # 性能优化单元测试
│   ├── test_code_quality_evaluator.py # 代码质量评估单元测试
│   ├── test_git_analyzer.py       # Git分析器单元测试
│   ├── test_integration.py        # 集成测试
│   └── test_performance.py        # 性能测试
├── pytest.ini                     # pytest配置文件
├── run_tests.py                   # 测试运行脚本
└── TESTING.md                     # 本文档
```

## 测试分类

### 1. 单元测试

测试单个函数、方法或类的功能。

- **test_exceptions.py**: 测试所有自定义异常类
- **test_validators.py**: 测试验证器装饰器和工具函数
- **test_performance_optimizer.py**: 测试性能监控、缓存和并行处理
- **test_code_quality_evaluator.py**: 测试代码质量评估功能
- **test_git_analyzer.py**: 测试仓库管理、提交分析和贡献度计算

### 2. 集成测试

测试模块间的协作和完整工作流。

- **test_integration.py**: 测试完整分析流程、模块协作、错误处理集成

### 3. 性能测试

测试大数据量处理能力和性能优化效果。

- **test_performance.py**: 测试并行处理、缓存效果、内存使用

## 运行测试

### 环境准备

```bash
# 安装依赖
pip install pytest pytest-cov pytest-timeout

# 可选：安装内存监控工具
pip install psutil
```

### 运行所有测试

```bash
# 使用pytest直接运行
python -m pytest

# 使用测试脚本
python run_tests.py
```

### 运行特定类型的测试

```bash
# 运行单元测试
python run_tests.py --type unit

# 运行集成测试
python run_tests.py --type integration

# 运行性能测试
python run_tests.py --type performance
```

### 运行快速测试

```bash
# 跳过慢速测试
python run_tests.py --quick
```

### 运行特定测试文件

```bash
# 运行特定文件的测试
python -m pytest tests/test_exceptions.py

# 运行特定测试类
python -m pytest tests/test_exceptions.py::TestGitAnalyzerError

# 运行特定测试方法
python -m pytest tests/test_exceptions.py::TestGitAnalyzerError::test_basic_error
```

### 使用标记过滤

```bash
# 运行带有特定标记的测试
python -m pytest -m unit
python -m pytest -m "not slow"
python -m pytest -m "integration and not slow"
```

### 详细输出

```bash
# 详细输出
python run_tests.py -v

# 或
python -m pytest -v
```

## 测试覆盖率

### 生成覆盖率报告

```bash
# 生成覆盖率报告
python run_tests.py --coverage

# 或
python -m pytest --cov=scripts --cov-report=html --cov-report=term
```

### 覆盖率要求

- **总体覆盖率**: >= 80%
- **核心模块覆盖率**: >= 85%
  - git_analyzer.py
  - code_quality_evaluator.py
  - performance_optimizer.py
  - validators.py
  - exceptions.py

### 查看覆盖率报告

运行测试后，打开 `htmlcov/index.html` 查看详细的HTML覆盖率报告。

## 测试Fixtures

### Git仓库Fixtures

- **temp_git_repo**: 创建临时Git仓库
- **git_repo_with_commits**: 创建包含多个提交的Git仓库
- **git_repo_with_branches**: 创建包含多个分支的Git仓库

### 代码文件Fixtures

- **sample_python_file**: 示例Python代码文件（高质量）
- **sample_bad_python_file**: 质量较差的Python代码文件
- **syntax_error_file**: 有语法错误的Python文件
- **large_python_file**: 大型Python文件（用于性能测试）

### 性能测试Fixtures

- **performance_test_repo**: 用于性能测试的大型Git仓库

## 测试最佳实践

### 1. 测试命名

```python
# 测试类命名：Test + 功能名称
class TestRepositoryManager:
    pass

# 测试方法命名：test_ + 功能描述
def test_is_git_repo_valid():
    pass
```

### 2. 测试组织

```python
class TestFeature:
    """测试功能描述"""
    
    def test_normal_case(self):
        """测试正常情况"""
        pass
    
    def test_edge_case(self):
        """测试边界情况"""
        pass
    
    def test_error_case(self):
        """测试错误情况"""
        pass
```

### 3. 使用Fixtures

```python
def test_with_fixture(temp_git_repo):
    """使用fixture的测试"""
    # temp_git_repo会自动创建和清理
    assert RepositoryManager.is_git_repo(temp_git_repo)
```

### 4. 使用标记

```python
@pytest.mark.unit
def test_unit_function():
    """单元测试"""
    pass

@pytest.mark.integration
def test_integration():
    """集成测试"""
    pass

@pytest.mark.slow
def test_slow_operation():
    """慢速测试"""
    pass
```

### 5. 参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    ("https://github.com/user/repo.git", True),
    ("not-a-url", False),
])
def test_url_validation(input, expected):
    """参数化测试"""
    assert is_valid_git_repo_url(input) == expected
```

## 性能基准

### 提交分析性能

- 50个提交的分析时间: < 30秒
- 单个提交详情获取: < 100ms

### 代码质量评估性能

- 单个文件评估: < 500ms
- 批量评估30个文件: < 10秒
- 缓存加速比: >= 2x

### 并行处理性能

- 并行加速比: >= 1.5x
- 内存增量: < 500MB

## 持续集成

### GitHub Actions配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.8
    
    - name: Install dependencies
      run: |
        pip install pytest pytest-cov
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python run_tests.py --quick
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

## 故障排查

### 常见问题

1. **测试失败：找不到模块**
   ```bash
   # 确保在项目根目录运行
   cd git-analyzer-skill
   python -m pytest
   ```

2. **Git相关测试失败**
   ```bash
   # 确保Git已安装
   git --version
   
   # 配置Git用户信息
   git config --global user.email "test@test.com"
   git config --global user.name "Test User"
   ```

3. **覆盖率报告不生成**
   ```bash
   # 安装pytest-cov
   pip install pytest-cov
   ```

4. **性能测试超时**
   ```bash
   # 跳过慢速测试
   python run_tests.py --quick
   ```

### 清理测试产物

```bash
# 清理所有测试产物
python run_tests.py --clean
```

## 测试报告

### 生成测试报告

```bash
# 生成JUnit XML报告
python -m pytest --junitxml=report.xml

# 生成HTML报告
pip install pytest-html
python -m pytest --html=report.html
```

## 贡献指南

### 添加新测试

1. 在 `tests/` 目录下创建测试文件
2. 使用 `test_*.py` 命名规范
3. 导入必要的fixtures和模块
4. 编写测试用例
5. 运行测试确保通过

### 测试代码规范

- 遵循PEP 8规范
- 每个测试方法添加文档字符串
- 使用有意义的测试名称
- 保持测试独立性
- 避免测试间的依赖

## 联系方式

如有问题或建议，请联系项目维护者。

---

**WING**
