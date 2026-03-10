#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git仓库分析工具输入验证装饰器

提供参数验证装饰器和验证工具函数，确保输入参数的有效性。

WING
"""

import os
import re
from datetime import datetime
from typing import Any, Callable, Optional, List, Union
from functools import wraps

from exceptions import (
    InvalidPathError,
    InvalidUrlError,
    InvalidDateError,
    InvalidParameterError,
    ParameterOutOfRangeError,
    MissingRequiredParameterError
)


def validate_path(
    param_name: str,
    must_exist: bool = False,
    must_be_dir: bool = False,
    must_be_file: bool = False
) -> Callable:
    """
    验证路径参数装饰器。
    
    Args:
        param_name: 参数名称。
        must_exist: 路径必须存在。
        must_be_dir: 路径必须是目录。
        must_be_file: 路径必须是文件。
    
    Returns:
        装饰器函数。
    
    Raises:
        InvalidPathError: 路径无效时抛出。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取参数值
            path = kwargs.get(param_name)
            if path is None and len(args) > 0:
                # 尝试从位置参数获取
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        path = args[idx]
            
            if path is None:
                # 参数未提供，跳过验证
                return func(*args, **kwargs)
            
            # 验证路径类型
            if not isinstance(path, str):
                raise InvalidPathError(
                    str(path),
                    f"路径必须是字符串类型，当前类型: {type(path).__name__}"
                )
            
            # 验证路径格式
            if not path or path.strip() == '':
                raise InvalidPathError(path, "路径不能为空")
            
            # 验证路径是否存在
            if must_exist and not os.path.exists(path):
                raise InvalidPathError(path, "路径不存在")
            
            # 验证是否为目录
            if must_be_dir and os.path.exists(path) and not os.path.isdir(path):
                raise InvalidPathError(path, "路径必须是目录")
            
            # 验证是否为文件
            if must_be_file and os.path.exists(path) and not os.path.isfile(path):
                raise InvalidPathError(path, "路径必须是文件")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_url(param_name: str) -> Callable:
    """
    验证URL参数装饰器。
    
    Args:
        param_name: 参数名称。
    
    Returns:
        装饰器函数。
    
    Raises:
        InvalidUrlError: URL无效时抛出。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取参数值
            url = kwargs.get(param_name)
            if url is None and len(args) > 0:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        url = args[idx]
            
            if url is None:
                return func(*args, **kwargs)
            
            # 验证URL类型
            if not isinstance(url, str):
                raise InvalidUrlError(
                    str(url),
                    f"URL必须是字符串类型，当前类型: {type(url).__name__}"
                )
            
            # 验证URL格式
            url_pattern = re.compile(
                r'^(https?|git|ssh)://'  # 协议
                r'([a-zA-Z0-9_-]+(?:\.[a-zA-Z0-9_-]+)*)'  # 域名
                r'(?::\d+)?'  # 端口（可选）
                r'(?:/[a-zA-Z0-9_.-]+)*'  # 路径
                r'(?:\.git)?$',  # .git后缀（可选）
                re.IGNORECASE
            )
            
            if not url_pattern.match(url):
                raise InvalidUrlError(url, "URL格式无效，支持http/https/git/ssh协议")
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_date(param_name: str, date_format: str = '%Y-%m-%d') -> Callable:
    """
    验证日期参数装饰器。
    
    Args:
        param_name: 参数名称。
        date_format: 日期格式。
    
    Returns:
        装饰器函数。
    
    Raises:
        InvalidDateError: 日期无效时抛出。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取参数值
            date_str = kwargs.get(param_name)
            if date_str is None and len(args) > 0:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        date_str = args[idx]
            
            if date_str is None:
                return func(*args, **kwargs)
            
            # 验证日期类型
            if isinstance(date_str, datetime):
                # 已经是datetime对象，无需验证
                return func(*args, **kwargs)
            
            if not isinstance(date_str, str):
                raise InvalidDateError(
                    str(date_str),
                    date_format
                )
            
            # 验证日期格式
            try:
                datetime.strptime(date_str, date_format)
            except ValueError:
                raise InvalidDateError(date_str, date_format)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_type(param_name: str, expected_types: Union[type, tuple]) -> Callable:
    """
    验证参数类型装饰器。
    
    Args:
        param_name: 参数名称。
        expected_types: 期望的类型或类型元组。
    
    Returns:
        装饰器函数。
    
    Raises:
        InvalidParameterError: 参数类型无效时抛出。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取参数值
            value = kwargs.get(param_name)
            if value is None and len(args) > 0:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        value = args[idx]
            
            if value is None:
                return func(*args, **kwargs)
            
            # 验证类型
            if not isinstance(value, expected_types):
                expected_type_names = (
                    ', '.join(t.__name__ for t in expected_types)
                    if isinstance(expected_types, tuple)
                    else expected_types.__name__
                )
                raise InvalidParameterError(
                    param_name,
                    value,
                    f"参数类型必须是 {expected_type_names}，当前类型: {type(value).__name__}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_range(
    param_name: str,
    min_value: Optional[Union[int, float]] = None,
    max_value: Optional[Union[int, float]] = None
) -> Callable:
    """
    验证参数范围装饰器。
    
    Args:
        param_name: 参数名称。
        min_value: 最小值。
        max_value: 最大值。
    
    Returns:
        装饰器函数。
    
    Raises:
        ParameterOutOfRangeError: 参数超出范围时抛出。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取参数值
            value = kwargs.get(param_name)
            if value is None and len(args) > 0:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        value = args[idx]
            
            if value is None:
                return func(*args, **kwargs)
            
            # 验证是否为数值类型
            if not isinstance(value, (int, float)):
                raise InvalidParameterError(
                    param_name,
                    value,
                    "参数必须是数值类型"
                )
            
            # 验证最小值
            if min_value is not None and value < min_value:
                raise ParameterOutOfRangeError(
                    param_name,
                    value,
                    min_value,
                    max_value
                )
            
            # 验证最大值
            if max_value is not None and value > max_value:
                raise ParameterOutOfRangeError(
                    param_name,
                    value,
                    min_value,
                    max_value
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_choices(param_name: str, choices: List[Any]) -> Callable:
    """
    验证参数值在可选列表中装饰器。
    
    Args:
        param_name: 参数名称。
        choices: 可选值列表。
    
    Returns:
        装饰器函数。
    
    Raises:
        InvalidParameterError: 参数值不在可选列表中时抛出。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取参数值
            value = kwargs.get(param_name)
            if value is None and len(args) > 0:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        value = args[idx]
            
            if value is None:
                return func(*args, **kwargs)
            
            # 验证值是否在可选列表中
            if value not in choices:
                raise InvalidParameterError(
                    param_name,
                    value,
                    f"参数值必须是以下之一: {', '.join(str(c) for c in choices)}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_required(*param_names: str) -> Callable:
    """
    验证必需参数装饰器。
    
    Args:
        *param_names: 必需参数名称列表。
    
    Returns:
        装饰器函数。
    
    Raises:
        MissingRequiredParameterError: 缺少必需参数时抛出。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import inspect
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            for param_name in param_names:
                # 检查关键字参数
                if param_name in kwargs:
                    continue
                
                # 检查位置参数
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        continue
                
                # 参数缺失
                raise MissingRequiredParameterError(param_name)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_positive(param_name: str) -> Callable:
    """
    验证参数为正数装饰器。
    
    Args:
        param_name: 参数名称。
    
    Returns:
        装饰器函数。
    
    Raises:
        InvalidParameterError: 参数不是正数时抛出。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取参数值
            value = kwargs.get(param_name)
            if value is None and len(args) > 0:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        value = args[idx]
            
            if value is None:
                return func(*args, **kwargs)
            
            # 验证是否为数值类型
            if not isinstance(value, (int, float)):
                raise InvalidParameterError(
                    param_name,
                    value,
                    "参数必须是数值类型"
                )
            
            # 验证是否为正数
            if value <= 0:
                raise InvalidParameterError(
                    param_name,
                    value,
                    "参数必须是正数"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def validate_non_empty_string(param_name: str) -> Callable:
    """
    验证参数为非空字符串装饰器。
    
    Args:
        param_name: 参数名称。
    
    Returns:
        装饰器函数。
    
    Raises:
        InvalidParameterError: 参数不是非空字符串时抛出。
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取参数值
            value = kwargs.get(param_name)
            if value is None and len(args) > 0:
                import inspect
                sig = inspect.signature(func)
                params = list(sig.parameters.keys())
                if param_name in params:
                    idx = params.index(param_name)
                    if idx < len(args):
                        value = args[idx]
            
            if value is None:
                return func(*args, **kwargs)
            
            # 验证是否为字符串类型
            if not isinstance(value, str):
                raise InvalidParameterError(
                    param_name,
                    value,
                    f"参数必须是字符串类型，当前类型: {type(value).__name__}"
                )
            
            # 验证是否为非空字符串
            if not value or value.strip() == '':
                raise InvalidParameterError(
                    param_name,
                    value,
                    "参数不能为空字符串"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# ==================== 工具函数 ====================

def is_valid_git_repo_url(url: str) -> bool:
    """
    检查是否为有效的Git仓库URL。
    
    Args:
        url: URL字符串。
    
    Returns:
        是否为有效的Git仓库URL。
    """
    if not isinstance(url, str):
        return False
    
    # 支持多种Git URL格式
    patterns = [
        # HTTPS/HTTP URL
        r'^https?://[a-zA-Z0-9.-]+(/[a-zA-Z0-9_.-]+)*(\.git)?$',
        # Git协议
        r'^git://[a-zA-Z0-9.-]+(/[a-zA-Z0-9_.-]+)*(\.git)?$',
        # SSH URL
        r'^git@[a-zA-Z0-9.-]+:[a-zA-Z0-9_.-]+(/[a-zA-Z0-9_.-]+)*(\.git)?$',
        # SSH URL with ssh://
        r'^ssh://git@[a-zA-Z0-9.-]+(/[a-zA-Z0-9_.-]+)*(\.git)?$'
    ]
    
    for pattern in patterns:
        if re.match(pattern, url, re.IGNORECASE):
            return True
    
    return False


def is_valid_commit_hash(commit_hash: str) -> bool:
    """
    检查是否为有效的提交哈希值。
    
    Args:
        commit_hash: 提交哈希值字符串。
    
    Returns:
        是否为有效的提交哈希值。
    """
    if not isinstance(commit_hash, str):
        return False
    
    # Git哈希值是40位的十六进制字符串，短哈希至少7位
    if not re.match(r'^[0-9a-fA-F]{7,40}$', commit_hash):
        return False
    
    return True


def is_valid_branch_name(branch_name: str) -> bool:
    """
    检查是否为有效的分支名称。
    
    Args:
        branch_name: 分支名称字符串。
    
    Returns:
        是否为有效的分支名称。
    """
    if not isinstance(branch_name, str):
        return False
    
    if not branch_name or branch_name.strip() == '':
        return False
    
    # Git分支名称规则
    # 不能以.开头
    # 不能包含.., ~, ^, :, ?, *, [, \\, 空格
    # 不能以/结尾
    # 不能以.lock结尾
    invalid_patterns = [
        r'^\.',  # 以.开头
        r'\.\.',  # 包含..
        r'[~^:?*\[\]\\ ]',  # 包含特殊字符
        r'/$',  # 以/结尾
        r'\.lock$',  # 以.lock结尾
        r'@\{'  # 包含@{
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, branch_name):
            return False
    
    return True


def sanitize_path(path: str) -> str:
    """
    清理和规范化路径。
    
    Args:
        path: 路径字符串。
    
    Returns:
        清理后的路径。
    """
    if not isinstance(path, str):
        raise InvalidPathError(str(path), "路径必须是字符串类型")
    
    # 去除首尾空格
    path = path.strip()
    
    # 规范化路径分隔符
    path = os.path.normpath(path)
    
    # 转换为绝对路径
    if not os.path.isabs(path):
        path = os.path.abspath(path)
    
    return path
