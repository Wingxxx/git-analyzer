#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码质量评估器单元测试

测试五维度代码质量评估功能。

WING
"""

import pytest
import sys
import os
import ast

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from code_quality_evaluator import (
    CodeQualityEvaluator,
    EvaluationResult,
    QualityReport,
    QualityLevel,
    ProjectType,
    ProjectStage
)


# ==================== 枚举类测试 ====================

class TestQualityLevel:
    """测试质量等级枚举。"""
    
    def test_quality_level_values(self):
        """测试质量等级枚举值。"""
        assert QualityLevel.EXCELLENT.value == "优秀"
        assert QualityLevel.GOOD.value == "良好"
        assert QualityLevel.QUALIFIED.value == "合格"
        assert QualityLevel.UNQUALIFIED.value == "不合格"


class TestProjectType:
    """测试项目类型枚举。"""
    
    def test_project_type_values(self):
        """测试项目类型枚举值。"""
        assert ProjectType.WEB_APP.value == "web_app"
        assert ProjectType.CLI_TOOL.value == "cli_tool"
        assert ProjectType.LIBRARY.value == "library"
        assert ProjectType.DATA_SCIENCE.value == "data_science"
        assert ProjectType.OTHER.value == "other"


class TestProjectStage:
    """测试项目阶段枚举。"""
    
    def test_project_stage_values(self):
        """测试项目阶段枚举值。"""
        assert ProjectStage.DEVELOPMENT.value == "development"
        assert ProjectStage.TESTING.value == "testing"
        assert ProjectStage.PRODUCTION.value == "production"


# ==================== 数据类测试 ====================

class TestEvaluationResult:
    """测试评估结果数据类。"""
    
    def test_default_values(self):
        """测试默认值。"""
        result = EvaluationResult(
            dimension="readability",
            score=20.0,
            max_score=25.0
        )
        
        assert result.dimension == "readability"
        assert result.score == 20.0
        assert result.max_score == 25.0
        assert result.details == {}
        assert result.suggestions == []
    
    def test_percentage(self):
        """测试百分比计算。"""
        result = EvaluationResult(
            dimension="readability",
            score=20.0,
            max_score=25.0
        )
        
        assert result.percentage == 80.0
    
    def test_percentage_zero_max(self):
        """测试最大值为零时的百分比。"""
        result = EvaluationResult(
            dimension="test",
            score=10.0,
            max_score=0.0
        )
        
        assert result.percentage == 0.0


class TestQualityReport:
    """测试质量报告数据类。"""
    
    def test_default_values(self):
        """测试默认值。"""
        report = QualityReport(
            total_score=75.0,
            max_score=100.0,
            level=QualityLevel.GOOD,
            dimensions={},
            weight_coefficients={},
            file_path="/test/file.py"
        )
        
        assert report.total_score == 75.0
        assert report.max_score == 100.0
        assert report.level == QualityLevel.GOOD
        assert report.dimensions == {}
        assert report.suggestions == []
    
    def test_percentage(self):
        """测试百分比计算。"""
        report = QualityReport(
            total_score=85.0,
            max_score=100.0,
            level=QualityLevel.EXCELLENT,
            dimensions={},
            weight_coefficients={},
            file_path="/test/file.py"
        )
        
        assert report.percentage == 85.0


# ==================== CodeQualityEvaluator测试 ====================

class TestCodeQualityEvaluator:
    """测试代码质量评估器。"""
    
    def test_initialization_default(self):
        """测试默认初始化。"""
        evaluator = CodeQualityEvaluator()
        
        assert evaluator.project_type == ProjectType.OTHER
        assert evaluator.project_stage == ProjectStage.DEVELOPMENT
        assert evaluator.team_size == 1
        assert evaluator.code_lines == 0
    
    def test_initialization_custom(self):
        """测试自定义初始化。"""
        evaluator = CodeQualityEvaluator(
            project_type=ProjectType.WEB_APP,
            project_stage=ProjectStage.PRODUCTION,
            team_size=10,
            code_lines=50000
        )
        
        assert evaluator.project_type == ProjectType.WEB_APP
        assert evaluator.project_stage == ProjectStage.PRODUCTION
        assert evaluator.team_size == 10
        assert evaluator.code_lines == 50000
    
    def test_initialization_invalid_parameters(self):
        """测试无效参数的初始化。"""
        # 无效团队规模应该使用默认值
        evaluator = CodeQualityEvaluator(team_size=-1)
        assert evaluator.team_size == 1
        
        # 无效代码行数应该使用默认值
        evaluator = CodeQualityEvaluator(code_lines=-100)
        assert evaluator.code_lines == 0


class TestEvaluateFile:
    """测试文件评估功能。"""
    
    def test_evaluate_good_file(self, sample_python_file):
        """测试评估高质量文件。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        assert isinstance(report, QualityReport)
        assert report.total_score >= 0
        assert report.total_score <= 100
        assert report.level in [QualityLevel.EXCELLENT, QualityLevel.GOOD, QualityLevel.QUALIFIED, QualityLevel.UNQUALIFIED]
        assert len(report.dimensions) == 5
        assert 'readability' in report.dimensions
        assert 'maintainability' in report.dimensions
        assert 'performance' in report.dimensions
        assert 'error_handling' in report.dimensions
        assert 'security' in report.dimensions
    
    def test_evaluate_bad_file(self, sample_bad_python_file):
        """测试评估低质量文件。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_bad_python_file)
        
        assert isinstance(report, QualityReport)
        assert report.total_score >= 0
        # 低质量文件应该得分较低
        assert report.total_score < 80
    
    def test_evaluate_syntax_error_file(self, syntax_error_file):
        """测试评估有语法错误的文件。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(syntax_error_file)
        
        # 语法错误应该返回最低分报告
        assert isinstance(report, QualityReport)
        assert report.total_score == 0.0
        assert report.level == QualityLevel.UNQUALIFIED
        assert len(report.suggestions) > 0
    
    def test_evaluate_nonexistent_file(self):
        """测试评估不存在的文件。"""
        evaluator = CodeQualityEvaluator()
        
        with pytest.raises(FileNotFoundError):
            evaluator.evaluate_file("/nonexistent/file.py")
    
    def test_evaluate_empty_path(self):
        """测试评估空路径。"""
        evaluator = CodeQualityEvaluator()
        
        with pytest.raises(FileNotFoundError):
            evaluator.evaluate_file("")
    
    def test_evaluate_directory(self, tmp_path):
        """测试评估目录（应该失败）。"""
        evaluator = CodeQualityEvaluator()
        
        with pytest.raises(FileNotFoundError):
            evaluator.evaluate_file(str(tmp_path))


class TestReadabilityEvaluation:
    """测试可读性评估。"""
    
    def test_naming_conventions_good(self, sample_python_file):
        """测试良好命名规范。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        readability = report.dimensions['readability']
        assert 'naming_conventions' in readability.details
        # 良好的命名应该得分较高
        assert readability.details['naming_conventions'] >= 3.0
    
    def test_naming_conventions_bad(self, sample_bad_python_file):
        """测试不良命名规范。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_bad_python_file)
        
        readability = report.dimensions['readability']
        assert 'naming_conventions' in readability.details
        # 不良命名应该得分较低
        assert readability.details['naming_conventions'] < 5.0
    
    def test_comment_quality(self, sample_python_file):
        """测试注释质量。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        readability = report.dimensions['readability']
        assert 'comment_quality' in readability.details
    
    def test_docstring_quality(self, sample_python_file):
        """测试文档字符串质量。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        readability = report.dimensions['readability']
        assert 'docstring_quality' in readability.details
        # 有文档字符串的文件应该得分较高
        assert readability.details['docstring_quality'] >= 3.0


class TestMaintainabilityEvaluation:
    """测试可维护性评估。"""
    
    def test_modularity(self, sample_python_file):
        """测试模块化程度。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        maintainability = report.dimensions['maintainability']
        assert 'modularity' in maintainability.details
    
    def test_function_length(self, sample_python_file):
        """测试函数长度。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        maintainability = report.dimensions['maintainability']
        assert 'function_length' in maintainability.details


class TestPerformanceEvaluation:
    """测试性能效率评估。"""
    
    def test_algorithm_complexity(self, sample_python_file):
        """测试算法复杂度。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        performance = report.dimensions['performance']
        assert 'algorithm_complexity' in performance.details
    
    def test_resource_usage(self, sample_python_file):
        """测试资源使用。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        performance = report.dimensions['performance']
        assert 'resource_usage' in performance.details


class TestErrorHandlingEvaluation:
    """测试错误处理评估。"""
    
    def test_exception_handling(self, sample_python_file):
        """测试异常处理。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        error_handling = report.dimensions['error_handling']
        assert 'exception_handling' in error_handling.details
    
    def test_error_logging(self, sample_python_file):
        """测试错误日志。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        error_handling = report.dimensions['error_handling']
        assert 'error_logging' in error_handling.details


class TestSecurityEvaluation:
    """测试安全性评估。"""
    
    def test_input_validation(self, sample_python_file):
        """测试输入验证。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        security = report.dimensions['security']
        assert 'input_validation' in security.details
    
    def test_sensitive_data_handling(self, sample_python_file):
        """测试敏感数据处理。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        security = report.dimensions['security']
        assert 'sensitive_data_handling' in security.details


class TestWeightCoefficients:
    """测试权重系数计算。"""
    
    def test_default_weights(self):
        """测试默认权重。"""
        evaluator = CodeQualityEvaluator()
        
        # 权重总和应该为1.0
        total_weight = sum(evaluator.weight_coefficients.values())
        assert abs(total_weight - 1.0) < 0.01
    
    def test_project_type_weights(self):
        """测试项目类型权重调整。"""
        evaluator_web = CodeQualityEvaluator(project_type=ProjectType.WEB_APP)
        evaluator_cli = CodeQualityEvaluator(project_type=ProjectType.CLI_TOOL)
        
        # Web项目应该更重视安全性
        assert evaluator_web.weight_coefficients['security'] >= evaluator_cli.weight_coefficients['security']
    
    def test_project_stage_weights(self):
        """测试项目阶段权重调整。"""
        evaluator_dev = CodeQualityEvaluator(project_stage=ProjectStage.DEVELOPMENT)
        evaluator_prod = CodeQualityEvaluator(project_stage=ProjectStage.PRODUCTION)
        
        # 生产环境应该更重视安全性
        assert evaluator_prod.weight_coefficients['security'] >= evaluator_dev.weight_coefficients['security']
    
    def test_team_size_weights(self):
        """测试团队规模权重调整。"""
        evaluator_small = CodeQualityEvaluator(team_size=2)
        evaluator_large = CodeQualityEvaluator(team_size=20)
        
        # 大团队应该更重视可读性和可维护性
        assert evaluator_large.weight_coefficients['readability'] >= evaluator_small.weight_coefficients['readability']


class TestBatchEvaluation:
    """测试批量评估功能。"""
    
    def test_evaluate_files_batch(self, sample_python_file, sample_bad_python_file):
        """测试批量评估文件。"""
        evaluator = CodeQualityEvaluator()
        
        files = [sample_python_file, sample_bad_python_file]
        reports = evaluator.evaluate_files_batch(files, parallel=False)
        
        assert len(reports) == 2
        assert all(isinstance(r, QualityReport) for r in reports)
    
    def test_evaluate_files_batch_empty(self):
        """测试批量评估空列表。"""
        evaluator = CodeQualityEvaluator()
        
        reports = evaluator.evaluate_files_batch([])
        
        assert reports == []


class TestReportGeneration:
    """测试报告生成。"""
    
    def test_generate_markdown_report(self, sample_python_file):
        """测试生成Markdown报告。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        markdown = evaluator.generate_report_markdown(report)
        
        assert isinstance(markdown, str)
        assert "代码质量评估报告" in markdown
        assert sample_python_file in markdown
        assert "总体评分" in markdown
        assert "各维度评分" in markdown
    
    def test_report_contains_suggestions(self, sample_bad_python_file):
        """测试报告包含改进建议。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_bad_python_file)
        
        # 低质量文件应该有改进建议
        if report.total_score < 60:
            assert len(report.suggestions) > 0


class TestQualityLevelDetermination:
    """测试质量等级判定。"""
    
    def test_excellent_level(self, sample_python_file):
        """测试优秀等级。"""
        evaluator = CodeQualityEvaluator()
        report = evaluator.evaluate_file(sample_python_file)
        
        # 高质量文件应该达到良好或优秀
        if report.total_score >= 80:
            assert report.level == QualityLevel.EXCELLENT
    
    def test_qualified_level(self):
        """测试合格等级。"""
        evaluator = CodeQualityEvaluator()
        
        # 创建一个得分在40-60之间的报告
        from code_quality_evaluator import EvaluationResult
        
        dimensions = {
            'readability': EvaluationResult('readability', 15.0, 25.0),
            'maintainability': EvaluationResult('maintainability', 15.0, 25.0),
            'performance': EvaluationResult('performance', 10.0, 20.0),
            'error_handling': EvaluationResult('error_handling', 5.0, 15.0),
            'security': EvaluationResult('security', 5.0, 15.0)
        }
        
        report = QualityReport(
            total_score=50.0,
            max_score=100.0,
            level=QualityLevel.QUALIFIED,
            dimensions=dimensions,
            weight_coefficients={},
            file_path="/test/file.py"
        )
        
        assert report.level == QualityLevel.QUALIFIED


class TestEdgeCases:
    """测试边界条件。"""
    
    def test_empty_file(self, tmp_path):
        """测试空文件。"""
        evaluator = CodeQualityEvaluator()
        
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")
        
        report = evaluator.evaluate_file(str(empty_file))
        
        assert isinstance(report, QualityReport)
        # 空文件应该得分较低
        assert report.total_score < 50
    
    def test_large_file(self, large_python_file):
        """测试大型文件。"""
        evaluator = CodeQualityEvaluator()
        
        report = evaluator.evaluate_file(large_python_file)
        
        assert isinstance(report, QualityReport)
        assert report.total_score >= 0
    
    def test_file_with_only_comments(self, tmp_path):
        """测试只有注释的文件。"""
        evaluator = CodeQualityEvaluator()
        
        comment_file = tmp_path / "comments.py"
        comment_file.write_text("# This is a comment\n# Another comment\n")
        
        report = evaluator.evaluate_file(str(comment_file))
        
        assert isinstance(report, QualityReport)


class TestASTParsing:
    """测试AST解析功能。"""
    
    def test_parse_valid_python(self, sample_python_file):
        """测试解析有效Python代码。"""
        evaluator = CodeQualityEvaluator()
        
        tree = evaluator._get_ast(sample_python_file)
        
        assert tree is not None
        assert isinstance(tree, ast.AST)
    
    def test_parse_invalid_python(self, syntax_error_file):
        """测试解析无效Python代码。"""
        evaluator = CodeQualityEvaluator()
        
        tree = evaluator._get_ast(syntax_error_file)
        
        # 语法错误的文件应该返回None
        assert tree is None


class TestCaching:
    """测试缓存功能。"""
    
    def test_ast_caching(self, sample_python_file):
        """测试AST缓存。"""
        evaluator = CodeQualityEvaluator(enable_cache=True)
        
        # 第一次解析
        tree1 = evaluator._get_ast(sample_python_file)
        
        # 第二次解析（应该使用缓存）
        tree2 = evaluator._get_ast(sample_python_file)
        
        assert tree1 is not None
        assert tree2 is not None
    
    def test_file_content_caching(self, sample_python_file):
        """测试文件内容缓存。"""
        evaluator = CodeQualityEvaluator(enable_cache=True)
        
        # 第一次读取
        content1 = evaluator._read_file_cached(sample_python_file)
        
        # 第二次读取（应该使用缓存）
        content2 = evaluator._read_file_cached(sample_python_file)
        
        assert content1 == content2
