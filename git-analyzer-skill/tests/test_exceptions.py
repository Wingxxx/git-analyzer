#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常类单元测试

测试所有自定义异常类的功能。

WING
"""

import pytest
import sys
import os

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

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
    FileNotFoundError as CustomFileNotFoundError,
    FileReadError,
    FileTooLargeError,
    SyntaxErrorInCode,
    UnsupportedLanguageError,
    InvalidPathError,
    InvalidUrlError,
    InvalidDateError,
    InvalidParameterError,
    ParameterOutOfRangeError,
    MissingRequiredParameterError,
    ReportGenerationError,
    InvalidOutputFormatError,
    InvalidConfigurationError,
    MissingConfigurationError
)


class TestGitAnalyzerError:
    """测试基础异常类。"""
    
    def test_basic_error(self):
        """测试基本错误创建。"""
        error = GitAnalyzerError("测试错误消息")
        assert error.message == "测试错误消息"
        assert error.details == {}
        assert "测试错误消息" in str(error)
    
    def test_error_with_details(self):
        """测试带详细信息的错误。"""
        error = GitAnalyzerError("测试错误", {'key': 'value', 'count': 42})
        assert error.message == "测试错误"
        assert error.details == {'key': 'value', 'count': 42}
        assert "key=value" in str(error)
        assert "count=42" in str(error)
    
    def test_error_inheritance(self):
        """测试异常继承。"""
        error = GitAnalyzerError("测试")
        assert isinstance(error, Exception)


class TestRepositoryErrors:
    """测试仓库相关异常。"""
    
    def test_repository_not_found_error(self):
        """测试仓库不存在异常。"""
        error = RepositoryNotFoundError("/path/to/repo")
        assert "Git仓库不存在" in str(error)
        assert error.details['path'] == "/path/to/repo"
        assert isinstance(error, GitAnalyzerError)
    
    def test_repository_clone_error(self):
        """测试仓库克隆失败异常。"""
        error = RepositoryCloneError("https://github.com/test/repo.git", "网络错误")
        assert "克隆仓库失败" in str(error)
        assert error.details['repo_url'] == "https://github.com/test/repo.git"
        assert error.details['reason'] == "网络错误"
    
    def test_repository_update_error(self):
        """测试仓库更新失败异常。"""
        error = RepositoryUpdateError("/path/to/repo", "权限不足")
        assert "更新仓库失败" in str(error)
        assert error.details['path'] == "/path/to/repo"
        assert error.details['reason'] == "权限不足"
    
    def test_branch_not_found_error(self):
        """测试分支不存在异常。"""
        error = BranchNotFoundError("feature-branch", ['main', 'develop'])
        assert "分支不存在" in str(error)
        assert error.details['branch_name'] == "feature-branch"
        assert "main, develop" in str(error)
    
    def test_branch_not_found_error_without_available(self):
        """测试分支不存在异常（无可用分支列表）。"""
        error = BranchNotFoundError("feature-branch")
        assert "分支不存在" in str(error)
        assert 'available_branches' not in error.details
    
    def test_branch_switch_error(self):
        """测试分支切换失败异常。"""
        error = BranchSwitchError("feature-branch", "未提交的更改")
        assert "切换分支失败" in str(error)
        assert error.details['branch_name'] == "feature-branch"
        assert error.details['reason'] == "未提交的更改"


class TestCommitErrors:
    """测试提交相关异常。"""
    
    def test_commit_not_found_error(self):
        """测试提交不存在异常。"""
        error = CommitNotFoundError("abc123def456")
        assert "提交不存在" in str(error)
        assert error.details['commit_hash'] == "abc123def456"
    
    def test_empty_repository_error(self):
        """测试空仓库异常。"""
        error = EmptyRepositoryError("/path/to/repo")
        assert "仓库为空" in str(error)
        assert error.details['path'] == "/path/to/repo"


class TestContributionErrors:
    """测试贡献度计算相关异常。"""
    
    def test_invalid_algorithm_mode_error(self):
        """测试无效算法模式异常。"""
        error = InvalidAlgorithmModeError("invalid", ["legacy", "quality"])
        assert "无效的算法模式" in str(error)
        assert error.details['mode'] == "invalid"
        assert "legacy, quality" in str(error)
    
    def test_invalid_algorithm_mode_error_without_valid_modes(self):
        """测试无效算法模式异常（无有效模式列表）。"""
        error = InvalidAlgorithmModeError("invalid")
        assert "无效的算法模式" in str(error)
        assert 'valid_modes' not in error.details
    
    def test_quality_evaluator_not_available_error(self):
        """测试代码质量评估器不可用异常。"""
        error = QualityEvaluatorNotAvailableError()
        assert "代码质量评估器不可用" in str(error)


class TestCodeQualityErrors:
    """测试代码质量评估相关异常。"""
    
    def test_file_not_found_error(self):
        """测试文件不存在异常。"""
        error = CustomFileNotFoundError("/path/to/file.py")
        assert "文件不存在" in str(error)
        assert error.details['file_path'] == "/path/to/file.py"
    
    def test_file_read_error(self):
        """测试文件读取失败异常。"""
        error = FileReadError("/path/to/file.py", "权限不足")
        assert "文件读取失败" in str(error)
        assert error.details['file_path'] == "/path/to/file.py"
        assert error.details['reason'] == "权限不足"
    
    def test_file_too_large_error(self):
        """测试文件过大异常。"""
        error = FileTooLargeError("/path/to/file.py", 20 * 1024 * 1024, 10 * 1024 * 1024)
        assert "文件过大" in str(error)
        assert error.details['file_path'] == "/path/to/file.py"
        assert "20.00MB" in str(error)
        assert "10.00MB" in str(error)
    
    def test_syntax_error_in_code(self):
        """测试代码语法错误异常。"""
        error = SyntaxErrorInCode("/path/to/file.py", 42, "invalid syntax")
        assert "代码语法错误" in str(error)
        assert error.details['file_path'] == "/path/to/file.py"
        assert error.details['line_number'] == 42
        assert error.details['error'] == "invalid syntax"
    
    def test_unsupported_language_error(self):
        """测试不支持的语言异常。"""
        error = UnsupportedLanguageError("/path/to/file.xyz", "UnknownLang")
        assert "不支持的语言类型" in str(error)
        assert error.details['file_path'] == "/path/to/file.xyz"
        assert error.details['language'] == "UnknownLang"


class TestValidationErrors:
    """测试输入验证相关异常。"""
    
    def test_invalid_path_error(self):
        """测试无效路径异常。"""
        error = InvalidPathError("/invalid/path", "路径格式无效")
        assert "路径无效" in str(error)
        assert error.details['path'] == "/invalid/path"
        assert error.details['reason'] == "路径格式无效"
    
    def test_invalid_url_error(self):
        """测试无效URL异常。"""
        error = InvalidUrlError("not-a-url", "URL格式无效")
        assert "URL无效" in str(error)
        assert error.details['url'] == "not-a-url"
        assert error.details['reason'] == "URL格式无效"
    
    def test_invalid_date_error(self):
        """测试无效日期异常。"""
        error = InvalidDateError("2024/01/01", "YYYY-MM-DD")
        assert "日期格式无效" in str(error)
        assert error.details['date_str'] == "2024/01/01"
        assert error.details['expected_format'] == "YYYY-MM-DD"
    
    def test_invalid_parameter_error(self):
        """测试无效参数异常。"""
        error = InvalidParameterError("team_size", -1, "必须为正整数")
        assert "参数无效" in str(error)
        assert error.details['param_name'] == "team_size"
        assert error.details['param_value'] == "-1"
        assert error.details['reason'] == "必须为正整数"
    
    def test_parameter_out_of_range_error(self):
        """测试参数超出范围异常。"""
        error = ParameterOutOfRangeError("age", 150, 0, 120)
        assert "参数超出范围" in str(error)
        assert error.details['param_name'] == "age"
        assert error.details['param_value'] == "150"
        assert error.details['min_value'] == "0"
        assert error.details['max_value'] == "120"
    
    def test_parameter_out_of_range_error_min_only(self):
        """测试参数超出范围异常（仅最小值）。"""
        error = ParameterOutOfRangeError("count", -5, min_value=0)
        assert "参数超出范围" in str(error)
        assert error.details['param_name'] == "count"
        assert 'min_value' in error.details
        assert 'max_value' not in error.details
    
    def test_missing_required_parameter_error(self):
        """测试缺少必需参数异常。"""
        error = MissingRequiredParameterError("repo_path")
        assert "缺少必需参数" in str(error)
        assert error.details['param_name'] == "repo_path"


class TestReportErrors:
    """测试报告生成相关异常。"""
    
    def test_report_generation_error(self):
        """测试报告生成失败异常。"""
        error = ReportGenerationError("/path/to/report.md", "磁盘空间不足")
        assert "报告生成失败" in str(error)
        assert error.details['output_path'] == "/path/to/report.md"
        assert error.details['reason'] == "磁盘空间不足"
    
    def test_invalid_output_format_error(self):
        """测试无效输出格式异常。"""
        error = InvalidOutputFormatError("docx", ["md", "html", "json"])
        assert "不支持的输出格式" in str(error)
        assert error.details['format_type'] == "docx"
        assert "md, html, json" in str(error)


class TestConfigurationErrors:
    """测试配置相关异常。"""
    
    def test_invalid_configuration_error(self):
        """测试无效配置异常。"""
        error = InvalidConfigurationError("max_size", -1, "必须为正整数")
        assert "配置无效" in str(error)
        assert error.details['config_key'] == "max_size"
        assert error.details['config_value'] == "-1"
        assert error.details['reason'] == "必须为正整数"
    
    def test_missing_configuration_error(self):
        """测试缺少配置异常。"""
        error = MissingConfigurationError("api_key")
        assert "缺少必需配置" in str(error)
        assert error.details['config_key'] == "api_key"


class TestExceptionChaining:
    """测试异常链。"""
    
    def test_exception_can_be_raised(self):
        """测试异常可以被正确抛出。"""
        with pytest.raises(RepositoryNotFoundError) as exc_info:
            raise RepositoryNotFoundError("/test/path")
        
        assert "Git仓库不存在" in str(exc_info.value)
    
    def test_exception_can_be_caught_as_base(self):
        """测试异常可以作为基类被捕获。"""
        with pytest.raises(GitAnalyzerError):
            raise RepositoryNotFoundError("/test/path")
    
    def test_exception_details_preserved(self):
        """测试异常详情被保留。"""
        try:
            raise InvalidParameterError("test_param", "test_value", "test_reason")
        except GitAnalyzerError as e:
            assert e.details['param_name'] == "test_param"
            assert e.details['param_value'] == "test_value"
            assert e.details['reason'] == "test_reason"


class TestExceptionStringRepresentation:
    """测试异常的字符串表示。"""
    
    def test_str_without_details(self):
        """测试无详情时的字符串表示。"""
        error = GitAnalyzerError("简单错误")
        assert str(error) == "简单错误"
    
    def test_str_with_details(self):
        """测试有详情时的字符串表示。"""
        error = GitAnalyzerError("错误", {'key1': 'value1', 'key2': 'value2'})
        error_str = str(error)
        assert "错误" in error_str
        assert "key1=value1" in error_str
        assert "key2=value2" in error_str
    
    def test_repr(self):
        """测试repr表示。"""
        error = GitAnalyzerError("测试错误")
        # repr应该包含类名
        assert "GitAnalyzerError" in repr(error)
