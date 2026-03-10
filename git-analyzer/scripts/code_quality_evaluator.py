#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码质量评估器

提供五维度代码质量评估功能，包括可读性、可维护性、性能效率、错误处理和安全性评估。

WING
"""

import os
import re
import ast
import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# 导入自定义异常类
try:
    from exceptions import (
        GitAnalyzerError,
        FileNotFoundError as CustomFileNotFoundError,
        FileReadError,
        FileTooLargeError,
        SyntaxErrorInCode,
        UnsupportedLanguageError,
        InvalidParameterError,
        InvalidConfigurationError
    )
    EXCEPTIONS_AVAILABLE = True
except ImportError:
    EXCEPTIONS_AVAILABLE = False
    logging.warning("exceptions模块未找到，将使用基础异常处理")

# 导入验证器
try:
    from validators import (
        validate_path,
        validate_type,
        validate_range,
        validate_positive,
        sanitize_path
    )
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False
    logging.warning("validators模块未找到，输入验证功能将受限")
from functools import lru_cache

# 导入性能优化模块
try:
    from performance_optimizer import (
        performance_monitor,
        cached,
        ParallelProcessor,
        PerformanceMonitor
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


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    """质量等级枚举。"""
    EXCELLENT = "优秀"
    GOOD = "良好"
    QUALIFIED = "合格"
    UNQUALIFIED = "不合格"


class ProjectType(Enum):
    """项目类型枚举。"""
    WEB_APP = "web_app"
    CLI_TOOL = "cli_tool"
    LIBRARY = "library"
    DATA_SCIENCE = "data_science"
    OTHER = "other"


class ProjectStage(Enum):
    """项目阶段枚举。"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class EvaluationResult:
    """评估结果数据类。"""
    dimension: str
    score: float
    max_score: float
    details: Dict[str, float] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        """计算得分百分比。"""
        return (self.score / self.max_score * 100) if self.max_score > 0 else 0.0


@dataclass
class QualityReport:
    """质量报告数据类。"""
    total_score: float
    max_score: float
    level: QualityLevel
    dimensions: Dict[str, EvaluationResult]
    weight_coefficients: Dict[str, float]
    file_path: str
    suggestions: List[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        """计算总分百分比。"""
        return (self.total_score / self.max_score * 100) if self.max_score > 0 else 0.0


class CodeQualityEvaluator:
    """
    代码质量评估器（优化版）。

    提供五维度代码质量评估功能：
    1. 可读性评估 (0-25分)
    2. 可维护性评估 (0-25分)
    3. 性能效率评估 (0-20分)
    4. 错误处理评估 (0-15分)
    5. 安全性评估 (0-15分)

    总分：0-100分

    验收阈值：
    - 优秀：>= 80分
    - 良好：>= 60分
    - 合格：>= 40分
    - 不合格：< 40分
    
    优化特性：
    - 增强的AST缓存机制
    - 批量并行评估
    - 内存使用优化
    - 细粒度性能监控
    """

    # 维度权重配置
    DIMENSION_WEIGHTS = {
        'readability': 0.25,      # 可读性权重
        'maintainability': 0.25,  # 可维护性权重
        'performance': 0.20,      # 性能效率权重
        'error_handling': 0.15,   # 错误处理权重
        'security': 0.15          # 安全性权重
    }

    # 维度满分配置
    DIMENSION_MAX_SCORES = {
        'readability': 25,
        'maintainability': 25,
        'performance': 20,
        'error_handling': 15,
        'security': 15
    }

    # 验收阈值
    QUALITY_THRESHOLDS = {
        QualityLevel.EXCELLENT: 80,
        QualityLevel.GOOD: 60,
        QualityLevel.QUALIFIED: 40
    }

    # 项目类型权重调整系数
    PROJECT_TYPE_COEFFICIENTS = {
        ProjectType.WEB_APP: {
            'security': 1.2,
            'performance': 1.1,
            'error_handling': 1.1
        },
        ProjectType.CLI_TOOL: {
            'error_handling': 1.2,
            'readability': 1.1
        },
        ProjectType.LIBRARY: {
            'readability': 1.2,
            'maintainability': 1.1
        },
        ProjectType.DATA_SCIENCE: {
            'performance': 1.2,
            'readability': 1.1
        },
        ProjectType.OTHER: {}
    }

    # 项目阶段权重调整系数
    PROJECT_STAGE_COEFFICIENTS = {
        ProjectStage.DEVELOPMENT: {
            'readability': 1.1,
            'maintainability': 1.1
        },
        ProjectStage.TESTING: {
            'error_handling': 1.2,
            'security': 1.1
        },
        ProjectStage.PRODUCTION: {
            'security': 1.3,
            'performance': 1.2,
            'error_handling': 1.2
        }
    }

    # 安全敏感关键词
    SECURITY_KEYWORDS = [
        'password', 'secret', 'key', 'token', 'api_key',
        'private_key', 'credential', 'auth', 'session'
    ]

    # 危险函数列表
    DANGEROUS_FUNCTIONS = [
        'eval', 'exec', 'compile', 'input',  # 代码执行
        'os.system', 'subprocess.call', 'subprocess.Popen',  # 命令执行
        'pickle.loads', 'marshal.loads',  # 反序列化
        'yaml.load',  # YAML解析
        'sql', 'execute', 'raw'  # SQL执行
    ]

    def __init__(
        self,
        project_type: ProjectType = ProjectType.OTHER,
        project_stage: ProjectStage = ProjectStage.DEVELOPMENT,
        team_size: int = 1,
        code_lines: int = 0,
        enable_cache: bool = True,
        cache_size: int = 256
    ):
        """
        初始化代码质量评估器。

        Args:
            project_type: 项目类型。
            project_stage: 项目阶段。
            team_size: 团队规模。
            code_lines: 代码行数。
            enable_cache: 是否启用缓存。
            cache_size: 缓存大小。
        
        Raises:
            InvalidParameterError: 参数无效时抛出。
            InvalidConfigurationError: 配置无效时抛出。
        """
        # 验证项目类型
        if not isinstance(project_type, ProjectType):
            logger.warning(f"项目类型必须是ProjectType枚举，当前类型: {type(project_type)}")
            project_type = ProjectType.OTHER
        
        # 验证项目阶段
        if not isinstance(project_stage, ProjectStage):
            logger.warning(f"项目阶段必须是ProjectStage枚举，当前类型: {type(project_stage)}")
            project_stage = ProjectStage.DEVELOPMENT
        
        # 验证团队规模
        if not isinstance(team_size, int) or team_size < 1:
            logger.warning(f"团队规模必须是正整数，当前值: {team_size}")
            team_size = 1
        
        # 验证代码行数
        if not isinstance(code_lines, int) or code_lines < 0:
            logger.warning(f"代码行数必须是非负整数，当前值: {code_lines}")
            code_lines = 0
        
        self.project_type = project_type
        self.project_stage = project_stage
        self.team_size = team_size
        self.code_lines = code_lines
        self.enable_cache = enable_cache and PERFORMANCE_OPTIMIZER_AVAILABLE
        
        try:
            self.weight_coefficients = self._calculate_weight_coefficients()
        except Exception as e:
            logger.error(f"计算权重系数失败: {e}")
            # 使用默认权重
            self.weight_coefficients = self.DIMENSION_WEIGHTS.copy()
        
        # AST缓存配置
        self._ast_cache_enabled = enable_cache
        self._cache_size = cache_size
        
        # 文件内容缓存
        self._file_content_cache: Dict[str, Tuple[str, float]] = {}
    
    @lru_cache(maxsize=128)
    def _parse_ast_cached(self, file_path: str, file_mtime: float) -> Optional[ast.AST]:
        """
        缓存AST解析结果。
        
        Args:
            file_path: 文件路径。
            file_mtime: 文件修改时间（用于缓存失效）。
        
        Returns:
            AST语法树或None。
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
            return ast.parse(code_content)
        except Exception as e:
            logger.error(f"AST解析失败: {e}")
            return None
    
    def _get_ast(self, file_path: str) -> Optional[ast.AST]:
        """
        获取AST语法树（带缓存）。
        
        Args:
            file_path: 文件路径。
        
        Returns:
            AST语法树或None。
        """
        if not self._ast_cache_enabled:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_content = f.read()
                return ast.parse(code_content)
            except Exception as e:
                logger.error(f"AST解析失败: {e}")
                return None
        
        # 使用文件修改时间作为缓存键的一部分
        try:
            file_mtime = os.path.getmtime(file_path)
            return self._parse_ast_cached(file_path, file_mtime)
        except Exception as e:
            logger.error(f"获取文件修改时间失败: {e}")
            return None

    def _calculate_weight_coefficients(self) -> Dict[str, float]:
        """
        计算权重系数。

        基于项目类型、项目阶段、团队规模和代码规模动态调整权重。

        Returns:
            权重系数字典。
        """
        coefficients = self.DIMENSION_WEIGHTS.copy()

        # 应用项目类型系数
        type_coefficients = self.PROJECT_TYPE_COEFFICIENTS.get(self.project_type, {})
        for dimension, coefficient in type_coefficients.items():
            if dimension in coefficients:
                coefficients[dimension] *= coefficient

        # 应用项目阶段系数
        stage_coefficients = self.PROJECT_STAGE_COEFFICIENTS.get(self.project_stage, {})
        for dimension, coefficient in stage_coefficients.items():
            if dimension in coefficients:
                coefficients[dimension] *= coefficient

        # 团队规模调整：大团队更重视可读性和可维护性
        if self.team_size > 5:
            coefficients['readability'] *= 1.1
            coefficients['maintainability'] *= 1.1
        elif self.team_size > 10:
            coefficients['readability'] *= 1.2
            coefficients['maintainability'] *= 1.2

        # 代码规模调整：大型项目更重视性能和可维护性
        if self.code_lines > 10000:
            coefficients['maintainability'] *= 1.15
            coefficients['performance'] *= 1.1
        elif self.code_lines > 50000:
            coefficients['maintainability'] *= 1.25
            coefficients['performance'] *= 1.2

        # 归一化权重，使总和为1.0
        total = sum(coefficients.values())
        if total > 0:
            coefficients = {k: v / total for k, v in coefficients.items()}

        return coefficients

    def _get_adjusted_max_scores(self) -> Dict[str, float]:
        """
        根据权重系数调整各维度的满分。

        Returns:
            调整后的各维度满分。
        """
        adjusted_scores = {}
        for dimension, base_score in self.DIMENSION_MAX_SCORES.items():
            # 根据权重系数调整满分
            weight = self.weight_coefficients.get(dimension, 1.0)
            # 使用权重系数的平方根来平滑调整幅度
            adjusted_score = base_score * (weight ** 0.5)
            adjusted_scores[dimension] = adjusted_score

        # 归一化，确保总和为100
        total = sum(adjusted_scores.values())
        if total > 0:
            scale_factor = 100.0 / total
            adjusted_scores = {k: v * scale_factor for k, v in adjusted_scores.items()}

        return adjusted_scores

    @performance_monitor
    def evaluate_file(self, file_path: str) -> QualityReport:
        """
        评估单个文件的代码质量（优化版，添加缓存）。

        Args:
            file_path: 文件路径。

        Returns:
            质量报告。
        
        Raises:
            FileNotFoundError: 文件不存在时抛出。
            FileReadError: 文件读取失败时抛出。
            FileTooLargeError: 文件过大时抛出。
        """
        # 输入验证
        if not file_path or not isinstance(file_path, str):
            error_msg = "文件路径无效"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise CustomFileNotFoundError(file_path or "")
            raise FileNotFoundError(error_msg)
        
        # 清理路径
        file_path = file_path.strip()
        if VALIDATORS_AVAILABLE:
            try:
                file_path = sanitize_path(file_path)
            except Exception as e:
                logger.error(f"路径清理失败: {e}")
                if EXCEPTIONS_AVAILABLE:
                    raise CustomFileNotFoundError(file_path)
                raise FileNotFoundError(str(e))
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            error_msg = f"文件不存在: {file_path}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise CustomFileNotFoundError(file_path)
            raise FileNotFoundError(error_msg)
        
        # 检查是否为文件
        if not os.path.isfile(file_path):
            error_msg = f"路径不是文件: {file_path}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise CustomFileNotFoundError(file_path)
            raise FileNotFoundError(error_msg)
        
        # 检查文件大小（限制为10MB）
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        try:
            file_size = os.path.getsize(file_path)
            if file_size > MAX_FILE_SIZE:
                error_msg = f"文件过大: {file_path}"
                logger.error(error_msg)
                if EXCEPTIONS_AVAILABLE:
                    raise FileTooLargeError(file_path, file_size, MAX_FILE_SIZE)
                raise ValueError(error_msg)
        except OSError as e:
            error_msg = f"无法获取文件大小: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise FileReadError(file_path, str(e))
            raise IOError(error_msg)
        
        # 读取文件内容（使用缓存）
        code_content = self._read_file_cached(file_path)
        
        # 使用缓存的AST解析
        tree = self._get_ast(file_path)
        if tree is None:
            # 返回最低分报告
            return self._create_minimal_report(file_path, "AST解析失败")

        # 执行五维度评估
        dimensions = {}
        adjusted_max_scores = self._get_adjusted_max_scores()

        try:
            # 1. 可读性评估
            readability_result = self._evaluate_readability(code_content, tree)
            # 根据调整后的满分缩放得分
            scale_factor = adjusted_max_scores['readability'] / self.DIMENSION_MAX_SCORES['readability']
            readability_result.score *= scale_factor
            readability_result.max_score = adjusted_max_scores['readability']
            dimensions['readability'] = readability_result
        except Exception as e:
            logger.warning(f"可读性评估失败: {e}")
            dimensions['readability'] = EvaluationResult(
                dimension='readability',
                score=0.0,
                max_score=adjusted_max_scores['readability'],
                suggestions=[f"可读性评估失败: {e}"]
            )

        try:
            # 2. 可维护性评估
            maintainability_result = self._evaluate_maintainability(code_content, tree)
            scale_factor = adjusted_max_scores['maintainability'] / self.DIMENSION_MAX_SCORES['maintainability']
            maintainability_result.score *= scale_factor
            maintainability_result.max_score = adjusted_max_scores['maintainability']
            dimensions['maintainability'] = maintainability_result
        except Exception as e:
            logger.warning(f"可维护性评估失败: {e}")
            dimensions['maintainability'] = EvaluationResult(
                dimension='maintainability',
                score=0.0,
                max_score=adjusted_max_scores['maintainability'],
                suggestions=[f"可维护性评估失败: {e}"]
            )

        try:
            # 3. 性能效率评估
            performance_result = self._evaluate_performance(code_content, tree)
            scale_factor = adjusted_max_scores['performance'] / self.DIMENSION_MAX_SCORES['performance']
            performance_result.score *= scale_factor
            performance_result.max_score = adjusted_max_scores['performance']
            dimensions['performance'] = performance_result
        except Exception as e:
            logger.warning(f"性能效率评估失败: {e}")
            dimensions['performance'] = EvaluationResult(
                dimension='performance',
                score=0.0,
                max_score=adjusted_max_scores['performance'],
                suggestions=[f"性能效率评估失败: {e}"]
            )

        try:
            # 4. 错误处理评估
            error_handling_result = self._evaluate_error_handling(code_content, tree)
            scale_factor = adjusted_max_scores['error_handling'] / self.DIMENSION_MAX_SCORES['error_handling']
            error_handling_result.score *= scale_factor
            error_handling_result.max_score = adjusted_max_scores['error_handling']
            dimensions['error_handling'] = error_handling_result
        except Exception as e:
            logger.warning(f"错误处理评估失败: {e}")
            dimensions['error_handling'] = EvaluationResult(
                dimension='error_handling',
                score=0.0,
                max_score=adjusted_max_scores['error_handling'],
                suggestions=[f"错误处理评估失败: {e}"]
            )

        try:
            # 5. 安全性评估
            security_result = self._evaluate_security(code_content, tree)
            scale_factor = adjusted_max_scores['security'] / self.DIMENSION_MAX_SCORES['security']
            security_result.score *= scale_factor
            security_result.max_score = adjusted_max_scores['security']
            dimensions['security'] = security_result
        except Exception as e:
            logger.warning(f"安全性评估失败: {e}")
            dimensions['security'] = EvaluationResult(
                dimension='security',
                score=0.0,
                max_score=adjusted_max_scores['security'],
                suggestions=[f"安全性评估失败: {e}"]
            )

        # 计算总分：各维度得分直接相加（总和为100分）
        total_score = sum(result.score for result in dimensions.values())

        # 确定质量等级
        level = self._determine_quality_level(total_score)

        # 生成建议
        suggestions = self._generate_suggestions(dimensions)

        return QualityReport(
            total_score=total_score,
            max_score=100.0,
            level=level,
            dimensions=dimensions,
            weight_coefficients=self.weight_coefficients,
            file_path=file_path,
            suggestions=suggestions
        )
    
    def _read_file_cached(self, file_path: str) -> str:
        """
        读取文件内容（带缓存）。
        
        Args:
            file_path: 文件路径。
        
        Returns:
            文件内容。
        """
        # 检查缓存
        if self.enable_cache and file_path in self._file_content_cache:
            cached_content, cached_mtime = self._file_content_cache[file_path]
            
            # 检查文件是否已修改
            try:
                current_mtime = os.path.getmtime(file_path)
                if current_mtime == cached_mtime:
                    return cached_content
            except Exception:
                pass
        
        # 读取文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code_content = f.read()
        except UnicodeDecodeError as e:
            # 尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    code_content = f.read()
            except Exception as e:
                error_msg = f"文件编码不支持: {e}"
                logger.error(error_msg)
                if EXCEPTIONS_AVAILABLE:
                    raise FileReadError(file_path, error_msg)
                raise IOError(error_msg)
        except PermissionError as e:
            error_msg = f"权限不足，无法读取文件: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise FileReadError(file_path, error_msg)
            raise IOError(error_msg)
        except IOError as e:
            error_msg = f"文件读取失败: {e}"
            logger.error(error_msg)
            if EXCEPTIONS_AVAILABLE:
                raise FileReadError(file_path, str(e))
            raise IOError(error_msg)
        
        # 缓存文件内容
        if self.enable_cache:
            try:
                file_mtime = os.path.getmtime(file_path)
                self._file_content_cache[file_path] = (code_content, file_mtime)
            except Exception:
                pass
        
        return code_content
    
    @performance_monitor
    def evaluate_files_batch(
        self,
        file_paths: List[str],
        parallel: bool = True,
        max_workers: Optional[int] = None
    ) -> List[QualityReport]:
        """
        批量评估多个文件（优化版，添加并行处理和进度监控）。
        
        Args:
            file_paths: 文件路径列表。
            parallel: 是否使用并行处理。
            max_workers: 最大工作进程数。
        
        Returns:
            质量报告列表。
        """
        if not file_paths:
            return []
        
        logger.info(f"开始批量评估 {len(file_paths)} 个文件")
        
        if parallel and PERFORMANCE_OPTIMIZER_AVAILABLE:
            # 使用并行处理
            results = ParallelProcessor.parallel_map(
                self._evaluate_file_safe,
                file_paths,
                task_type='cpu',
                max_workers=max_workers,
                retry_count=1
            )
        else:
            # 串行处理
            results = [self._evaluate_file_safe(fp) for fp in file_paths]
        
        # 过滤掉None结果
        valid_results = [r for r in results if r is not None]
        
        logger.info(f"成功评估 {len(valid_results)}/{len(file_paths)} 个文件")
        
        return valid_results
    
    @performance_monitor
    def _evaluate_file_safe(self, file_path: str) -> Optional[QualityReport]:
        """
        安全评估单个文件（捕获异常，优化版）。
        
        Args:
            file_path: 文件路径。
        
        Returns:
            质量报告或None。
        """
        try:
            return self.evaluate_file(file_path)
        except Exception as e:
            logger.error(f"评估文件失败 {file_path}: {e}")
            return None

    def _evaluate_readability(self, code_content: str, tree: ast.AST) -> EvaluationResult:
        """
        评估代码可读性。

        评估维度：
        1. 命名规范 (0-5分)
        2. 注释质量 (0-5分)
        3. 代码格式 (0-5分)
        4. 代码复杂度 (0-5分)
        5. 文档字符串 (0-5分)

        Args:
            code_content: 代码内容。
            tree: AST语法树。

        Returns:
            可读性评估结果。
        """
        details = {}
        suggestions = []

        # 1. 命名规范评估 (0-5分)
        naming_score = self._evaluate_naming_conventions(tree)
        details['naming_conventions'] = naming_score
        if naming_score < 3:
            suggestions.append("建议使用更具描述性的变量名和函数名，遵循PEP 8命名规范")

        # 2. 注释质量评估 (0-5分)
        comment_score = self._evaluate_comments(code_content)
        details['comment_quality'] = comment_score
        if comment_score < 3:
            suggestions.append("建议增加代码注释，特别是复杂逻辑和关键算法部分")

        # 3. 代码格式评估 (0-5分)
        format_score = self._evaluate_code_format(code_content)
        details['code_format'] = format_score
        if format_score < 3:
            suggestions.append("建议遵循PEP 8代码格式规范，使用一致的缩进和空格")

        # 4. 代码复杂度评估 (0-5分)
        complexity_score = self._evaluate_complexity(tree)
        details['code_complexity'] = complexity_score
        if complexity_score < 3:
            suggestions.append("建议简化复杂函数，拆分过长的函数为多个小函数")

        # 5. 文档字符串评估 (0-5分)
        docstring_score = self._evaluate_docstrings(tree)
        details['docstring_quality'] = docstring_score
        if docstring_score < 3:
            suggestions.append("建议为函数和类添加文档字符串，说明参数、返回值和功能")

        total_score = sum(details.values())
        return EvaluationResult(
            dimension='readability',
            score=total_score,
            max_score=25.0,
            details=details,
            suggestions=suggestions
        )

    def _evaluate_naming_conventions(self, tree: ast.AST) -> float:
        """
        评估命名规范。

        检查：
        - 变量名、函数名、类名是否符合PEP 8规范
        - 命名是否具有描述性

        Args:
            tree: AST语法树。

        Returns:
            命名规范得分 (0-5分)。
        """
        score = 5.0
        violations = 0

        for node in ast.walk(tree):
            # 检查函数名
            if isinstance(node, ast.FunctionDef):
                if not self._is_valid_function_name(node.name):
                    violations += 1
                # 检查是否为单字母或无意义命名
                if len(node.name) <= 2 and node.name not in ['id', 'ok', 'io']:
                    violations += 0.5

            # 检查类名
            elif isinstance(node, ast.ClassDef):
                if not self._is_valid_class_name(node.name):
                    violations += 1

            # 检查变量名
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):  # 变量赋值
                    if not self._is_valid_variable_name(node.id):
                        violations += 0.5

        # 根据违规数量扣分
        score -= min(violations * 0.5, 5.0)
        return max(score, 0.0)

    def _is_valid_function_name(self, name: str) -> bool:
        """检查函数名是否符合PEP 8规范（小写+下划线）。"""
        if name.startswith('_'):
            return True  # 私有方法或特殊方法
        return bool(re.match(r'^[a-z][a-z0-9_]*$', name))

    def _is_valid_class_name(self, name: str) -> bool:
        """检查类名是否符合PEP 8规范（大驼峰）。"""
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))

    def _is_valid_variable_name(self, name: str) -> bool:
        """检查变量名是否符合PEP 8规范。"""
        if name.startswith('_'):
            return True
        return bool(re.match(r'^[a-z][a-z0-9_]*$', name))

    def _evaluate_comments(self, code_content: str) -> float:
        """
        评估注释质量。

        检查：
        - 注释密度
        - 注释位置
        - 注释内容质量

        Args:
            code_content: 代码内容。

        Returns:
            注释质量得分 (0-5分)。
        """
        lines = code_content.split('\n')
        total_lines = len(lines)
        comment_lines = 0
        inline_comments = 0

        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                comment_lines += 1
            elif '#' in stripped and not stripped.startswith('#'):
                inline_comments += 0.5

        # 计算注释密度
        comment_density = (comment_lines + inline_comments) / total_lines if total_lines > 0 else 0

        # 根据注释密度评分
        if comment_density >= 0.15:
            return 5.0
        elif comment_density >= 0.10:
            return 4.0
        elif comment_density >= 0.05:
            return 3.0
        elif comment_density >= 0.02:
            return 2.0
        elif comment_density > 0:
            return 1.0
        else:
            return 0.0

    def _evaluate_code_format(self, code_content: str) -> float:
        """
        评估代码格式。

        检查：
        - 缩进一致性
        - 行长度
        - 空行使用

        Args:
            code_content: 代码内容。

        Returns:
            代码格式得分 (0-5分)。
        """
        score = 5.0
        lines = code_content.split('\n')

        # 检查行长度
        long_lines = sum(1 for line in lines if len(line) > 100)
        if long_lines > 0:
            score -= min(long_lines * 0.1, 2.0)

        # 检查缩进一致性
        indent_pattern = re.compile(r'^( *)\S')
        indents = []
        for line in lines:
            match = indent_pattern.match(line)
            if match:
                indent_len = len(match.group(1))
                if indent_len > 0:
                    indents.append(indent_len)

        if indents:
            # 检查是否使用4空格缩进
            inconsistent_indents = sum(1 for indent in indents if indent % 4 != 0)
            if inconsistent_indents > 0:
                score -= min(inconsistent_indents * 0.1, 1.5)

        # 检查过多空行
        consecutive_empty = 0
        max_consecutive_empty = 0
        for line in lines:
            if line.strip() == '':
                consecutive_empty += 1
                max_consecutive_empty = max(max_consecutive_empty, consecutive_empty)
            else:
                consecutive_empty = 0

        if max_consecutive_empty > 2:
            score -= min((max_consecutive_empty - 2) * 0.5, 1.5)

        return max(score, 0.0)

    def _evaluate_complexity(self, tree: ast.AST) -> float:
        """
        评估代码复杂度。

        检查：
        - 函数圈复杂度
        - 嵌套深度
        - 函数长度

        Args:
            tree: AST语法树。

        Returns:
            代码复杂度得分 (0-5分)。
        """
        score = 5.0
        violations = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 计算函数长度
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 0
                if func_lines > 50:
                    violations += (func_lines - 50) / 20

                # 计算嵌套深度
                max_depth = self._calculate_max_depth(node)
                if max_depth > 4:
                    violations += (max_depth - 4) * 0.5

                # 计算圈复杂度
                complexity = self._calculate_cyclomatic_complexity(node)
                if complexity > 10:
                    violations += (complexity - 10) / 5

        score -= min(violations, 5.0)
        return max(score, 0.0)

    def _calculate_max_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """计算AST节点的最大嵌套深度。"""
        max_depth = current_depth

        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                child_depth = self._calculate_max_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_max_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数的圈复杂度。"""
        complexity = 1  # 基础复杂度

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # and/or 操作增加复杂度
                complexity += len(child.values) - 1

        return complexity

    def _evaluate_docstrings(self, tree: ast.AST) -> float:
        """
        评估文档字符串质量。

        检查：
        - 函数文档字符串
        - 类文档字符串
        - 模块文档字符串

        Args:
            tree: AST语法树。

        Returns:
            文档字符串得分 (0-5分)。
        """
        total_nodes = 0
        documented_nodes = 0

        # 检查模块文档字符串
        if ast.get_docstring(tree):
            documented_nodes += 1
        total_nodes += 1

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                total_nodes += 1
                if ast.get_docstring(node):
                    documented_nodes += 1

        # 计算文档覆盖率
        coverage = documented_nodes / total_nodes if total_nodes > 0 else 0

        # 根据覆盖率评分
        if coverage >= 0.8:
            return 5.0
        elif coverage >= 0.6:
            return 4.0
        elif coverage >= 0.4:
            return 3.0
        elif coverage >= 0.2:
            return 2.0
        elif coverage > 0:
            return 1.0
        else:
            return 0.0

    def _evaluate_maintainability(self, code_content: str, tree: ast.AST) -> EvaluationResult:
        """
        评估代码可维护性。

        评估维度：
        1. 模块化程度 (0-5分)
        2. 代码重复度 (0-5分)
        3. 依赖管理 (0-5分)
        4. 函数长度 (0-5分)
        5. 类设计 (0-5分)

        Args:
            code_content: 代码内容。
            tree: AST语法树。

        Returns:
            可维护性评估结果。
        """
        details = {}
        suggestions = []

        # 1. 模块化程度评估 (0-5分)
        modularity_score = self._evaluate_modularity(tree)
        details['modularity'] = modularity_score
        if modularity_score < 3:
            suggestions.append("建议提高代码模块化程度，将相关功能组织到独立的函数或类中")

        # 2. 代码重复度评估 (0-5分)
        duplication_score = self._evaluate_code_duplication(code_content)
        details['code_duplication'] = duplication_score
        if duplication_score < 3:
            suggestions.append("建议消除重复代码，提取公共逻辑到独立函数")

        # 3. 依赖管理评估 (0-5分)
        dependency_score = self._evaluate_dependencies(tree)
        details['dependency_management'] = dependency_score
        if dependency_score < 3:
            suggestions.append("建议优化依赖管理，减少不必要的导入")

        # 4. 函数长度评估 (0-5分)
        function_length_score = self._evaluate_function_length(tree)
        details['function_length'] = function_length_score
        if function_length_score < 3:
            suggestions.append("建议缩短过长的函数，每个函数只做一件事")

        # 5. 类设计评估 (0-5分)
        class_design_score = self._evaluate_class_design(tree)
        details['class_design'] = class_design_score
        if class_design_score < 3:
            suggestions.append("建议优化类设计，遵循单一职责原则")

        total_score = sum(details.values())
        return EvaluationResult(
            dimension='maintainability',
            score=total_score,
            max_score=25.0,
            details=details,
            suggestions=suggestions
        )

    def _evaluate_modularity(self, tree: ast.AST) -> float:
        """评估模块化程度。"""
        functions = []
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node)
            elif isinstance(node, ast.ClassDef):
                classes.append(node)

        # 检查是否有合理的函数和类组织
        if len(functions) == 0 and len(classes) == 0:
            return 2.0  # 没有函数或类，模块化程度低

        # 计算平均函数长度
        if functions:
            avg_func_length = sum(
                (node.end_lineno - node.lineno) if hasattr(node, 'end_lineno') else 10
                for node in functions
            ) / len(functions)

            # 平均函数长度在10-30行为最佳
            if 10 <= avg_func_length <= 30:
                return 5.0
            elif 5 <= avg_func_length < 10 or 30 < avg_func_length <= 50:
                return 4.0
            else:
                return 3.0

        return 4.0

    def _evaluate_code_duplication(self, code_content: str) -> float:
        """评估代码重复度。"""
        lines = [line.strip() for line in code_content.split('\n') if line.strip()]
        if not lines:
            return 5.0

        # 简单的重复检测：检查连续相同行
        duplicates = 0
        for i in range(len(lines) - 1):
            if lines[i] == lines[i + 1]:
                duplicates += 1

        duplication_ratio = duplicates / len(lines) if lines else 0

        if duplication_ratio < 0.05:
            return 5.0
        elif duplication_ratio < 0.10:
            return 4.0
        elif duplication_ratio < 0.15:
            return 3.0
        elif duplication_ratio < 0.20:
            return 2.0
        else:
            return 1.0

    def _evaluate_dependencies(self, tree: ast.AST) -> float:
        """评估依赖管理。"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(node)

        # 检查导入数量
        if len(imports) <= 10:
            return 5.0
        elif len(imports) <= 20:
            return 4.0
        elif len(imports) <= 30:
            return 3.0
        else:
            return 2.0

    def _evaluate_function_length(self, tree: ast.AST) -> float:
        """评估函数长度。"""
        violations = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_lines = (node.end_lineno - node.lineno) if hasattr(node, 'end_lineno') else 0
                if func_lines > 100:
                    violations += 2
                elif func_lines > 50:
                    violations += 1

        if violations == 0:
            return 5.0
        elif violations <= 2:
            return 4.0
        elif violations <= 4:
            return 3.0
        else:
            return 2.0

    def _evaluate_class_design(self, tree: ast.AST) -> float:
        """评估类设计。"""
        classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node)

        if not classes:
            return 4.0  # 没有类，不扣分

        score = 5.0

        for cls in classes:
            # 检查类的方法数量
            methods = [n for n in cls.body if isinstance(n, ast.FunctionDef)]
            if len(methods) > 20:
                score -= 0.5  # 类过于庞大

            # 检查类的属性数量
            attributes = [n for n in cls.body if isinstance(n, ast.Assign)]
            if len(attributes) > 15:
                score -= 0.3

        return max(score, 0.0)

    def _evaluate_performance(self, code_content: str, tree: ast.AST) -> EvaluationResult:
        """
        评估性能效率。

        评估维度：
        1. 算法复杂度 (0-5分)
        2. 资源使用 (0-5分)
        3. 数据结构选择 (0-5分)
        4. 循环优化 (0-5分)

        Args:
            code_content: 代码内容。
            tree: AST语法树。

        Returns:
            性能效率评估结果。
        """
        details = {}
        suggestions = []

        # 1. 算法复杂度评估 (0-5分)
        algorithm_score = self._evaluate_algorithm_complexity(tree)
        details['algorithm_complexity'] = algorithm_score
        if algorithm_score < 3:
            suggestions.append("建议优化算法复杂度，避免嵌套循环和递归深度过大")

        # 2. 资源使用评估 (0-5分)
        resource_score = self._evaluate_resource_usage(tree)
        details['resource_usage'] = resource_score
        if resource_score < 3:
            suggestions.append("建议优化资源使用，及时释放文件句柄、数据库连接等资源")

        # 3. 数据结构选择评估 (0-5分)
        data_structure_score = self._evaluate_data_structures(tree)
        details['data_structures'] = data_structure_score
        if data_structure_score < 3:
            suggestions.append("建议选择合适的数据结构，如使用集合代替列表进行成员检查")

        # 4. 循环优化评估 (0-5分)
        loop_score = self._evaluate_loop_optimization(tree)
        details['loop_optimization'] = loop_score
        if loop_score < 3:
            suggestions.append("建议优化循环，避免在循环中进行重复计算")

        total_score = sum(details.values())
        return EvaluationResult(
            dimension='performance',
            score=total_score,
            max_score=20.0,
            details=details,
            suggestions=suggestions
        )

    def _evaluate_algorithm_complexity(self, tree: ast.AST) -> float:
        """评估算法复杂度。"""
        score = 5.0
        nested_loops = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # 检查嵌套循环
                for child in ast.walk(node):
                    if isinstance(child, (ast.For, ast.While)) and child != node:
                        nested_loops += 1

        # 嵌套循环扣分
        score -= min(nested_loops * 0.5, 3.0)

        return max(score, 0.0)

    def _evaluate_resource_usage(self, tree: ast.AST) -> float:
        """评估资源使用。"""
        score = 5.0

        # 检查是否使用with语句管理资源
        with_statements = 0
        open_calls = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                with_statements += 1
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    open_calls += 1

        # 如果有open调用但没有使用with，扣分
        if open_calls > 0 and with_statements == 0:
            score -= 2.0

        return max(score, 0.0)

    def _evaluate_data_structures(self, tree: ast.AST) -> float:
        """评估数据结构选择。"""
        score = 5.0

        # 检查是否在循环中使用列表进行成员检查（应该用集合）
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                for child in ast.walk(node):
                    if isinstance(child, ast.Compare):
                        if isinstance(child.ops[0], ast.In):
                            # 检查是否在列表中查找
                            if isinstance(child.comparators[0], ast.Name):
                                # 可能需要优化为集合
                                pass

        return score

    def _evaluate_loop_optimization(self, tree: ast.AST) -> float:
        """评估循环优化。"""
        score = 5.0

        # 检查循环中是否有重复计算
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                # 简单检查：循环体内是否有函数调用
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and child != node:
                        # 可能需要将函数调用移出循环
                        pass

        return score

    def _evaluate_error_handling(self, code_content: str, tree: ast.AST) -> EvaluationResult:
        """
        评估错误处理。

        评估维度：
        1. 异常捕获 (0-5分)
        2. 错误日志 (0-5分)
        3. 边界检查 (0-5分)

        Args:
            code_content: 代码内容。
            tree: AST语法树。

        Returns:
            错误处理评估结果。
        """
        details = {}
        suggestions = []

        # 1. 异常捕获评估 (0-5分)
        exception_score = self._evaluate_exception_handling(tree)
        details['exception_handling'] = exception_score
        if exception_score < 3:
            suggestions.append("建议增加异常处理，避免程序因未捕获异常而崩溃")

        # 2. 错误日志评估 (0-5分)
        logging_score = self._evaluate_logging(code_content)
        details['error_logging'] = logging_score
        if logging_score < 3:
            suggestions.append("建议增加错误日志记录，便于问题追踪和调试")

        # 3. 边界检查评估 (0-5分)
        boundary_score = self._evaluate_boundary_checks(tree)
        details['boundary_checks'] = boundary_score
        if boundary_score < 3:
            suggestions.append("建议增加边界条件检查，如空值、索引越界等")

        total_score = sum(details.values())
        return EvaluationResult(
            dimension='error_handling',
            score=total_score,
            max_score=15.0,
            details=details,
            suggestions=suggestions
        )

    def _evaluate_exception_handling(self, tree: ast.AST) -> float:
        """评估异常捕获。"""
        try_blocks = 0
        dangerous_operations = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                try_blocks += 1

            # 检查危险操作
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['open', 'int', 'float', 'eval', 'exec']:
                        dangerous_operations += 1

        # 如果有危险操作但没有try块，扣分
        if dangerous_operations > 0 and try_blocks == 0:
            return 2.0
        elif try_blocks > 0:
            return 5.0
        else:
            return 4.0

    def _evaluate_logging(self, code_content: str) -> float:
        """评估错误日志。"""
        # 检查是否使用logging模块
        if 'import logging' in code_content or 'from logging' in code_content:
            # 检查是否有日志调用
            if 'logger.' in code_content or 'logging.' in code_content:
                return 5.0
            else:
                return 3.0
        else:
            return 2.0

    def _evaluate_boundary_checks(self, tree: ast.AST) -> float:
        """评估边界检查。"""
        score = 5.0

        # 检查是否有None检查
        none_checks = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for comparator in node.comparators:
                    if isinstance(comparator, ast.Constant) and comparator.value is None:
                        none_checks += 1

        # 如果没有None检查，扣分
        if none_checks == 0:
            score -= 1.0

        return max(score, 0.0)

    def _evaluate_security(self, code_content: str, tree: ast.AST) -> EvaluationResult:
        """
        评估安全性。

        评估维度：
        1. 输入验证 (0-5分)
        2. 敏感数据处理 (0-5分)
        3. 安全编码实践 (0-5分)

        Args:
            code_content: 代码内容。
            tree: AST语法树。

        Returns:
            安全性评估结果。
        """
        details = {}
        suggestions = []

        # 1. 输入验证评估 (0-5分)
        input_validation_score = self._evaluate_input_validation(tree)
        details['input_validation'] = input_validation_score
        if input_validation_score < 3:
            suggestions.append("建议增加输入验证，防止恶意输入导致安全问题")

        # 2. 敏感数据处理评估 (0-5分)
        sensitive_data_score = self._evaluate_sensitive_data_handling(code_content)
        details['sensitive_data_handling'] = sensitive_data_score
        if sensitive_data_score < 3:
            suggestions.append("建议妥善处理敏感数据，避免硬编码密码、密钥等信息")

        # 3. 安全编码实践评估 (0-5分)
        secure_coding_score = self._evaluate_secure_coding_practices(tree)
        details['secure_coding_practices'] = secure_coding_score
        if secure_coding_score < 3:
            suggestions.append("建议遵循安全编码实践，避免使用危险函数")

        total_score = sum(details.values())
        return EvaluationResult(
            dimension='security',
            score=total_score,
            max_score=15.0,
            details=details,
            suggestions=suggestions
        )

    def _evaluate_input_validation(self, tree: ast.AST) -> float:
        """评估输入验证。"""
        score = 5.0

        # 检查是否有输入函数
        input_functions = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'input':
                    input_functions += 1

        # 如果有输入函数但没有验证，扣分
        if input_functions > 0:
            # 简单检查：是否有if语句对输入进行验证
            has_validation = False
            for node in ast.walk(tree):
                if isinstance(node, ast.If):
                    has_validation = True
                    break

            if not has_validation:
                score -= 2.0

        return max(score, 0.0)

    def _evaluate_sensitive_data_handling(self, code_content: str) -> float:
        """评估敏感数据处理。"""
        score = 5.0

        # 检查是否有硬编码的敏感信息
        for keyword in self.SECURITY_KEYWORDS:
            # 检查是否有类似 password = "xxx" 的模式
            pattern = rf'{keyword}\s*=\s*["\']([^"\']+)["\']'
            if re.search(pattern, code_content, re.IGNORECASE):
                score -= 2.0

        return max(score, 0.0)

    def _evaluate_secure_coding_practices(self, tree: ast.AST) -> float:
        """评估安全编码实践。"""
        score = 5.0

        # 检查是否使用危险函数
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = f"{node.func.value.id}.{node.func.attr}" if isinstance(node.func.value, ast.Name) else node.func.attr

                if func_name in self.DANGEROUS_FUNCTIONS:
                    score -= 1.0

        return max(score, 0.0)

    def _determine_quality_level(self, total_score: float) -> QualityLevel:
        """
        确定质量等级。

        Args:
            total_score: 总分。

        Returns:
            质量等级。
        """
        if total_score >= self.QUALITY_THRESHOLDS[QualityLevel.EXCELLENT]:
            return QualityLevel.EXCELLENT
        elif total_score >= self.QUALITY_THRESHOLDS[QualityLevel.GOOD]:
            return QualityLevel.GOOD
        elif total_score >= self.QUALITY_THRESHOLDS[QualityLevel.QUALIFIED]:
            return QualityLevel.QUALIFIED
        else:
            return QualityLevel.UNQUALIFIED

    def _generate_suggestions(self, dimensions: Dict[str, EvaluationResult]) -> List[str]:
        """
        生成改进建议。

        Args:
            dimensions: 各维度评估结果。

        Returns:
            改进建议列表。
        """
        suggestions = []
        for dimension, result in dimensions.items():
            suggestions.extend(result.suggestions)
        return suggestions

    def _create_minimal_report(self, file_path: str, error_message: str) -> QualityReport:
        """
        创建最低分报告（用于语法错误等情况）。

        Args:
            file_path: 文件路径。
            error_message: 错误信息。

        Returns:
            最低分质量报告。
        """
        dimensions = {}
        for dimension in self.DIMENSION_WEIGHTS.keys():
            max_score = self.DIMENSION_MAX_SCORES.get(dimension, 20)
            dimensions[dimension] = EvaluationResult(
                dimension=dimension,
                score=0.0,
                max_score=float(max_score),
                suggestions=[error_message]
            )

        return QualityReport(
            total_score=0.0,
            max_score=100.0,
            level=QualityLevel.UNQUALIFIED,
            dimensions=dimensions,
            weight_coefficients=self.weight_coefficients,
            file_path=file_path,
            suggestions=[error_message]
        )

    def generate_report_markdown(self, report: QualityReport) -> str:
        """
        生成Markdown格式的质量报告。

        Args:
            report: 质量报告。

        Returns:
            Markdown格式的报告。
        """
        markdown = f"# 代码质量评估报告\n\n"
        markdown += f"**文件**: {report.file_path}\n\n"
        markdown += f"**评估时间**: {self._get_current_time()}\n\n"

        # 总体评分
        markdown += f"## 总体评分\n\n"
        markdown += f"- **总分**: {report.total_score:.2f} / {report.max_score:.0f}\n"
        markdown += f"- **得分率**: {report.percentage:.1f}%\n"
        markdown += f"- **质量等级**: {report.level.value}\n\n"

        # 各维度评分
        markdown += f"## 各维度评分\n\n"
        markdown += f"| 维度 | 得分 | 满分 | 得分率 | 状态 |\n"
        markdown += f"|------|------|------|--------|------|\n"

        dimension_names = {
            'readability': '可读性',
            'maintainability': '可维护性',
            'performance': '性能效率',
            'error_handling': '错误处理',
            'security': '安全性'
        }

        for dimension, result in report.dimensions.items():
            status = "✓" if result.percentage >= 60 else "✗"
            markdown += f"| {dimension_names.get(dimension, dimension)} | {result.score:.2f} | {result.max_score:.0f} | {result.percentage:.1f}% | {status} |\n"

        markdown += "\n"

        # 详细评分
        markdown += f"## 详细评分\n\n"
        for dimension, result in report.dimensions.items():
            markdown += f"### {dimension_names.get(dimension, dimension)}\n\n"
            if result.details:
                markdown += f"| 子项 | 得分 |\n"
                markdown += f"|------|------|\n"
                for detail_name, detail_score in result.details.items():
                    markdown += f"| {detail_name} | {detail_score:.2f} |\n"
                markdown += "\n"

            if result.suggestions:
                markdown += f"**改进建议**:\n"
                for suggestion in result.suggestions:
                    markdown += f"- {suggestion}\n"
                markdown += "\n"

        # 权重系数
        markdown += f"## 权重系数\n\n"
        markdown += f"| 维度 | 权重系数 |\n"
        markdown += f"|------|----------|\n"
        for dimension, coefficient in report.weight_coefficients.items():
            markdown += f"| {dimension_names.get(dimension, dimension)} | {coefficient:.4f} |\n"
        markdown += "\n"

        # 总体建议
        if report.suggestions:
            markdown += f"## 总体改进建议\n\n"
            for suggestion in report.suggestions:
                markdown += f"- {suggestion}\n"
            markdown += "\n"

        return markdown

    def _get_current_time(self) -> str:
        """获取当前时间字符串。"""
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def main():
    """主函数，用于测试。"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python code_quality_evaluator.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]

    # 创建评估器
    evaluator = CodeQualityEvaluator(
        project_type=ProjectType.CLI_TOOL,
        project_stage=ProjectStage.DEVELOPMENT,
        team_size=1,
        code_lines=0
    )

    # 评估文件
    try:
        report = evaluator.evaluate_file(file_path)

        # 生成Markdown报告
        markdown_report = evaluator.generate_report_markdown(report)
        print(markdown_report)

        # 保存报告
        output_file = file_path.replace('.py', '_quality_report.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_report)

        print(f"\n报告已保存到: {output_file}")

    except FileNotFoundError as e:
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"评估失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
