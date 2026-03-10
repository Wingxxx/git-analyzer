#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证器单元测试

测试所有验证器装饰器和工具函数。

WING
"""

import pytest
import sys
import os
from datetime import datetime

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

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

from exceptions import (
    InvalidPathError,
    InvalidUrlError,
    InvalidDateError,
    InvalidParameterError,
    ParameterOutOfRangeError,
    MissingRequiredParameterError
)


# ==================== 工具函数测试 ====================

class TestIsValidGitRepoUrl:
    """测试Git仓库URL验证函数。"""
    
    def test_valid_https_url(self):
        """测试有效的HTTPS URL。"""
        assert is_valid_git_repo_url("https://github.com/user/repo.git") is True
        assert is_valid_git_repo_url("https://github.com/user/repo") is True
        assert is_valid_git_repo_url("http://github.com/user/repo.git") is True
    
    def test_valid_git_protocol_url(self):
        """测试有效的Git协议URL。"""
        assert is_valid_git_repo_url("git://github.com/user/repo.git") is True
        assert is_valid_git_repo_url("git://github.com/user/repo") is True
    
    def test_valid_ssh_url(self):
        """测试有效的SSH URL。"""
        assert is_valid_git_repo_url("git@github.com:user/repo.git") is True
        assert is_valid_git_repo_url("git@github.com:user/repo") is True
        assert is_valid_git_repo_url("ssh://git@github.com/user/repo.git") is True
    
    def test_invalid_url(self):
        """测试无效的URL。"""
        assert is_valid_git_repo_url("") is False
        assert is_valid_git_repo_url("not-a-url") is False
        assert is_valid_git_repo_url("ftp://github.com/user/repo.git") is False
        assert is_valid_git_repo_url("http://") is False
    
    def test_non_string_input(self):
        """测试非字符串输入。"""
        assert is_valid_git_repo_url(123) is False
        assert is_valid_git_repo_url(None) is False
        assert is_valid_git_repo_url([]) is False


class TestIsValidCommitHash:
    """测试提交哈希值验证函数。"""
    
    def test_valid_full_hash(self):
        """测试有效的完整哈希值。"""
        assert is_valid_commit_hash("abc123def456789abc123def456789abc123def45") is True
        assert is_valid_commit_hash("ABC123DEF456789ABCDEF123456789ABCDEF1234") is True
    
    def test_valid_short_hash(self):
        """测试有效的短哈希值。"""
        assert is_valid_commit_hash("abc123d") is True
        assert is_valid_commit_hash("abc123def") is True
        assert is_valid_commit_hash("abc123def456") is True
    
    def test_invalid_hash(self):
        """测试无效的哈希值。"""
        assert is_valid_commit_hash("") is False
        assert is_valid_commit_hash("abc") is False  # 太短
        assert is_valid_commit_hash("ghijkl") is False  # 非法字符
        assert is_valid_commit_hash("abc123def456789abc123def456789abc123def456") is False  # 太长
    
    def test_non_string_input(self):
        """测试非字符串输入。"""
        assert is_valid_commit_hash(123) is False
        assert is_valid_commit_hash(None) is False


class TestIsValidBranchName:
    """测试分支名称验证函数。"""
    
    def test_valid_branch_names(self):
        """测试有效的分支名称。"""
        assert is_valid_branch_name("main") is True
        assert is_valid_branch_name("master") is True
        assert is_valid_branch_name("feature/new-feature") is True
        assert is_valid_branch_name("bugfix-123") is True
        assert is_valid_branch_name("release/v1.0.0") is True
        assert is_valid_branch_name("develop") is True
    
    def test_invalid_branch_names(self):
        """测试无效的分支名称。"""
        assert is_valid_branch_name("") is False
        assert is_valid_branch_name(".hidden") is False  # 以.开头
        assert is_valid_branch_name("branch..name") is False  # 包含..
        assert is_valid_branch_name("branch~name") is False  # 包含~
        assert is_valid_branch_name("branch^name") is False  # 包含^
        assert is_valid_branch_name("branch name") is False  # 包含空格
        assert is_valid_branch_name("branch/") is False  # 以/结尾
        assert is_valid_branch_name("branch.lock") is False  # 以.lock结尾
        assert is_valid_branch_name("branch@{name") is False  # 包含@{
    
    def test_non_string_input(self):
        """测试非字符串输入。"""
        assert is_valid_branch_name(123) is False
        assert is_valid_branch_name(None) is False


class TestSanitizePath:
    """测试路径清理函数。"""
    
    def test_sanitize_relative_path(self):
        """测试相对路径清理。"""
        path = sanitize_path("test/path")
        assert os.path.isabs(path)
    
    def test_sanitize_absolute_path(self):
        """测试绝对路径清理。"""
        path = sanitize_path("/tmp/test")
        assert os.path.isabs(path)
    
    def test_sanitize_path_with_spaces(self):
        """测试带空格的路径。"""
        path = sanitize_path("  test/path  ")
        assert "test" in path
        assert "path" in path
    
    def test_sanitize_non_string_input(self):
        """测试非字符串输入。"""
        with pytest.raises(InvalidPathError):
            sanitize_path(123)
        
        with pytest.raises(InvalidPathError):
            sanitize_path(None)


# ==================== 验证装饰器测试 ====================

class TestValidatePath:
    """测试路径验证装饰器。"""
    
    def test_valid_path(self, tmp_path):
        """测试有效路径。"""
        @validate_path('path', must_exist=False)
        def test_func(path):
            return path
        
        result = test_func("/tmp/test")
        assert result == "/tmp/test"
    
    def test_path_must_exist(self, tmp_path):
        """测试路径必须存在。"""
        @validate_path('path', must_exist=True)
        def test_func(path):
            return path
        
        # 存在的路径
        result = test_func(str(tmp_path))
        assert result == str(tmp_path)
        
        # 不存在的路径
        with pytest.raises(InvalidPathError):
            test_func("/nonexistent/path")
    
    def test_path_must_be_dir(self, tmp_path):
        """测试路径必须是目录。"""
        @validate_path('path', must_exist=True, must_be_dir=True)
        def test_func(path):
            return path
        
        # 目录
        result = test_func(str(tmp_path))
        assert result == str(tmp_path)
        
        # 文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        with pytest.raises(InvalidPathError):
            test_func(str(test_file))
    
    def test_path_must_be_file(self, tmp_path):
        """测试路径必须是文件。"""
        @validate_path('path', must_exist=True, must_be_file=True)
        def test_func(path):
            return path
        
        # 创建文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        
        # 文件
        result = test_func(str(test_file))
        assert result == str(test_file)
        
        # 目录
        with pytest.raises(InvalidPathError):
            test_func(str(tmp_path))
    
    def test_invalid_path_type(self):
        """测试无效路径类型。"""
        @validate_path('path')
        def test_func(path):
            return path
        
        with pytest.raises(InvalidPathError):
            test_func(123)
    
    def test_empty_path(self):
        """测试空路径。"""
        @validate_path('path')
        def test_func(path):
            return path
        
        with pytest.raises(InvalidPathError):
            test_func("")
        
        with pytest.raises(InvalidPathError):
            test_func("   ")


class TestValidateUrl:
    """测试URL验证装饰器。"""
    
    def test_valid_url(self):
        """测试有效URL。"""
        @validate_url('url')
        def test_func(url):
            return url
        
        result = test_func("https://github.com/user/repo.git")
        assert result == "https://github.com/user/repo.git"
    
    def test_invalid_url(self):
        """测试无效URL。"""
        @validate_url('url')
        def test_func(url):
            return url
        
        with pytest.raises(InvalidUrlError):
            test_func("not-a-url")
    
    def test_invalid_url_type(self):
        """测试无效URL类型。"""
        @validate_url('url')
        def test_func(url):
            return url
        
        with pytest.raises(InvalidUrlError):
            test_func(123)


class TestValidateDate:
    """测试日期验证装饰器。"""
    
    def test_valid_date_string(self):
        """测试有效日期字符串。"""
        @validate_date('date')
        def test_func(date):
            return date
        
        result = test_func("2024-01-15")
        assert result == "2024-01-15"
    
    def test_valid_datetime_object(self):
        """测试有效的datetime对象。"""
        @validate_date('date')
        def test_func(date):
            return date
        
        dt = datetime(2024, 1, 15)
        result = test_func(dt)
        assert result == dt
    
    def test_invalid_date_format(self):
        """测试无效日期格式。"""
        @validate_date('date')
        def test_func(date):
            return date
        
        with pytest.raises(InvalidDateError):
            test_func("2024/01/15")
        
        with pytest.raises(InvalidDateError):
            test_func("invalid-date")
    
    def test_invalid_date_type(self):
        """测试无效日期类型。"""
        @validate_date('date')
        def test_func(date):
            return date
        
        with pytest.raises(InvalidDateError):
            test_func(123)


class TestValidateType:
    """测试类型验证装饰器。"""
    
    def test_valid_type(self):
        """测试有效类型。"""
        @validate_type('value', str)
        def test_func(value):
            return value
        
        result = test_func("test")
        assert result == "test"
    
    def test_valid_type_tuple(self):
        """测试有效类型元组。"""
        @validate_type('value', (str, int))
        def test_func(value):
            return value
        
        result1 = test_func("test")
        assert result1 == "test"
        
        result2 = test_func(123)
        assert result2 == 123
    
    def test_invalid_type(self):
        """测试无效类型。"""
        @validate_type('value', str)
        def test_func(value):
            return value
        
        with pytest.raises(InvalidParameterError) as exc_info:
            test_func(123)
        
        assert "参数类型必须是" in str(exc_info.value)


class TestValidateRange:
    """测试范围验证装饰器。"""
    
    def test_valid_range(self):
        """测试有效范围。"""
        @validate_range('value', min_value=0, max_value=100)
        def test_func(value):
            return value
        
        result = test_func(50)
        assert result == 50
    
    def test_value_below_min(self):
        """测试值低于最小值。"""
        @validate_range('value', min_value=0, max_value=100)
        def test_func(value):
            return value
        
        with pytest.raises(ParameterOutOfRangeError):
            test_func(-1)
    
    def test_value_above_max(self):
        """测试值高于最大值。"""
        @validate_range('value', min_value=0, max_value=100)
        def test_func(value):
            return value
        
        with pytest.raises(ParameterOutOfRangeError):
            test_func(101)
    
    def test_non_numeric_value(self):
        """测试非数值类型。"""
        @validate_range('value', min_value=0, max_value=100)
        def test_func(value):
            return value
        
        with pytest.raises(InvalidParameterError):
            test_func("not-a-number")


class TestValidateChoices:
    """测试选项验证装饰器。"""
    
    def test_valid_choice(self):
        """测试有效选项。"""
        @validate_choices('choice', ['a', 'b', 'c'])
        def test_func(choice):
            return choice
        
        result = test_func('a')
        assert result == 'a'
    
    def test_invalid_choice(self):
        """测试无效选项。"""
        @validate_choices('choice', ['a', 'b', 'c'])
        def test_func(choice):
            return choice
        
        with pytest.raises(InvalidParameterError) as exc_info:
            test_func('d')
        
        assert "参数值必须是以下之一" in str(exc_info.value)


class TestValidateRequired:
    """测试必需参数验证装饰器。"""
    
    def test_required_parameter_provided(self):
        """测试提供了必需参数。"""
        @validate_required('name', 'value')
        def test_func(name, value):
            return name, value
        
        result = test_func("test_name", "test_value")
        assert result == ("test_name", "test_value")
    
    def test_required_parameter_missing(self):
        """测试缺少必需参数。"""
        @validate_required('name', 'value')
        def test_func(name, value):
            return name, value
        
        with pytest.raises(MissingRequiredParameterError) as exc_info:
            test_func("test_name")
        
        assert exc_info.value.details['param_name'] == 'value'


class TestValidatePositive:
    """测试正数验证装饰器。"""
    
    def test_positive_value(self):
        """测试正数值。"""
        @validate_positive('value')
        def test_func(value):
            return value
        
        result = test_func(10)
        assert result == 10
    
    def test_zero_value(self):
        """测试零值。"""
        @validate_positive('value')
        def test_func(value):
            return value
        
        with pytest.raises(InvalidParameterError):
            test_func(0)
    
    def test_negative_value(self):
        """测试负数值。"""
        @validate_positive('value')
        def test_func(value):
            return value
        
        with pytest.raises(InvalidParameterError):
            test_func(-1)
    
    def test_non_numeric_value(self):
        """测试非数值类型。"""
        @validate_positive('value')
        def test_func(value):
            return value
        
        with pytest.raises(InvalidParameterError):
            test_func("not-a-number")


class TestValidateNonEmptyString:
    """测试非空字符串验证装饰器。"""
    
    def test_non_empty_string(self):
        """测试非空字符串。"""
        @validate_non_empty_string('value')
        def test_func(value):
            return value
        
        result = test_func("test")
        assert result == "test"
    
    def test_empty_string(self):
        """测试空字符串。"""
        @validate_non_empty_string('value')
        def test_func(value):
            return value
        
        with pytest.raises(InvalidParameterError):
            test_func("")
    
    def test_whitespace_string(self):
        """测试空白字符串。"""
        @validate_non_empty_string('value')
        def test_func(value):
            return value
        
        with pytest.raises(InvalidParameterError):
            test_func("   ")
    
    def test_non_string_type(self):
        """测试非字符串类型。"""
        @validate_non_empty_string('value')
        def test_func(value):
            return value
        
        with pytest.raises(InvalidParameterError):
            test_func(123)


# ==================== 组合装饰器测试 ====================

class TestCombinedValidators:
    """测试组合验证装饰器。"""
    
    def test_multiple_validators(self):
        """测试多个验证器组合。"""
        @validate_required('path')
        @validate_path('path', must_exist=False)
        @validate_non_empty_string('path')
        def test_func(path):
            return path
        
        result = test_func("/tmp/test")
        assert result == "/tmp/test"
    
    def test_validator_order(self):
        """测试验证器执行顺序。"""
        # required应该先执行
        @validate_required('value')
        @validate_positive('value')
        def test_func(value):
            return value
        
        # 缺少参数应该先报错
        with pytest.raises(MissingRequiredParameterError):
            test_func()


# ==================== 边界条件测试 ====================

class TestEdgeCases:
    """测试边界条件。"""
    
    def test_none_value_with_optional_parameter(self):
        """测试可选参数的None值。"""
        @validate_path('path', must_exist=False)
        def test_func(path=None):
            return path
        
        result = test_func()
        assert result is None
    
    def test_keyword_arguments(self):
        """测试关键字参数。"""
        @validate_type('value', str)
        def test_func(value):
            return value
        
        result = test_func(value="test")
        assert result == "test"
    
    def test_positional_and_keyword_arguments(self):
        """测试位置参数和关键字参数。"""
        @validate_type('a', int)
        @validate_type('b', str)
        def test_func(a, b):
            return a, b
        
        result = test_func(1, b="test")
        assert result == (1, "test")
