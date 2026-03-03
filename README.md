# Git-Analyzer Skill for OpenClaw

## 项目简介

Git-Analyzer是一个专为OpenClaw设计的Git仓库分析工具，提供全面的仓库管理、贡献度分析和报告生成功能。它可以帮助团队了解代码贡献情况，评估开发者绩效，以及进行项目回顾。

## 功能特点

- **仓库管理**：检测、克隆、更新Git仓库
- **分支管理**：列出和切换分支
- **提交记录分析**：查看提交历史，按时间范围过滤
- **贡献度计算**：基于多种指标计算开发者贡献度
- **报告生成**：生成Markdown格式的分析报告

## 系统要求

- Python 3.6 或更高版本
- Git
- OpenClaw 2026.3 或更高版本
- GitPython 3.1.0 或更高版本

## 安装方法

### 1. 安装GitPython依赖

```bash
pip install GitPython
```

### 2. 安装到OpenClaw

#### 方法一：使用.skill文件安装

```bash
openclaw skill install path/to/git-analyzer.skill
```

#### 方法二：直接安装目录

```bash
openclaw skill install .
```

### 3. 验证安装

```bash
openclaw skill list
```

## 使用示例

### 检查仓库状态

```bash
openclaw git-analyzer status
```

### 分析贡献度

```bash
openclaw git-analyzer analyze --since 2024-01-01
```

### 生成分析报告

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

## 命令参考

| 命令 | 描述 | 示例 |
|------|------|------|
| `status` | 检查仓库状态 | `openclaw git-analyzer status` |
| `clone` | 克隆仓库 | `openclaw git-analyzer clone <url> <path>` |
| `update` | 更新仓库 | `openclaw git-analyzer update` |
| `branches` | 列出分支 | `openclaw git-analyzer branches` |
| `switch` | 切换分支 | `openclaw git-analyzer switch <branch>` |
| `commits` | 查看提交记录 | `openclaw git-analyzer commits --since 2024-01-01` |
| `analyze` | 分析贡献度 | `openclaw git-analyzer analyze --since 2024-01-01` |
| `report` | 生成分析报告 | `openclaw git-analyzer report --output report.md` |

## 常见问题

### GitPython未安装

**错误信息**：`ModuleNotFoundError: No module named 'git'`

**解决方案**：安装GitPython库

```bash
pip install GitPython
```

### 仓库路径错误

**错误信息**：`错误: [path] 不是Git仓库`

**解决方案**：确保提供的路径是有效的Git仓库，或者使用`clone`命令克隆一个仓库

### 时间格式错误

**错误信息**：`日期格式错误: [date]，应为YYYY-MM-DD`

**解决方案**：使用正确的日期格式，例如：2024-01-01

## 支持和反馈

如果您在使用git-analyzer skill时遇到任何问题，请联系：

- 作者：Wing
- 邮箱：wing@example.com

## 版本历史

- v1.0.0：初始版本，包含基本的Git仓库分析功能

## 许可证

MIT License

## 致谢

感谢OpenClaw团队提供的优秀AI Agent框架，以及GitPython库的开发者们。
