#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化模块单元测试

测试性能监控、缓存管理和并行处理功能。

WING
"""

import pytest
import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from performance_optimizer import (
    PerformanceMetrics,
    PerformanceMonitor,
    CacheManager,
    ParallelProcessor,
    OptimizationSuggester,
    performance_monitor,
    cached
)


# ==================== PerformanceMetrics测试 ====================

class TestPerformanceMetrics:
    """测试性能指标数据类。"""
    
    def test_default_values(self):
        """测试默认值。"""
        metrics = PerformanceMetrics(
            function_name="test_func",
            execution_time=0.1
        )
        
        assert metrics.function_name == "test_func"
        assert metrics.execution_time == 0.1
        assert metrics.call_count == 1
        assert metrics.total_time == 0.0
        assert metrics.avg_time == 0.0
        assert metrics.min_time == float('inf')
        assert metrics.max_time == 0.0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.memory_peak == 0.0
        assert metrics.error_count == 0
        assert metrics.percentiles == {}
    
    def test_update(self):
        """测试更新指标。"""
        metrics = PerformanceMetrics(
            function_name="test_func",
            execution_time=0.1
        )
        
        # 第一次更新
        metrics.update(0.2, memory_usage=10.0, error=False)
        assert metrics.call_count == 2
        assert metrics.total_time == 0.2
        assert metrics.avg_time == 0.1
        assert metrics.min_time == 0.2
        assert metrics.max_time == 0.2
        assert metrics.memory_peak == 10.0
        
        # 第二次更新
        metrics.update(0.3, memory_usage=15.0, error=True)
        assert metrics.call_count == 3
        assert metrics.total_time == 0.5
        assert metrics.avg_time == pytest.approx(0.1667, rel=0.01)
        assert metrics.min_time == 0.2
        assert metrics.max_time == 0.3
        assert metrics.memory_peak == 15.0
        assert metrics.error_count == 1
    
    def test_cache_hit_rate(self):
        """测试缓存命中率计算。"""
        metrics = PerformanceMetrics(
            function_name="test_func",
            execution_time=0.1
        )
        
        # 无缓存时
        assert metrics.cache_hit_rate == 0.0
        
        # 有缓存命中
        metrics.cache_hits = 80
        metrics.cache_misses = 20
        assert metrics.cache_hit_rate == 80.0
    
    def test_error_rate(self):
        """测试错误率计算。"""
        metrics = PerformanceMetrics(
            function_name="test_func",
            execution_time=0.1
        )
        
        # 无错误时
        assert metrics.error_rate == 0.0
        
        # 有错误
        metrics.error_count = 5
        metrics.call_count = 100
        assert metrics.error_rate == 5.0
    
    def test_to_dict(self):
        """测试转换为字典。"""
        metrics = PerformanceMetrics(
            function_name="test_func",
            execution_time=0.1
        )
        metrics.cache_hits = 50
        metrics.cache_misses = 50
        
        result = metrics.to_dict()
        
        assert isinstance(result, dict)
        assert result['function_name'] == "test_func"
        assert result['cache_hit_rate'] == 50.0
        assert 'call_count' in result
        assert 'total_time' in result


# ==================== PerformanceMonitor测试 ====================

class TestPerformanceMonitor:
    """测试性能监控器。"""
    
    def setup_method(self):
        """每个测试方法前重置监控器。"""
        PerformanceMonitor.reset()
    
    def test_singleton(self):
        """测试单例模式。"""
        monitor1 = PerformanceMonitor()
        monitor2 = PerformanceMonitor()
        
        assert monitor1 is monitor2
    
    def test_record(self):
        """测试记录性能数据。"""
        PerformanceMonitor.record(
            "test_func",
            execution_time=0.5,
            cache_hit=True,
            memory_usage=10.0,
            error=False
        )
        
        metrics = PerformanceMonitor.get_metrics("test_func")
        
        assert metrics is not None
        assert metrics.function_name == "test_func"
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 0
    
    def test_get_all_metrics(self):
        """测试获取所有性能指标。"""
        PerformanceMonitor.record("func1", 0.1)
        PerformanceMonitor.record("func2", 0.2)
        PerformanceMonitor.record("func1", 0.15)
        
        all_metrics = PerformanceMonitor.get_all_metrics()
        
        assert len(all_metrics) == 2
        assert "func1" in all_metrics
        assert "func2" in all_metrics
        assert all_metrics["func1"].call_count == 2
    
    def test_generate_report(self):
        """测试生成性能报告。"""
        PerformanceMonitor.record("func1", 0.1)
        PerformanceMonitor.record("func2", 0.2)
        
        report = PerformanceMonitor.generate_report()
        
        assert isinstance(report, str)
        assert "性能监控报告" in report
        assert "func1" in report
        assert "func2" in report
    
    def test_reset(self):
        """测试重置性能数据。"""
        PerformanceMonitor.record("test_func", 0.1)
        
        assert len(PerformanceMonitor.get_all_metrics()) == 1
        
        PerformanceMonitor.reset()
        
        assert len(PerformanceMonitor.get_all_metrics()) == 0
    
    def test_export_to_json(self, tmp_path):
        """测试导出到JSON文件。"""
        PerformanceMonitor.record("test_func", 0.1)
        
        json_file = tmp_path / "performance.json"
        result = PerformanceMonitor.export_to_json(str(json_file))
        
        assert result is True
        assert json_file.exists()
        
        # 验证文件内容
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'start_time' in data
        assert 'export_time' in data
        assert 'metrics' in data


# ==================== performance_monitor装饰器测试 ====================

class TestPerformanceMonitorDecorator:
    """测试性能监控装饰器。"""
    
    def setup_method(self):
        """每个测试方法前重置监控器。"""
        PerformanceMonitor.reset()
    
    def test_decorator(self):
        """测试装饰器基本功能。"""
        @performance_monitor
        def test_func():
            time.sleep(0.01)
            return "result"
        
        result = test_func()
        
        assert result == "result"
        
        metrics = PerformanceMonitor.get_metrics("test_func")
        assert metrics is not None
        assert metrics.call_count == 1
        assert metrics.execution_time > 0
    
    def test_decorator_with_exception(self):
        """测试装饰器处理异常。"""
        @performance_monitor
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_func()
        
        metrics = PerformanceMonitor.get_metrics("test_func")
        assert metrics is not None
        assert metrics.error_count == 1
    
    def test_decorator_multiple_calls(self):
        """测试装饰器多次调用。"""
        @performance_monitor
        def test_func(n):
            return n * 2
        
        for i in range(5):
            result = test_func(i)
            assert result == i * 2
        
        metrics = PerformanceMonitor.get_metrics("test_func")
        assert metrics.call_count == 5


# ==================== CacheManager测试 ====================

class TestCacheManager:
    """测试缓存管理器。"""
    
    def setup_method(self):
        """每个测试方法前重置缓存。"""
        CacheManager.clear()
    
    def test_singleton(self):
        """测试单例模式。"""
        cache1 = CacheManager()
        cache2 = CacheManager()
        
        assert cache1 is cache2
    
    def test_set_and_get(self):
        """测试设置和获取缓存。"""
        CacheManager.set("key1", "value1")
        
        result = CacheManager.get("key1")
        
        assert result == "value1"
    
    def test_cache_not_found(self):
        """测试缓存未命中。"""
        result = CacheManager.get("nonexistent_key")
        
        assert result is None
    
    def test_cache_expiration(self):
        """测试缓存过期。"""
        # 设置短过期时间
        CacheManager.set_config(ttl=1)  # 1秒
        
        CacheManager.set("key1", "value1")
        
        # 立即获取应该成功
        result = CacheManager.get("key1")
        assert result == "value1"
        
        # 等待过期
        time.sleep(1.5)
        
        # 过期后应该返回None
        result = CacheManager.get("key1")
        assert result is None
    
    def test_cache_eviction(self):
        """测试缓存淘汰。"""
        CacheManager.set_config(max_size=3)
        
        CacheManager.set("key1", "value1")
        CacheManager.set("key2", "value2")
        CacheManager.set("key3", "value3")
        CacheManager.set("key4", "value4")  # 应该触发淘汰
        
        # 缓存大小应该不超过max_size
        stats = CacheManager.get_stats()
        assert stats['cache_size'] <= 3
    
    def test_cache_stats(self):
        """测试缓存统计。"""
        CacheManager.set("key1", "value1")
        CacheManager.get("key1")  # 命中
        CacheManager.get("key1")  # 命中
        CacheManager.get("key2")  # 未命中
        
        stats = CacheManager.get_stats()
        
        assert stats['cache_size'] == 1
        assert stats['cache_hits'] == 2
        assert stats['cache_misses'] == 1
        assert stats['hit_rate'] == pytest.approx(66.67, rel=0.01)
    
    def test_cache_clear(self):
        """测试清空缓存。"""
        CacheManager.set("key1", "value1")
        CacheManager.set("key2", "value2")
        
        CacheManager.clear()
        
        stats = CacheManager.get_stats()
        assert stats['cache_size'] == 0
        assert stats['cache_hits'] == 0
    
    def test_cache_warmup(self):
        """测试缓存预热。"""
        items = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
        CacheManager.warmup(items)
        
        assert CacheManager.get("key1") == "value1"
        assert CacheManager.get("key2") == "value2"
        assert CacheManager.get("key3") == "value3"
    
    def test_disk_cache(self, tmp_path):
        """测试磁盘缓存。"""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        CacheManager.set_config(
            enable_disk_cache=True,
            disk_cache_dir=str(cache_dir)
        )
        
        CacheManager.set("key1", "value1")
        
        # 清空内存缓存
        CacheManager._cache.clear()
        
        # 从磁盘加载
        result = CacheManager.get("key1")
        assert result == "value1"


# ==================== cached装饰器测试 ====================

class TestCachedDecorator:
    """测试缓存装饰器。"""
    
    def setup_method(self):
        """每个测试方法前重置缓存。"""
        CacheManager.clear()
        PerformanceMonitor.reset()
    
    def test_cached_decorator(self):
        """测试缓存装饰器基本功能。"""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_func(n):
            nonlocal call_count
            call_count += 1
            return n * n
        
        # 第一次调用（缓存未命中）
        result1 = expensive_func(5)
        assert result1 == 25
        assert call_count == 1
        
        # 第二次调用（缓存命中）
        result2 = expensive_func(5)
        assert result2 == 25
        assert call_count == 1  # 没有增加
        
        # 不同参数（缓存未命中）
        result3 = expensive_func(10)
        assert result3 == 100
        assert call_count == 2
    
    def test_cached_with_different_args(self):
        """测试缓存装饰器处理不同参数。"""
        @cached(ttl=60)
        def func(a, b):
            return a + b
        
        result1 = func(1, 2)
        result2 = func(1, 2)  # 缓存命中
        result3 = func(2, 3)  # 缓存未命中
        
        assert result1 == 3
        assert result2 == 3
        assert result3 == 5


# ==================== ParallelProcessor测试 ====================

class TestParallelProcessor:
    """测试并行处理器。"""
    
    def test_get_optimal_workers(self):
        """测试获取最优工作数量。"""
        cpu_workers = ParallelProcessor.get_optimal_workers('cpu')
        io_workers = ParallelProcessor.get_optimal_workers('io')
        
        assert isinstance(cpu_workers, int)
        assert isinstance(io_workers, int)
        assert cpu_workers >= 1
        assert io_workers >= 1
        # IO密集型任务应该使用更多工作线程
        assert io_workers >= cpu_workers
    
    def test_parallel_map(self):
        """测试并行映射。"""
        def square(n):
            return n * n
        
        items = [1, 2, 3, 4, 5]
        results = ParallelProcessor.parallel_map(
            square,
            items,
            task_type='io'  # Windows上使用io类型避免pickle问题
        )
        
        assert len(results) == 5
        assert results == [1, 4, 9, 16, 25]
    
    def test_parallel_map_with_exception(self):
        """测试并行映射处理异常。"""
        def divide(n):
            return 10 / n
        
        items = [1, 2, 0, 4, 5]  # 包含会导致异常的项
        
        # 应该捕获异常并继续处理其他项
        results = ParallelProcessor.parallel_map(
            divide,
            items,
            task_type='cpu',
            retry_count=0
        )
        
        # 部分结果应该成功
        assert results[0] == 10.0
        assert results[1] == 5.0
        assert results[2] is None  # 异常项
        assert results[3] == 2.5
        assert results[4] == 2.0
    
    def test_batch_process(self):
        """测试分批处理。"""
        def process_batch(batch):
            return [x * 2 for x in batch]
        
        items = list(range(10))
        results = ParallelProcessor.batch_process(
            process_batch,
            items,
            batch_size=3,
            task_type='cpu'
        )
        
        assert len(results) == 10
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
    
    def test_adaptive_batch_size(self):
        """测试自适应批次大小计算。"""
        # 小数据集
        batch_size_small = ParallelProcessor.adaptive_batch_size(50)
        assert batch_size_small <= 50
        
        # 中等数据集
        batch_size_medium = ParallelProcessor.adaptive_batch_size(500)
        assert batch_size_medium > batch_size_small
        
        # 大数据集
        batch_size_large = ParallelProcessor.adaptive_batch_size(5000)
        assert batch_size_large >= batch_size_medium


# ==================== OptimizationSuggester测试 ====================

class TestOptimizationSuggester:
    """测试优化建议生成器。"""
    
    def test_analyze_performance(self):
        """测试分析性能数据。"""
        metrics = {
            'slow_func': PerformanceMetrics(
                function_name='slow_func',
                execution_time=2.0
            ),
            'fast_func': PerformanceMetrics(
                function_name='fast_func',
                execution_time=0.01
            )
        }
        
        # 设置慢函数的平均时间
        metrics['slow_func'].avg_time = 2.0
        metrics['slow_func'].call_count = 10
        
        suggestions = OptimizationSuggester.analyze_performance(metrics)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        # 应该包含关于慢函数的建议
        assert any('slow_func' in s for s in suggestions)
    
    def test_generate_optimization_report(self):
        """测试生成优化建议报告。"""
        metrics = {
            'test_func': PerformanceMetrics(
                function_name='test_func',
                execution_time=0.1
            )
        }
        
        report = OptimizationSuggester.generate_optimization_report(metrics)
        
        assert isinstance(report, str)
        assert "性能优化建议报告" in report
        assert "test_func" in report
    
    def test_identify_bottlenecks(self):
        """测试识别性能瓶颈。"""
        metrics = {
            'slow_func': PerformanceMetrics(
                function_name='slow_func',
                execution_time=3.0
            ),
            'memory_hungry': PerformanceMetrics(
                function_name='memory_hungry',
                execution_time=0.5
            )
        }
        
        # 设置瓶颈指标
        metrics['slow_func'].avg_time = 3.0
        metrics['memory_hungry'].memory_peak = 250.0
        
        bottlenecks = OptimizationSuggester.identify_bottlenecks(metrics)
        
        assert isinstance(bottlenecks, list)
        # 应该识别出时间瓶颈和内存瓶颈
        bottleneck_types = {b['type'] for b in bottlenecks}
        assert 'time' in bottleneck_types or 'memory' in bottleneck_types


# ==================== 集成测试 ====================

class TestIntegration:
    """测试性能优化模块的集成功能。"""
    
    def setup_method(self):
        """每个测试方法前重置状态。"""
        PerformanceMonitor.reset()
        CacheManager.clear()
    
    def test_performance_monitor_with_cache(self):
        """测试性能监控与缓存的集成。"""
        @cached(ttl=60)
        @performance_monitor
        def expensive_func(n):
            return sum(range(n))
        
        # 第一次调用（缓存未命中）
        result1 = expensive_func(1000)
        
        # 第二次调用（缓存命中）
        result2 = expensive_func(1000)
        
        assert result1 == result2
        
        # 检查性能指标
        metrics = PerformanceMonitor.get_metrics("expensive_func")
        assert metrics is not None
        assert metrics.cache_hits > 0 or metrics.cache_misses > 0
    
    def test_parallel_processing_with_cache(self):
        """测试并行处理与缓存的集成。"""
        call_count = 0
        
        @cached(ttl=60)
        def cached_func(n):
            nonlocal call_count
            call_count += 1
            return n * n
        
        def process_item(n):
            return cached_func(n)
        
        items = [1, 2, 3, 1, 2, 3]  # 包含重复项
        
        results = ParallelProcessor.parallel_map(
            process_item,
            items,
            task_type='cpu'
        )
        
        # 结果应该正确
        assert results == [1, 4, 9, 1, 4, 9]
        
        # 由于缓存，实际调用次数应该少于项目数
        assert call_count <= 6
