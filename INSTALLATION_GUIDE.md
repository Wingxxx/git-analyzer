# Git-Analyzer Skill - OpenClaw 安装指南

## 项目概述

Git-Analyzer是一个强大的Git仓库分析工具，作为OpenClaw的skill提供以下功能：

- 仓库管理：检测、克隆、更新仓库
- 分支管理：列出和切换分支
- 提交记录分析：查看提交历史，按时间范围过滤
- 贡献度计算：基于多种指标计算开发者贡献度
- 报告生成：生成Markdown格式的分析报告

## 系统要求

- Python 3.6 或更高版本
- Git
- OpenClaw 2026.3 或更高版本
- GitPython 3.1.0 或更高版本

## 安装步骤

### 1. 安装GitPython依赖

在安装git-analyzer skill之前，需要先安装GitPython库：

#### Windows环境

```bash
pip install GitPython
```

#### WSL环境

```bash
# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装GitPython
pip install GitPython
```

### 2. 安装git-analyzer skill到OpenClaw

#### 方法一：复制到OpenClaw技能目录（推荐）

1. 进入git-analyzer项目目录
2. 运行以下命令将技能复制到OpenClaw的skills目录：

```bash
# Windows用户在WSL中运行
wsl cp -r git-analyzer-skill ~/.npm-global/lib/node_modules/openclaw/skills/

# Linux/macOS用户运行
cp -r git-analyzer-skill ~/.npm-global/lib/node_modules/openclaw/skills/
```

3. 重启OpenClaw网关以加载新技能：

```bash
openclaw gateway restart
```

#### 方法二：使用.skill文件安装

1. 首先确保你已经打包了skill文件（如果还没有打包，请参考下面的打包步骤）
2. 运行以下命令安装skill：

```bash
openclaw plugins install git-analyzer.skill
```

### 3. 验证安装

安装完成后，运行以下命令验证skill是否成功安装：

```bash
openclaw skills list | grep -i git
```

你应该能在输出中看到 `✓ ready   │ 📦 git-analyzer`。

## 打包skill（可选）

如果你需要将skill打包为可安装的.skill文件，可以按照以下步骤操作：

1. 确保你在git-analyzer项目目录中
2. 创建一个打包脚本：

```python
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
```

3. 运行脚本生成.skill文件：

```bash
python package_skill.py
```

4. 生成的.skill文件将位于项目根目录中

## 使用方法

### 命令格式

```bash
openclaw git-analyzer <command> [options]
```

### 可用命令

#### 1. status - 检查仓库状态

**功能**：检测指定路径是否为Git仓库

**用法**：
```bash
openclaw git-analyzer status [path]
```

**参数**：
- `path`：仓库路径，默认为当前目录

**示例**：
```bash
openclaw git-analyzer status
```

#### 2. clone - 克隆仓库

**功能**：从远程地址克隆Git仓库到本地

**用法**：
```bash
openclaw git-analyzer clone <url> <path>
```

**参数**：
- `url`：仓库远程地址
- `path`：本地保存路径

**示例**：
```bash
openclaw git-analyzer clone https://github.com/user/repo.git ./my-repo
```

#### 3. update - 更新仓库

**功能**：更新本地Git仓库到最新版本

**用法**：
```bash
openclaw git-analyzer update [path]
```

**参数**：
- `path`：仓库路径，默认为当前目录

**示例**：
```bash
openclaw git-analyzer update ./my-repo
```

#### 4. branches - 列出分支

**功能**：列出仓库的所有分支

**用法**：
```bash
openclaw git-analyzer branches [path]
```

**参数**：
- `path`：仓库路径，默认为当前目录

**示例**：
```bash
openclaw git-analyzer branches
```

#### 5. switch - 切换分支

**功能**：切换到指定分支

**用法**：
```bash
openclaw git-analyzer switch <branch> [path]
```

**参数**：
- `branch`：分支名称
- `path`：仓库路径，默认为当前目录

**示例**：
```bash
openclaw git-analyzer switch develop
```

#### 6. commits - 查看提交记录

**功能**：获取仓库的提交记录，支持按时间范围过滤

**用法**：
```bash
openclaw git-analyzer commits [path] [--since <date>] [--until <date>]
```

**参数**：
- `path`：仓库路径，默认为当前目录
- `--since`：开始日期，格式为YYYY-MM-DD
- `--until`：结束日期，格式为YYYY-MM-DD

**示例**：
```bash
openclaw git-analyzer commits --since 2024-01-01 --until 2024-01-31
```

#### 7. analyze - 分析贡献度

**功能**：分析仓库的贡献度情况

**用法**：
```bash
openclaw git-analyzer analyze [path] [--since <date>] [--until <date>]
```

**参数**：
- `path`：仓库路径，默认为当前目录
- `--since`：开始日期，格式为YYYY-MM-DD
- `--until`：结束日期，格式为YYYY-MM-DD

**示例**：
```bash
openclaw git-analyzer analyze --since 2024-01-01
```

#### 8. report - 生成分析报告

**功能**：生成Markdown格式的仓库分析报告

**用法**：
```bash
openclaw git-analyzer report [path] [--output <file>] [--since <date>] [--until <date>]
```

**参数**：
- `path`：仓库路径，默认为当前目录
- `--output`：输出文件路径，默认为git_analysis_report.md
- `--since`：开始日期，格式为YYYY-MM-DD
- `--until`：结束日期，格式为YYYY-MM-DD

**示例**：
```bash
openclaw git-analyzer report --output analysis.md --since 2024-01-01
```

## 贡献度计算方法

贡献度计算基于以下指标：

1. **提交次数**：每个提交记2分
2. **文件变更数**：每个变更的文件记1.5分
3. **代码变更行数**：每行变更记0.5分
4. **提交价值**：基于以下因素计算：
   - 提交消息质量（长度、关键字）
   - 变更大小
   - 文件类型（代码文件权重高于文档文件）

总得分 = 提交次数得分 + 文件变更得分 + 代码变更得分 + 价值得分

## 报告内容

生成的Markdown报告包含以下内容：

1. **报告信息**：生成时间、分析仓库、时间范围
2. **贡献度排名**：按总得分排序的开发者贡献度列表
3. **最近提交记录**：最近10条提交的详细信息
4. **团队整体分析**：参与开发者数量、总提交次数、总文件变更数、总代码变更行数
5. **最活跃开发者**：贡献度最高的开发者信息

## 常见问题和解决方案

### 1. GitPython未安装

**错误信息**：`ModuleNotFoundError: No module named 'git'`

**解决方案**：安装GitPython库

```bash
pip install GitPython
```

### 2. 仓库路径错误

**错误信息**：`错误: [path] 不是Git仓库`

**解决方案**：确保提供的路径是有效的Git仓库，或者使用`clone`命令克隆一个仓库

### 3. 权限问题

**错误信息**：`Permission denied`

**解决方案**：确保有足够的权限访问仓库目录

### 4. 网络问题

**错误信息**：`fatal: unable to access 'https://github.com/...'`

**解决方案**：确保网络连接正常，或者检查仓库URL是否正确

### 5. 时间格式错误

**错误信息**：`日期格式错误: [date]，应为YYYY-MM-DD`

**解决方案**：使用正确的日期格式，例如：2024-01-01

## 示例使用场景

1. **项目回顾**：分析团队在某个时间段的贡献情况
   ```bash
   openclaw git-analyzer report --output quarterly_report.md --since 2024-01-01 --until 2024-03-31
   ```

2. **绩效评估**：基于贡献度数据进行开发者绩效评估
   ```bash
   openclaw git-analyzer analyze --since 2024-01-01
   ```

3. **代码质量监控**：通过提交记录分析代码变更趋势
   ```bash
   openclaw git-analyzer commits --since 2024-01-01
   ```

4. **团队协作分析**：了解团队成员的工作分布情况
   ```bash
   openclaw git-analyzer report --output team_analysis.md
   ```

## 支持和反馈

如果您在使用git-analyzer skill时遇到任何问题，请联系：

- 作者：Wing
- 邮箱：wing@example.com

## 版本历史

- v1.0.0：初始版本，包含基本的Git仓库分析功能
