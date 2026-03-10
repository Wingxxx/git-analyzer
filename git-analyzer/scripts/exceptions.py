#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git仓库分析工具自定义异常类

定义所有自定义异常，提供清晰的错误分类和友好的错误提示。

WING
"""

from typing import Optional, Any


class GitAnalyzerError(Exception):
    """
    Git分析工具基础异常类。
    
    所有自定义异常的基类，提供统一的错误处理接口。
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        """
        初始化异常。
        
        Args:
            message: 错误消息。
            details: 错误详细信息。
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        """返回友好的错误消息。"""
        if self.details:
            detail_str = ', '.join(f'{k}={v}' for k, v in self.details.items())
            return f"{self.message} (详情: {detail_str})"
        return self.message


# ==================== 仓库相关异常 ====================

class RepositoryError(GitAnalyzerError):
    """仓库相关异常基类。"""
    pass


class RepositoryNotFoundError(RepositoryError):
    """仓库不存在异常。"""
    
    def __init__(self, path: str):
        message = f"Git仓库不存在或路径无效: {path}"
        details = {'path': path}
        super().__init__(message, details)


class RepositoryCloneError(RepositoryError):
    """仓库克隆失败异常。"""
    
    def __init__(self, repo_url: str, reason: str = "未知原因"):
        message = f"克隆仓库失败: {repo_url}"
        details = {'repo_url': repo_url, 'reason': reason}
        super().__init__(message, details)


class RepositoryUpdateError(RepositoryError):
    """仓库更新失败异常。"""
    
    def __init__(self, path: str, reason: str = "未知原因"):
        message = f"更新仓库失败: {path}"
        details = {'path': path, 'reason': reason}
        super().__init__(message, details)


class BranchNotFoundError(RepositoryError):
    """分支不存在异常。"""
    
    def __init__(self, branch_name: str, available_branches: Optional[list] = None):
        message = f"分支不存在: {branch_name}"
        details = {'branch_name': branch_name}
        if available_branches:
            details['available_branches'] = ', '.join(available_branches)
        super().__init__(message, details)


class BranchSwitchError(RepositoryError):
    """分支切换失败异常。"""
    
    def __init__(self, branch_name: str, reason: str = "未知原因"):
        message = f"切换分支失败: {branch_name}"
        details = {'branch_name': branch_name, 'reason': reason}
        super().__init__(message, details)


# ==================== 提交相关异常 ====================

class CommitError(GitAnalyzerError):
    """提交相关异常基类。"""
    pass


class CommitNotFoundError(CommitError):
    """提交不存在异常。"""
    
    def __init__(self, commit_hash: str):
        message = f"提交不存在或哈希值无效: {commit_hash}"
        details = {'commit_hash': commit_hash}
        super().__init__(message, details)


class EmptyRepositoryError(CommitError):
    """空仓库异常（无提交记录）。"""
    
    def __init__(self, path: str):
        message = f"仓库为空，没有任何提交记录: {path}"
        details = {'path': path}
        super().__init__(message, details)


# ==================== 贡献度计算相关异常 ====================

class ContributionError(GitAnalyzerError):
    """贡献度计算相关异常基类。"""
    pass


class InvalidAlgorithmModeError(ContributionError):
    """无效算法模式异常。"""
    
    def __init__(self, mode: str, valid_modes: Optional[list] = None):
        message = f"无效的算法模式: {mode}"
        details = {'mode': mode}
        if valid_modes:
            details['valid_modes'] = ', '.join(valid_modes)
        super().__init__(message, details)


class QualityEvaluatorNotAvailableError(ContributionError):
    """代码质量评估器不可用异常。"""
    
    def __init__(self):
        message = "代码质量评估器不可用，请确保已安装code_quality_evaluator模块"
        super().__init__(message)


# ==================== 代码质量评估相关异常 ====================

class CodeQualityError(GitAnalyzerError):
    """代码质量评估相关异常基类。"""
    pass


class FileNotFoundError(CodeQualityError):
    """文件不存在异常。"""
    
    def __init__(self, file_path: str):
        message = f"文件不存在: {file_path}"
        details = {'file_path': file_path}
        super().__init__(message, details)


class FileReadError(CodeQualityError):
    """文件读取失败异常。"""
    
    def __init__(self, file_path: str, reason: str = "未知原因"):
        message = f"文件读取失败: {file_path}"
        details = {'file_path': file_path, 'reason': reason}
        super().__init__(message, details)


class FileTooLargeError(CodeQualityError):
    """文件过大异常。"""
    
    def __init__(self, file_path: str, file_size: int, max_size: int):
        message = f"文件过大，超过最大限制: {file_path}"
        details = {
            'file_path': file_path,
            'file_size': f"{file_size / 1024 / 1024:.2f}MB",
            'max_size': f"{max_size / 1024 / 1024:.2f}MB"
        }
        super().__init__(message, details)


class SyntaxErrorInCode(CodeQualityError):
    """代码语法错误异常。"""
    
    def __init__(self, file_path: str, line_number: int, error_msg: str):
        message = f"代码语法错误: {file_path}"
        details = {
            'file_path': file_path,
            'line_number': line_number,
            'error': error_msg
        }
        super().__init__(message, details)


class UnsupportedLanguageError(CodeQualityError):
    """不支持的语言异常。"""
    
    def __init__(self, file_path: str, language: str):
        message = f"不支持的语言类型: {language}"
        details = {'file_path': file_path, 'language': language}
        super().__init__(message, details)


# ==================== 输入验证相关异常 ====================

class ValidationError(GitAnalyzerError):
    """输入验证相关异常基类。"""
    pass


class InvalidPathError(ValidationError):
    """无效路径异常。"""
    
    def __init__(self, path: str, reason: str = "路径格式无效"):
        message = f"路径无效: {path}"
        details = {'path': path, 'reason': reason}
        super().__init__(message, details)


class InvalidUrlError(ValidationError):
    """无效URL异常。"""
    
    def __init__(self, url: str, reason: str = "URL格式无效"):
        message = f"URL无效: {url}"
        details = {'url': url, 'reason': reason}
        super().__init__(message, details)


class InvalidDateError(ValidationError):
    """无效日期异常。"""
    
    def __init__(self, date_str: str, expected_format: str = "YYYY-MM-DD"):
        message = f"日期格式无效: {date_str}"
        details = {'date_str': date_str, 'expected_format': expected_format}
        super().__init__(message, details)


class InvalidParameterError(ValidationError):
    """无效参数异常。"""
    
    def __init__(self, param_name: str, param_value: Any, reason: str = "参数值无效"):
        message = f"参数无效: {param_name}"
        details = {
            'param_name': param_name,
            'param_value': str(param_value),
            'reason': reason
        }
        super().__init__(message, details)


class ParameterOutOfRangeError(ValidationError):
    """参数超出范围异常。"""
    
    def __init__(self, param_name: str, param_value: Any, min_value: Any = None, max_value: Any = None):
        message = f"参数超出范围: {param_name}"
        details = {
            'param_name': param_name,
            'param_value': str(param_value)
        }
        if min_value is not None:
            details['min_value'] = str(min_value)
        if max_value is not None:
            details['max_value'] = str(max_value)
        super().__init__(message, details)


class MissingRequiredParameterError(ValidationError):
    """缺少必需参数异常。"""
    
    def __init__(self, param_name: str):
        message = f"缺少必需参数: {param_name}"
        details = {'param_name': param_name}
        super().__init__(message, details)


# ==================== 报告生成相关异常 ====================

class ReportError(GitAnalyzerError):
    """报告生成相关异常基类。"""
    pass


class ReportGenerationError(ReportError):
    """报告生成失败异常。"""
    
    def __init__(self, output_path: str, reason: str = "未知原因"):
        message = f"报告生成失败: {output_path}"
        details = {'output_path': output_path, 'reason': reason}
        super().__init__(message, details)


class InvalidOutputFormatError(ReportError):
    """无效输出格式异常。"""
    
    def __init__(self, format_type: str, valid_formats: Optional[list] = None):
        message = f"不支持的输出格式: {format_type}"
        details = {'format_type': format_type}
        if valid_formats:
            details['valid_formats'] = ', '.join(valid_formats)
        super().__init__(message, details)


# ==================== 配置相关异常 ====================

class ConfigurationError(GitAnalyzerError):
    """配置相关异常基类。"""
    pass


class InvalidConfigurationError(ConfigurationError):
    """无效配置异常。"""
    
    def __init__(self, config_key: str, config_value: Any, reason: str = "配置值无效"):
        message = f"配置无效: {config_key}"
        details = {
            'config_key': config_key,
            'config_value': str(config_value),
            'reason': reason
        }
        super().__init__(message, details)


class MissingConfigurationError(ConfigurationError):
    """缺少配置异常。"""
    
    def __init__(self, config_key: str):
        message = f"缺少必需配置: {config_key}"
        details = {'config_key': config_key}
        super().__init__(message, details)
