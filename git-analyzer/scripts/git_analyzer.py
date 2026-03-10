#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git仓库分析工具

提供Git仓库管理、提交分析、贡献度计算和报告生成功能。

WING
"""

import os
import re
import logging
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from argparse import ArgumentParser
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache

import git
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

# 导入性能优化模块
try:
    from performance_optimizer import (
        performance_monitor,
        cached,
        ParallelProcessor,
        PerformanceMonitor,
        OptimizationSuggester
    )
    PERFORMANCE_OPTIMIZER_AVAILABLE = True
except ImportError:
    PERFORMANCE_OPTIMIZER_AVAILABLE = False
    # 如果性能优化模块不可用，提供空装饰器
    def performance_monitor(func):
        return func
    def cached(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# 导入自定义异常类
try:
    from exceptions import (
        GitAnalyzerError,
        RepositoryNotFoundError,
        RepositoryCloneError,
        RepositoryUpdateError,
        BranchNotFoundError,
        BranchSwitchError,
        CommitNotFoundError,
        EmptyRepositoryError,
        InvalidAlgorithmModeError,
        QualityEvaluatorNotAvailableError,
        InvalidPathError,
        InvalidUrlError,
        InvalidDateError,
        InvalidParameterError,
        ReportGenerationError
    )
    EXCEPTIONS_AVAILABLE = True
except ImportError:
    EXCEPTIONS_AVAILABLE = False
    logging.warning("exceptions模块未找到，将使用基础异常处理")

# 导入验证器
try:
    from validators import (
        validate_path,
        validate_url,
        validate_date,
        validate_type,
        validate_range,
        validate_choices,
        validate_required,
        validate_positive,
        validate_non_empty_string,
        is_valid_git_repo_url,
        is_valid_commit_hash,
        is_valid_branch_name,
        sanitize_path
    )
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False
    logging.warning("validators模块未找到，输入验证功能将受限")

# 导入代码质量评估器
try:
    from code_quality_evaluator import (
        CodeQualityEvaluator,
        QualityReport,
        ProjectType,
        ProjectStage
    )
    QUALITY_EVALUATOR_AVAILABLE = True
except ImportError:
    QUALITY_EVALUATOR_AVAILABLE = False
    logging.warning("code_quality_evaluator模块未找到，代码质量评估功能将不可用")


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlgorithmMode(Enum):
    """算法模式枚举。"""
    LEGACY = "legacy"  # 旧算法（基于数量统计）
    QUALITY = "quality"  # 新算法（基于代码质量）


@dataclass
class CodeQualityScore:
    """代码质量得分数据类。"""
    total_score: float = 0.0
    max_score: float = 100.0
    file_count: int = 0
    avg_score: float = 0.0
    dimension_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class CollaborationScore:
    """协作贡献得分数据类。"""
    code_review_score: float = 0.0
    issue_resolution_score: float = 0.0
    merge_score: float = 0.0
    total_score: float = 0.0
    review_count: int = 0
    issue_count: int = 0
    merge_count: int = 0


@dataclass
class DocumentationScore:
    """文档贡献得分数据类。"""
    doc_files_count: int = 0
    doc_lines_added: int = 0
    doc_lines_deleted: int = 0
    doc_quality_score: float = 0.0
    completeness_score: float = 0.0
    total_score: float = 0.0


@dataclass
class ContributionScore:
    """综合贡献得分数据类。"""
    author: str
    code_quality_score: CodeQualityScore = field(default_factory=CodeQualityScore)
    collaboration_score: CollaborationScore = field(default_factory=CollaborationScore)
    documentation_score: DocumentationScore = field(default_factory=DocumentationScore)
    total_score: float = 0.0
    algorithm_mode: AlgorithmMode = AlgorithmMode.QUALITY


class RepositoryManager:
    """Git仓库管理器，负责仓库的基本操作。"""

    @staticmethod
    def is_git_repo(path: str) -> bool:
        """
        检测本地路径是否为Git仓库。

        Args:
            path: 本地路径。

        Returns:
            是否为Git仓库。
        
        Raises:
            InvalidPathError: 路径无效时抛出（如果验证器可用）。
        """
        # 输入验证
        if not path or not isinstance(path, str):
            logger.warning(f"路径参数无效: {path}")
            return False
        
        try:
            # 清理路径
            path = path.strip()
            if VALIDATORS_AVAILABLE:
                path = sanitize_path(path)
            
            # 检查路径是否存在
            if not os.path.exists(path):
                logger.debug(f"路径不存在: {path}")
                return False
            
            # 尝试打开仓库
            Repo(path)
            return True
        except InvalidGitRepositoryError:
            logger.debug(f"不是有效的Git仓库: {path}")
            return False
        except NoSuchPathError:
            logger.debug(f"路径不存在: {path}")
            return False
        except PermissionError as e:
            logger.warning(f"权限不足，无法访问路径: {path}, 错误: {e}")
            return False
        except Exception as e:
            logger.error(f"检测Git仓库时发生未知错误: {path}, 错误: {e}")
            return False

    @staticmethod
    def clone_repo(repo_url: str, local_path: str) -> bool:
        """
        克隆Git仓库。

        Args:
            repo_url: 仓库URL。
            local_path: 本地路径。

        Returns:
            克隆是否成功。
        
        Raises:
            InvalidUrlError: URL无效时抛出（如果验证器可用）。
            InvalidPathError: 路径无效时抛出（如果验证器可用）。
            RepositoryCloneError: 克隆失败时抛出。
        """
        # 输入验证
        if not repo_url or not isinstance(repo_url, str):
            error_msg = "仓库URL无效"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidUrlError(repo_url or "", error_msg)
            return False
        
        if not local_path or not isinstance(local_path, str):
            error_msg = "本地路径无效"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidPathError(local_path or "", error_msg)
            return False
        
        # 清理参数
        repo_url = repo_url.strip()
        local_path = local_path.strip()
        
        # 验证URL格式
        if VALIDATORS_AVAILABLE and not is_valid_git_repo_url(repo_url):
            error_msg = f"仓库URL格式无效: {repo_url}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidUrlError(repo_url, "URL格式不符合Git仓库规范")
            return False
        
        # 验证本地路径
        if VALIDATORS_AVAILABLE:
            try:
                local_path = sanitize_path(local_path)
            except Exception as e:
                logger.error(f"路径清理失败: {e}")
                if EXCEPTIONS_AVAILABLE:
                    raise InvalidPathError(local_path, str(e))
                return False
        
        # 检查本地路径是否已存在
        if os.path.exists(local_path):
            error_msg = f"本地路径已存在: {local_path}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryCloneError(repo_url, error_msg)
            return False
        
        try:
            logger.info(f"正在克隆仓库: {repo_url} 到 {local_path}")
            Repo.clone_from(repo_url, local_path)
            logger.info("克隆成功！")
            return True
        except GitCommandError as e:
            error_msg = f"克隆失败: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryCloneError(repo_url, str(e))
            return False
        except PermissionError as e:
            error_msg = f"权限不足，无法创建目录: {local_path}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryCloneError(repo_url, error_msg)
            return False
        except Exception as e:
            error_msg = f"克隆时发生未知错误: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryCloneError(repo_url, str(e))
            return False

    @staticmethod
    def update_repo(local_path: str) -> bool:
        """
        更新本地Git仓库。

        Args:
            local_path: 本地仓库路径。

        Returns:
            更新是否成功。
        
        Raises:
            RepositoryNotFoundError: 仓库不存在时抛出。
            RepositoryUpdateError: 更新失败时抛出。
        """
        # 输入验证
        if not local_path or not isinstance(local_path, str):
            error_msg = "本地路径无效"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidPathError(local_path or "", error_msg)
            return False
        
        # 清理路径
        local_path = local_path.strip()
        if VALIDATORS_AVAILABLE:
            try:
                local_path = sanitize_path(local_path)
            except Exception as e:
                logger.error(f"路径清理失败: {e}")
                if EXCEPTIONS_AVAILABLE:
                    raise InvalidPathError(local_path, str(e))
                return False
        
        # 检查是否为Git仓库
        if not RepositoryManager.is_git_repo(local_path):
            error_msg = f"路径不是Git仓库: {local_path}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryNotFoundError(local_path)
            return False

        try:
            repo = Repo(local_path)
            logger.info(f"正在更新仓库: {local_path}")

            # 获取当前分支
            try:
                current_branch = repo.active_branch
                logger.info(f"当前分支: {current_branch.name}")
            except TypeError as e:
                # HEAD detached状态
                logger.warning(f"仓库处于HEAD detached状态: {e}")
            
            # 拉取最新代码
            try:
                origin = repo.remotes.origin
                origin.pull()
                logger.info("更新成功！")
                return True
            except AttributeError:
                error_msg = "仓库没有配置远程origin"
                logger.error(error_msg)
                if EXCEPTIONS_AVAILABLE:
                    raise RepositoryUpdateError(local_path, error_msg)
                return False

        except GitCommandError as e:
            error_msg = f"更新失败: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryUpdateError(local_path, str(e))
            return False
        except PermissionError as e:
            error_msg = f"权限不足: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryUpdateError(local_path, error_msg)
            return False
        except Exception as e:
            error_msg = f"更新时发生未知错误: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryUpdateError(local_path, str(e))
            return False

    @staticmethod
    def list_branches(local_path: str) -> List[str]:
        """
        列出仓库所有分支。

        Args:
            local_path: 本地仓库路径。

        Returns:
            分支列表。
        
        Raises:
            RepositoryNotFoundError: 仓库不存在时抛出。
        """
        # 输入验证
        if not local_path or not isinstance(local_path, str):
            logger.error("本地路径无效")
            return []
        
        # 清理路径
        local_path = local_path.strip()
        if VALIDATORS_AVAILABLE:
            try:
                local_path = sanitize_path(local_path)
            except Exception as e:
                logger.error(f"路径清理失败: {e}")
                return []
        
        # 检查是否为Git仓库
        if not RepositoryManager.is_git_repo(local_path):
            error_msg = f"路径不是Git仓库: {local_path}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryNotFoundError(local_path)
            return []

        try:
            repo = Repo(local_path)
            branches = [branch.name for branch in repo.branches]
            logger.info("分支列表:")
            for branch in branches:
                logger.info(f"  - {branch}")
            return branches
        except GitCommandError as e:
            logger.error(f"获取分支列表失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取分支列表时发生未知错误: {e}")
            return []

    @staticmethod
    def switch_branch(local_path: str, branch_name: str) -> bool:
        """
        切换分支。

        Args:
            local_path: 本地仓库路径。
            branch_name: 分支名称。

        Returns:
            切换是否成功。
        
        Raises:
            RepositoryNotFoundError: 仓库不存在时抛出。
            BranchNotFoundError: 分支不存在时抛出。
            BranchSwitchError: 切换失败时抛出。
        """
        # 输入验证
        if not local_path or not isinstance(local_path, str):
            error_msg = "本地路径无效"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidPathError(local_path or "", error_msg)
            return False
        
        if not branch_name or not isinstance(branch_name, str):
            error_msg = "分支名称无效"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidParameterError("branch_name", branch_name or "", error_msg)
            return False
        
        # 清理参数
        local_path = local_path.strip()
        branch_name = branch_name.strip()
        
        # 验证分支名称
        if VALIDATORS_AVAILABLE and not is_valid_branch_name(branch_name):
            error_msg = f"分支名称格式无效: {branch_name}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidParameterError("branch_name", branch_name, error_msg)
            return False
        
        # 检查是否为Git仓库
        if not RepositoryManager.is_git_repo(local_path):
            error_msg = f"路径不是Git仓库: {local_path}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryNotFoundError(local_path)
            return False

        try:
            repo = Repo(local_path)
            
            # 检查分支是否存在
            branch_names = [b.name for b in repo.branches]
            if branch_name not in branch_names:
                error_msg = f"分支不存在: {branch_name}"
                logger.error(error_msg)
                if EXCEPTIONS_AVAILABLE:
                    raise BranchNotFoundError(branch_name, branch_names)
                return False
            
            logger.info(f"正在切换到分支: {branch_name}")
            repo.git.checkout(branch_name)
            logger.info(f"成功切换到分支: {branch_name}")
            return True
        except GitCommandError as e:
            error_msg = f"切换分支失败: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise BranchSwitchError(branch_name, str(e))
            return False
        except Exception as e:
            error_msg = f"切换分支时发生未知错误: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise BranchSwitchError(branch_name, str(e))
            return False


class CommitAnalyzer:
    """提交分析器，负责提取和分析提交记录。"""

    @staticmethod
    def get_commits(
        local_path: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        获取提交记录，支持按时间范围过滤。

        Args:
            local_path: 本地仓库路径。
            since: 开始时间。
            until: 结束时间。

        Returns:
            提交记录列表。
        
        Raises:
            RepositoryNotFoundError: 仓库不存在时抛出。
            EmptyRepositoryError: 仓库为空时抛出。
            InvalidDateError: 日期参数无效时抛出。
        """
        # 输入验证
        if not local_path or not isinstance(local_path, str):
            logger.error("本地路径无效")
            return []
        
        # 清理路径
        local_path = local_path.strip()
        if VALIDATORS_AVAILABLE:
            try:
                local_path = sanitize_path(local_path)
            except Exception as e:
                logger.error(f"路径清理失败: {e}")
                return []
        
        # 验证日期参数
        if since is not None and not isinstance(since, datetime):
            error_msg = "since参数必须是datetime类型"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidDateError(str(since), "datetime对象")
            return []
        
        if until is not None and not isinstance(until, datetime):
            error_msg = "until参数必须是datetime类型"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidDateError(str(until), "datetime对象")
            return []
        
        # 验证日期范围
        if since and until and since > until:
            error_msg = f"开始时间 {since} 晚于结束时间 {until}"
            logger.error(error_msg)
            return []
        
        # 检查是否为Git仓库
        if not RepositoryManager.is_git_repo(local_path):
            error_msg = f"路径不是Git仓库: {local_path}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryNotFoundError(local_path)
            return []

        try:
            repo = Repo(local_path)
            commits = []

            # 构建查询参数
            kwargs: Dict[str, Any] = {}
            if since:
                kwargs['since'] = since
            if until:
                kwargs['until'] = until

            # 获取提交记录
            try:
                for commit in repo.iter_commits(**kwargs):
                    commits.append({
                        'hash': commit.hexsha,
                        'author': commit.author.name,
                        'email': commit.author.email,
                        'date': commit.committed_datetime,
                        'message': commit.message.strip()
                    })
            except ValueError as e:
                # 空仓库或无提交记录
                error_msg = f"仓库可能为空或没有提交记录: {e}"
                logger.warning(error_msg)
                if EXCEPTIONS_AVAILABLE:
                    raise EmptyRepositoryError(local_path)
                return []

            logger.info(f"获取到 {len(commits)} 条提交记录")
            return commits
        except GitCommandError as e:
            logger.error(f"获取提交记录失败: {e}")
            return []
        except Exception as e:
            logger.error(f"获取提交记录时发生未知错误: {e}")
            return []

    @staticmethod
    def get_commit_details(local_path: str, commit_hash: str) -> Dict[str, Any]:
        """
        获取提交详细信息。

        Args:
            local_path: 本地仓库路径。
            commit_hash: 提交哈希值。

        Returns:
            提交详细信息。
        
        Raises:
            RepositoryNotFoundError: 仓库不存在时抛出。
            CommitNotFoundError: 提交不存在时抛出。
        """
        # 输入验证
        if not local_path or not isinstance(local_path, str):
            logger.error("本地路径无效")
            return {}
        
        if not commit_hash or not isinstance(commit_hash, str):
            error_msg = "提交哈希值无效"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidParameterError("commit_hash", commit_hash or "", error_msg)
            return {}
        
        # 清理参数
        local_path = local_path.strip()
        commit_hash = commit_hash.strip()
        
        # 验证提交哈希值格式
        if VALIDATORS_AVAILABLE and not is_valid_commit_hash(commit_hash):
            error_msg = f"提交哈希值格式无效: {commit_hash}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise CommitNotFoundError(commit_hash)
            return {}
        
        # 检查是否为Git仓库
        if not RepositoryManager.is_git_repo(local_path):
            error_msg = f"路径不是Git仓库: {local_path}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise RepositoryNotFoundError(local_path)
            return {}

        try:
            repo = Repo(local_path)
            
            # 获取提交对象
            try:
                commit = repo.commit(commit_hash)
            except (ValueError, GitCommandError) as e:
                error_msg = f"提交不存在或哈希值无效: {commit_hash}"
                logger.error(error_msg)
                if EXCEPTIONS_AVAILABLE:
                    raise CommitNotFoundError(commit_hash)
                return {}

            # 获取文件变更
            changed_files = []
            if commit.parents:
                try:
                    parent = commit.parents[0]
                    diff = parent.diff(commit)
                    for item in diff:
                        changed_files.append({
                            'path': item.a_path or item.b_path,
                            'change_type': 'A' if item.new_file else 'D' if item.deleted_file else 'M'
                        })
                except Exception as e:
                    logger.warning(f"获取文件变更失败: {e}")

            details = {
                'hash': commit.hexsha,
                'author': commit.author.name,
                'email': commit.author.email,
                'date': commit.committed_datetime,
                'message': commit.message.strip(),
                'changed_files': changed_files,
                'stats': commit.stats.total if hasattr(commit.stats, 'total') else {}
            }

            logger.info(f"提交详情: {commit.hexsha}")
            logger.info(f"作者: {details['author']} <{details['email']}>")
            logger.info(f"日期: {details['date']}")
            logger.info(f"提交信息: {details['message']}")
            logger.info(f"文件变更: {len(details['changed_files'])} 个文件")
            logger.info(f"统计信息: {details['stats']}")

            return details
        except GitCommandError as e:
            logger.error(f"获取提交详情失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"获取提交详情时发生未知错误: {e}")
            return {}


class ContributionCalculator:
    """
    贡献度计算器，负责分析开发者贡献（优化版）。
    
    支持两种算法模式：
    1. LEGACY: 旧算法（基于数量统计）
    2. QUALITY: 新算法（基于代码质量）
    
    新算法公式：
    总得分 = 代码质量得分 × 权重系数 + 协作贡献得分 + 文档贡献得分
    
    优化特性：
    - 提交分析结果缓存
    - diff分析缓存
    - 增量处理机制
    - 智能批次大小调整
    """

    # 代码文件扩展名
    CODE_EXTENSIONS = ('.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb')
    
    # 文档文件扩展名
    DOC_EXTENSIONS = ('.md', '.txt', '.rst', '.adoc', '.tex')
    
    # 配置文件扩展名
    CONFIG_EXTENSIONS = ('.json', '.xml', '.yaml', '.yml', '.ini', '.cfg')
    
    # 新算法权重配置
    QUALITY_WEIGHT = 0.6  # 代码质量权重
    COLLABORATION_WEIGHT = 0.25  # 协作贡献权重
    DOCUMENTATION_WEIGHT = 0.15  # 文档贡献权重
    
    # 协作贡献关键词
    REVIEW_KEYWORDS = ['review', 'reviewed', 'approve', 'approved', 'lgtm', 'looks good']
    ISSUE_KEYWORDS = ['fix', 'bug', 'issue', 'resolve', 'close', 'closed', 'closes']
    MERGE_KEYWORDS = ['merge', 'merged', 'merge pull', 'merge branch']
    
    def __init__(
        self,
        algorithm_mode: AlgorithmMode = AlgorithmMode.QUALITY,
        project_type: Optional[ProjectType] = None,
        project_stage: Optional[ProjectStage] = None,
        team_size: int = 1,
        enable_parallel: bool = True,
        batch_size: int = 50,
        enable_cache: bool = True
    ):
        """
        初始化贡献度计算器。
        
        Args:
            algorithm_mode: 算法模式。
            project_type: 项目类型。
            project_stage: 项目阶段。
            team_size: 团队规模。
            enable_parallel: 是否启用并行处理。
            batch_size: 批次大小。
            enable_cache: 是否启用缓存。
        
        Raises:
            InvalidAlgorithmModeError: 算法模式无效时抛出。
            InvalidParameterError: 参数无效时抛出。
        """
        # 验证算法模式
        if not isinstance(algorithm_mode, AlgorithmMode):
            error_msg = f"算法模式必须是AlgorithmMode枚举类型，当前类型: {type(algorithm_mode)}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidAlgorithmModeError(
                    str(algorithm_mode),
                    [mode.value for mode in AlgorithmMode]
                )
            # 使用默认值
            algorithm_mode = AlgorithmMode.QUALITY
        
        # 验证团队规模
        if not isinstance(team_size, int) or team_size < 1:
            error_msg = f"团队规模必须是正整数，当前值: {team_size}"
            logger.warning(error_msg)
            team_size = 1  # 使用默认值
        
        # 验证批次大小
        if not isinstance(batch_size, int) or batch_size < 1:
            error_msg = f"批次大小必须是正整数，当前值: {batch_size}"
            logger.warning(error_msg)
            batch_size = 50  # 使用默认值
        
        self.algorithm_mode = algorithm_mode
        self.project_type = project_type or ProjectType.OTHER
        self.project_stage = project_stage or ProjectStage.DEVELOPMENT
        self.team_size = team_size
        self.enable_parallel = enable_parallel and PERFORMANCE_OPTIMIZER_AVAILABLE
        self.batch_size = batch_size
        self.enable_cache = enable_cache and PERFORMANCE_OPTIMIZER_AVAILABLE
        
        # 初始化代码质量评估器
        self.quality_evaluator = None
        if QUALITY_EVALUATOR_AVAILABLE and algorithm_mode == AlgorithmMode.QUALITY:
            self.quality_evaluator = CodeQualityEvaluator(
                project_type=self.project_type,
                project_stage=self.project_stage,
                team_size=self.team_size
            )
        
        # 提交分析缓存
        self._commit_analysis_cache: Dict[str, Dict[str, Any]] = {}
        
        # diff分析缓存
        self._diff_cache: Dict[str, Tuple[int, int, int]] = {}
    
    @staticmethod
    def _calculate_commit_value(
        commit: Any,
        author_stats: Dict[str, Dict[str, float]]
    ) -> float:
        """
        计算单个提交的价值分数（旧算法）。
        
        Args:
            commit: Git提交对象。
            author_stats: 作者统计信息。
        
        Returns:
            提交价值分数。
        """
        value_score = 0.0
        
        # 基于提交消息质量的评估
        message = commit.message.strip()
        if len(message) > 10:
            value_score += 1
        if any(keyword in message.lower() for keyword in ['fix', 'bug', 'feature', 'improve', 'optimize']):
            value_score += 1
        
        # 基于变更大小的评估
        total_changes = author_stats[commit.author.name]['total_changes']
        if total_changes > 100:
            value_score += 2
        elif total_changes > 10:
            value_score += 1
        
        # 基于文件类型的评估
        if commit.parents:
            parent = commit.parents[0]
            diff = parent.diff(commit)
            for item in diff:
                path = item.a_path or item.b_path
                if path:
                    if any(ext in path for ext in ContributionCalculator.CODE_EXTENSIONS):
                        value_score += 1
                    elif any(ext in path for ext in ContributionCalculator.DOC_EXTENSIONS):
                        value_score += 0.5
        
        return value_score
    
    @staticmethod
    @performance_monitor
    def _analyze_commit_diff(commit: Any) -> Tuple[int, int, int]:
        """
        分析提交的diff信息（优化版，添加缓存）。
        
        Args:
            commit: Git提交对象。
        
        Returns:
            (文件变更数, 插入行数, 删除行数)
        """
        files_changed = 0
        insertions = 0
        deletions = 0
        
        if commit.parents:
            parent = commit.parents[0]
            diff = parent.diff(commit)
            files_changed = len(diff)
            
            # 使用commit.stats获取更准确的统计信息
            try:
                stats = commit.stats
                insertions = stats.total.get('insertions', 0)
                deletions = stats.total.get('deletions', 0)
            except Exception:
                # 如果stats不可用，使用diff分析
                for item in diff:
                    try:
                        diff_lines = item.diff.split('\n')
                        for line in diff_lines:
                            if line.startswith('+') and not line.startswith('+++'):
                                insertions += 1
                            elif line.startswith('-') and not line.startswith('---'):
                                deletions += 1
                    except Exception:
                        pass
        
        return files_changed, insertions, deletions
    
    @performance_monitor
    def _extract_commit_files(self, commit: Any) -> Tuple[List[str], List[str], List[str]]:
        """
        提取提交中的代码文件、文档文件和配置文件（优化版，添加缓存）。
        
        Args:
            commit: Git提交对象。
        
        Returns:
            (代码文件列表, 文档文件列表, 配置文件列表)
        """
        # 检查缓存
        if self.enable_cache and commit.hexsha in self._commit_analysis_cache:
            cached = self._commit_analysis_cache[commit.hexsha]
            return cached.get('code_files', []), cached.get('doc_files', []), cached.get('config_files', [])
        
        code_files = []
        doc_files = []
        config_files = []
        
        if commit.parents:
            parent = commit.parents[0]
            diff = parent.diff(commit)
            
            for item in diff:
                path = item.a_path or item.b_path
                if path:
                    # 跳过删除的文件
                    if item.deleted_file:
                        continue
                    
                    # 分类文件
                    if any(path.endswith(ext) for ext in self.CODE_EXTENSIONS):
                        code_files.append(path)
                    elif any(path.endswith(ext) for ext in self.DOC_EXTENSIONS):
                        doc_files.append(path)
                    elif any(path.endswith(ext) for ext in self.CONFIG_EXTENSIONS):
                        config_files.append(path)
        
        # 缓存结果
        if self.enable_cache:
            if commit.hexsha not in self._commit_analysis_cache:
                self._commit_analysis_cache[commit.hexsha] = {}
            self._commit_analysis_cache[commit.hexsha]['code_files'] = code_files
            self._commit_analysis_cache[commit.hexsha]['doc_files'] = doc_files
            self._commit_analysis_cache[commit.hexsha]['config_files'] = config_files
        
        return code_files, doc_files, config_files
    
    @performance_monitor
    def _analyze_collaboration(self, commit: Any) -> Tuple[float, float, float]:
        """
        分析提交的协作贡献（优化版，添加缓存）。
        
        Args:
            commit: Git提交对象。
        
        Returns:
            (代码审查得分, 问题解决得分, 合并得分)
        """
        # 检查缓存
        if self.enable_cache and commit.hexsha in self._commit_analysis_cache:
            cached = self._commit_analysis_cache[commit.hexsha]
            if 'collaboration' in cached:
                return cached['collaboration']
        
        message = commit.message.lower()
        
        # 代码审查得分
        review_score = 0.0
        for keyword in self.REVIEW_KEYWORDS:
            if keyword in message:
                review_score += 2.0
                break
        
        # 问题解决得分
        issue_score = 0.0
        for keyword in self.ISSUE_KEYWORDS:
            if keyword in message:
                issue_score += 2.0
                # 检查是否有Issue编号引用
                if re.search(r'#\d+', message):
                    issue_score += 1.0
                break
        
        # 合并得分
        merge_score = 0.0
        for keyword in self.MERGE_KEYWORDS:
            if keyword in message:
                merge_score += 1.5
                break
        
        result = (review_score, issue_score, merge_score)
        
        # 缓存结果
        if self.enable_cache:
            if commit.hexsha not in self._commit_analysis_cache:
                self._commit_analysis_cache[commit.hexsha] = {}
            self._commit_analysis_cache[commit.hexsha]['collaboration'] = result
        
        return result
    
    @performance_monitor
    def _analyze_documentation(self, commit: Any) -> Tuple[int, int, int]:
        """
        分析提交的文档贡献（优化版，添加缓存）。
        
        Args:
            commit: Git提交对象。
        
        Returns:
            (文档文件数, 新增行数, 删除行数)
        """
        # 检查缓存
        if self.enable_cache and commit.hexsha in self._commit_analysis_cache:
            cached = self._commit_analysis_cache[commit.hexsha]
            if 'documentation' in cached:
                return cached['documentation']
        
        _, doc_files, _ = self._extract_commit_files(commit)
        
        doc_lines_added = 0
        doc_lines_deleted = 0
        
        if commit.parents and doc_files:
            parent = commit.parents[0]
            diff = parent.diff(commit)
            
            for item in diff:
                path = item.a_path or item.b_path
                if path in doc_files:
                    try:
                        diff_lines = item.diff.decode('utf-8', errors='ignore').split('\n')
                        for line in diff_lines:
                            if line.startswith('+') and not line.startswith('+++'):
                                doc_lines_added += 1
                            elif line.startswith('-') and not line.startswith('---'):
                                doc_lines_deleted += 1
                    except Exception:
                        pass
        
        result = (len(doc_files), doc_lines_added, doc_lines_deleted)
        
        # 缓存结果
        if self.enable_cache:
            if commit.hexsha not in self._commit_analysis_cache:
                self._commit_analysis_cache[commit.hexsha] = {}
            self._commit_analysis_cache[commit.hexsha]['documentation'] = result
        
        return result
    
    @performance_monitor
    def _evaluate_code_quality(
        self,
        local_path: str,
        code_files: List[str],
        commit: Any
    ) -> CodeQualityScore:
        """
        评估代码质量（优化版，添加缓存）。
        
        Args:
            local_path: 本地仓库路径。
            code_files: 代码文件列表。
            commit: Git提交对象。
        
        Returns:
            代码质量得分。
        """
        score = CodeQualityScore()
        
        if not self.quality_evaluator or not code_files:
            return score
        
        # 检查缓存
        cache_key = f"{commit.hexsha}_{len(code_files)}"
        if self.enable_cache and cache_key in self._commit_analysis_cache:
            cached = self._commit_analysis_cache[cache_key]
            if 'code_quality' in cached:
                return cached['code_quality']
        
        total_score = 0.0
        file_count = 0
        dimension_totals = {
            'readability': 0.0,
            'maintainability': 0.0,
            'performance': 0.0,
            'error_handling': 0.0,
            'security': 0.0
        }
        
        # 评估每个代码文件
        for file_path in code_files:
            full_path = os.path.join(local_path, file_path)
            
            # 检查文件是否存在（可能已被删除）
            if not os.path.exists(full_path):
                continue
            
            try:
                report = self.quality_evaluator.evaluate_file(full_path)
                total_score += report.total_score
                file_count += 1
                
                # 累加各维度得分
                for dimension, result in report.dimensions.items():
                    if dimension in dimension_totals:
                        dimension_totals[dimension] += result.score
            except Exception as e:
                logger.warning(f"评估文件 {file_path} 失败: {e}")
                continue
        
        # 计算平均得分
        if file_count > 0:
            score.total_score = total_score
            score.file_count = file_count
            score.avg_score = total_score / file_count
            score.dimension_scores = {
                k: v / file_count for k, v in dimension_totals.items()
            }
        
        # 缓存结果
        if self.enable_cache:
            if cache_key not in self._commit_analysis_cache:
                self._commit_analysis_cache[cache_key] = {}
            self._commit_analysis_cache[cache_key]['code_quality'] = score
        
        return score
    
    def _calculate_documentation_score(
        self,
        doc_files_count: int,
        doc_lines_added: int,
        doc_lines_deleted: int
    ) -> DocumentationScore:
        """
        计算文档贡献得分。
        
        Args:
            doc_files_count: 文档文件数。
            doc_lines_added: 新增行数。
            doc_lines_deleted: 删除行数。
        
        Returns:
            文档贡献得分。
        """
        score = DocumentationScore()
        score.doc_files_count = doc_files_count
        score.doc_lines_added = doc_lines_added
        score.doc_lines_deleted = doc_lines_deleted
        
        # 文档数量得分（每个文档文件2分，最多10分）
        score.completeness_score = min(doc_files_count * 2.0, 10.0)
        
        # 文档质量得分（基于行数变化）
        net_lines = doc_lines_added - doc_lines_deleted
        if net_lines > 0:
            # 新增文档内容
            score.doc_quality_score = min(net_lines * 0.1, 10.0)
        elif net_lines < 0:
            # 删除文档内容（可能是清理过时文档）
            score.doc_quality_score = min(abs(net_lines) * 0.05, 5.0)
        else:
            score.doc_quality_score = 0.0
        
        # 总分
        score.total_score = score.completeness_score + score.doc_quality_score
        
        return score
    
    @performance_monitor
    def calculate_contribution(
        self,
        local_path: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        计算贡献度（优化版，添加智能批次调整）。
        
        Args:
            local_path: 本地仓库路径。
            since: 开始时间。
            until: 结束时间。
        
        Returns:
            贡献度分析结果，按作者分组。
        
        Raises:
            RepositoryNotFoundError: 仓库不存在时抛出。
            EmptyRepositoryError: 仓库为空时抛出。
            InvalidDateError: 日期参数无效时抛出。
        """
        # 输入验证
        if not local_path or not isinstance(local_path, str):
            logger.error("本地路径无效")
            return {}
        
        # 清理路径
        local_path = local_path.strip()
        if VALIDATORS_AVAILABLE:
            try:
                local_path = sanitize_path(local_path)
            except Exception as e:
                logger.error(f"路径清理失败: {e}")
                return []
        
        # 验证日期参数
        if since is not None and not isinstance(since, datetime):
            error_msg = "since参数必须是datetime类型"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidDateError(str(since), "datetime对象")
            return {}
        
        if until is not None and not isinstance(until, datetime):
            error_msg = "until参数必须是datetime类型"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise InvalidDateError(str(until), "datetime对象")
            return {}
        
        # 验证日期范围
        if since and until and since > until:
            error_msg = f"开始时间 {since} 晚于结束时间 {until}"
            logger.error(error_msg)
            return {}
        
        try:
            if not RepositoryManager.is_git_repo(local_path):
                error_msg = f"路径不是Git仓库: {local_path}"
                logger.error(error_msg)
                if EXCEPTIONS_AVAILABLE:
                    raise RepositoryNotFoundError(local_path)
                return {}
            
            repo = Repo(local_path)
            
            # 检查仓库是否有提交记录
            try:
                commit_count = sum(1 for _ in repo.iter_commits())
                if commit_count == 0:
                    error_msg = f"仓库为空，没有提交记录: {local_path}"
                    logger.warning(error_msg)
                    if EXCEPTIONS_AVAILABLE:
                        raise EmptyRepositoryError(local_path)
                    return {}
            except Exception as e:
                logger.warning(f"检查提交记录时出错: {e}")
            
            # 智能调整批次大小
            if self.enable_parallel and PERFORMANCE_OPTIMIZER_AVAILABLE:
                adjusted_batch_size = ParallelProcessor.adaptive_batch_size(
                    commit_count,
                    avg_item_size=1024,  # 估计每个提交对象约1KB
                    memory_limit_mb=500
                )
                self.batch_size = min(self.batch_size, adjusted_batch_size)
                logger.info(f"智能调整批次大小为: {self.batch_size}")
            
            # 根据算法模式选择计算方法
            if self.algorithm_mode == AlgorithmMode.LEGACY:
                return self._calculate_contribution_legacy(repo, since, until)
            else:
                return self._calculate_contribution_quality(repo, local_path, since, until)
        
        except GitCommandError as e:
            logger.error(f"计算贡献度失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"计算贡献度时发生未知错误: {e}")
            return {}
    
    def _calculate_contribution_legacy(
        self,
        repo: Repo,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        使用旧算法计算贡献度（基于数量统计）。
        
        Args:
            repo: Git仓库对象。
            since: 开始时间。
            until: 结束时间。
        
        Returns:
            贡献度分析结果。
        """
        author_stats: Dict[str, Dict[str, float]] = {}
        
        # 构建查询参数
        kwargs: Dict[str, Any] = {}
        if since:
            kwargs['since'] = since
        if until:
            kwargs['until'] = until
        
        # 遍历提交记录
        for commit in repo.iter_commits(**kwargs):
            author = commit.author.name
            
            # 初始化作者统计信息
            if author not in author_stats:
                author_stats[author] = {
                    'commits': 0,
                    'files_changed': 0,
                    'insertions': 0,
                    'deletions': 0,
                    'total_changes': 0,
                    'value_score': 0.0
                }
            
            # 统计提交次数
            author_stats[author]['commits'] += 1
            
            # 分析提交diff
            files_changed, insertions, deletions = self._analyze_commit_diff(commit)
            author_stats[author]['files_changed'] += files_changed
            author_stats[author]['insertions'] += insertions
            author_stats[author]['deletions'] += deletions
            author_stats[author]['total_changes'] += insertions + deletions
            
            # 评估提交价值
            value_score = self._calculate_commit_value(commit, author_stats)
            author_stats[author]['value_score'] += value_score
        
        # 计算最终贡献度分数
        for author, stats in author_stats.items():
            # 综合得分计算
            commits_score = stats['commits'] * 2
            files_score = stats['files_changed'] * 1.5
            changes_score = stats['total_changes'] * 0.5
            value_score = stats['value_score'] * 3
            
            total_score = commits_score + files_score + changes_score + value_score
            author_stats[author]['total_score'] = total_score
        
        # 按总得分排序
        sorted_authors = sorted(
            author_stats.items(),
            key=lambda x: x[1]['total_score'],
            reverse=True
        )
        
        # 打印贡献度分析结果
        logger.info("\n贡献度分析结果（旧算法）:")
        logger.info("=" * 80)
        logger.info(f"{'作者':<20} {'提交次数':<10} {'文件变更':<10} {'代码变更':<10} {'价值得分':<10} {'总得分':<10}")
        logger.info("-" * 80)
        
        for author, stats in sorted_authors:
            logger.info(
                f"{author:<20} {int(stats['commits']):<10} "
                f"{int(stats['files_changed']):<10} {int(stats['total_changes']):<10} "
                f"{stats['value_score']:<10.1f} {stats['total_score']:<10.1f}"
            )
        
        logger.info("=" * 80)
        
        return author_stats
    
    def _calculate_contribution_quality(
        self,
        repo: Repo,
        local_path: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        使用新算法计算贡献度（基于代码质量）。
        
        Args:
            repo: Git仓库对象。
            local_path: 本地仓库路径。
            since: 开始时间。
            until: 结束时间。
        
        Returns:
            贡献度分析结果。
        """
        author_scores: Dict[str, ContributionScore] = {}
        
        # 构建查询参数
        kwargs: Dict[str, Any] = {}
        if since:
            kwargs['since'] = since
        if until:
            kwargs['until'] = until
        
        # 获取所有提交
        commits = list(repo.iter_commits(**kwargs))
        total_commits = len(commits)
        logger.info(f"获取到 {total_commits} 条提交记录")
        
        # 分批处理提交
        if self.enable_parallel and total_commits > self.batch_size:
            # 使用并行分批处理
            result = self._process_commits_parallel(commits, local_path)
            author_scores = result
        else:
            # 串行处理
            author_scores = self._process_commits_serial(commits, local_path)
        
        # 计算最终得分
        result = self._finalize_scores(author_scores)
        
        # 按总得分排序
        sorted_authors = sorted(
            result.items(),
            key=lambda x: x[1]['total_score'],
            reverse=True
        )
        
        # 打印贡献度分析结果
        logger.info("\n贡献度分析结果（新算法 - 基于代码质量）:")
        logger.info("=" * 100)
        logger.info(
            f"{'作者':<20} {'代码质量':<12} {'协作贡献':<12} "
            f"{'文档贡献':<12} {'总得分':<12}"
        )
        logger.info("-" * 100)
        
        for author, stats in sorted_authors:
            logger.info(
                f"{author:<20} {stats['code_quality_score']:<12.1f} "
                f"{stats['collaboration_score']:<12.1f} "
                f"{stats['documentation_score']:<12.1f} "
                f"{stats['total_score']:<12.1f}"
            )
        
        logger.info("=" * 100)
        
        return result
    
    def _process_commits_serial(
        self,
        commits: List[Any],
        local_path: str
    ) -> Dict[str, ContributionScore]:
        """
        串行处理提交记录。
        
        Args:
            commits: 提交列表。
            local_path: 本地仓库路径。
        
        Returns:
            作者得分字典。
        """
        author_scores: Dict[str, ContributionScore] = {}
        
        for commit in commits:
            author = commit.author.name
            
            # 初始化作者得分
            if author not in author_scores:
                author_scores[author] = ContributionScore(
                    author=author,
                    algorithm_mode=AlgorithmMode.QUALITY
                )
            
            score = author_scores[author]
            
            # 1. 分析协作贡献
            review_score, issue_score, merge_score = self._analyze_collaboration(commit)
            score.collaboration_score.code_review_score += review_score
            score.collaboration_score.issue_resolution_score += issue_score
            score.collaboration_score.merge_score += merge_score
            
            if review_score > 0:
                score.collaboration_score.review_count += 1
            if issue_score > 0:
                score.collaboration_score.issue_count += 1
            if merge_score > 0:
                score.collaboration_score.merge_count += 1
            
            # 2. 分析文档贡献
            doc_files, doc_added, doc_deleted = self._analyze_documentation(commit)
            score.documentation_score.doc_files_count += doc_files
            score.documentation_score.doc_lines_added += doc_added
            score.documentation_score.doc_lines_deleted += doc_deleted
            
            # 3. 分析代码质量（仅评估代码文件）
            code_files, _, _ = self._extract_commit_files(commit)
            if code_files and self.quality_evaluator:
                quality_score = self._evaluate_code_quality(local_path, code_files, commit)
                score.code_quality_score.total_score += quality_score.total_score
                score.code_quality_score.file_count += quality_score.file_count
                
                # 累加各维度得分
                for dimension, dim_score in quality_score.dimension_scores.items():
                    if dimension not in score.code_quality_score.dimension_scores:
                        score.code_quality_score.dimension_scores[dimension] = 0.0
                    score.code_quality_score.dimension_scores[dimension] += dim_score
        
        return author_scores
    
    def _process_commits_parallel(
        self,
        commits: List[Any],
        local_path: str
    ) -> Dict[str, ContributionScore]:
        """
        并行处理提交记录。
        
        Args:
            commits: 提交列表。
            local_path: 本地仓库路径。
        
        Returns:
            作者得分字典。
        """
        # 分批
        batches = [
            commits[i:i + self.batch_size]
            for i in range(0, len(commits), self.batch_size)
        ]
        
        logger.info(f"将 {len(commits)} 个提交分为 {len(batches)} 批次并行处理")
        
        # 并行处理每批
        def process_batch(commit_batch):
            """处理一批提交。"""
            batch_scores: Dict[str, ContributionScore] = {}
            
            for commit in commit_batch:
                author = commit.author.name
                
                if author not in batch_scores:
                    batch_scores[author] = ContributionScore(
                        author=author,
                        algorithm_mode=AlgorithmMode.QUALITY
                    )
                
                score = batch_scores[author]
                
                # 分析协作贡献
                review_score, issue_score, merge_score = self._analyze_collaboration(commit)
                score.collaboration_score.code_review_score += review_score
                score.collaboration_score.issue_resolution_score += issue_score
                score.collaboration_score.merge_score += merge_score
                
                if review_score > 0:
                    score.collaboration_score.review_count += 1
                if issue_score > 0:
                    score.collaboration_score.issue_count += 1
                if merge_score > 0:
                    score.collaboration_score.merge_count += 1
                
                # 分析文档贡献
                doc_files, doc_added, doc_deleted = self._analyze_documentation(commit)
                score.documentation_score.doc_files_count += doc_files
                score.documentation_score.doc_lines_added += doc_added
                score.documentation_score.doc_lines_deleted += doc_deleted
                
                # 分析代码质量
                code_files, _, _ = self._extract_commit_files(commit)
                if code_files and self.quality_evaluator:
                    quality_score = self._evaluate_code_quality(local_path, code_files, commit)
                    score.code_quality_score.total_score += quality_score.total_score
                    score.code_quality_score.file_count += quality_score.file_count
                    
                    for dimension, dim_score in quality_score.dimension_scores.items():
                        if dimension not in score.code_quality_score.dimension_scores:
                            score.code_quality_score.dimension_scores[dimension] = 0.0
                        score.code_quality_score.dimension_scores[dimension] += dim_score
            
            return batch_scores
        
        # 并行执行
        batch_results = ParallelProcessor.parallel_map(
            process_batch,
            batches,
            task_type='cpu'
        )
        
        # 合并结果
        author_scores: Dict[str, ContributionScore] = {}
        
        for batch_result in batch_results:
            if batch_result is None:
                continue
            
            for author, score in batch_result.items():
                if author not in author_scores:
                    author_scores[author] = ContributionScore(
                        author=author,
                        algorithm_mode=AlgorithmMode.QUALITY
                    )
                
                # 合并得分
                existing_score = author_scores[author]
                existing_score.collaboration_score.code_review_score += score.collaboration_score.code_review_score
                existing_score.collaboration_score.issue_resolution_score += score.collaboration_score.issue_resolution_score
                existing_score.collaboration_score.merge_score += score.collaboration_score.merge_score
                existing_score.collaboration_score.review_count += score.collaboration_score.review_count
                existing_score.collaboration_score.issue_count += score.collaboration_score.issue_count
                existing_score.collaboration_score.merge_count += score.collaboration_score.merge_count
                
                existing_score.documentation_score.doc_files_count += score.documentation_score.doc_files_count
                existing_score.documentation_score.doc_lines_added += score.documentation_score.doc_lines_added
                existing_score.documentation_score.doc_lines_deleted += score.documentation_score.doc_lines_deleted
                
                existing_score.code_quality_score.total_score += score.code_quality_score.total_score
                existing_score.code_quality_score.file_count += score.code_quality_score.file_count
                
                for dimension, dim_score in score.code_quality_score.dimension_scores.items():
                    if dimension not in existing_score.code_quality_score.dimension_scores:
                        existing_score.code_quality_score.dimension_scores[dimension] = 0.0
                    existing_score.code_quality_score.dimension_scores[dimension] += dim_score
        
        return author_scores
    
    def _finalize_scores(
        self,
        author_scores: Dict[str, ContributionScore]
    ) -> Dict[str, Dict[str, Any]]:
        """
        计算最终得分。
        
        Args:
            author_scores: 作者得分字典。
        
        Returns:
            最终得分字典。
        """
        result = {}
        
        for author, score in author_scores.items():
            # 计算代码质量平均得分
            if score.code_quality_score.file_count > 0:
                score.code_quality_score.avg_score = (
                    score.code_quality_score.total_score / score.code_quality_score.file_count
                )
                # 归一化到0-100分
                score.code_quality_score.total_score = min(
                    score.code_quality_score.avg_score * 10,
                    100.0
                )
            else:
                # 如果没有代码文件，给予基础分
                score.code_quality_score.total_score = 50.0
            
            # 计算协作贡献总分
            score.collaboration_score.total_score = (
                score.collaboration_score.code_review_score +
                score.collaboration_score.issue_resolution_score +
                score.collaboration_score.merge_score
            )
            
            # 计算文档贡献总分
            doc_score = self._calculate_documentation_score(
                score.documentation_score.doc_files_count,
                score.documentation_score.doc_lines_added,
                score.documentation_score.doc_lines_deleted
            )
            score.documentation_score.total_score = doc_score.total_score
            score.documentation_score.doc_quality_score = doc_score.doc_quality_score
            score.documentation_score.completeness_score = doc_score.completeness_score
            
            # 计算总得分
            score.total_score = (
                score.code_quality_score.total_score * self.QUALITY_WEIGHT +
                score.collaboration_score.total_score * self.COLLABORATION_WEIGHT +
                score.documentation_score.total_score * self.DOCUMENTATION_WEIGHT
            )
            
            # 转换为字典格式
            result[author] = {
                'code_quality_score': score.code_quality_score.total_score,
                'code_quality_avg': score.code_quality_score.avg_score,
                'code_files_count': score.code_quality_score.file_count,
                'collaboration_score': score.collaboration_score.total_score,
                'review_count': score.collaboration_score.review_count,
                'issue_count': score.collaboration_score.issue_count,
                'merge_count': score.collaboration_score.merge_score,
                'documentation_score': score.documentation_score.total_score,
                'doc_files_count': score.documentation_score.doc_files_count,
                'total_score': score.total_score,
                'algorithm_mode': self.algorithm_mode.value
            }
        
        return result


class ReportGenerator:
    """报告生成器，负责生成分析报告。"""

    @staticmethod
    def generate_markdown_report(
        local_path: str,
        output_file: str = "git_analysis_report.md",
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        algorithm_mode: AlgorithmMode = AlgorithmMode.QUALITY
    ) -> bool:
        """
        生成Markdown格式的分析报告。

        Args:
            local_path: 本地仓库路径。
            output_file: 输出文件路径。
            since: 开始时间。
            until: 结束时间。
            algorithm_mode: 算法模式。

        Returns:
            报告生成是否成功。
        """
        try:
            if not RepositoryManager.is_git_repo(local_path):
                logger.error(f"错误: {local_path} 不是Git仓库")
                return False

            # 创建贡献度计算器
            calculator = ContributionCalculator(algorithm_mode=algorithm_mode)
            
            # 获取数据
            contribution_data = calculator.calculate_contribution(local_path, since, until)
            commits = CommitAnalyzer.get_commits(local_path, since, until)

            # 生成Markdown内容
            markdown_content = "# Git仓库分析报告\n\n"

            # 添加报告生成时间
            markdown_content += "## 报告信息\n"
            markdown_content += f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            markdown_content += f"- 分析仓库: {local_path}\n"
            markdown_content += f"- 算法模式: {algorithm_mode.value} ({'基于代码质量' if algorithm_mode == AlgorithmMode.QUALITY else '基于数量统计'})\n"
            if since:
                markdown_content += f"- 分析开始时间: {since.strftime('%Y-%m-%d')}\n"
            if until:
                markdown_content += f"- 分析结束时间: {until.strftime('%Y-%m-%d')}\n"
            markdown_content += "\n"

            # 添加贡献度排名
            markdown_content += "## 贡献度排名\n"
            if contribution_data:
                # 按总得分排序
                sorted_authors = sorted(
                    contribution_data.items(),
                    key=lambda x: x[1]['total_score'],
                    reverse=True
                )
                
                # 根据算法模式生成不同的表格
                if algorithm_mode == AlgorithmMode.QUALITY:
                    markdown_content += "| 排名 | 作者 | 代码质量得分 | 协作贡献得分 | 文档贡献得分 | 总得分 |\n"
                    markdown_content += "|------|------|--------------|--------------|--------------|--------|\n"
                    
                    for i, (author, stats) in enumerate(sorted_authors, 1):
                        markdown_content += (
                            f"| {i} | {author} | {stats['code_quality_score']:.1f} | "
                            f"{stats['collaboration_score']:.1f} | {stats['documentation_score']:.1f} | "
                            f"{stats['total_score']:.1f} |\n"
                        )
                else:
                    markdown_content += "| 排名 | 作者 | 提交次数 | 文件变更 | 代码变更 | 价值得分 | 总得分 |\n"
                    markdown_content += "|------|------|----------|----------|----------|----------|--------|\n"
                    
                    for i, (author, stats) in enumerate(sorted_authors, 1):
                        markdown_content += (
                            f"| {i} | {author} | {int(stats['commits'])} | "
                            f"{int(stats['files_changed'])} | {int(stats['total_changes'])} | "
                            f"{stats['value_score']:.1f} | {stats['total_score']:.1f} |\n"
                        )
            else:
                markdown_content += "暂无贡献数据\n"
            markdown_content += "\n"

            # 添加详细分析（仅新算法）
            if algorithm_mode == AlgorithmMode.QUALITY and contribution_data:
                markdown_content += "## 详细分析\n\n"
                
                # 代码质量分析
                markdown_content += "### 代码质量分析\n"
                markdown_content += "| 作者 | 代码文件数 | 平均质量得分 | 质量等级 |\n"
                markdown_content += "|------|------------|--------------|----------|\n"
                
                for author, stats in sorted_authors:
                    avg_score = stats.get('code_quality_avg', 0)
                    if avg_score >= 80:
                        quality_level = "优秀"
                    elif avg_score >= 60:
                        quality_level = "良好"
                    elif avg_score >= 40:
                        quality_level = "合格"
                    else:
                        quality_level = "待改进"
                    
                    markdown_content += (
                        f"| {author} | {stats['code_files_count']} | "
                        f"{avg_score:.1f} | {quality_level} |\n"
                    )
                markdown_content += "\n"
                
                # 协作贡献分析
                markdown_content += "### 协作贡献分析\n"
                markdown_content += "| 作者 | 代码审查 | 问题解决 | 合并贡献 | 协作总分 |\n"
                markdown_content += "|------|----------|----------|----------|----------|\n"
                
                for author, stats in sorted_authors:
                    markdown_content += (
                        f"| {author} | {stats['review_count']} | "
                        f"{stats['issue_count']} | {stats['merge_count']} | "
                        f"{stats['collaboration_score']:.1f} |\n"
                    )
                markdown_content += "\n"
                
                # 文档贡献分析
                markdown_content += "### 文档贡献分析\n"
                markdown_content += "| 作者 | 文档文件数 | 文档得分 |\n"
                markdown_content += "|------|------------|----------|\n"
                
                for author, stats in sorted_authors:
                    markdown_content += (
                        f"| {author} | {stats['doc_files_count']} | "
                        f"{stats['documentation_score']:.1f} |\n"
                    )
                markdown_content += "\n"

            # 添加最近提交记录
            markdown_content += "## 最近提交记录\n"
            if commits:
                for i, commit in enumerate(commits[:10], 1):  # 显示最近10条提交
                    markdown_content += f"### {i}. {commit['hash'][:7]}\n"
                    markdown_content += f"- 作者: {commit['author']} <{commit['email']}>\n"
                    markdown_content += f"- 日期: {commit['date'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                    markdown_content += f"- 提交信息: {commit['message']}\n\n"
            else:
                markdown_content += "暂无提交记录\n"
            markdown_content += "\n"

            # 添加团队整体分析
            markdown_content += "## 团队整体分析\n"
            if contribution_data:
                total_authors = len(contribution_data)
                
                if algorithm_mode == AlgorithmMode.QUALITY:
                    avg_quality = sum(stats['code_quality_score'] for stats in contribution_data.values()) / total_authors
                    avg_collab = sum(stats['collaboration_score'] for stats in contribution_data.values()) / total_authors
                    avg_doc = sum(stats['documentation_score'] for stats in contribution_data.values()) / total_authors
                    
                    markdown_content += f"- 参与开发者: {total_authors} 人\n"
                    markdown_content += f"- 平均代码质量得分: {avg_quality:.1f} 分\n"
                    markdown_content += f"- 平均协作贡献得分: {avg_collab:.1f} 分\n"
                    markdown_content += f"- 平均文档贡献得分: {avg_doc:.1f} 分\n\n"
                else:
                    total_commits = sum(int(stats['commits']) for stats in contribution_data.values())
                    total_files_changed = sum(int(stats['files_changed']) for stats in contribution_data.values())
                    total_changes = sum(int(stats['total_changes']) for stats in contribution_data.values())
                    
                    markdown_content += f"- 参与开发者: {total_authors} 人\n"
                    markdown_content += f"- 总提交次数: {total_commits} 次\n"
                    markdown_content += f"- 总文件变更: {total_files_changed} 个\n"
                    markdown_content += f"- 总代码变更: {total_changes} 行\n\n"

                # 分析最活跃的开发者
                if sorted_authors:
                    most_active = sorted_authors[0]
                    markdown_content += "### 最活跃开发者\n"
                    markdown_content += f"- 姓名: {most_active[0]}\n"
                    markdown_content += f"- 总得分: {most_active[1]['total_score']:.1f} 分\n"
                    
                    if algorithm_mode == AlgorithmMode.QUALITY:
                        markdown_content += f"- 代码质量得分: {most_active[1]['code_quality_score']:.1f} 分\n"
                        markdown_content += f"- 协作贡献得分: {most_active[1]['collaboration_score']:.1f} 分\n"
                        markdown_content += f"- 文档贡献得分: {most_active[1]['documentation_score']:.1f} 分\n"
                    else:
                        markdown_content += f"- 提交次数: {int(most_active[1]['commits'])} 次\n"
            else:
                markdown_content += "暂无团队分析数据\n"

            # 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            logger.info(f"报告生成成功！文件保存至: {output_file}")
            
            # 生成性能优化建议报告（如果性能优化模块可用）
            if PERFORMANCE_OPTIMIZER_AVAILABLE:
                try:
                    metrics = PerformanceMonitor.get_all_metrics()
                    if metrics:
                        perf_report = OptimizationSuggester.generate_optimization_report(metrics)
                        perf_file = output_file.replace('.md', '_performance.md')
                        with open(perf_file, 'w', encoding='utf-8') as f:
                            f.write(perf_report)
                        logger.info(f"性能优化建议报告已生成: {perf_file}")
                except Exception as e:
                    logger.warning(f"生成性能报告失败: {e}")
            
            return True
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return False


class GitAnalyzerCLI:
    """Git分析工具命令行接口。"""

    @staticmethod
    def parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """
        解析日期字符串。

        Args:
            date_str: 日期字符串，格式为YYYY-MM-DD。

        Returns:
            datetime对象或None。
        """
        if date_str:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                logger.error(f"日期格式错误: {date_str}，应为YYYY-MM-DD")
                return None
        return None

    @staticmethod
    def main() -> None:
        """主函数，处理命令行参数并执行相应操作。"""
        parser = ArgumentParser(
            prog='git-analyzer',
            description='Git仓库分析工具',
            epilog='更多信息请访问: https://github.com/git-analyzer'
        )

        # 创建子命令解析器
        subparsers = parser.add_subparsers(
            dest='command',
            help='可用命令'
        )

        # status命令
        status_parser = subparsers.add_parser('status', help='检查仓库状态')
        status_parser.add_argument('path', nargs='?', default='.', help='仓库路径')

        # clone命令
        clone_parser = subparsers.add_parser('clone', help='克隆仓库')
        clone_parser.add_argument('url', help='仓库URL')
        clone_parser.add_argument('path', help='本地路径')

        # update命令
        update_parser = subparsers.add_parser('update', help='更新仓库')
        update_parser.add_argument('path', nargs='?', default='.', help='仓库路径')

        # branches命令
        branches_parser = subparsers.add_parser('branches', help='列出分支')
        branches_parser.add_argument('path', nargs='?', default='.', help='仓库路径')

        # switch命令
        switch_parser = subparsers.add_parser('switch', help='切换分支')
        switch_parser.add_argument('branch', help='分支名称')
        switch_parser.add_argument('path', nargs='?', default='.', help='仓库路径')

        # commits命令
        commits_parser = subparsers.add_parser('commits', help='查看提交记录')
        commits_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        commits_parser.add_argument('--since', help='开始时间 (YYYY-MM-DD)')
        commits_parser.add_argument('--until', help='结束时间 (YYYY-MM-DD)')

        # analyze命令
        analyze_parser = subparsers.add_parser('analyze', help='分析贡献度')
        analyze_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        analyze_parser.add_argument('--since', help='开始时间 (YYYY-MM-DD)')
        analyze_parser.add_argument('--until', help='结束时间 (YYYY-MM-DD)')
        analyze_parser.add_argument(
            '--algorithm',
            choices=['legacy', 'quality'],
            default='quality',
            help='算法模式: legacy(旧算法-基于数量统计) 或 quality(新算法-基于代码质量，默认)'
        )
        analyze_parser.add_argument(
            '--no-parallel',
            action='store_true',
            help='禁用并行处理（用于调试）'
        )

        # report命令
        report_parser = subparsers.add_parser('report', help='生成分析报告')
        report_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        report_parser.add_argument('--output', default='git_analysis_report.md', help='输出文件路径')
        report_parser.add_argument('--since', help='开始时间 (YYYY-MM-DD)')
        report_parser.add_argument('--until', help='结束时间 (YYYY-MM-DD)')
        report_parser.add_argument(
            '--algorithm',
            choices=['legacy', 'quality'],
            default='quality',
            help='算法模式: legacy(旧算法-基于数量统计) 或 quality(新算法-基于代码质量，默认)'
        )

        # 解析参数
        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        # 处理路径参数
        path = os.path.abspath(args.path)

        if args.command == 'status':
            is_repo = RepositoryManager.is_git_repo(path)
            logger.info(f"{path} {'是' if is_repo else '不是'} Git仓库")

        elif args.command == 'clone':
            RepositoryManager.clone_repo(args.url, path)

        elif args.command == 'update':
            RepositoryManager.update_repo(path)

        elif args.command == 'branches':
            RepositoryManager.list_branches(path)

        elif args.command == 'switch':
            RepositoryManager.switch_branch(path, args.branch)

        elif args.command == 'commits':
            since = GitAnalyzerCLI.parse_date(args.since)
            until = GitAnalyzerCLI.parse_date(args.until)
            CommitAnalyzer.get_commits(path, since, until)

        elif args.command == 'analyze':
            since = GitAnalyzerCLI.parse_date(args.since)
            until = GitAnalyzerCLI.parse_date(args.until)
            algorithm_mode = AlgorithmMode.LEGACY if args.algorithm == 'legacy' else AlgorithmMode.QUALITY
            enable_parallel = not getattr(args, 'no_parallel', False)
            calculator = ContributionCalculator(algorithm_mode=algorithm_mode, enable_parallel=enable_parallel)
            calculator.calculate_contribution(path, since, until)

        elif args.command == 'report':
            since = GitAnalyzerCLI.parse_date(args.since)
            until = GitAnalyzerCLI.parse_date(args.until)
            algorithm_mode = AlgorithmMode.LEGACY if args.algorithm == 'legacy' else AlgorithmMode.QUALITY
            ReportGenerator.generate_markdown_report(path, args.output, since, until, algorithm_mode)


if __name__ == '__main__':
    GitAnalyzerCLI.main()
