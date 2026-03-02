# OpenClaw Git分析工具

## 项目概述

OpenClaw Git分析工具是一个基于Git仓库的团队成员贡献度分析系统，能够自动分析提交记录、计算贡献度，并生成详细的分析报告。

## 核心功能

- **Git仓库管理**: 支持克隆、更新和检测本地仓库
- **提交记录分析**: 支持按时间范围过滤提交，提取详细信息
- **贡献度计算**: 基于内容的贡献价值评估，考虑代码复杂度、重要性和提交消息质量
- **报告生成**: 生成Markdown格式的分析报告，包含贡献度排名和团队整体分析
- **OpenClaw集成**: 作为OpenClaw工具使用，提供命令行接口

## 安装方法

### 1. 安装依赖

```bash
# 安装GitPython库
pip install GitPython

# 安装OpenClaw
npm install -g openclaw@latest
```

### 2. 安装本工具

```bash
# 克隆仓库
git clone <仓库地址>
cd openclaw

# 安装工具
pip install -e .
```

## 使用方法

### 命令行使用

```bash
# 查看帮助信息
openclaw --help
openclaw git-analyzer --help

# 检查仓库状态
openclaw git-analyzer status

# 克隆仓库
openclaw git-analyzer clone <仓库URL> <本地路径>

# 更新仓库
openclaw git-analyzer update <本地路径>

# 列出分支
openclaw git-analyzer branches <本地路径>

# 切换分支
openclaw git-analyzer switch <分支名称> <本地路径>

# 查看提交记录
openclaw git-analyzer commits <本地路径> --since 2026-01-01

# 分析贡献度
openclaw git-analyzer analyze <本地路径> --since 2026-01-01

# 生成分析报告
openclaw git-analyzer report <本地路径> --since 2026-01-01 --output analysis.md
```

### 作为Python模块使用

```python
from git_analyzer.main import GitAnalyzer

# 初始化分析器
analyzer = GitAnalyzer()

# 克隆仓库
analyzer.clone_repo('https://github.com/example/repo.git', 'local-repo')

# 分析提交
commits = analyzer.get_commits('local-repo', since='2026-01-01')

# 计算贡献度
contribution = analyzer.calculate_contribution('local-repo', since='2026-01-01')

# 生成报告
analyzer.generate_markdown_report('local-repo', 'report.md', since='2026-01-01')
```

## 贡献度评估算法

本工具使用基于内容的贡献价值评估算法，考虑以下因素：

1. **代码内容分析**:
   - 文件类型权重（核心业务文件权重更高）
   - 代码复杂度（圈复杂度、认知复杂度）
   - 代码重要性（文件修改频率、依赖关系）

2. **提交质量分析**:
   - 提交消息质量（长度、格式、内容）
   - 提交范围（文件数量、变更规模）

3. **技术价值评估**:
   - 功能实现（新功能、bug修复、性能优化）
   - 技术债务（代码质量、可读性）

## 报告格式

生成的Markdown报告包含以下内容：

- **报告信息**: 生成时间、仓库路径、分析时间范围
- **贡献度排名**: 按贡献价值排序的团队成员排名
- **最近提交记录**: 最近10条提交的详细信息
- **团队整体分析**: 参与开发者人数、总提交次数、总文件变更、总代码变更
- **最活跃开发者**: 贡献最多的开发者分析

## 性能指标

- **分析速度**: 1000次提交在30秒内完成
- **内存使用**: 分析过程中内存使用不超过500MB
- **可扩展性**: 支持分析超过10,000次提交的大型仓库

## 注意事项

- 确保目标Git仓库可通过网络访问
- 对于大型仓库，首次分析可能需要较长时间
- 建议定期运行分析，以获取最新的贡献度数据
- 贡献度评估结果仅供参考，不应作为唯一的绩效评估依据

## 版本历史

- **v1.0.0**: 初始版本，实现核心功能
- **v1.0.1**: 性能优化，支持大型仓库分析
- **v1.0.2**: 改进贡献度评估算法，增加代码质量分析

## 联系方式

如有问题或建议，请联系：
- GitHub: https://github.com/openclaw/openclaw
- 文档: https://docs.openclaw.dev
- 支持: support@openclaw.dev
