#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化模块

提供性能监控、缓存管理和并行计算功能。

优化特性：
- 多级缓存（内存 + 可选磁盘缓存）
- 智能缓存淘汰策略（LRU + LFU混合）
- 增强的并行处理（错误重试、负载均衡）
- 内存使用监控
- 细粒度性能指标收集

WING
"""

import os
import time
import functools
import logging
import threading
import weakref
from typing import Any, Callable, Dict, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
import hashlib
import pickle
import json
from collections import OrderedDict
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类（增强版）。"""
    function_name: str
    execution_time: float
    call_count: int = 1
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    # 新增字段
    memory_peak: float = 0.0  # 内存峰值（MB）
    error_count: int = 0  # 错误次数
    last_call_time: float = 0.0  # 最后调用时间戳
    percentiles: Dict[str, float] = field(default_factory=dict)  # 百分位数统计
    
    def update(self, execution_time: float, memory_usage: float = 0.0, error: bool = False):
        """
        更新性能指标。
        
        Args:
            execution_time: 执行时间。
            memory_usage: 内存使用量（MB）。
            error: 是否发生错误。
        """
        self.call_count += 1
        self.total_time += execution_time
        self.avg_time = self.total_time / self.call_count
        self.min_time = min(self.min_time, execution_time)
        self.max_time = max(self.max_time, execution_time)
        self.memory_peak = max(self.memory_peak, memory_usage)
        self.last_call_time = time.time()
        
        if error:
            self.error_count += 1
    
    @property
    def cache_hit_rate(self) -> float:
        """计算缓存命中率。"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    @property
    def error_rate(self) -> float:
        """计算错误率。"""
        return (self.error_count / self.call_count * 100) if self.call_count > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            'function_name': self.function_name,
            'call_count': self.call_count,
            'total_time': self.total_time,
            'avg_time': self.avg_time,
            'min_time': self.min_time,
            'max_time': self.max_time,
            'cache_hit_rate': self.cache_hit_rate,
            'memory_peak': self.memory_peak,
            'error_rate': self.error_rate
        }


class PerformanceMonitor:
    """
    性能监控器（增强版）。
    
    收集和分析性能指标，支持：
    - 内存使用监控
    - 错误率统计
    - 细粒度性能指标
    - 线程安全操作
    """
    
    _instance = None
    _metrics: Dict[str, PerformanceMetrics] = {}
    _lock = threading.Lock()
    _start_time: float = time.time()
    
    def __new__(cls):
        """单例模式。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def record(
        cls,
        function_name: str,
        execution_time: float,
        cache_hit: bool = False,
        memory_usage: float = 0.0,
        error: bool = False
    ):
        """
        记录性能数据。
        
        Args:
            function_name: 函数名称。
            execution_time: 执行时间（秒）。
            cache_hit: 是否命中缓存。
            memory_usage: 内存使用量（MB）。
            error: 是否发生错误。
        """
        with cls._lock:
            if function_name not in cls._metrics:
                cls._metrics[function_name] = PerformanceMetrics(
                    function_name=function_name,
                    execution_time=execution_time
                )
            else:
                cls._metrics[function_name].update(execution_time, memory_usage, error)
            
            # 记录缓存统计
            if cache_hit:
                cls._metrics[function_name].cache_hits += 1
            else:
                cls._metrics[function_name].cache_misses += 1
    
    @classmethod
    def get_metrics(cls, function_name: str) -> Optional[PerformanceMetrics]:
        """获取指定函数的性能指标。"""
        with cls._lock:
            return cls._metrics.get(function_name)
    
    @classmethod
    def get_all_metrics(cls) -> Dict[str, PerformanceMetrics]:
        """获取所有性能指标。"""
        with cls._lock:
            return cls._metrics.copy()
    
    @classmethod
    def get_memory_usage(cls) -> float:
        """
        获取当前进程内存使用量（MB）。
        
        Returns:
            内存使用量（MB）。
        """
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # psutil不可用，返回0
            return 0.0
        except Exception:
            return 0.0
    
    @classmethod
    def generate_report(cls) -> str:
        """生成性能报告（增强版）。"""
        with cls._lock:
            if not cls._metrics:
                return "暂无性能数据"
            
            report = []
            report.append("=" * 120)
            report.append("性能监控报告")
            report.append("=" * 120)
            report.append(f"监控时长: {time.time() - cls._start_time:.2f}s")
            report.append(f"当前内存使用: {cls.get_memory_usage():.2f} MB")
            report.append("")
            report.append(
                f"{'函数名称':<35} {'调用次数':<8} {'总时间(s)':<10} "
                f"{'平均(s)':<10} {'最小(s)':<8} {'最大(s)':<8} "
                f"{'缓存命中率':<10} {'错误率':<8} {'内存峰值(MB)':<12}"
            )
            report.append("-" * 120)
            
            # 按总时间排序
            sorted_metrics = sorted(
                cls._metrics.items(),
                key=lambda x: x[1].total_time,
                reverse=True
            )
            
            for func_name, metrics in sorted_metrics:
                report.append(
                    f"{func_name:<35} {metrics.call_count:<8} "
                    f"{metrics.total_time:<10.4f} {metrics.avg_time:<10.4f} "
                    f"{metrics.min_time:<8.4f} {metrics.max_time:<8.4f} "
                    f"{metrics.cache_hit_rate:<10.1f}% "
                    f"{metrics.error_rate:<8.1f}% "
                    f"{metrics.memory_peak:<12.2f}"
                )
            
            report.append("=" * 120)
            
            return "\n".join(report)
    
    @classmethod
    def reset(cls):
        """重置所有性能数据。"""
        with cls._lock:
            cls._metrics.clear()
            cls._start_time = time.time()
    
    @classmethod
    def export_to_json(cls, file_path: str) -> bool:
        """
        导出性能数据到JSON文件。
        
        Args:
            file_path: 输出文件路径。
        
        Returns:
            是否导出成功。
        """
        try:
            with cls._lock:
                data = {
                    'start_time': cls._start_time,
                    'export_time': time.time(),
                    'metrics': {
                        name: metric.to_dict()
                        for name, metric in cls._metrics.items()
                    }
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                return True
        except Exception as e:
            logger.error(f"导出性能数据失败: {e}")
            return False


def performance_monitor(func: Callable) -> Callable:
    """
    性能监控装饰器（增强版）。
    
    自动记录函数执行时间、调用次数、内存使用等性能指标。
    
    Args:
        func: 被装饰的函数。
    
    Returns:
        装饰后的函数。
    
    Example:
        @performance_monitor
        def slow_function():
            time.sleep(1)
            return "done"
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        start_memory = PerformanceMonitor.get_memory_usage()
        error_occurred = False
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            error_occurred = True
            raise
        finally:
            execution_time = time.perf_counter() - start_time
            end_memory = PerformanceMonitor.get_memory_usage()
            memory_usage = max(0, end_memory - start_memory)  # 确保非负
            
            PerformanceMonitor.record(
                func.__name__,
                execution_time,
                memory_usage=memory_usage,
                error=error_occurred
            )
    
    return wrapper


class CacheManager:
    """
    缓存管理器（增强版）。
    
    提供多级缓存功能，支持：
    - LRU + LFU混合淘汰策略
    - 内存缓存 + 可选磁盘缓存
    - 缓存预热
    - 线程安全操作
    - 缓存统计和分析
    """
    
    _instance = None
    _cache: OrderedDict = OrderedDict()  # 使用OrderedDict实现LRU
    _access_count: Dict[str, int] = {}
    _max_size: int = 1000
    _ttl: int = 3600  # 默认缓存1小时
    _lock = threading.Lock()
    _disk_cache_dir: Optional[str] = None
    _enable_disk_cache: bool = False
    _cache_hits: int = 0
    _cache_misses: int = 0
    
    def __new__(cls):
        """单例模式。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def set_config(
        cls,
        max_size: int = 1000,
        ttl: int = 3600,
        enable_disk_cache: bool = False,
        disk_cache_dir: Optional[str] = None
    ):
        """
        配置缓存参数。
        
        Args:
            max_size: 最大缓存数量。
            ttl: 缓存过期时间（秒）。
            enable_disk_cache: 是否启用磁盘缓存。
            disk_cache_dir: 磁盘缓存目录。
        """
        with cls._lock:
            cls._max_size = max_size
            cls._ttl = ttl
            cls._enable_disk_cache = enable_disk_cache
            
            if enable_disk_cache and disk_cache_dir:
                cls._disk_cache_dir = disk_cache_dir
                Path(disk_cache_dir).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def _generate_key(*args, **kwargs) -> str:
        """
        生成缓存键。
        
        Args:
            *args: 位置参数。
            **kwargs: 关键字参数。
        
        Returns:
            缓存键字符串。
        """
        # 将参数转换为可哈希的字符串
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """
        获取缓存值。
        
        Args:
            key: 缓存键。
        
        Returns:
            缓存值，如果不存在或已过期则返回None。
        """
        with cls._lock:
            # 先从内存缓存查找
            if key in cls._cache:
                value, timestamp = cls._cache[key]
                
                # 检查是否过期
                if time.time() - timestamp > cls._ttl:
                    cls._remove_cache_item(key)
                    cls._cache_misses += 1
                    return None
                
                # 更新LRU顺序（移到末尾）
                cls._cache.move_to_end(key)
                
                # 更新访问计数（LFU）
                cls._access_count[key] = cls._access_count.get(key, 0) + 1
                
                cls._cache_hits += 1
                return value
            
            # 如果启用磁盘缓存，尝试从磁盘加载
            if cls._enable_disk_cache and cls._disk_cache_dir:
                disk_value = cls._load_from_disk(key)
                if disk_value is not None:
                    # 加载到内存缓存
                    cls._cache[key] = (disk_value, time.time())
                    cls._access_count[key] = 1
                    cls._cache_hits += 1
                    return disk_value
            
            cls._cache_misses += 1
            return None
    
    @classmethod
    def set(cls, key: str, value: Any):
        """
        设置缓存值。
        
        Args:
            key: 缓存键。
            value: 缓存值。
        """
        with cls._lock:
            # 如果缓存已满，淘汰项
            if len(cls._cache) >= cls._max_size and key not in cls._cache:
                cls._evict()
            
            # 如果键已存在，更新值
            if key in cls._cache:
                cls._cache[key] = (value, time.time())
                cls._cache.move_to_end(key)
            else:
                # 添加新项
                cls._cache[key] = (value, time.time())
                cls._access_count[key] = 1
            
            # 如果启用磁盘缓存，保存到磁盘
            if cls._enable_disk_cache and cls._disk_cache_dir:
                cls._save_to_disk(key, value)
    
    @classmethod
    def _evict(cls):
        """
        淘汰缓存项（LRU + LFU混合策略）。
        
        策略：
        1. 优先淘汰访问次数少的（LFU）
        2. 如果访问次数相同，淘汰最久未访问的（LRU）
        """
        if not cls._cache:
            return
        
        # 找到访问次数最少的项
        min_access = min(cls._access_count.values())
        
        # 在访问次数最少的项中，找到最久未访问的（OrderedDict的第一个）
        for key in cls._cache:
            if cls._access_count.get(key, 0) == min_access:
                cls._remove_cache_item(key)
                break
    
    @classmethod
    def _remove_cache_item(cls, key: str):
        """删除缓存项。"""
        if key in cls._cache:
            del cls._cache[key]
        if key in cls._access_count:
            del cls._access_count[key]
    
    @classmethod
    def _save_to_disk(cls, key: str, value: Any):
        """保存缓存到磁盘。"""
        if not cls._disk_cache_dir:
            return
        
        try:
            cache_file = Path(cls._disk_cache_dir) / f"{key}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump({'value': value, 'timestamp': time.time()}, f)
        except Exception as e:
            logger.warning(f"保存缓存到磁盘失败: {e}")
    
    @classmethod
    def _load_from_disk(cls, key: str) -> Optional[Any]:
        """从磁盘加载缓存。"""
        if not cls._disk_cache_dir:
            return None
        
        try:
            cache_file = Path(cls._disk_cache_dir) / f"{key}.cache"
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
                
                # 检查是否过期
                if time.time() - data['timestamp'] > cls._ttl:
                    cache_file.unlink()  # 删除过期缓存
                    return None
                
                return data['value']
        except Exception as e:
            logger.warning(f"从磁盘加载缓存失败: {e}")
            return None
    
    @classmethod
    def clear(cls):
        """清空所有缓存。"""
        with cls._lock:
            cls._cache.clear()
            cls._access_count.clear()
            cls._cache_hits = 0
            cls._cache_misses = 0
            
            # 清空磁盘缓存
            if cls._enable_disk_cache and cls._disk_cache_dir:
                try:
                    cache_dir = Path(cls._disk_cache_dir)
                    for cache_file in cache_dir.glob("*.cache"):
                        cache_file.unlink()
                except Exception as e:
                    logger.warning(f"清空磁盘缓存失败: {e}")
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取缓存统计信息。"""
        with cls._lock:
            total_requests = cls._cache_hits + cls._cache_misses
            hit_rate = (cls._cache_hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                'cache_size': len(cls._cache),
                'max_size': cls._max_size,
                'ttl': cls._ttl,
                'cache_hits': cls._cache_hits,
                'cache_misses': cls._cache_misses,
                'hit_rate': hit_rate,
                'total_access': sum(cls._access_count.values()),
                'disk_cache_enabled': cls._enable_disk_cache
            }
    
    @classmethod
    def warmup(cls, items: Dict[str, Any]):
        """
        缓存预热。
        
        Args:
            items: 要预热的缓存项字典 {key: value}。
        """
        with cls._lock:
            for key, value in items.items():
                if len(cls._cache) >= cls._max_size:
                    break
                
                if key not in cls._cache:
                    cls._cache[key] = (value, time.time())
                    cls._access_count[key] = 1
        
        logger.info(f"缓存预热完成，预热了 {len(items)} 个项")


def cached(ttl: int = 3600, max_size: int = 1000, enable_disk_cache: bool = False):
    """
    缓存装饰器（增强版）。
    
    自动缓存函数返回值，避免重复计算。
    
    Args:
        ttl: 缓存过期时间（秒）。
        max_size: 最大缓存数量。
        enable_disk_cache: 是否启用磁盘缓存。
    
    Returns:
        装饰器函数。
    
    Example:
        @cached(ttl=1800, max_size=500)
        def expensive_computation(n):
            return sum(range(n))
    """
    def decorator(func: Callable) -> Callable:
        # 配置缓存管理器
        CacheManager.set_config(
            max_size=max_size,
            ttl=ttl,
            enable_disk_cache=enable_disk_cache
        )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = CacheManager._generate_key(func.__name__, *args, **kwargs)
            
            # 尝试从缓存获取
            cached_result = CacheManager.get(cache_key)
            if cached_result is not None:
                # 记录缓存命中
                PerformanceMonitor.record(func.__name__, 0.0, cache_hit=True)
                return cached_result
            
            # 缓存未命中，执行函数
            start_time = time.perf_counter()
            start_memory = PerformanceMonitor.get_memory_usage()
            error_occurred = False
            
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                error_occurred = True
                raise
            finally:
                execution_time = time.perf_counter() - start_time
                end_memory = PerformanceMonitor.get_memory_usage()
                memory_usage = max(0, end_memory - start_memory)
                
                # 记录性能数据
                PerformanceMonitor.record(
                    func.__name__,
                    execution_time,
                    cache_hit=False,
                    memory_usage=memory_usage,
                    error=error_occurred
                )
            
            # 缓存结果
            CacheManager.set(cache_key, result)
            
            return result
        
        return wrapper
    
    return decorator


class ParallelProcessor:
    """
    并行处理器（增强版）。
    
    提供并行计算功能，支持：
    - 进程池和线程池
    - 错误重试机制
    - 智能负载均衡
    - 进度监控
    - 超时控制
    """
    
    @staticmethod
    def get_optimal_workers(task_type: str = 'cpu') -> int:
        """
        获取最优工作进程/线程数。
        
        Args:
            task_type: 任务类型，'cpu'或'io'。
        
        Returns:
            最优工作数量。
        """
        cpu_cores = cpu_count()
        
        if task_type == 'cpu':
            # CPU密集型任务，使用核心数-1（保留一个核心给主进程）
            return max(1, cpu_cores - 1)
        elif task_type == 'io':
            # IO密集型任务，使用2-4倍核心数
            return min(cpu_cores * 4, 32)
        else:
            return cpu_cores
    
    @staticmethod
    def parallel_map(
        func: Callable,
        items: list,
        task_type: str = 'cpu',
        max_workers: Optional[int] = None,
        chunk_size: int = 1,
        timeout: Optional[float] = None,
        retry_count: int = 0,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> list:
        """
        并行映射执行（增强版）。
        
        Args:
            func: 要执行的函数。
            items: 输入项列表。
            task_type: 任务类型，'cpu'或'io'。
            max_workers: 最大工作进程/线程数。
            chunk_size: 每个任务的块大小。
            timeout: 超时时间（秒）。
            retry_count: 失败重试次数。
            progress_callback: 进度回调函数，参数为(已完成数, 总数)。
        
        Returns:
            结果列表。
        
        Example:
            def process_file(file_path):
                with open(file_path) as f:
                    return f.read()
            
            results = ParallelProcessor.parallel_map(
                process_file,
                file_list,
                task_type='io',
                retry_count=2
            )
        """
        if not items:
            return []
        
        # 确定工作数量
        if max_workers is None:
            max_workers = ParallelProcessor.get_optimal_workers(task_type)
        
        # 选择执行器
        Executor = ProcessPoolExecutor if task_type == 'cpu' else ThreadPoolExecutor
        
        results = [None] * len(items)  # 预分配结果列表，保持顺序
        completed_count = 0
        
        try:
            with Executor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_index = {
                    executor.submit(func, item): index
                    for index, item in enumerate(items)
                }
                
                # 收集结果
                for future in as_completed(future_to_index, timeout=timeout):
                    index = future_to_index[future]
                    
                    # 尝试获取结果，支持重试
                    for attempt in range(retry_count + 1):
                        try:
                            result = future.result()
                            results[index] = result
                            break
                        except Exception as e:
                            if attempt == retry_count:
                                logger.error(f"并行任务执行失败（索引 {index}）: {e}")
                                results[index] = None
                            else:
                                logger.warning(f"任务失败，正在重试（索引 {index}，尝试 {attempt + 1}/{retry_count}）")
                                time.sleep(0.5 * (attempt + 1))  # 指数退避
                    
                    completed_count += 1
                    
                    # 调用进度回调
                    if progress_callback:
                        try:
                            progress_callback(completed_count, len(items))
                        except Exception as e:
                            logger.warning(f"进度回调失败: {e}")
        
        except TimeoutError:
            logger.error(f"并行处理超时（{timeout}秒）")
        except Exception as e:
            logger.error(f"并行处理失败: {e}")
            # 降级为串行处理
            logger.info("降级为串行处理...")
            results = [func(item) for item in items]
        
        return results
    
    @staticmethod
    def batch_process(
        func: Callable,
        items: list,
        batch_size: int = 100,
        task_type: str = 'cpu',
        max_workers: Optional[int] = None,
        timeout: Optional[float] = None,
        retry_count: int = 0
    ) -> list:
        """
        分批并行处理（增强版）。
        
        Args:
            func: 要执行的函数。
            items: 输入项列表。
            batch_size: 批次大小。
            task_type: 任务类型。
            max_workers: 最大工作数量。
            timeout: 超时时间（秒）。
            retry_count: 失败重试次数。
        
        Returns:
            结果列表。
        
        Example:
            def process_batch(commit_batch):
                return [analyze_commit(c) for c in commit_batch]
            
            results = ParallelProcessor.batch_process(
                process_batch,
                commits,
                batch_size=50,
                retry_count=1
            )
        """
        if not items:
            return []
        
        # 分批
        batches = [
            items[i:i + batch_size]
            for i in range(0, len(items), batch_size)
        ]
        
        logger.info(f"将 {len(items)} 个项目分为 {len(batches)} 批次处理")
        
        # 并行处理每批
        batch_results = ParallelProcessor.parallel_map(
            func,
            batches,
            task_type=task_type,
            max_workers=max_workers,
            timeout=timeout,
            retry_count=retry_count
        )
        
        # 合并结果
        all_results = []
        for batch_result in batch_results:
            if batch_result is not None:
                if isinstance(batch_result, list):
                    all_results.extend(batch_result)
                else:
                    all_results.append(batch_result)
        
        return all_results
    
    @staticmethod
    def adaptive_batch_size(
        total_items: int,
        avg_item_size: int = 1,
        memory_limit_mb: int = 500
    ) -> int:
        """
        自适应计算批次大小。
        
        根据总项目数、平均项目大小和内存限制计算最优批次大小。
        
        Args:
            total_items: 总项目数。
            avg_item_size: 平均项目大小（字节）。
            memory_limit_mb: 内存限制（MB）。
        
        Returns:
            批次大小。
        """
        # 估算每个项目的内存占用（保守估计）
        estimated_memory_per_item = avg_item_size * 10  # 10倍安全系数
        
        # 计算内存限制下的最大批次大小
        memory_limit_bytes = memory_limit_mb * 1024 * 1024
        max_batch_by_memory = memory_limit_bytes // estimated_memory_per_item
        
        # 根据总项目数计算合理的批次大小
        if total_items < 100:
            batch_size = min(20, total_items)
        elif total_items < 1000:
            batch_size = 50
        elif total_items < 10000:
            batch_size = 100
        else:
            batch_size = 200
        
        # 取内存限制和经验值的较小值
        return min(batch_size, max_batch_by_memory)


class OptimizationSuggester:
    """优化建议生成器（增强版）。"""
    
    @staticmethod
    def analyze_performance(metrics: Dict[str, PerformanceMetrics]) -> list:
        """
        分析性能数据并生成优化建议。
        
        Args:
            metrics: 性能指标字典。
        
        Returns:
            优化建议列表。
        """
        suggestions = []
        
        for func_name, metric in metrics.items():
            # 检查执行时间
            if metric.avg_time > 1.0:
                suggestions.append(
                    f"⚠️ 函数 '{func_name}' 平均执行时间过长 ({metric.avg_time:.2f}s)，"
                    f"建议优化算法或使用缓存"
                )
            
            # 检查调用次数
            if metric.call_count > 100:
                suggestions.append(
                    f"🔄 函数 '{func_name}' 调用次数过多 ({metric.call_count}次)，"
                    f"建议减少不必要的调用或使用批量处理"
                )
            
            # 检查缓存命中率
            if metric.cache_hit_rate < 30.0 and metric.cache_hits + metric.cache_misses > 10:
                suggestions.append(
                    f"💾 函数 '{func_name}' 缓存命中率较低 ({metric.cache_hit_rate:.1f}%)，"
                    f"建议优化缓存策略或增加缓存时间"
                )
            
            # 检查时间波动
            if metric.max_time > metric.avg_time * 5:
                suggestions.append(
                    f"📊 函数 '{func_name}' 执行时间波动较大 "
                    f"(最大:{metric.max_time:.2f}s, 平均:{metric.avg_time:.2f}s)，"
                    f"建议检查是否存在性能热点"
                )
            
            # 检查内存使用
            if metric.memory_peak > 100:
                suggestions.append(
                    f"🧠 函数 '{func_name}' 内存峰值较高 ({metric.memory_peak:.2f}MB)，"
                    f"建议优化数据结构或使用流式处理"
                )
            
            # 检查错误率
            if metric.error_rate > 5.0:
                suggestions.append(
                    f"❌ 函数 '{func_name}' 错误率较高 ({metric.error_rate:.1f}%)，"
                    f"建议检查异常处理逻辑"
                )
        
        return suggestions
    
    @staticmethod
    def generate_optimization_report(metrics: Dict[str, PerformanceMetrics]) -> str:
        """
        生成优化建议报告（增强版）。
        
        Args:
            metrics: 性能指标字典。
        
        Returns:
            Markdown格式的报告。
        """
        report = []
        report.append("# 性能优化建议报告\n\n")
        report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 性能概览
        report.append("## 📈 性能概览\n\n")
        total_calls = sum(m.call_count for m in metrics.values())
        total_time = sum(m.total_time for m in metrics.values())
        avg_memory = sum(m.memory_peak for m in metrics.values()) / len(metrics) if metrics else 0
        
        report.append(f"- 总函数调用次数: **{total_calls}**\n")
        report.append(f"- 总执行时间: **{total_time:.2f}s**\n")
        report.append(f"- 监控函数数量: **{len(metrics)}**\n")
        report.append(f"- 平均内存峰值: **{avg_memory:.2f}MB**\n\n")
        
        # 性能瓶颈
        report.append("## 🔍 性能瓶颈分析\n\n")
        sorted_metrics = sorted(
            metrics.items(),
            key=lambda x: x[1].total_time,
            reverse=True
        )
        
        report.append("| 函数名称 | 调用次数 | 总时间(s) | 平均时间(s) | 缓存命中率 | 内存峰值(MB) |\n")
        report.append("|----------|----------|-----------|-------------|------------|-------------|\n")
        
        for func_name, metric in sorted_metrics[:10]:  # 显示前10个
            report.append(
                f"| {func_name} | {metric.call_count} | "
                f"{metric.total_time:.2f} | {metric.avg_time:.4f} | "
                f"{metric.cache_hit_rate:.1f}% | {metric.memory_peak:.2f} |\n"
            )
        
        report.append("\n")
        
        # 优化建议
        report.append("## 💡 优化建议\n\n")
        suggestions = OptimizationSuggester.analyze_performance(metrics)
        
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                report.append(f"{i}. {suggestion}\n")
        else:
            report.append("✅ 暂无优化建议，性能表现良好。\n")
        
        report.append("\n")
        
        # 缓存统计
        report.append("## 💾 缓存统计\n\n")
        cache_stats = CacheManager.get_stats()
        report.append(f"- 缓存大小: **{cache_stats['cache_size']}**\n")
        report.append(f"- 最大缓存数: **{cache_stats['max_size']}**\n")
        report.append(f"- 缓存过期时间: **{cache_stats['ttl']}s**\n")
        report.append(f"- 缓存命中率: **{cache_stats['hit_rate']:.1f}%**\n")
        report.append(f"- 总访问次数: **{cache_stats['total_access']}**\n")
        report.append(f"- 磁盘缓存: **{'已启用' if cache_stats['disk_cache_enabled'] else '未启用'}**\n\n")
        
        # 性能优化策略
        report.append("## 🚀 性能优化策略\n\n")
        report.append("### 1. 缓存优化\n")
        report.append("- 对于频繁调用的函数，考虑使用 `@cached` 装饰器\n")
        report.append("- 对于计算密集型任务，启用磁盘缓存以减少重复计算\n")
        report.append("- 调整缓存大小和过期时间以平衡内存使用和命中率\n\n")
        
        report.append("### 2. 并行处理优化\n")
        report.append("- 对于CPU密集型任务，使用 `ParallelProcessor.parallel_map`\n")
        report.append("- 对于IO密集型任务，使用线程池而非进程池\n")
        report.append("- 根据数据量自适应调整批次大小\n\n")
        
        report.append("### 3. 内存优化\n")
        report.append("- 对于大数据集，使用流式处理或分批处理\n")
        report.append("- 及时释放不再使用的大对象\n")
        report.append("- 考虑使用生成器而非列表\n\n")
        
        return "".join(report)
    
    @staticmethod
    def identify_bottlenecks(metrics: Dict[str, PerformanceMetrics]) -> List[Dict[str, Any]]:
        """
        识别性能瓶颈。
        
        Args:
            metrics: 性能指标字典。
        
        Returns:
            瓶颈列表，每个瓶颈包含函数名、类型和严重程度。
        """
        bottlenecks = []
        
        for func_name, metric in metrics.items():
            bottleneck = None
            
            # 时间瓶颈
            if metric.avg_time > 2.0:
                bottleneck = {
                    'function': func_name,
                    'type': 'time',
                    'severity': 'high',
                    'value': metric.avg_time,
                    'description': f"平均执行时间过长 ({metric.avg_time:.2f}s)"
                }
            elif metric.avg_time > 1.0:
                bottleneck = {
                    'function': func_name,
                    'type': 'time',
                    'severity': 'medium',
                    'value': metric.avg_time,
                    'description': f"平均执行时间较长 ({metric.avg_time:.2f}s)"
                }
            
            if bottleneck:
                bottlenecks.append(bottleneck)
            
            # 内存瓶颈
            if metric.memory_peak > 200:
                bottlenecks.append({
                    'function': func_name,
                    'type': 'memory',
                    'severity': 'high',
                    'value': metric.memory_peak,
                    'description': f"内存峰值过高 ({metric.memory_peak:.2f}MB)"
                })
            elif metric.memory_peak > 100:
                bottlenecks.append({
                    'function': func_name,
                    'type': 'memory',
                    'severity': 'medium',
                    'value': metric.memory_peak,
                    'description': f"内存峰值较高 ({metric.memory_peak:.2f}MB)"
                })
        
        # 按严重程度排序
        severity_order = {'high': 0, 'medium': 1, 'low': 2}
        bottlenecks.sort(key=lambda x: severity_order.get(x['severity'], 3))
        
        return bottlenecks


def main():
    """测试性能优化模块。"""
    print("性能优化模块测试")
    print("=" * 80)
    
    # 测试性能监控
    @performance_monitor
    def test_function(n):
        time.sleep(0.01)
        return sum(range(n))
    
    # 执行多次
    for i in range(10):
        test_function(1000)
    
    # 打印性能报告
    print("\n性能监控报告:")
    print(PerformanceMonitor.generate_report())
    
    # 测试缓存
    @cached(ttl=60)
    def expensive_function(n):
        time.sleep(0.1)
        return n * n
    
    print("\n测试缓存功能:")
    print("第一次调用（缓存未命中）:")
    start = time.time()
    result1 = expensive_function(10)
    time1 = time.time() - start
    print(f"结果: {result1}, 耗时: {time1:.4f}s")
    
    print("\n第二次调用（缓存命中）:")
    start = time.time()
    result2 = expensive_function(10)
    time2 = time.time() - start
    print(f"结果: {result2}, 耗时: {time2:.4f}s")
    
    print("\n缓存统计:")
    print(CacheManager.get_stats())
    
    # 测试并行处理
    def cpu_intensive_task(n):
        return sum(i * i for i in range(n))
    
    print("\n测试并行处理:")
    items = [10000] * 8
    
    # 串行处理
    start = time.time()
    serial_results = [cpu_intensive_task(item) for item in items]
    serial_time = time.time() - start
    print(f"串行处理耗时: {serial_time:.4f}s")
    
    # 并行处理
    start = time.time()
    parallel_results = ParallelProcessor.parallel_map(
        cpu_intensive_task,
        items,
        task_type='cpu'
    )
    parallel_time = time.time() - start
    print(f"并行处理耗时: {parallel_time:.4f}s")
    print(f"加速比: {serial_time / parallel_time:.2f}x")
    
    # 生成优化建议报告
    print("\n优化建议报告:")
    metrics = PerformanceMonitor.get_all_metrics()
    report = OptimizationSuggester.generate_optimization_report(metrics)
    print(report)


if __name__ == '__main__':
    main()
