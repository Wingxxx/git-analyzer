---
name: git-analyzer
description: |
  Git仓库分析工具技能。用于管理Git仓库、分析提交记录、计算贡献度和生成分析报告。
  
  当用户需要以下任何操作时，必须使用此技能：
  - 分析Git仓库、查看提交历史、计算开发者贡献度
  - 生成仓库分析报告、评估团队绩效、进行项目回顾
  - 克隆仓库、切换分支、更新仓库或检查仓库状态
  - 用户提到"git分析"、"贡献度"、"提交记录"、"仓库报告"、"团队绩效"、"代码统计"等关键词
  
  即使没有明确提到"git-analyzer"，只要涉及Git仓库分析相关任务，都应该使用此技能。
compatibility:
  tools:
    - Read
    - Write
    - RunCommand
    - Grep
    - Glob
    - LS
  dependencies:
    - Git
    - GitPython
---

# Git-Analyzer Skill

## 功能概述

Git-Analyzer是一个强大的Git仓库分析工具技能，提供四大核心功能：

1. **仓库管理**：检测、克隆、更新Git仓库，管理分支
2. **提交分析**：查看提交历史，获取提交详细信息
3. **贡献度计算**：基于多维度指标分析开发者贡献
4. **报告生成**：生成专业的Markdown格式分析报告

## 触发场景

当用户表达以下意图时，立即使用此技能：

**仓库管理类**：
- "检查这个目录是不是Git仓库"
- "克隆一个仓库到本地"
- "更新我的本地仓库"
- "列出所有分支" / "切换到某个分支"

**分析类**：
- "分析这个仓库的贡献度"
- "查看最近的提交记录"
- "谁提交的代码最多"
- "生成团队贡献报告"

**报告类**：
- "生成一个Git分析报告"
- "导出仓库分析结果"
- "评估团队绩效"

## 核心工作流

### 步骤1：意图识别

首先理解用户想要执行的操作类型：

| 用户表述 | 操作类型 | 对应命令 |
|---------|---------|---------|
| "检查仓库状态"、"是不是git仓库" | 仓库检测 | status |
| "克隆仓库"、"下载仓库" | 仓库克隆 | clone |
| "更新仓库"、"拉取最新代码" | 仓库更新 | update |
| "列出分支"、"有哪些分支" | 分支列表 | branches |
| "切换分支"、"切换到xxx分支" | 分支切换 | switch |
| "查看提交"、"提交记录" | 提交分析 | commits |
| "分析贡献度"、"谁贡献最多" | 贡献分析 | analyze |
| "生成报告"、"导出分析" | 报告生成 | report |

### 步骤2：参数提取

从用户输入中提取必要参数：

**路径参数**：
- 如果用户指定了路径，使用指定路径
- 如果没有指定，默认使用当前工作目录

**时间参数**：
- 用户可能说"最近一个月"、"今年以来"、"2024年的提交"
- 转换为 `--since` 和 `--until` 参数
- 格式：YYYY-MM-DD

**分支参数**：
- 用户说"切换到develop分支"，提取"develop"
- 用户说"列出分支"，无需额外参数

**URL参数**：
- 用户说"克隆 https://xxx"，提取URL
- 用户说"克隆到 ./my-repo"，提取目标路径

### 步骤3：执行脚本

使用Python脚本执行操作：

```bash
python scripts/git_analyzer.py <command> [options]
```

**示例**：
```bash
# 检查仓库状态
python scripts/git_analyzer.py status

# 分析2024年以来的贡献度
python scripts/git_analyzer.py analyze --since 2024-01-01

# 生成报告
python scripts/git_analyzer.py report --output analysis.md
```

### 步骤4：结果呈现

根据操作类型呈现结果：

**仓库管理类**：
- 直接展示操作结果（成功/失败）
- 列出分支名称
- 显示当前分支状态

**分析类**：
- 展示贡献度排名表格
- 显示关键统计信息
- 突出显示最活跃开发者

**报告类**：
- 告知报告生成位置
- 展示报告摘要
- 提供报告文件路径供用户查看

## 命令参考

### status - 检查仓库状态
```bash
python scripts/git_analyzer.py status [path]
```
检测指定路径是否为Git仓库。

### clone - 克隆仓库
```bash
python scripts/git_analyzer.py clone <url> <path>
```
从远程地址克隆Git仓库到本地。

### update - 更新仓库
```bash
python scripts/git_analyzer.py update [path]
```
更新本地Git仓库到最新版本。

### branches - 列出分支
```bash
python scripts/git_analyzer.py branches [path]
```
列出仓库的所有分支。

### switch - 切换分支
```bash
python scripts/git_analyzer.py switch <branch> [path]
```
切换到指定分支。

### commits - 查看提交记录
```bash
python scripts/git_analyzer.py commits [path] [--since YYYY-MM-DD] [--until YYYY-MM-DD]
```
获取仓库的提交记录，支持按时间范围过滤。

### analyze - 分析贡献度
```bash
python scripts/git_analyzer.py analyze [path] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--algorithm mode]
```
分析仓库的贡献度情况。

**参数说明**：
- `--algorithm`: 算法模式，可选值：
  - `quality`（默认）：新算法，基于代码质量评估
  - `legacy`：旧算法，基于数量统计

**示例**：
```bash
# 使用新算法（默认）
python scripts/git_analyzer.py analyze --since 2024-01-01

# 使用旧算法
python scripts/git_analyzer.py analyze --algorithm legacy --since 2024-01-01
```

### report - 生成分析报告
```bash
python scripts/git_analyzer.py report [path] [--output file] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--algorithm mode]
```
生成Markdown格式的仓库分析报告。

**参数说明**：
- `--output`: 输出文件名，默认为 `git_analysis_report.md`
- `--algorithm`: 算法模式，可选值：
  - `quality`（默认）：新算法，基于代码质量评估
  - `legacy`：旧算法，基于数量统计

**示例**：
```bash
# 使用新算法生成报告（默认）
python scripts/git_analyzer.py report --output analysis.md --since 2024-01-01

# 使用旧算法生成报告
python scripts/git_analyzer.py report --algorithm legacy --output legacy_report.md
```

## 贡献度计算方法

Git-Analyzer支持两种算法模式：

### 新算法（QUALITY模式，默认推荐）

**核心思想**：基于代码质量的综合贡献度评估

**计算公式**：
```
总得分 = 代码质量得分 × 0.6 + 协作贡献得分 × 0.25 + 文档贡献得分 × 0.15
```

**评分维度**：
1. **代码质量得分**（权重60%）
   - 可读性评估（0-25分）
   - 可维护性评估（0-25分）
   - 性能效率评估（0-20分）
   - 错误处理评估（0-15分）
   - 安全性评估（0-15分）

2. **协作贡献得分**（权重25%）
   - 代码审查贡献
   - 问题解决贡献
   - 合并贡献

3. **文档贡献得分**（权重15%）
   - 文档完整性
   - 文档质量

**优势**：
- 防止刷分：移除易刷分的数量指标
- 质量导向：真正评估代码质量
- 协作重视：认可团队协作贡献
- 文档认可：公平对待文档贡献者

### 旧算法（LEGACY模式）

**核心思想**：基于数量统计的贡献度评估

**计算公式**：
```
总得分 = 提交次数得分 + 文件变更得分 + 代码变更得分 + 价值得分
```

**评分指标**：
1. **提交次数**：每个提交记2分
2. **文件变更数**：每个变更的文件记1.5分
3. **代码变更行数**：每行变更记0.5分
4. **提交价值**：基于提交消息质量、变更大小、文件类型计算

**适用场景**：快速统计、历史数据对比

详细算法请参考 `references/contribution_analysis.md`。

## 最佳实践

### 1. 明确路径
- 始终确认用户想要操作的仓库路径
- 如果用户没有指定，询问或使用当前目录

### 2. 合理的时间范围
- 分析贡献度时，建议使用合理的时间范围
- 常见范围：最近一个月、最近一季度、今年以来

### 3. 报告命名
- 生成报告时使用有意义的文件名
- 例如：`team_contribution_2024Q1.md`

### 4. 错误处理
- 如果路径不是Git仓库，友好提示用户
- 如果缺少依赖，提示安装GitPython：`pip install GitPython`

## 详细参考文档

如需更详细的信息，请查阅以下参考文档：

- **仓库管理详细指南**：`references/repository_management.md`
- **贡献度分析详细指南**：`references/contribution_analysis.md`
- **代码质量评估指南**：`references/quality_evaluation.md`
- **报告生成详细指南**：`references/report_generation.md`

## 常见问题

### GitPython未安装
**错误**：`ModuleNotFoundError: No module named 'git'`
**解决**：`pip install GitPython`

### 路径不是Git仓库
**错误**：`错误: [path] 不是Git仓库`
**解决**：确认路径正确，或使用clone命令克隆仓库

### 时间格式错误
**错误**：`日期格式错误`
**解决**：使用YYYY-MM-DD格式，例如：2024-01-01

## 使用示例

**示例1：检查当前仓库状态**
```
用户：检查当前目录是不是Git仓库
执行：python scripts/git_analyzer.py status
```

**示例2：分析2024年贡献度**
```
用户：分析这个仓库2024年以来的贡献度
执行：python scripts/git_analyzer.py analyze --since 2024-01-01
```

**示例3：生成团队报告**
```
用户：生成一个团队贡献分析报告
执行：python scripts/git_analyzer.py report --output team_report.md
```

**示例4：克隆仓库**
```
用户：克隆 https://github.com/user/repo.git 到 ./my-repo
执行：python scripts/git_analyzer.py clone https://github.com/user/repo.git ./my-repo
```
