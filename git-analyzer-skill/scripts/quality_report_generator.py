#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量检验报告生成器

提供详细的代码质量检验报告生成功能，包括各维度评估、问题清单、优化建议和对比分析。

WING
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# 导入代码质量评估器
try:
    from code_quality_evaluator import (
        CodeQualityEvaluator,
        QualityReport,
        QualityLevel,
        ProjectType,
        ProjectStage
    )
    QUALITY_EVALUATOR_AVAILABLE = True
except ImportError:
    QUALITY_EVALUATOR_AVAILABLE = False
    logging.warning("code_quality_evaluator模块未找到，质量评估功能将不可用")

# 导入Git分析器
try:
    from git_analyzer import (
        RepositoryManager,
        CommitAnalyzer,
        ContributionCalculator,
        AlgorithmMode
    )
    GIT_ANALYZER_AVAILABLE = True
except ImportError:
    GIT_ANALYZER_AVAILABLE = False
    logging.warning("git_analyzer模块未找到，Git分析功能将不可用")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """问题严重程度枚举。"""
    CRITICAL = "critical"  # 严重问题
    HIGH = "high"          # 重要问题
    MEDIUM = "medium"      # 中等问题
    LOW = "low"            # 轻微问题


@dataclass
class QualityIssue:
    """质量问题数据类。"""
    issue_id: str
    dimension: str
    description: str
    severity: IssueSeverity
    impact_scope: str
    suggestion: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class OptimizationSuggestion:
    """优化建议数据类。"""
    title: str
    description: str
    priority: str  # short_term, mid_term, long_term
    estimated_effort: str
    expected_improvement: str
    related_dimensions: List[str] = field(default_factory=list)


@dataclass
class HistoricalComparison:
    """历史对比数据类。"""
    historical_score: float
    current_score: float
    score_diff: float
    dimension_changes: Dict[str, Tuple[float, float, float]]  # dimension: (historical, current, diff)
    improvement_points: List[str]
    regression_points: List[str]


@dataclass
class DeveloperComparison:
    """开发者对比数据类。"""
    developer_name: str
    total_score: float
    dimension_scores: Dict[str, float]
    rank: int
    quality_level: str
    strengths: List[str]
    weaknesses: List[str]


class QualityReportGenerator:
    """
    质量检验报告生成器。

    功能：
    1. 生成详细的代码质量检验报告
    2. 提供各维度评估和问题清单
    3. 生成优化建议
    4. 支持历史版本对比
    5. 支持开发者对比分析
    """

    # 维度名称映射
    DIMENSION_NAMES = {
        'readability': '可读性',
        'maintainability': '可维护性',
        'performance': '性能效率',
        'error_handling': '错误处理',
        'security': '安全性'
    }

    # 子项名称映射
    SUBITEM_NAMES = {
        # 可读性子项
        'naming_conventions': '命名规范',
        'comment_quality': '注释质量',
        'code_format': '代码格式',
        'code_complexity': '代码复杂度',
        'docstring_quality': '文档字符串',
        # 可维护性子项
        'modularity': '模块化程度',
        'code_duplication': '代码重复度',
        'dependency_management': '依赖管理',
        'function_length': '函数长度',
        'class_design': '类设计',
        # 性能子项
        'algorithm_complexity': '算法复杂度',
        'resource_usage': '资源使用',
        'data_structures': '数据结构选择',
        'loop_optimization': '循环优化',
        # 错误处理子项
        'exception_handling': '异常捕获',
        'error_logging': '错误日志',
        'boundary_checks': '边界检查',
        # 安全性子项
        'input_validation': '输入验证',
        'sensitive_data_handling': '敏感数据处理',
        'secure_coding_practices': '安全编码实践'
    }

    def __init__(
        self,
        project_type: ProjectType = ProjectType.OTHER,
        project_stage: ProjectStage = ProjectStage.DEVELOPMENT,
        team_size: int = 1
    ):
        """
        初始化质量检验报告生成器。

        Args:
            project_type: 项目类型。
            project_stage: 项目阶段。
            team_size: 团队规模。
        """
        if not QUALITY_EVALUATOR_AVAILABLE:
            raise ImportError("code_quality_evaluator模块未找到，无法初始化质量报告生成器")

        self.project_type = project_type
        self.project_stage = project_stage
        self.team_size = team_size
        self.evaluator = CodeQualityEvaluator(
            project_type=project_type,
            project_stage=project_stage,
            team_size=team_size
        )

    def generate_quality_report(
        self,
        local_path: str,
        output_file: str,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        include_comparison: bool = False,
        comparison_since: Optional[datetime] = None,
        comparison_until: Optional[datetime] = None
    ) -> bool:
        """
        生成完整的质量检验报告。

        Args:
            local_path: 本地仓库路径。
            output_file: 输出文件路径。
            since: 分析开始时间。
            until: 分析结束时间。
            include_comparison: 是否包含历史对比。
            comparison_since: 对比开始时间。
            comparison_until: 对比结束时间。

        Returns:
            报告生成是否成功。
        """
        try:
            logger.info(f"开始生成质量检验报告: {local_path}")

            # 1. 收集代码文件
            code_files = self._collect_code_files(local_path)
            if not code_files:
                logger.warning("未找到代码文件")
                return False

            logger.info(f"找到 {len(code_files)} 个代码文件")

            # 2. 评估代码质量
            quality_reports = self._evaluate_code_quality(code_files)
            if not quality_reports:
                logger.warning("代码质量评估失败")
                return False

            # 3. 汇总质量数据
            aggregated_data = self._aggregate_quality_data(quality_reports)

            # 4. 识别问题
            issues = self._identify_issues(quality_reports)

            # 5. 生成优化建议
            suggestions = self._generate_optimization_suggestions(issues, aggregated_data)

            # 6. 历史对比（如果需要）
            historical_comparison = None
            if include_comparison and comparison_since and comparison_until:
                historical_comparison = self._compare_with_history(
                    local_path,
                    comparison_since,
                    comparison_until,
                    aggregated_data
                )

            # 7. 开发者对比
            developer_comparisons = None
            if GIT_ANALYZER_AVAILABLE:
                developer_comparisons = self._compare_developers(
                    local_path,
                    since,
                    until,
                    quality_reports
                )

            # 8. 生成Markdown报告
            markdown_content = self._generate_markdown_report(
                aggregated_data,
                issues,
                suggestions,
                historical_comparison,
                developer_comparisons,
                local_path,
                since,
                until
            )

            # 9. 写入文件
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            logger.info(f"质量检验报告生成成功: {output_file}")
            return True

        except Exception as e:
            logger.error(f"生成质量检验报告失败: {e}")
            return False

    def _collect_code_files(self, local_path: str) -> List[str]:
        """
        收集代码文件。

        Args:
            local_path: 本地仓库路径。

        Returns:
            代码文件路径列表。
        """
        code_extensions = ('.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb')
        code_files = []

        for root, dirs, files in os.walk(local_path):
            # 跳过隐藏目录和常见的非代码目录
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__', 'build', 'dist']]

            for file in files:
                if file.endswith(code_extensions):
                    file_path = os.path.join(root, file)
                    code_files.append(file_path)

        return code_files

    def _evaluate_code_quality(self, code_files: List[str]) -> List[QualityReport]:
        """
        评估代码质量。

        Args:
            code_files: 代码文件列表。

        Returns:
            质量报告列表。
        """
        logger.info("开始评估代码质量...")
        quality_reports = []

        # 使用批量评估
        if len(code_files) > 10:
            quality_reports = self.evaluator.evaluate_files_batch(code_files, parallel=True)
        else:
            for file_path in code_files:
                try:
                    report = self.evaluator.evaluate_file(file_path)
                    quality_reports.append(report)
                except Exception as e:
                    logger.warning(f"评估文件失败 {file_path}: {e}")

        logger.info(f"成功评估 {len(quality_reports)} 个文件")
        return quality_reports

    def _aggregate_quality_data(self, quality_reports: List[QualityReport]) -> Dict[str, Any]:
        """
        汇总质量数据。

        Args:
            quality_reports: 质量报告列表。

        Returns:
            汇总的质量数据。
        """
        if not quality_reports:
            return {}

        # 初始化汇总数据
        aggregated = {
            'total_score': 0.0,
            'file_count': len(quality_reports),
            'dimension_scores': {
                'readability': 0.0,
                'maintainability': 0.0,
                'performance': 0.0,
                'error_handling': 0.0,
                'security': 0.0
            },
            'dimension_details': {},
            'quality_level': QualityLevel.UNQUALIFIED
        }

        # 汇总各维度得分
        for report in quality_reports:
            aggregated['total_score'] += report.total_score

            for dimension, result in report.dimensions.items():
                if dimension in aggregated['dimension_scores']:
                    aggregated['dimension_scores'][dimension] += result.score

                # 汇总子项得分
                if dimension not in aggregated['dimension_details']:
                    aggregated['dimension_details'][dimension] = {}

                for detail_name, detail_score in result.details.items():
                    if detail_name not in aggregated['dimension_details'][dimension]:
                        aggregated['dimension_details'][dimension][detail_name] = 0.0
                    aggregated['dimension_details'][dimension][detail_name] += detail_score

        # 计算平均得分
        if aggregated['file_count'] > 0:
            aggregated['total_score'] /= aggregated['file_count']
            for dimension in aggregated['dimension_scores']:
                aggregated['dimension_scores'][dimension] /= aggregated['file_count']

            for dimension in aggregated['dimension_details']:
                for detail_name in aggregated['dimension_details'][dimension]:
                    aggregated['dimension_details'][dimension][detail_name] /= aggregated['file_count']

        # 确定质量等级
        aggregated['quality_level'] = self._determine_quality_level(aggregated['total_score'])

        return aggregated

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """
        确定质量等级。

        Args:
            score: 总分。

        Returns:
            质量等级。
        """
        if score >= 80:
            return QualityLevel.EXCELLENT
        elif score >= 60:
            return QualityLevel.GOOD
        elif score >= 40:
            return QualityLevel.QUALIFIED
        else:
            return QualityLevel.UNQUALIFIED

    def _identify_issues(self, quality_reports: List[QualityReport]) -> List[QualityIssue]:
        """
        识别质量问题。

        Args:
            quality_reports: 质量报告列表。

        Returns:
            质量问题列表。
        """
        issues = []
        issue_id = 1

        for report in quality_reports:
            for dimension, result in report.dimensions.items():
                # 检查得分低于阈值的维度
                if result.percentage < 60:
                    severity = self._determine_issue_severity(result.percentage)

                    # 为每个建议创建一个问题
                    for suggestion in result.suggestions:
                        issue = QualityIssue(
                            issue_id=f"ISSUE-{issue_id:03d}",
                            dimension=dimension,
                            description=f"{self.DIMENSION_NAMES.get(dimension, dimension)}得分较低: {result.score:.1f}/{result.max_score:.0f}",
                            severity=severity,
                            impact_scope=f"文件: {os.path.basename(report.file_path)}",
                            suggestion=suggestion,
                            file_path=report.file_path
                        )
                        issues.append(issue)
                        issue_id += 1

                # 检查子项得分
                for detail_name, detail_score in result.details.items():
                    if detail_score < 3.0:  # 子项得分低于3分视为问题
                        severity = IssueSeverity.LOW if detail_score >= 2.0 else IssueSeverity.MEDIUM

                        issue = QualityIssue(
                            issue_id=f"ISSUE-{issue_id:03d}",
                            dimension=dimension,
                            description=f"{self.SUBITEM_NAMES.get(detail_name, detail_name)}需要改进: {detail_score:.1f}/5.0",
                            severity=severity,
                            impact_scope=f"文件: {os.path.basename(report.file_path)}",
                            suggestion=self._get_subitem_suggestion(dimension, detail_name),
                            file_path=report.file_path
                        )
                        issues.append(issue)
                        issue_id += 1

        return issues

    def _determine_issue_severity(self, percentage: float) -> IssueSeverity:
        """
        确定问题严重程度。

        Args:
            percentage: 得分百分比。

        Returns:
            问题严重程度。
        """
        if percentage < 30:
            return IssueSeverity.CRITICAL
        elif percentage < 45:
            return IssueSeverity.HIGH
        elif percentage < 60:
            return IssueSeverity.MEDIUM
        else:
            return IssueSeverity.LOW

    def _get_subitem_suggestion(self, dimension: str, subitem: str) -> str:
        """
        获取子项改进建议。

        Args:
            dimension: 维度名称。
            subitem: 子项名称。

        Returns:
            改进建议。
        """
        suggestions = {
            # 可读性子项
            'naming_conventions': "使用更具描述性的变量名和函数名，遵循PEP 8命名规范",
            'comment_quality': "增加代码注释，特别是复杂逻辑和关键算法部分",
            'code_format': "遵循PEP 8代码格式规范，使用一致的缩进和空格",
            'code_complexity': "简化复杂函数，拆分过长的函数为多个小函数",
            'docstring_quality': "为函数和类添加文档字符串，说明参数、返回值和功能",
            # 可维护性子项
            'modularity': "提高代码模块化程度，将相关功能组织到独立的函数或类中",
            'code_duplication': "消除重复代码，提取公共逻辑到独立函数",
            'dependency_management': "优化依赖管理，减少不必要的导入",
            'function_length': "缩短过长的函数，每个函数只做一件事",
            'class_design': "优化类设计，遵循单一职责原则",
            # 性能子项
            'algorithm_complexity': "优化算法复杂度，避免嵌套循环和递归深度过大",
            'resource_usage': "优化资源使用，及时释放文件句柄、数据库连接等资源",
            'data_structures': "选择合适的数据结构，如使用集合代替列表进行成员检查",
            'loop_optimization': "优化循环，避免在循环中进行重复计算",
            # 错误处理子项
            'exception_handling': "增加异常处理，避免程序因未捕获异常而崩溃",
            'error_logging': "增加错误日志记录，便于问题追踪和调试",
            'boundary_checks': "增加边界条件检查，如空值、索引越界等",
            # 安全性子项
            'input_validation': "增加输入验证，防止恶意输入导致安全问题",
            'sensitive_data_handling': "妥善处理敏感数据，避免硬编码密码、密钥等信息",
            'secure_coding_practices': "遵循安全编码实践，避免使用危险函数"
        }

        return suggestions.get(subitem, f"改进{self.SUBITEM_NAMES.get(subitem, subitem)}")

    def _generate_optimization_suggestions(
        self,
        issues: List[QualityIssue],
        aggregated_data: Dict[str, Any]
    ) -> List[OptimizationSuggestion]:
        """
        生成优化建议。

        Args:
            issues: 问题列表。
            aggregated_data: 汇总数据。

        Returns:
            优化建议列表。
        """
        suggestions = []

        # 按严重程度统计问题
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]
        medium_issues = [i for i in issues if i.severity == IssueSeverity.MEDIUM]
        low_issues = [i for i in issues if i.severity == IssueSeverity.LOW]

        # 短期建议（1-2周）
        if critical_issues:
            suggestions.append(OptimizationSuggestion(
                title="修复严重质量问题",
                description=f"发现 {len(critical_issues)} 个严重质量问题，需要立即修复",
                priority="short_term",
                estimated_effort="1-2周",
                expected_improvement="显著提升代码质量得分",
                related_dimensions=list(set(i.dimension for i in critical_issues))
            ))

        if high_issues:
            suggestions.append(OptimizationSuggestion(
                title="解决重要质量问题",
                description=f"发现 {len(high_issues)} 个重要质量问题，建议优先处理",
                priority="short_term",
                estimated_effort="1-2周",
                expected_improvement="提升代码质量和可维护性",
                related_dimensions=list(set(i.dimension for i in high_issues))
            ))

        # 中期建议（1-2月）
        if medium_issues:
            suggestions.append(OptimizationSuggestion(
                title="改进中等质量问题",
                description=f"发现 {len(medium_issues)} 个中等质量问题，建议制定改进计划",
                priority="mid_term",
                estimated_effort="1-2月",
                expected_improvement="全面提升代码质量",
                related_dimensions=list(set(i.dimension for i in medium_issues))
            ))

        # 长期建议（3-6月）
        if low_issues:
            suggestions.append(OptimizationSuggestion(
                title="优化轻微质量问题",
                description=f"发现 {len(low_issues)} 个轻微质量问题，建议持续改进",
                priority="long_term",
                estimated_effort="3-6月",
                expected_improvement="达到代码质量最佳实践",
                related_dimensions=list(set(i.dimension for i in low_issues))
            ))

        # 根据维度得分生成建议
        for dimension, score in aggregated_data.get('dimension_scores', {}).items():
            max_score = self.evaluator.DIMENSION_MAX_SCORES.get(dimension, 20)
            percentage = (score / max_score * 100) if max_score > 0 else 0

            if percentage < 60:
                suggestions.append(OptimizationSuggestion(
                    title=f"提升{self.DIMENSION_NAMES.get(dimension, dimension)}",
                    description=f"{self.DIMENSION_NAMES.get(dimension, dimension)}得分较低({score:.1f}/{max_score:.0f})，需要重点改进",
                    priority="mid_term" if percentage >= 40 else "short_term",
                    estimated_effort="2-4周",
                    expected_improvement=f"{self.DIMENSION_NAMES.get(dimension, dimension)}得分提升20%以上",
                    related_dimensions=[dimension]
                ))

        return suggestions

    def _compare_with_history(
        self,
        local_path: str,
        comparison_since: datetime,
        comparison_until: datetime,
        current_data: Dict[str, Any]
    ) -> Optional[HistoricalComparison]:
        """
        与历史版本对比。

        Args:
            local_path: 本地仓库路径。
            comparison_since: 对比开始时间。
            comparison_until: 对比结束时间。
            current_data: 当前数据。

        Returns:
            历史对比数据。
        """
        try:
            logger.info(f"开始历史对比分析: {comparison_since} 到 {comparison_until}")

            # 收集历史代码文件
            historical_code_files = self._collect_code_files(local_path)

            # 评估历史代码质量
            historical_reports = self._evaluate_code_quality(historical_code_files)
            if not historical_reports:
                return None

            # 汇总历史数据
            historical_data = self._aggregate_quality_data(historical_reports)

            # 计算变化
            historical_score = historical_data['total_score']
            current_score = current_data['total_score']
            score_diff = current_score - historical_score

            # 计算各维度变化
            dimension_changes = {}
            improvement_points = []
            regression_points = []

            for dimension in self.DIMENSION_NAMES.keys():
                hist_score = historical_data['dimension_scores'].get(dimension, 0)
                curr_score = current_data['dimension_scores'].get(dimension, 0)
                diff = curr_score - hist_score

                dimension_changes[dimension] = (hist_score, curr_score, diff)

                if diff > 5:
                    improvement_points.append(
                        f"{self.DIMENSION_NAMES[dimension]}提升了{diff:.1f}分"
                    )
                elif diff < -5:
                    regression_points.append(
                        f"{self.DIMENSION_NAMES[dimension]}下降了{abs(diff):.1f}分"
                    )

            return HistoricalComparison(
                historical_score=historical_score,
                current_score=current_score,
                score_diff=score_diff,
                dimension_changes=dimension_changes,
                improvement_points=improvement_points,
                regression_points=regression_points
            )

        except Exception as e:
            logger.error(f"历史对比分析失败: {e}")
            return None

    def _compare_developers(
        self,
        local_path: str,
        since: Optional[datetime],
        until: Optional[datetime],
        quality_reports: List[QualityReport]
    ) -> Optional[List[DeveloperComparison]]:
        """
        对比开发者代码质量。

        Args:
            local_path: 本地仓库路径。
            since: 开始时间。
            until: 结束时间。
            quality_reports: 质量报告列表。

        Returns:
            开发者对比列表。
        """
        try:
            if not GIT_ANALYZER_AVAILABLE:
                return None

            logger.info("开始开发者对比分析")

            # 获取提交记录
            commits = CommitAnalyzer.get_commits(local_path, since, until)
            if not commits:
                return None

            # 按作者分组提交
            author_commits: Dict[str, List[Dict]] = {}
            for commit in commits:
                author = commit['author']
                if author not in author_commits:
                    author_commits[author] = []
                author_commits[author].append(commit)

            # 为每个开发者计算质量得分
            developer_comparisons = []

            for author, author_commit_list in author_commits.items():
                # 获取该开发者修改的文件
                author_files = set()
                for commit in author_commit_list:
                    details = CommitAnalyzer.get_commit_details(local_path, commit['hash'])
                    for file_info in details.get('changed_files', []):
                        file_path = os.path.join(local_path, file_info['path'])
                        if os.path.exists(file_path):
                            author_files.add(file_path)

                # 计算该开发者的平均质量得分
                if author_files:
                    author_reports = [r for r in quality_reports if r.file_path in author_files]
                    if author_reports:
                        avg_score = sum(r.total_score for r in author_reports) / len(author_reports)

                        # 计算各维度平均得分
                        dimension_scores = {}
                        for dimension in self.DIMENSION_NAMES.keys():
                            dim_scores = [r.dimensions[dimension].score for r in author_reports if dimension in r.dimensions]
                            dimension_scores[dimension] = sum(dim_scores) / len(dim_scores) if dim_scores else 0

                        # 确定优势和劣势
                        strengths = []
                        weaknesses = []

                        for dimension, score in dimension_scores.items():
                            max_score = self.evaluator.DIMENSION_MAX_SCORES.get(dimension, 20)
                            percentage = (score / max_score * 100) if max_score > 0 else 0

                            if percentage >= 70:
                                strengths.append(self.DIMENSION_NAMES[dimension])
                            elif percentage < 50:
                                weaknesses.append(self.DIMENSION_NAMES[dimension])

                        developer_comparisons.append(DeveloperComparison(
                            developer_name=author,
                            total_score=avg_score,
                            dimension_scores=dimension_scores,
                            rank=0,  # 稍后设置
                            quality_level=self._determine_quality_level(avg_score).value,
                            strengths=strengths,
                            weaknesses=weaknesses
                        ))

            # 按总分排序并设置排名
            developer_comparisons.sort(key=lambda x: x.total_score, reverse=True)
            for i, dev in enumerate(developer_comparisons, 1):
                dev.rank = i

            return developer_comparisons

        except Exception as e:
            logger.error(f"开发者对比分析失败: {e}")
            return None

    def _generate_markdown_report(
        self,
        aggregated_data: Dict[str, Any],
        issues: List[QualityIssue],
        suggestions: List[OptimizationSuggestion],
        historical_comparison: Optional[HistoricalComparison],
        developer_comparisons: Optional[List[DeveloperComparison]],
        local_path: str,
        since: Optional[datetime],
        until: Optional[datetime]
    ) -> str:
        """
        生成Markdown格式的报告。

        Args:
            aggregated_data: 汇总数据。
            issues: 问题列表。
            suggestions: 建议列表。
            historical_comparison: 历史对比数据。
            developer_comparisons: 开发者对比数据。
            local_path: 本地路径。
            since: 开始时间。
            until: 结束时间。

        Returns:
            Markdown格式的报告内容。
        """
        # 直接生成报告内容，不使用模板文件
        markdown_content = self._build_report_content(
            aggregated_data,
            issues,
            suggestions,
            historical_comparison,
            developer_comparisons,
            local_path,
            since,
            until
        )

        return markdown_content

    def _build_report_content(
        self,
        aggregated_data: Dict[str, Any],
        issues: List[QualityIssue],
        suggestions: List[OptimizationSuggestion],
        historical_comparison: Optional[HistoricalComparison],
        developer_comparisons: Optional[List[DeveloperComparison]],
        local_path: str,
        since: Optional[datetime],
        until: Optional[datetime]
    ) -> str:
        """
        构建报告内容。

        Args:
            aggregated_data: 汇总数据。
            issues: 问题列表。
            suggestions: 建议列表。
            historical_comparison: 历史对比数据。
            developer_comparisons: 开发者对比数据。
            local_path: 本地路径。
            since: 开始时间。
            until: 结束时间。

        Returns:
            Markdown格式的报告内容。
        """
        now = datetime.now()
        total_score = aggregated_data.get('total_score', 0)
        quality_level = aggregated_data.get('quality_level', QualityLevel.UNQUALIFIED).value

        # 构建报告
        markdown = f"# 代码质量检验报告\n\n"
        markdown += f"**生成时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown += f"**分析仓库**: {local_path}\n"
        markdown += f"**分析时间范围**: {since.strftime('%Y-%m-%d') if since else '开始'} 到 {until.strftime('%Y-%m-%d') if until else '现在'}\n"
        markdown += f"**算法模式**: 基于代码质量\n\n"
        markdown += "---\n\n"

        # 一、总体质量评估
        markdown += "## 一、总体质量评估\n\n"
        markdown += "### 1.1 综合得分\n\n"
        markdown += f"```\n"
        markdown += f"╔══════════════════════════════════════════════════════════════╗\n"
        markdown += f"║                    代码质量总评分                             ║\n"
        markdown += f"╠══════════════════════════════════════════════════════════════╣\n"
        markdown += f"║  总分: {total_score:.2f} / 100.00                              ║\n"
        markdown += f"║  等级: {quality_level}                                        ║\n"
        markdown += f"║  得分率: {total_score:.1f}%                              ║\n"
        markdown += f"╚══════════════════════════════════════════════════════════════╝\n"
        markdown += f"```\n\n"

        # 各维度得分
        markdown += "### 1.2 各维度得分概览\n\n"
        markdown += "| 维度 | 得分 | 满分 | 得分率 | 状态 |\n"
        markdown += "|------|------|------|--------|------|\n"

        dimension_scores = aggregated_data.get('dimension_scores', {})
        for dimension, dimension_name in self.DIMENSION_NAMES.items():
            score = dimension_scores.get(dimension, 0)
            max_score = self.evaluator.DIMENSION_MAX_SCORES.get(dimension, 20)
            percentage = (score / max_score * 100) if max_score > 0 else 0
            status = "✓" if percentage >= 60 else "✗"
            markdown += f"| {dimension_name} | {score:.2f} | {max_score:.0f} | {percentage:.1f}% | {status} |\n"

        markdown += "\n---\n\n"

        # 二、各维度详细评估
        markdown += "## 二、各维度详细评估\n\n"
        markdown += self._generate_dimension_details_markdown(aggregated_data)

        # 三、问题汇总与优先级
        markdown += "## 三、问题汇总与优先级\n\n"

        critical_count = len([i for i in issues if i.severity == IssueSeverity.CRITICAL])
        high_count = len([i for i in issues if i.severity == IssueSeverity.HIGH])
        medium_count = len([i for i in issues if i.severity == IssueSeverity.MEDIUM])
        low_count = len([i for i in issues if i.severity == IssueSeverity.LOW])

        markdown += "### 3.1 问题严重程度分布\n\n"
        markdown += f"```\n"
        markdown += f"严重问题 (Critical)    : {critical_count} 个\n"
        markdown += f"重要问题 (High)        : {high_count} 个\n"
        markdown += f"中等问题 (Medium)      : {medium_count} 个\n"
        markdown += f"轻微问题 (Low)         : {low_count} 个\n"
        markdown += f"```\n\n"

        markdown += "### 3.2 问题详细清单\n\n"
        markdown += self._generate_issues_table(issues)
        markdown += "\n---\n\n"

        # 四、优化建议汇总
        markdown += "## 四、优化建议汇总\n\n"
        markdown += self._generate_optimization_suggestions_markdown(suggestions)
        markdown += "---\n\n"

        # 五、对比分析
        markdown += "## 五、对比分析\n\n"
        markdown += self._generate_comparison_section(historical_comparison, developer_comparisons)
        markdown += "---\n\n"

        # 六、行动计划
        markdown += "## 六、行动计划\n\n"
        markdown += self._generate_action_plan(issues, suggestions)
        markdown += "---\n\n"

        # 七、附录
        markdown += "## 七、附录\n\n"
        markdown += "### 7.1 评估方法说明\n\n"
        markdown += "本报告采用五维度代码质量评估体系：\n\n"
        markdown += "1. **可读性评估**（25分）：评估代码命名规范、注释质量、代码格式、复杂度和文档字符串\n"
        markdown += "2. **可维护性评估**（25分）：评估模块化程度、代码重复度、依赖管理、函数长度和类设计\n"
        markdown += "3. **性能效率评估**（20分）：评估算法复杂度、资源使用、数据结构选择和循环优化\n"
        markdown += "4. **错误处理评估**（15分）：评估异常捕获、错误日志和边界检查\n"
        markdown += "5. **安全性评估**（15分）：评估输入验证、敏感数据处理和安全编码实践\n\n"

        markdown += "### 7.2 评估范围\n\n"
        markdown += f"- **分析文件数**: {aggregated_data.get('file_count', 0)} 个\n"
        markdown += f"- **评估器版本**: 1.0\n\n"

        markdown += "---\n\n"
        markdown += f"**报告生成器**: Git Analyzer Quality Reporter v1.0\n"
        markdown += f"**作者**: WING\n"
        markdown += f"**生成日期**: {now.strftime('%Y-%m-%d')}\n"

        return markdown

    def _generate_action_plan(
        self,
        issues: List[QualityIssue],
        suggestions: List[OptimizationSuggestion]
    ) -> str:
        """
        生成行动计划。

        Args:
            issues: 问题列表。
            suggestions: 建议列表。

        Returns:
            行动计划的Markdown内容。
        """
        markdown = ""

        # 立即执行
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        high_issues = [i for i in issues if i.severity == IssueSeverity.HIGH]

        markdown += "### 6.1 立即执行（本周）\n\n"
        if critical_issues:
            markdown += "**严重问题修复**:\n"
            for issue in critical_issues[:5]:  # 最多显示5个
                markdown += f"- [{issue.issue_id}] {issue.description}\n"
            markdown += "\n"

        if high_issues:
            markdown += "**重要问题处理**:\n"
            for issue in high_issues[:5]:
                markdown += f"- [{issue.issue_id}] {issue.description}\n"
            markdown += "\n"

        if not critical_issues and not high_issues:
            markdown += "暂无需要立即处理的问题\n\n"

        # 短期计划
        short_term_suggestions = [s for s in suggestions if s.priority == 'short_term']
        markdown += "### 6.2 短期计划（本月）\n\n"
        if short_term_suggestions:
            for suggestion in short_term_suggestions:
                markdown += f"- **{suggestion.title}**: {suggestion.description}\n"
            markdown += "\n"
        else:
            markdown += "暂无短期计划\n\n"

        # 中期计划
        mid_term_suggestions = [s for s in suggestions if s.priority == 'mid_term']
        markdown += "### 6.3 中期计划（本季度）\n\n"
        if mid_term_suggestions:
            for suggestion in mid_term_suggestions:
                markdown += f"- **{suggestion.title}**: {suggestion.description}\n"
            markdown += "\n"
        else:
            markdown += "暂无中期计划\n\n"

        return markdown

    def _get_default_template(self) -> str:
        """获取默认模板。"""
        return """# 代码质量检验报告

**生成时间**: {generation_time}
**分析仓库**: {repository_path}
**分析时间范围**: {time_range}

---

## 一、总体质量评估

### 1.1 综合得分

总分: {total_score:.2f} / 100.00
等级: {quality_level}
得分率: {score_percentage:.1f}%

---

## 二、各维度详细评估

{dimension_details}

---

## 三、问题汇总与优先级

### 3.1 问题严重程度分布

严重问题 (Critical)    : {critical_count} 个
重要问题 (High)        : {high_count} 个
中等问题 (Medium)      : {medium_count} 个
轻微问题 (Low)         : {low_count} 个

### 3.2 问题详细清单

{issues_table}

---

## 四、优化建议汇总

{optimization_suggestions}

---

## 五、对比分析

{comparison_section}

---

**报告生成器**: Git Analyzer Quality Reporter v1.0
**作者**: WING
**生成日期**: {generation_date}
"""

    def _generate_dimension_details_markdown(self, aggregated_data: Dict[str, Any]) -> str:
        """生成各维度详细评估的Markdown内容。"""
        markdown = ""

        dimension_scores = aggregated_data.get('dimension_scores', {})
        dimension_details = aggregated_data.get('dimension_details', {})

        for dimension, dimension_name in self.DIMENSION_NAMES.items():
            score = dimension_scores.get(dimension, 0)
            max_score = self.evaluator.DIMENSION_MAX_SCORES.get(dimension, 20)
            percentage = (score / max_score * 100) if max_score > 0 else 0

            markdown += f"### {dimension_name}评估（满分{max_score:.0f}分）\n\n"
            markdown += f"**得分**: {score:.2f} / {max_score:.0f}\n"
            markdown += f"**得分率**: {percentage:.1f}%\n\n"

            # 子项评分
            if dimension in dimension_details:
                markdown += "#### 子项评分\n\n"
                markdown += "| 子项 | 得分 | 满分 | 状态 |\n"
                markdown += "|------|------|------|------|\n"

                for subitem, subitem_score in dimension_details[dimension].items():
                    subitem_name = self.SUBITEM_NAMES.get(subitem, subitem)
                    status = "✓" if subitem_score >= 3.0 else "✗"
                    markdown += f"| {subitem_name} | {subitem_score:.2f} | 5.00 | {status} |\n"

                markdown += "\n"

            markdown += "---\n\n"

        return markdown

    def _generate_issues_table(self, issues: List[QualityIssue]) -> str:
        """生成问题表格的Markdown内容。"""
        if not issues:
            return "暂无问题\n"

        markdown = "| 编号 | 维度 | 问题描述 | 严重程度 | 影响范围 | 建议措施 |\n"
        markdown += "|------|------|----------|----------|----------|----------|\n"

        for issue in issues:
            dimension_name = self.DIMENSION_NAMES.get(issue.dimension, issue.dimension)
            severity_emoji = {
                IssueSeverity.CRITICAL: "🔴",
                IssueSeverity.HIGH: "🟠",
                IssueSeverity.MEDIUM: "🟡",
                IssueSeverity.LOW: "🟢"
            }.get(issue.severity, "")

            markdown += f"| {issue.issue_id} | {dimension_name} | {issue.description} | {severity_emoji} {issue.severity.value} | {issue.impact_scope} | {issue.suggestion} |\n"

        return markdown

    def _generate_optimization_suggestions_markdown(self, suggestions: List[OptimizationSuggestion]) -> str:
        """生成优化建议的Markdown内容。"""
        if not suggestions:
            return "暂无优化建议\n"

        markdown = ""

        # 短期建议
        short_term = [s for s in suggestions if s.priority == 'short_term']
        if short_term:
            markdown += "### 4.1 短期优化建议（1-2周）\n\n"
            for i, suggestion in enumerate(short_term, 1):
                markdown += f"{i}. **{suggestion.title}**\n"
                markdown += f"   - 描述: {suggestion.description}\n"
                markdown += f"   - 预计工作量: {suggestion.estimated_effort}\n"
                markdown += f"   - 预期改进: {suggestion.expected_improvement}\n\n"

        # 中期建议
        mid_term = [s for s in suggestions if s.priority == 'mid_term']
        if mid_term:
            markdown += "### 4.2 中期优化建议（1-2月）\n\n"
            for i, suggestion in enumerate(mid_term, 1):
                markdown += f"{i}. **{suggestion.title}**\n"
                markdown += f"   - 描述: {suggestion.description}\n"
                markdown += f"   - 预计工作量: {suggestion.estimated_effort}\n"
                markdown += f"   - 预期改进: {suggestion.expected_improvement}\n\n"

        # 长期建议
        long_term = [s for s in suggestions if s.priority == 'long_term']
        if long_term:
            markdown += "### 4.3 长期优化建议（3-6月）\n\n"
            for i, suggestion in enumerate(long_term, 1):
                markdown += f"{i}. **{suggestion.title}**\n"
                markdown += f"   - 描述: {suggestion.description}\n"
                markdown += f"   - 预计工作量: {suggestion.estimated_effort}\n"
                markdown += f"   - 预期改进: {suggestion.expected_improvement}\n\n"

        return markdown

    def _generate_comparison_section(
        self,
        historical_comparison: Optional[HistoricalComparison],
        developer_comparisons: Optional[List[DeveloperComparison]]
    ) -> str:
        """生成对比分析部分的Markdown内容。"""
        markdown = ""

        # 历史对比
        if historical_comparison:
            markdown += "### 5.1 历史版本对比\n\n"

            # 趋势描述
            if historical_comparison.score_diff > 0:
                trend_direction = "提升"
                trend_description = f"质量提升了{historical_comparison.score_diff:.1f}分"
            elif historical_comparison.score_diff < 0:
                trend_direction = "下降"
                trend_description = f"质量下降了{abs(historical_comparison.score_diff):.1f}分"
            else:
                trend_direction = "持平"
                trend_description = "质量保持稳定"

            markdown += f"**总体趋势**: {trend_description}\n\n"

            # 变化详情表格
            markdown += "#### 变化详情\n\n"
            markdown += "| 维度 | 历史得分 | 当前得分 | 变化 | 趋势 |\n"
            markdown += "|------|----------|----------|------|------|\n"

            for dimension, (hist, curr, diff) in historical_comparison.dimension_changes.items():
                dimension_name = self.DIMENSION_NAMES.get(dimension, dimension)
                trend = "↑" if diff > 0 else "↓" if diff < 0 else "→"
                markdown += f"| {dimension_name} | {hist:.1f} | {curr:.1f} | {diff:+.1f} | {trend} |\n"

            markdown += "\n"

            # 改进点
            if historical_comparison.improvement_points:
                markdown += "#### 改进点分析\n\n"
                for point in historical_comparison.improvement_points:
                    markdown += f"- {point}\n"
                markdown += "\n"

            # 退步点
            if historical_comparison.regression_points:
                markdown += "#### 退步点分析\n\n"
                for point in historical_comparison.regression_points:
                    markdown += f"- {point}\n"
                markdown += "\n"

        # 开发者对比
        if developer_comparisons:
            markdown += "### 5.2 开发者对比分析\n\n"

            # 排名表格
            markdown += "#### 开发者质量排名\n\n"
            markdown += "| 排名 | 开发者 | 总分 | 可读性 | 可维护性 | 性能 | 错误处理 | 安全性 |\n"
            markdown += "|------|--------|------|--------|----------|------|----------|--------|\n"

            for dev in developer_comparisons:
                markdown += f"| {dev.rank} | {dev.developer_name} | {dev.total_score:.1f} | "
                markdown += f"{dev.dimension_scores.get('readability', 0):.1f} | "
                markdown += f"{dev.dimension_scores.get('maintainability', 0):.1f} | "
                markdown += f"{dev.dimension_scores.get('performance', 0):.1f} | "
                markdown += f"{dev.dimension_scores.get('error_handling', 0):.1f} | "
                markdown += f"{dev.dimension_scores.get('security', 0):.1f} |\n"

            markdown += "\n"

            # 最佳实践开发者
            if developer_comparisons:
                best_dev = developer_comparisons[0]
                markdown += "#### 最佳实践开发者\n\n"
                markdown += f"**{best_dev.developer_name}** (得分: {best_dev.total_score:.1f})\n\n"

                if best_dev.strengths:
                    markdown += "**优势领域**:\n"
                    for strength in best_dev.strengths:
                        markdown += f"- {strength}\n"
                    markdown += "\n"

            # 需要改进的开发者
            if len(developer_comparisons) > 1:
                needs_improvement = [d for d in developer_comparisons if d.quality_level in ['不合格', '合格']]
                if needs_improvement:
                    markdown += "#### 需要改进的开发者\n\n"
                    for dev in needs_improvement:
                        markdown += f"**{dev.developer_name}** (得分: {dev.total_score:.1f})\n\n"

                        if dev.weaknesses:
                            markdown += "**待改进领域**:\n"
                            for weakness in dev.weaknesses:
                                markdown += f"- {weakness}\n"
                            markdown += "\n"

        if not historical_comparison and not developer_comparisons:
            markdown += "暂无对比分析数据\n"

        return markdown


def main():
    """主函数，用于测试。"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python quality_report_generator.py <repository_path> [output_file]")
        sys.exit(1)

    repository_path = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "quality_inspection_report.md"

    # 创建报告生成器
    generator = QualityReportGenerator(
        project_type=ProjectType.OTHER,
        project_stage=ProjectStage.DEVELOPMENT,
        team_size=1
    )

    # 生成报告
    success = generator.generate_quality_report(
        local_path=repository_path,
        output_file=output_file,
        include_comparison=False
    )

    if success:
        print(f"质量检验报告生成成功: {output_file}")
    else:
        print("质量检验报告生成失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
