# 仓库管理详细指南

本文档提供Git仓库管理功能的详细操作指南。

## 目录

1. [仓库检测](#仓库检测)
2. [仓库克隆](#仓库克隆)
3. [仓库更新](#仓库更新)
4. [分支管理](#分支管理)

---

## 仓库检测

### 功能说明

检测指定路径是否为Git仓库。这是所有其他操作的前提条件。

### 使用场景

- 确认当前目录是否已初始化为Git仓库
- 在执行其他操作前验证路径有效性
- 快速诊断Git环境问题

### 命令格式

```bash
python scripts/git_analyzer.py status [path]
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | 否 | 当前目录 | 要检测的路径 |

### 返回结果

**成功时**：
```
/path/to/repo 是 Git仓库
```

**失败时**：
```
/path/to/directory 不是 Git仓库
```

### 实现原理

通过尝试初始化`git.Repo`对象来判断路径是否为Git仓库：

```python
from git import Repo
from git.exc import InvalidGitRepositoryError

try:
    Repo(path)
    return True
except InvalidGitRepositoryError:
    return False
```

### 常见问题

**Q: 为什么我的目录明明有.git文件夹，却显示不是Git仓库？**

A: 可能的原因：
1. .git文件夹损坏
2. 权限不足
3. 路径中包含特殊字符

**Q: 如何将普通目录转换为Git仓库？**

A: 使用`git init`命令初始化：
```bash
git init /path/to/directory
```

---

## 仓库克隆

### 功能说明

从远程地址克隆Git仓库到本地。

### 使用场景

- 获取远程仓库的本地副本
- 参与开源项目开发
- 备份远程仓库

### 命令格式

```bash
python scripts/git_analyzer.py clone <url> <path>
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| url | string | 是 | - | 远程仓库URL |
| path | string | 是 | - | 本地保存路径 |

### URL格式支持

- HTTPS: `https://github.com/user/repo.git`
- SSH: `git@github.com:user/repo.git`
- Git协议: `git://github.com/user/repo.git`

### 返回结果

**成功时**：
```
正在克隆仓库: https://github.com/user/repo.git 到 /path/to/local
克隆成功！
```

**失败时**：
```
克隆失败: [错误信息]
```

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `Repository not found` | 仓库不存在或无权限 | 检查URL和访问权限 |
| `Permission denied` | SSH密钥未配置 | 配置SSH密钥或使用HTTPS |
| `Path already exists` | 目标路径已存在 | 选择其他路径或删除现有目录 |

### 最佳实践

1. **使用HTTPS**：对于公开仓库，HTTPS更简单直接
2. **使用SSH**：对于需要频繁推送的私有仓库，SSH更安全便捷
3. **路径命名**：使用有意义的目录名，如项目名或`项目名-用途`

---

## 仓库更新

### 功能说明

更新本地Git仓库到最新版本（执行git pull）。

### 使用场景

- 获取远程最新代码
- 同步团队协作成果
- 更新本地分支

### 命令格式

```bash
python scripts/git_analyzer.py update [path]
```

### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| path | string | 否 | 当前目录 | 仓库路径 |

### 执行流程

1. 检测路径是否为Git仓库
2. 获取当前分支名称
3. 从origin远程拉取最新代码
4. 显示更新结果

### 返回结果

**成功时**：
```
正在更新仓库: /path/to/repo
当前分支: main
更新成功！
```

**失败时**：
```
更新失败: [错误信息]
```

### 常见问题

**Q: 更新失败提示"conflict"怎么办？**

A: 存在本地修改与远程冲突：
1. 提交或暂存本地修改
2. 手动解决冲突
3. 重新执行更新

**Q: 如何查看更新了哪些内容？**

A: 更新后使用`git log`查看最新提交记录。

---

## 分支管理

### 列出分支

#### 功能说明

列出仓库的所有本地分支。

#### 命令格式

```bash
python scripts/git_analyzer.py branches [path]
```

#### 返回结果

```
分支列表:
  - main
  - develop
  - feature/new-feature
```

### 切换分支

#### 功能说明

切换到指定的本地分支。

#### 命令格式

```bash
python scripts/git_analyzer.py switch <branch> [path]
```

#### 参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| branch | string | 是 | - | 目标分支名称 |
| path | string | 否 | 当前目录 | 仓库路径 |

#### 返回结果

**成功时**：
```
正在切换到分支: develop
成功切换到分支: develop
```

**失败时**：
```
切换分支失败: pathspec 'branch-name' did not match any file(s) known to git
```

### 分支管理最佳实践

1. **命名规范**：
   - `main`/`master`: 主分支
   - `develop`: 开发分支
   - `feature/*`: 功能分支
   - `hotfix/*`: 热修复分支
   - `release/*`: 发布分支

2. **切换前检查**：
   - 确保当前分支没有未提交的修改
   - 或使用`git stash`暂存修改

3. **远程分支**：
   - 本命令只列出和切换本地分支
   - 如需切换远程分支，先使用`git checkout -b <local-branch> origin/<remote-branch>`

---

## 错误处理

### 通用错误

| 错误类型 | 说明 | 处理方式 |
|---------|------|---------|
| `InvalidGitRepositoryError` | 路径不是Git仓库 | 检查路径或初始化仓库 |
| `GitCommandError` | Git命令执行失败 | 查看详细错误信息 |
| `NoSuchPathError` | 路径不存在 | 检查路径拼写 |

### 错误处理流程

1. 捕获异常并记录日志
2. 向用户显示友好的错误信息
3. 提供可能的解决方案
4. 返回适当的错误码

---

## 技术实现

### 依赖库

- **GitPython**: Python的Git库
- **git**: 系统Git命令

### 安装依赖

```bash
pip install GitPython
```

### 核心类

```python
class RepositoryManager:
    """Git仓库管理器"""
    
    @staticmethod
    def is_git_repo(path: str) -> bool:
        """检测是否为Git仓库"""
        
    @staticmethod
    def clone_repo(repo_url: str, local_path: str) -> bool:
        """克隆仓库"""
        
    @staticmethod
    def update_repo(local_path: str) -> bool:
        """更新仓库"""
        
    @staticmethod
    def list_branches(local_path: str) -> List[str]:
        """列出分支"""
        
    @staticmethod
    def switch_branch(local_path: str, branch_name: str) -> bool:
        """切换分支"""
```

---

## 附录

### Git基础命令对照

| 技能命令 | Git命令 |
|---------|---------|
| status | `git rev-parse --is-inside-work-tree` |
| clone | `git clone <url> <path>` |
| update | `git pull` |
| branches | `git branch` |
| switch | `git checkout <branch>` |

### 相关文档

- [贡献度分析详细指南](./contribution_analysis.md)
- [报告生成详细指南](./report_generation.md)
