# Git仓库分析工具 - 错误处理文档

**WING**

## 概述

本文档详细说明了Git仓库分析工具的错误处理机制，包括自定义异常类、输入验证、边界条件处理和最佳实践。

## 目录

1. [自定义异常类](#自定义异常类)
2. [输入验证](#输入验证)
3. [边界条件处理](#边界条件处理)
4. [错误处理最佳实践](#错误处理最佳实践)
5. [测试覆盖](#测试覆盖)

---

## 自定义异常类

### 异常层次结构

所有自定义异常都继承自 `GitAnalyzerError` 基类，形成清晰的异常层次结构：

```
GitAnalyzerError (基类)
├── RepositoryError (仓库相关异常)
│   ├── RepositoryNotFoundError
│   ├── RepositoryCloneError
│   ├── RepositoryUpdateError
│   ├── BranchNotFoundError
│   └── BranchSwitchError
├── CommitError (提交相关异常)
│   ├── CommitNotFoundError
│   └── EmptyRepositoryError
├── ContributionError (贡献度计算异常)
│   ├── InvalidAlgorithmModeError
│   └── QualityEvaluatorNotAvailableError
├── CodeQualityError (代码质量评估异常)
│   ├── FileNotFoundError
│   ├── FileReadError
│   ├── FileTooLargeError
│   ├── SyntaxErrorInCode
│   └── UnsupportedLanguageError
├── ValidationError (输入验证异常)
│   ├── InvalidPathError
│   ├── InvalidUrlError
│   ├── InvalidDateError
│   ├── InvalidParameterError
│   ├── ParameterOutOfRangeError
│   └── MissingRequiredParameterError
├── ReportError (报告生成异常)
│   ├── ReportGenerationError
│   └── InvalidOutputFormatError
└── ConfigurationError (配置相关异常)
    ├── InvalidConfigurationError
    └── MissingConfigurationError
```

### 异常使用示例

#### 基本用法

```python
from exceptions import RepositoryNotFoundError, InvalidPathError

def open_repository(path: str):
    """打开Git仓库。"""
    # 验证路径
    if not path or not isinstance(path, str):
        raise InvalidPathError(path or "", "路径不能为空")
    
    # 检查仓库是否存在
    if not os.path.exists(path):
        raise RepositoryNotFoundError(path)
    
    # ... 其他逻辑
```

#### 异常捕获

```python
from exceptions import GitAnalyzerError, RepositoryNotFoundError

try:
    result = analyze_repository("/path/to/repo")
except RepositoryNotFoundError as e:
    print(f"仓库不存在: {e}")
    print(f"详情: {e.details}")
except GitAnalyzerError as e:
    print(f"分析失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

---

## 输入验证

### 验证装饰器

系统提供了多种验证装饰器，用于函数参数验证：

#### 1. 路径验证

```python
from validators import validate_path

@validate_path('file_path', must_exist=True, must_be_file=True)
def read_file(file_path: str):
    """读取文件内容。"""
    # 如果路径无效，会自动抛出InvalidPathError
    with open(file_path, 'r') as f:
        return f.read()
```

#### 2. URL验证

```python
from validators import validate_url

@validate_url('repo_url')
def clone_repository(repo_url: str, local_path: str):
    """克隆Git仓库。"""
    # 如果URL无效，会自动抛出InvalidUrlError
    # ...
```

#### 3. 日期验证

```python
from validators import validate_date

@validate_date('since', date_format='%Y-%m-%d')
@validate_date('until', date_format='%Y-%m-%d')
def get_commits(path: str, since: str = None, until: str = None):
    """获取提交记录。"""
    # 如果日期格式无效，会自动抛出InvalidDateError
    # ...
```

#### 4. 类型验证

```python
from validators import validate_type

@validate_type('team_size', int)
def calculate_contribution(path: str, team_size: int):
    """计算贡献度。"""
    # 如果team_size不是整数，会自动抛出InvalidParameterError
    # ...
```

#### 5. 范围验证

```python
from validators import validate_range

@validate_range('score', min_value=0, max_value=100)
def evaluate_quality(score: float):
    """评估质量得分。"""
    # 如果score不在0-100范围内，会自动抛出ParameterOutOfRangeError
    # ...
```

#### 6. 必需参数验证

```python
from validators import validate_required

@validate_required('repo_path', 'output_file')
def generate_report(repo_path: str, output_file: str):
    """生成报告。"""
    # 如果缺少必需参数，会自动抛出MissingRequiredParameterError
    # ...
```

### 验证工具函数

#### Git URL验证

```python
from validators import is_valid_git_repo_url

# 验证Git仓库URL
is_valid = is_valid_git_repo_url("https://github.com/user/repo.git")
# 返回: True

is_valid = is_valid_git_repo_url("not-a-url")
# 返回: False
```

#### 提交哈希验证

```python
from validators import is_valid_commit_hash

# 验证提交哈希值
is_valid = is_valid_commit_hash("abc123def456")
# 返回: True

is_valid = is_valid_commit_hash("invalid")
# 返回: False
```

#### 分支名称验证

```python
from validators import is_valid_branch_name

# 验证分支名称
is_valid = is_valid_branch_name("feature/new-feature")
# 返回: True

is_valid = is_valid_branch_name("branch..name")
# 返回: False (包含..)
```

#### 路径清理

```python
from validators import sanitize_path

# 清理和规范化路径
path = sanitize_path("test/path")
# 返回规范化的绝对路径
```

---

## 边界条件处理

### 1. 空仓库处理

```python
from exceptions import EmptyRepositoryError

def calculate_contribution(local_path: str):
    """计算贡献度。"""
    repo = Repo(local_path)
    
    # 检查仓库是否有提交记录
    try:
        commit_count = sum(1 for _ in repo.iter_commits())
        if commit_count == 0:
            raise EmptyRepositoryError(local_path)
    except Exception as e:
        logger.warning(f"检查提交记录时出错: {e}")
        return {}
    
    # ... 其他逻辑
```

### 2. 大文件处理

```python
from exceptions import FileTooLargeError

def evaluate_file(file_path: str):
    """评估文件代码质量。"""
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # 检查文件大小
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        raise FileTooLargeError(file_path, file_size, MAX_FILE_SIZE)
    
    # ... 其他逻辑
```

### 3. 语法错误处理

```python
def evaluate_file(file_path: str):
    """评估文件代码质量。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        tree = ast.parse(code_content)
    except SyntaxError as e:
        # 返回最低分报告而不是抛出异常
        return self._create_minimal_report(
            file_path, 
            f"语法错误: 第{e.lineno}行: {e.msg}"
        )
    
    # ... 其他逻辑
```

### 4. 空参数处理

```python
def get_commits(local_path: str):
    """获取提交记录。"""
    # 输入验证
    if not local_path or not isinstance(local_path, str):
        logger.error("本地路径无效")
        return []
    
    # 清理路径
    local_path = local_path.strip()
    
    # ... 其他逻辑
```

### 5. 权限错误处理

```python
from exceptions import FileReadError

def read_file(file_path: str):
    """读取文件内容。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except PermissionError as e:
        raise FileReadError(file_path, f"权限不足: {e}")
    except IOError as e:
        raise FileReadError(file_path, str(e))
```

---

## 错误处理最佳实践

### 1. 分层错误处理

```python
def analyze_repository(path: str):
    """分析仓库。"""
    # 第一层：输入验证
    if not path:
        raise InvalidPathError(path, "路径不能为空")
    
    # 第二层：前置条件检查
    if not RepositoryManager.is_git_repo(path):
        raise RepositoryNotFoundError(path)
    
    # 第三层：业务逻辑错误处理
    try:
        commits = CommitAnalyzer.get_commits(path)
        if not commits:
            raise EmptyRepositoryError(path)
        
        # ... 其他逻辑
    except GitCommandError as e:
        logger.error(f"Git命令执行失败: {e}")
        raise RepositoryUpdateError(path, str(e))
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise GitAnalyzerError(f"仓库分析失败: {e}")
```

### 2. 友好的错误消息

```python
# 好的做法
raise InvalidParameterError(
    "team_size", 
    team_size, 
    "团队规模必须是正整数，当前值无效"
)

# 不好的做法
raise Exception("参数错误")
```

### 3. 详细的错误详情

```python
# 好的做法
raise BranchNotFoundError(
    branch_name="feature-branch",
    available_branches=['main', 'develop', 'hotfix']
)
# 错误消息会包含可用分支列表

# 不好的做法
raise Exception("分支不存在")
```

### 4. 优雅降级

```python
def calculate_contribution(local_path: str):
    """计算贡献度。"""
    try:
        # 尝试使用新算法
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        return calculator.calculate_contribution(local_path)
    except QualityEvaluatorNotAvailableError:
        logger.warning("质量评估器不可用，降级使用旧算法")
        # 降级到旧算法
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.LEGACY)
        return calculator.calculate_contribution(local_path)
```

### 5. 日志记录

```python
def process_repository(path: str):
    """处理仓库。"""
    try:
        # ... 业务逻辑
        pass
    except RepositoryNotFoundError as e:
        logger.error(f"仓库不存在: {e}")
        logger.debug(f"错误详情: {e.details}")
        raise
    except Exception as e:
        logger.error(f"处理仓库时发生未知错误: {e}", exc_info=True)
        raise
```

---

## 测试覆盖

### 测试文件

错误处理测试位于 `test_error_handling.py` 文件中，包含以下测试类：

1. **TestExceptions**: 测试自定义异常类
2. **TestValidators**: 测试输入验证器
3. **TestRepositoryManagerErrorHandling**: 测试RepositoryManager的错误处理
4. **TestCommitAnalyzerErrorHandling**: 测试CommitAnalyzer的错误处理
5. **TestContributionCalculatorErrorHandling**: 测试ContributionCalculator的错误处理
6. **TestCodeQualityEvaluatorErrorHandling**: 测试CodeQualityEvaluator的错误处理
7. **TestEdgeCases**: 测试边界条件

### 运行测试

```bash
# 运行所有错误处理测试
python test_error_handling.py

# 使用pytest运行
pytest test_error_handling.py -v
```

### 测试覆盖率

确保错误处理代码的测试覆盖率至少达到80%：

```bash
# 使用coverage工具
coverage run test_error_handling.py
coverage report -m
```

---

## 常见错误场景

### 场景1：仓库不存在

```python
from exceptions import RepositoryNotFoundError

try:
    result = analyze_repository("/nonexistent/path")
except RepositoryNotFoundError as e:
    print(f"错误: {e}")
    print(f"建议: 请检查路径是否正确")
```

### 场景2：文件过大

```python
from exceptions import FileTooLargeError

try:
    report = evaluator.evaluate_file("/path/to/large_file.py")
except FileTooLargeError as e:
    print(f"错误: {e}")
    print(f"文件大小: {e.details['file_size']}")
    print(f"最大限制: {e.details['max_size']}")
    print(f"建议: 请分割文件或增加文件大小限制")
```

### 场景3：分支不存在

```python
from exceptions import BranchNotFoundError

try:
    RepositoryManager.switch_branch(path, "nonexistent-branch")
except BranchNotFoundError as e:
    print(f"错误: {e}")
    print(f"可用分支: {e.details['available_branches']}")
    print(f"建议: 请使用正确的分支名称")
```

### 场景4：无效参数

```python
from exceptions import InvalidParameterError

try:
    calculator = ContributionCalculator(team_size=-1)
except InvalidParameterError as e:
    print(f"错误: {e}")
    print(f"参数名: {e.details['param_name']}")
    print(f"参数值: {e.details['param_value']}")
    print(f"原因: {e.details['reason']}")
```

---

## 总结

本错误处理机制提供了：

1. **清晰的异常层次结构**：便于捕获和处理特定类型的错误
2. **全面的输入验证**：防止无效输入导致程序崩溃
3. **边界条件处理**：妥善处理空值、大文件、权限等边界情况
4. **友好的错误消息**：提供详细的错误信息和解决建议
5. **优雅降级**：在功能不可用时自动降级到备用方案
6. **完善的测试覆盖**：确保错误处理代码的可靠性

通过遵循本文档的最佳实践，可以确保Git仓库分析工具在各种异常情况下都能稳定运行，并提供友好的用户体验。
