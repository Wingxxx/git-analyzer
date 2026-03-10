# Git-Analyzer 项目开发指南

> **作者**: WING  
> **版本**: 1.0.0  
> **更新日期**: 2026-03-10

---

## 目录

1. [项目概述](#一项目概述)
2. [项目结构](#二项目结构)
3. [核心模块详解](#三核心模块详解)
4. [算法模式说明](#四算法模式说明)
5. [命令行接口](#五命令行接口)
6. [开发规范](#六开发规范)
7. [构建与测试](#七构建与测试)
8. [依赖项](#八依赖项)
9. [最佳实践](#九最佳实践)
10. [常见问题](#十常见问题)

---

## 一、项目概述

### 1.1 项目简介

**Git-Analyzer** 是一个通用的 Git 仓库分析工具技能包，兼容 Agent IDE 等 AI 开发环境，提供全面的仓库管理、贡献度分析和报告生成功能。

### 1.2 功能特点

- **仓库管理**：检测、克隆、更新Git仓库，管理分支
- **提交分析**：查看提交历史，获取提交详细信息
- **贡献度计算**：基于多维度指标分析开发者贡献
- **报告生成**：生成专业的Markdown格式分析报告

### 1.3 系统要求

| 要求 | 版本 |
|------|------|
| Python | >= 3.6 |
| Git | 任意版本 |
| GitPython | >= 3.1.0 |

---

## 二、项目结构

```
openclaw/
├── git-analyzer/                    # 输出目录（构建后的技能包）
│   ├── scripts/                     # 核心Python脚本
│   │   ├── git_analyzer.py          # 主入口脚本
│   │   ├── code_quality_evaluator.py # 代码质量评估器
│   │   ├── performance_optimizer.py  # 性能优化模块
│   │   ├── exceptions.py            # 自定义异常类
│   │   ├── validators.py            # 输入验证装饰器
│   │   └── quality_report_template.md
│   ├── references/                  # 参考文档
│   │   ├── contribution_analysis.md
│   │   ├── quality_evaluation.md
│   │   ├── report_generation.md
│   │   └── repository_management.md
│   ├── SKILL.md                     # 技能说明文档
│   ├── INSTALL.md
│   └── VERSION.json
│
├── git-analyzer-skill/              # 源代码目录（开发目录）
│   ├── scripts/                     # 核心脚本
│   ├── references/                  # 参考文档
│   ├── tests/                       # 测试文件
│   ├── evals/                       # 评估文件
│   └── *.md                         # 各类文档
│
├── build_skill.py                   # 构建脚本
├── skill_manifest.json              # 构建配置
├── git-analyzer.skill               # 打包后的技能文件
└── README.md                        # 项目说明
```

---

## 三、核心模块详解

### 3.1 主入口脚本 (git_analyzer.py)

#### 3.1.1 类结构

| 类名 | 职责 | 主要方法 |
|------|------|---------|
| `RepositoryManager` | Git仓库管理 | `is_git_repo()`, `clone_repo()`, `update_repo()`, `list_branches()`, `switch_branch()` |
| `CommitAnalyzer` | 提交分析 | `get_commits()`, `get_commit_details()` |
| `ContributionCalculator` | 贡献度计算 | `calculate_contribution()`, `_calculate_contribution_legacy()`, `_calculate_contribution_quality()` |
| `ReportGenerator` | 报告生成 | `generate_markdown_report()` |
| `GitAnalyzerCLI` | 命令行接口 | `main()`, `parse_date()` |

#### 3.1.2 数据类

```python
class AlgorithmMode(Enum):
    LEGACY = "legacy"      # 旧算法（基于数量统计）
    QUALITY = "quality"    # 新算法（基于代码质量）

@dataclass
class CodeQualityScore:
    total_score: float = 0.0
    max_score: float = 100.0
    file_count: int = 0
    avg_score: float = 0.0
    dimension_scores: Dict[str, float] = field(default_factory=dict)

@dataclass
class CollaborationScore:
    code_review_score: float = 0.0
    issue_resolution_score: float = 0.0
    merge_score: float = 0.0
    total_score: float = 0.0

@dataclass
class DocumentationScore:
    doc_files_count: int = 0
    doc_lines_added: int = 0
    doc_lines_deleted: int = 0
    doc_quality_score: float = 0.0
    total_score: float = 0.0

@dataclass
class ContributionScore:
    author: str
    code_quality_score: CodeQualityScore
    collaboration_score: CollaborationScore
    documentation_score: DocumentationScore
    total_score: float = 0.0
    algorithm_mode: AlgorithmMode = AlgorithmMode.QUALITY
```

#### 3.1.3 核心流程

```
用户输入 → GitAnalyzerCLI.main() 
         → 解析命令和参数
         → 调用对应模块
         → 返回结果/生成报告
```

---

### 3.2 代码质量评估器 (code_quality_evaluator.py)

#### 3.2.1 五维度评估体系

| 维度 | 满分 | 评估内容 |
|------|------|---------|
| 可读性 (readability) | 25分 | 命名规范、注释质量、代码格式、复杂度、文档字符串 |
| 可维护性 (maintainability) | 25分 | 模块化程度、代码重复度、依赖管理、函数长度、类设计 |
| 性能效率 (performance) | 20分 | 算法复杂度、资源使用、数据结构选择、循环优化 |
| 错误处理 (error_handling) | 15分 | 异常捕获、错误日志、边界检查 |
| 安全性 (security) | 15分 | 输入验证、敏感数据处理、安全编码实践 |

#### 3.2.2 质量等级

| 等级 | 分数范围 | 说明 |
|------|---------|------|
| 优秀 (EXCELLENT) | >= 80分 | 高质量代码 |
| 良好 (GOOD) | >= 60分 | 代码质量较好 |
| 合格 (QUALIFIED) | >= 40分 | 基本合格 |
| 不合格 (UNQUALIFIED) | < 40分 | 需要改进 |

#### 3.2.3 使用示例

```python
from code_quality_evaluator import CodeQualityEvaluator, ProjectType, ProjectStage

evaluator = CodeQualityEvaluator(
    project_type=ProjectType.CLI_TOOL,
    project_stage=ProjectStage.DEVELOPMENT,
    team_size=1
)

report = evaluator.evaluate_file("path/to/file.py")
print(f"总分: {report.total_score}")
print(f"等级: {report.level.value}")
```

---

### 3.3 性能优化模块 (performance_optimizer.py)

#### 3.3.1 核心组件

| 组件 | 功能 | 特性 |
|------|------|------|
| `PerformanceMonitor` | 性能监控 | 单例模式、线程安全、内存监控、错误率统计 |
| `CacheManager` | 缓存管理 | LRU+LFU混合策略、内存缓存、可选磁盘缓存 |
| `ParallelProcessor` | 并行处理 | 进程池/线程池、错误重试、负载均衡、超时控制 |
| `OptimizationSuggester` | 优化建议 | 性能分析、瓶颈识别、优化建议生成 |

#### 3.3.2 装饰器使用

```python
from performance_optimizer import performance_monitor, cached

@performance_monitor
def slow_function():
    pass

@cached(ttl=3600, max_size=1000)
def expensive_computation(n):
    return sum(range(n))
```

#### 3.3.3 并行处理

```python
from performance_optimizer import ParallelProcessor

results = ParallelProcessor.parallel_map(
    process_function,
    items_list,
    task_type='cpu',      # 或 'io'
    max_workers=4,
    retry_count=2
)
```

---

### 3.4 异常处理 (exceptions.py)

#### 3.4.1 异常层级

```
GitAnalyzerError (基类)
├── RepositoryError
│   ├── RepositoryNotFoundError
│   ├── RepositoryCloneError
│   ├── RepositoryUpdateError
│   ├── BranchNotFoundError
│   └── BranchSwitchError
├── CommitError
│   ├── CommitNotFoundError
│   └── EmptyRepositoryError
├── ContributionError
│   ├── InvalidAlgorithmModeError
│   └── QualityEvaluatorNotAvailableError
├── CodeQualityError
│   ├── FileNotFoundError
│   ├── FileReadError
│   ├── FileTooLargeError
│   ├── SyntaxErrorInCode
│   └── UnsupportedLanguageError
├── ValidationError
│   ├── InvalidPathError
│   ├── InvalidUrlError
│   ├── InvalidDateError
│   ├── InvalidParameterError
│   ├── ParameterOutOfRangeError
│   └── MissingRequiredParameterError
├── ReportError
│   ├── ReportGenerationError
│   └── InvalidOutputFormatError
└── ConfigurationError
    ├── InvalidConfigurationError
    └── MissingConfigurationError
```

#### 3.4.2 使用示例

```python
from exceptions import RepositoryNotFoundError, InvalidPathError

try:
    result = RepositoryManager.is_git_repo(path)
except RepositoryNotFoundError as e:
    print(f"错误: {e}")
    print(f"详情: {e.details}")
```

---

### 3.5 输入验证 (validators.py)

#### 3.5.1 装饰器列表

| 装饰器 | 验证内容 |
|--------|---------|
| `@validate_path()` | 路径验证（存在性、类型） |
| `@validate_url()` | URL格式验证 |
| `@validate_date()` | 日期格式验证 |
| `@validate_type()` | 参数类型验证 |
| `@validate_range()` | 参数范围验证 |
| `@validate_choices()` | 参数值列表验证 |
| `@validate_required()` | 必需参数验证 |
| `@validate_positive()` | 正数验证 |
| `@validate_non_empty_string()` | 非空字符串验证 |

#### 3.5.2 使用示例

```python
from validators import validate_path, validate_url, validate_date

@validate_path('file_path', must_exist=True, must_be_file=True)
def read_file(file_path: str):
    pass

@validate_url('repo_url')
def clone_repo(repo_url: str, local_path: str):
    pass
```

#### 3.5.3 工具函数

| 函数 | 用途 |
|------|------|
| `is_valid_git_repo_url()` | 检查Git仓库URL有效性 |
| `is_valid_commit_hash()` | 检查提交哈希值有效性 |
| `is_valid_branch_name()` | 检查分支名称有效性 |
| `sanitize_path()` | 清理和规范化路径 |

---

## 四、算法模式说明

### 4.1 LEGACY模式（旧算法）

**核心思想**: 基于数量统计的贡献度评估

**计算公式**:
```
总得分 = 提交次数得分 + 文件变更得分 + 代码变更得分 + 价值得分
```

**评分指标**:
- 提交次数：每个提交记2分
- 文件变更数：每个变更的文件记1.5分
- 代码变更行数：每行变更记0.5分
- 提交价值：基于提交消息质量、变更大小、文件类型计算

**适用场景**: 快速统计、历史数据对比

---

### 4.2 QUALITY模式（新算法，默认推荐）

**核心思想**: 基于代码质量的综合贡献度评估

**计算公式**:
```
总得分 = 代码质量得分 × 0.6 + 协作贡献得分 × 0.25 + 文档贡献得分 × 0.15
```

**评分维度**:

#### 4.2.1 代码质量得分（权重60%）

基于五维度代码质量评估：
- 可读性评估（0-25分）
- 可维护性评估（0-25分）
- 性能效率评估（0-20分）
- 错误处理评估（0-15分）
- 安全性评估（0-15分）

#### 4.2.2 协作贡献得分（权重25%）

**代码审查贡献**：
- 关键词：`review`, `reviewed`, `approve`, `approved`, `lgtm`, `looks good`
- 得分：每次审查 +2.0分

**问题解决贡献**：
- 关键词：`fix`, `bug`, `issue`, `resolve`, `close`, `closes`
- 得分：基础 +2.0分，包含Issue编号额外 +1.0分

**合并贡献**：
- 关键词：`merge`, `merged`, `merge pull`, `merge branch`
- 得分：每次合并 +1.5分

#### 4.2.3 文档贡献得分（权重15%）

- 文档完整性：每个文档文件 +2.0分（最多10分）
- 文档质量：新增内容每行 +0.1分，删除内容每行 +0.05分
- 文档文件类型：`.md`, `.txt`, `.rst`, `.adoc`, `.tex`

**优势**:
- 防止刷分：移除易刷分的数量指标
- 质量导向：真正评估代码质量
- 协作重视：认可团队协作贡献
- 文档认可：公平对待文档贡献者

---

## 五、命令行接口

### 5.1 命令列表

| 命令 | 描述 | 示例 |
|------|------|------|
| `status` | 检查仓库状态 | `python scripts/git_analyzer.py status` |
| `clone` | 克隆仓库 | `python scripts/git_analyzer.py clone <url> <path>` |
| `update` | 更新仓库 | `python scripts/git_analyzer.py update` |
| `branches` | 列出分支 | `python scripts/git_analyzer.py branches` |
| `switch` | 切换分支 | `python scripts/git_analyzer.py switch <branch>` |
| `commits` | 查看提交记录 | `python scripts/git_analyzer.py commits --since 2024-01-01` |
| `analyze` | 分析贡献度 | `python scripts/git_analyzer.py analyze --algorithm quality` |
| `report` | 生成分析报告 | `python scripts/git_analyzer.py report --output report.md` |

### 5.2 通用参数

| 参数 | 描述 |
|------|------|
| `path` | 仓库路径（默认当前目录） |
| `--since` | 开始时间 (YYYY-MM-DD) |
| `--until` | 结束时间 (YYYY-MM-DD) |
| `--algorithm` | 算法模式 (legacy/quality) |
| `--output` | 输出文件路径 |

### 5.3 详细用法

#### status - 检查仓库状态
```bash
python scripts/git_analyzer.py status [path]
```

#### clone - 克隆仓库
```bash
python scripts/git_analyzer.py clone <url> <path>
```

#### update - 更新仓库
```bash
python scripts/git_analyzer.py update [path]
```

#### branches - 列出分支
```bash
python scripts/git_analyzer.py branches [path]
```

#### switch - 切换分支
```bash
python scripts/git_analyzer.py switch <branch> [path]
```

#### commits - 查看提交记录
```bash
python scripts/git_analyzer.py commits [path] [--since YYYY-MM-DD] [--until YYYY-MM-DD]
```

#### analyze - 分析贡献度
```bash
python scripts/git_analyzer.py analyze [path] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--algorithm legacy|quality]
```

#### report - 生成分析报告
```bash
python scripts/git_analyzer.py report [path] [--output file] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--algorithm legacy|quality]
```

---

## 六、开发规范

### 6.1 代码风格

- 遵循 PEP 8 规范
- 使用 UTF-8 编码
- 文件头部署名：`WING`
- 使用 dataclass 定义数据类
- 使用 Enum 定义枚举类型
- 不添加注释（除非明确要求）

### 6.2 异常处理

- 使用自定义异常类（定义在 exceptions.py）
- 所有异常继承自 `GitAnalyzerError`
- 异常消息包含详细信息和建议
- 使用 try-except 捕获并转换为自定义异常

### 6.3 输入验证

- 使用 validators.py 中的装饰器
- 验证失败抛出对应的 ValidationError
- 路径使用 `sanitize_path()` 清理

### 6.4 性能优化

- 使用 `@performance_monitor` 装饰器监控性能
- 使用 `@cached` 装饰器缓存计算结果
- 大数据量使用 `ParallelProcessor` 并行处理
- 批量操作使用 `batch_process()` 方法

---

## 七、构建与测试

### 7.1 构建脚本

```bash
python build_skill.py              # 同步文件并生成 .skill 文件
python build_skill.py --dir-only   # 只同步文件到安装目录
python build_skill.py --skill-only # 只生成 .skill 文件
python build_skill.py --zip        # 同步并打包为zip
python build_skill.py --clean      # 清理安装目录后重新构建
```

### 7.2 测试框架

**测试目录**: `git-analyzer-skill/tests/`

**测试类型**:
- 单元测试：`test_*.py`
- 集成测试：`test_integration.py`
- 性能测试：`test_performance.py`

**运行测试**:
```bash
python -m pytest                   # 运行所有测试
python run_tests.py --quick        # 快速测试
python run_tests.py --coverage     # 带覆盖率
```

**覆盖率要求**:
- 总体覆盖率: >= 80%
- 核心模块覆盖率: >= 85%

---

## 八、依赖项

### 8.1 必需依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | >= 3.6 | 运行环境 |
| Git | - | 版本控制 |
| GitPython | >= 3.1.0 | Git操作库 |

### 8.2 可选依赖

| 依赖 | 用途 |
|------|------|
| psutil | 内存监控 |
| pytest | 测试框架 |
| pytest-cov | 覆盖率报告 |
| pytest-timeout | 超时控制 |

### 8.3 安装依赖

```bash
pip install GitPython
pip install pytest pytest-cov pytest-timeout
pip install psutil
```

---

## 九、最佳实践

### 9.1 贡献度分析建议

1. **定期分析**：建议每月或每季度进行一次贡献度分析
2. **多维度评估**：结合代码质量、协作贡献、文档贡献综合评估
3. **趋势分析**：关注贡献度变化趋势而非单点数据
4. **公平对待**：认可不同类型的贡献（代码、文档、协作）

### 9.2 提高贡献度评分

#### 提高代码质量得分

| 维度 | 最佳实践 | 评分提升 |
|------|---------|---------|
| 可读性 | 使用有意义的变量名、添加必要注释、保持代码格式统一 | +5~15分 |
| 可维护性 | 模块化设计、减少代码重复、合理拆分函数 | +5~15分 |
| 性能效率 | 选择合适的数据结构、优化循环、减少资源消耗 | +5~10分 |
| 错误处理 | 完善异常捕获、添加边界检查、记录错误日志 | +5~10分 |
| 安全性 | 输入验证、敏感数据加密、遵循安全编码规范 | +5~10分 |

#### 提高协作贡献得分

**代码审查贡献**：
- 在提交消息中使用关键词：`review`, `reviewed`, `approve`, `approved`, `lgtm`, `looks good`
- 示例：`Reviewed and approved PR #123`

**问题解决贡献**：
- 在提交消息中使用关键词：`fix`, `bug`, `issue`, `resolve`, `close`, `closes`
- 引用Issue编号获得额外加分
- 示例：`Fix login bug, closes #456`

**合并贡献**：
- 在提交消息中使用关键词：`merge`, `merged`, `merge pull`, `merge branch`
- 示例：`Merge pull request #789 from feature/new-api`

### 9.3 提交消息规范

推荐使用规范的提交消息格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型（type）**：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**：
```
feat(auth): add OAuth2 authentication

- Implement OAuth2 login flow
- Add token refresh mechanism
- Update user session management

Closes #123
Reviewed-by: John Doe
```

---

## 十、常见问题

### Q1: 新算法和旧算法有什么区别？

| 特性 | 新算法（QUALITY） | 旧算法（LEGACY） |
|------|------------------|-----------------|
| 核心思想 | 基于代码质量评估 | 基于数量统计 |
| 防刷分 | 有效防止刷分 | 容易被刷分 |
| 质量导向 | 高质量代码得分高 | 数量多得分高 |
| 协作认可 | 重视协作贡献 | 不评估协作 |
| 文档认可 | 公平对待文档贡献 | 文档贡献权重低 |
| 适用场景 | 绩效评估、质量改进 | 快速统计、历史对比 |

### Q2: 如何提高代码质量得分？

1. **可读性**：使用有意义的命名、添加注释、保持格式统一
2. **可维护性**：模块化设计、减少重复代码、合理拆分函数
3. **性能效率**：选择合适的数据结构、优化算法复杂度
4. **错误处理**：完善异常捕获、添加边界检查
5. **安全性**：输入验证、敏感数据加密

### Q3: GitPython未安装怎么办？

**错误**：`ModuleNotFoundError: No module named 'git'`

**解决**：
```bash
pip install GitPython
```

### Q4: 路径不是Git仓库怎么办？

**错误**：`错误: [path] 不是Git仓库`

**解决**：
1. 确认路径正确
2. 使用 `clone` 命令克隆仓库
3. 检查目录是否包含 `.git` 文件夹

### Q5: 日期格式错误怎么办？

**错误**：`日期格式错误`

**解决**：使用 YYYY-MM-DD 格式，例如：`2024-01-01`

---

## 附录

### A. 文件扩展名定义

**代码文件**：`.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs`, `.rb`

**文档文件**：`.md`, `.txt`, `.rst`, `.adoc`, `.tex`

**配置文件**：`.json`, `.xml`, `.yaml`, `.yml`, `.ini`, `.cfg`

### B. 权重配置

```python
QUALITY_WEIGHT = 0.6           # 代码质量权重
COLLABORATION_WEIGHT = 0.25    # 协作贡献权重
DOCUMENTATION_WEIGHT = 0.15    # 文档贡献权重
```

### C. 相关文档

- [仓库管理详细指南](git-analyzer/references/repository_management.md)
- [贡献度分析详细指南](git-analyzer/references/contribution_analysis.md)
- [代码质量评估指南](git-analyzer/references/quality_evaluation.md)
- [报告生成详细指南](git-analyzer/references/report_generation.md)
- [测试文档](git-analyzer-skill/TESTING.md)
- [性能优化指南](git-analyzer-skill/PERFORMANCE_OPTIMIZATION_GUIDE.md)

---

**WING**
