#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试

测试大数据量处理能力和性能优化效果。

WING
"""

import pytest
import sys
import os
import time
import tempfile
import shutil
from datetime import datetime, timedelta

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from git_analyzer import (
    ContributionCalculator,
    CommitAnalyzer,
    ReportGenerator,
    AlgorithmMode
)

from code_quality_evaluator import CodeQualityEvaluator

from performance_optimizer import (
    PerformanceMonitor,
    CacheManager,
    ParallelProcessor,
    OptimizationSuggester
)


# ==================== 大数据量测试 ====================

class TestLargeDataProcessing:
    """测试大数据量处理能力。"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_repo_analysis(self, performance_test_repo):
        """测试大型仓库分析性能。"""
        PerformanceMonitor.reset()
        
        calculator = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True,
            batch_size=50
        )
        
        start_time = time.time()
        result = calculator.calculate_contribution(performance_test_repo)
        elapsed_time = time.time() - start_time
        
        # 验证结果
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # 性能要求：50个提交应该在60秒内完成
        assert elapsed_time < 60, f"分析耗时 {elapsed_time:.2f}s 超过60秒限制"
        
        print(f"\n大型仓库分析耗时: {elapsed_time:.2f}s")
        print(f"分析作者数: {len(result)}")
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_large_file_evaluation(self, large_python_file):
        """测试大型文件评估性能。"""
        evaluator = CodeQualityEvaluator()
        
        start_time = time.time()
        report = evaluator.evaluate_file(large_python_file)
        elapsed_time = time.time() - start_time
        
        # 验证结果
        assert report.total_score >= 0
        
        # 性能要求：大型文件应该在5秒内完成
        assert elapsed_time < 5, f"评估耗时 {elapsed_time:.2f}s 超过5秒限制"
        
        print(f"\n大型文件评估耗时: {elapsed_time:.2f}s")
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_batch_file_evaluation(self, tmp_path):
        """测试批量文件评估性能。"""
        # 创建多个测试文件
        num_files = 30
        test_files = []
        
        for i in range(num_files):
            file_path = tmp_path / f"test_file_{i}.py"
            file_path.write_text(f'"""测试文件 {i}"""\n\ndef func_{i}():\n    pass\n')
            test_files.append(str(file_path))
        
        evaluator = CodeQualityEvaluator()
        
        # 串行评估
        start_time = time.time()
        serial_reports = []
        for file_path in test_files:
            report = evaluator.evaluate_file(file_path)
            serial_reports.append(report)
        serial_time = time.time() - start_time
        
        # 并行评估
        start_time = time.time()
        parallel_reports = evaluator.evaluate_files_batch(test_files, parallel=True)
        parallel_time = time.time() - start_time
        
        # 验证结果数量
        assert len(serial_reports) == num_files
        assert len(parallel_reports) == num_files
        
        # 并行应该更快（或至少不慢）
        print(f"\n串行评估耗时: {serial_time:.2f}s")
        print(f"并行评估耗时: {parallel_time:.2f}s")
        print(f"加速比: {serial_time / parallel_time:.2f}x")


# ==================== 并行处理性能测试 ====================

class TestParallelPerformance:
    """测试并行处理性能。"""
    
    @pytest.mark.performance
    def test_parallel_vs_serial_commits(self, performance_test_repo):
        """测试并行vs串行提交处理。"""
        PerformanceMonitor.reset()
        
        # 串行处理
        calculator_serial = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=False
        )
        start_time = time.time()
        result_serial = calculator_serial.calculate_contribution(performance_test_repo)
        serial_time = time.time() - start_time
        
        # 并行处理
        calculator_parallel = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True,
            batch_size=50
        )
        start_time = time.time()
        result_parallel = calculator_parallel.calculate_contribution(performance_test_repo)
        parallel_time = time.time() - start_time
        
        # 结果应该一致
        assert len(result_serial) == len(result_parallel)
        
        # 计算加速比
        speedup = serial_time / parallel_time if parallel_time > 0 else 1.0
        
        print(f"\n串行处理耗时: {serial_time:.2f}s")
        print(f"并行处理耗时: {parallel_time:.2f}s")
        print(f"加速比: {speedup:.2f}x")
        
        # 并行应该有加速效果（至少不慢）
        assert speedup >= 0.8, f"并行加速比 {speedup:.2f}x 低于预期"
    
    @pytest.mark.performance
    def test_different_batch_sizes(self, performance_test_repo):
        """测试不同批次大小的性能。"""
        batch_sizes = [10, 25, 50, 100]
        results = []
        
        for batch_size in batch_sizes:
            PerformanceMonitor.reset()
            
            calculator = ContributionCalculator(
                algorithm_mode=AlgorithmMode.QUALITY,
                enable_parallel=True,
                batch_size=batch_size
            )
            
            start_time = time.time()
            result = calculator.calculate_contribution(performance_test_repo)
            elapsed_time = time.time() - start_time
            
            results.append({
                'batch_size': batch_size,
                'time': elapsed_time,
                'authors': len(result)
            })
            
            print(f"\n批次大小 {batch_size}: 耗时 {elapsed_time:.2f}s")
        
        # 验证所有批次大小都成功完成
        assert all(r['authors'] > 0 for r in results)


# ==================== 缓存性能测试 ====================

class TestCachePerformance:
    """测试缓存性能。"""
    
    @pytest.mark.performance
    def test_cache_effectiveness(self, sample_python_file):
        """测试缓存效果。"""
        CacheManager.clear()
        PerformanceMonitor.reset()
        
        evaluator = CodeQualityEvaluator(enable_cache=True)
        
        # 第一次评估（缓存未命中）
        start_time = time.time()
        report1 = evaluator.evaluate_file(sample_python_file)
        first_time = time.time() - start_time
        
        # 第二次评估（缓存命中）
        start_time = time.time()
        report2 = evaluator.evaluate_file(sample_python_file)
        second_time = time.time() - start_time
        
        # 结果应该一致
        assert report1.total_score == report2.total_score
        
        # 缓存应该加速
        cache_speedup = first_time / second_time if second_time > 0 else 1.0
        
        print(f"\n第一次评估耗时: {first_time:.4f}s")
        print(f"第二次评估耗时: {second_time:.4f}s")
        print(f"缓存加速比: {cache_speedup:.2f}x")
        
        # 缓存应该有显著加速
        assert cache_speedup >= 1.5, f"缓存加速比 {cache_speedup:.2f}x 低于预期"
    
    @pytest.mark.performance
    def test_cache_with_multiple_files(self, tmp_path):
        """测试多文件缓存效果。"""
        CacheManager.clear()
        
        # 创建多个测试文件
        num_files = 20
        test_files = []
        
        for i in range(num_files):
            file_path = tmp_path / f"cache_test_{i}.py"
            file_path.write_text(f'"""文件 {i}"""\n\ndef func():\n    return {i}\n')
            test_files.append(str(file_path))
        
        evaluator = CodeQualityEvaluator(enable_cache=True)
        
        # 第一次批量评估
        start_time = time.time()
        reports1 = evaluator.evaluate_files_batch(test_files, parallel=False)
        first_time = time.time() - start_time
        
        # 第二次批量评估（应该使用缓存）
        start_time = time.time()
        reports2 = evaluator.evaluate_files_batch(test_files, parallel=False)
        second_time = time.time() - start_time
        
        # 结果应该一致
        assert len(reports1) == len(reports2)
        
        cache_speedup = first_time / second_time if second_time > 0 else 1.0
        
        print(f"\n第一次批量评估耗时: {first_time:.2f}s")
        print(f"第二次批量评估耗时: {second_time:.2f}s")
        print(f"缓存加速比: {cache_speedup:.2f}x")


# ==================== 内存使用测试 ====================

class TestMemoryUsage:
    """测试内存使用。"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_large_repo(self, performance_test_repo):
        """测试大型仓库内存使用。"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            calculator = ContributionCalculator(
                algorithm_mode=AlgorithmMode.QUALITY,
                enable_parallel=True,
                batch_size=50
            )
            
            result = calculator.calculate_contribution(performance_test_repo)
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            print(f"\n初始内存: {initial_memory:.2f} MB")
            print(f"最终内存: {final_memory:.2f} MB")
            print(f"内存增量: {memory_increase:.2f} MB")
            
            # 内存增量应该在合理范围内（小于500MB）
            assert memory_increase < 500, f"内存增量 {memory_increase:.2f}MB 超过500MB限制"
            
        except ImportError:
            pytest.skip("psutil未安装，跳过内存测试")
    
    @pytest.mark.performance
    def test_cache_memory_efficiency(self, tmp_path):
        """测试缓存内存效率。"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            # 创建大量文件
            num_files = 50
            test_files = []
            
            for i in range(num_files):
                file_path = tmp_path / f"mem_test_{i}.py"
                file_path.write_text(f'"""文件 {i}"""\n\ndef func():\n    pass\n')
                test_files.append(str(file_path))
            
            CacheManager.clear()
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            evaluator = CodeQualityEvaluator(enable_cache=True)
            
            # 评估所有文件
            for file_path in test_files:
                evaluator.evaluate_file(file_path)
            
            cached_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = cached_memory - initial_memory
            
            print(f"\n缓存 {num_files} 个文件后的内存增量: {memory_increase:.2f} MB")
            
            # 内存增量应该在合理范围内
            assert memory_increase < 100, f"缓存内存增量 {memory_increase:.2f}MB 过大"
            
        except ImportError:
            pytest.skip("psutil未安装，跳过内存测试")


# ==================== 性能监控测试 ====================

class TestPerformanceMonitoring:
    """测试性能监控功能。"""
    
    @pytest.mark.performance
    def test_performance_metrics_collection(self, performance_test_repo):
        """测试性能指标收集。"""
        PerformanceMonitor.reset()
        
        calculator = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True
        )
        
        result = calculator.calculate_contribution(performance_test_repo)
        
        # 获取性能指标
        metrics = PerformanceMonitor.get_all_metrics()
        
        # 应该收集到一些性能数据
        assert len(metrics) > 0
        
        # 生成性能报告
        report = PerformanceMonitor.generate_report()
        
        assert isinstance(report, str)
        assert len(report) > 0
        
        print("\n性能监控报告:")
        print(report)
    
    @pytest.mark.performance
    def test_optimization_suggestions(self, performance_test_repo):
        """测试优化建议生成。"""
        PerformanceMonitor.reset()
        
        calculator = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True
        )
        
        result = calculator.calculate_contribution(performance_test_repo)
        
        # 获取性能指标
        metrics = PerformanceMonitor.get_all_metrics()
        
        # 生成优化建议
        suggestions = OptimizationSuggester.analyze_performance(metrics)
        
        assert isinstance(suggestions, list)
        
        print("\n优化建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
    
    @pytest.mark.performance
    def test_bottleneck_identification(self, performance_test_repo):
        """测试性能瓶颈识别。"""
        PerformanceMonitor.reset()
        
        calculator = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True
        )
        
        result = calculator.calculate_contribution(performance_test_repo)
        
        # 获取性能指标
        metrics = PerformanceMonitor.get_all_metrics()
        
        # 识别瓶颈
        bottlenecks = OptimizationSuggester.identify_bottlenecks(metrics)
        
        assert isinstance(bottlenecks, list)
        
        print("\n性能瓶颈:")
        for bottleneck in bottlenecks:
            print(f"- {bottleneck['function']}: {bottleneck['description']}")


# ==================== 压力测试 ====================

class TestStress:
    """压力测试。"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_repeated_analysis(self, performance_test_repo):
        """测试重复分析。"""
        PerformanceMonitor.reset()
        
        calculator = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True
        )
        
        # 重复分析多次
        num_iterations = 5
        times = []
        
        for i in range(num_iterations):
            start_time = time.time()
            result = calculator.calculate_contribution(performance_test_repo)
            elapsed_time = time.time() - start_time
            times.append(elapsed_time)
            
            print(f"\n第 {i+1} 次分析耗时: {elapsed_time:.2f}s")
        
        # 计算统计数据
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\n平均耗时: {avg_time:.2f}s")
        print(f"最小耗时: {min_time:.2f}s")
        print(f"最大耗时: {max_time:.2f}s")
        
        # 性能应该稳定
        assert max_time < min_time * 2, "性能波动过大"
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_analysis(self, performance_test_repo):
        """测试并发分析。"""
        from concurrent.futures import ThreadPoolExecutor
        
        PerformanceMonitor.reset()
        
        def analyze():
            calculator = ContributionCalculator(
                algorithm_mode=AlgorithmMode.QUALITY,
                enable_parallel=True
            )
            return calculator.calculate_contribution(performance_test_repo)
        
        # 并发执行多个分析
        num_concurrent = 3
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(analyze) for _ in range(num_concurrent)]
            results = [future.result() for future in futures]
        elapsed_time = time.time() - start_time
        
        # 所有分析都应该成功
        assert all(isinstance(r, dict) for r in results)
        
        print(f"\n并发 {num_concurrent} 个分析耗时: {elapsed_time:.2f}s")


# ==================== 性能基准测试 ====================

class TestBenchmarks:
    """性能基准测试。"""
    
    @pytest.mark.performance
    def test_commit_analysis_benchmark(self, git_repo_with_commits):
        """测试提交分析基准。"""
        repo_path, commits = git_repo_with_commits
        
        start_time = time.time()
        commit_list = CommitAnalyzer.get_commits(repo_path)
        elapsed_time = time.time() - start_time
        
        # 记录基准
        print(f"\n提交分析基准:")
        print(f"提交数量: {len(commit_list)}")
        print(f"耗时: {elapsed_time:.4f}s")
        print(f"平均每提交: {elapsed_time / len(commit_list) * 1000:.2f}ms")
    
    @pytest.mark.performance
    def test_contribution_calculation_benchmark(self, git_repo_with_commits):
        """测试贡献度计算基准。"""
        repo_path, commits = git_repo_with_commits
        
        # 旧算法基准
        calculator_legacy = ContributionCalculator(algorithm_mode=AlgorithmMode.LEGACY)
        start_time = time.time()
        result_legacy = calculator_legacy.calculate_contribution(repo_path)
        legacy_time = time.time() - start_time
        
        # 新算法基准
        calculator_quality = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        start_time = time.time()
        result_quality = calculator_quality.calculate_contribution(repo_path)
        quality_time = time.time() - start_time
        
        print(f"\n贡献度计算基准:")
        print(f"旧算法耗时: {legacy_time:.4f}s")
        print(f"新算法耗时: {quality_time:.4f}s")
        print(f"速度比: {quality_time / legacy_time:.2f}x")
    
    @pytest.mark.performance
    def test_report_generation_benchmark(self, git_repo_with_commits, tmp_path):
        """测试报告生成基准。"""
        repo_path, commits = git_repo_with_commits
        report_file = tmp_path / "benchmark_report.md"
        
        start_time = time.time()
        success = ReportGenerator.generate_markdown_report(
            repo_path,
            str(report_file),
            algorithm_mode=AlgorithmMode.QUALITY
        )
        elapsed_time = time.time() - start_time
        
        assert success
        
        # 记录基准
        report_size = report_file.stat().st_size
        
        print(f"\n报告生成基准:")
        print(f"耗时: {elapsed_time:.4f}s")
        print(f"报告大小: {report_size} 字节")


# ==================== 性能回归测试 ====================

class TestPerformanceRegression:
    """性能回归测试。"""
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_no_performance_regression(self, performance_test_repo):
        """测试性能无回归。"""
        PerformanceMonitor.reset()
        
        # 定义性能基线（根据实际情况调整）
        BASELINE_TIME = 30  # 30秒
        
        calculator = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True,
            batch_size=50
        )
        
        start_time = time.time()
        result = calculator.calculate_contribution(performance_test_repo)
        elapsed_time = time.time() - start_time
        
        # 性能不应该比基线差太多
        assert elapsed_time < BASELINE_TIME * 1.5, \
            f"性能回归: {elapsed_time:.2f}s 超过基线 {BASELINE_TIME}s 的150%"
        
        print(f"\n性能回归测试:")
        print(f"基线时间: {BASELINE_TIME}s")
        print(f"实际时间: {elapsed_time:.2f}s")
        print(f"性能比: {elapsed_time / BASELINE_TIME * 100:.1f}%")
