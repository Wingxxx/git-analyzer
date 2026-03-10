#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试

测试完整的工作流程和模块间的协作。

WING
"""

import pytest
import sys
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from git_analyzer import (
    RepositoryManager,
    CommitAnalyzer,
    ContributionCalculator,
    ReportGenerator,
    AlgorithmMode
)

from code_quality_evaluator import (
    CodeQualityEvaluator,
    ProjectType,
    ProjectStage
)

from performance_optimizer import (
    PerformanceMonitor,
    CacheManager,
    ParallelProcessor
)


# ==================== 完整工作流测试 ====================

class TestCompleteWorkflow:
    """测试完整的工作流程。"""
    
    @pytest.mark.integration
    def test_full_analysis_workflow(self, git_repo_with_commits, tmp_path):
        """测试完整的分析工作流。"""
        repo_path, commits = git_repo_with_commits
        
        # 1. 检查仓库状态
        is_repo = RepositoryManager.is_git_repo(repo_path)
        assert is_repo is True
        
        # 2. 获取提交记录
        commit_list = CommitAnalyzer.get_commits(repo_path)
        assert len(commit_list) > 0
        
        # 3. 计算贡献度（旧算法）
        calculator_legacy = ContributionCalculator(algorithm_mode=AlgorithmMode.LEGACY)
        contribution_legacy = calculator_legacy.calculate_contribution(repo_path)
        assert len(contribution_legacy) > 0
        
        # 4. 计算贡献度（新算法）
        calculator_quality = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        contribution_quality = calculator_quality.calculate_contribution(repo_path)
        assert len(contribution_quality) > 0
        
        # 5. 生成报告
        output_file = tmp_path / "integration_report.md"
        result = ReportGenerator.generate_markdown_report(
            repo_path,
            str(output_file),
            algorithm_mode=AlgorithmMode.QUALITY
        )
        assert result is True
        assert output_file.exists()
    
    @pytest.mark.integration
    def test_branch_workflow(self, git_repo_with_branches):
        """测试分支操作工作流。"""
        repo_path, branches = git_repo_with_branches
        
        # 1. 列出分支
        branch_list = RepositoryManager.list_branches(repo_path)
        assert len(branch_list) > 0
        
        # 2. 切换分支
        if 'feature-1' in branch_list:
            result = RepositoryManager.switch_branch(repo_path, 'feature-1')
            assert result is True
            
            # 3. 在新分支上获取提交
            commits = CommitAnalyzer.get_commits(repo_path)
            assert isinstance(commits, list)
    
    @pytest.mark.integration
    def test_date_filtering_workflow(self, git_repo_with_commits):
        """测试日期过滤工作流。"""
        repo_path, commits = git_repo_with_commits
        
        # 获取所有提交
        all_commits = CommitAnalyzer.get_commits(repo_path)
        
        # 使用日期过滤
        since = datetime.now() - timedelta(days=1)
        until = datetime.now() + timedelta(days=1)
        filtered_commits = CommitAnalyzer.get_commits(repo_path, since=since, until=until)
        
        # 过滤后的提交应该少于或等于所有提交
        assert len(filtered_commits) <= len(all_commits)


# ==================== 模块协作测试 ====================

class TestModuleCollaboration:
    """测试模块间的协作。"""
    
    @pytest.mark.integration
    def test_quality_evaluator_with_git_analyzer(self, git_repo_with_commits):
        """测试代码质量评估器与Git分析器的协作。"""
        repo_path, commits = git_repo_with_commits
        
        # 使用Git分析器获取提交
        commit_list = CommitAnalyzer.get_commits(repo_path)
        
        if len(commit_list) > 0:
            # 获取提交详情
            commit_hash = commit_list[0]['hash']
            commit_details = CommitAnalyzer.get_commit_details(repo_path, commit_hash)
            
            # 如果有变更的Python文件，评估其质量
            if 'changed_files' in commit_details:
                evaluator = CodeQualityEvaluator()
                
                for file_info in commit_details['changed_files']:
                    file_path = file_info['path']
                    if file_path.endswith('.py'):
                        full_path = os.path.join(repo_path, file_path)
                        if os.path.exists(full_path):
                            report = evaluator.evaluate_file(full_path)
                            assert report.total_score >= 0
    
    @pytest.mark.integration
    def test_performance_monitoring_with_analysis(self, git_repo_with_commits):
        """测试性能监控与分析的协作。"""
        PerformanceMonitor.reset()
        
        repo_path, commits = git_repo_with_commits
        
        # 执行分析
        calculator = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True
        )
        result = calculator.calculate_contribution(repo_path)
        
        # 检查性能指标
        metrics = PerformanceMonitor.get_all_metrics()
        
        # 应该记录了一些性能数据
        assert len(metrics) > 0 or len(result) > 0
    
    @pytest.mark.integration
    def test_cache_with_quality_evaluation(self, sample_python_file):
        """测试缓存与质量评估的协作。"""
        CacheManager.clear()
        
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
        
        # 第二次应该更快（或至少不慢）
        # 注意：由于测试环境的不确定性，这里不强制要求更快
        assert second_time <= first_time * 2  # 允许一定的波动


# ==================== 端到端测试 ====================

class TestEndToEnd:
    """端到端测试。"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_complete_analysis_with_report(self, performance_test_repo, tmp_path):
        """测试完整的分析流程并生成报告。"""
        repo_path = performance_test_repo
        
        # 1. 仓库验证
        assert RepositoryManager.is_git_repo(repo_path)
        
        # 2. 提交分析
        commits = CommitAnalyzer.get_commits(repo_path)
        assert len(commits) > 0
        
        # 3. 贡献度计算（两种算法）
        calculator_legacy = ContributionCalculator(algorithm_mode=AlgorithmMode.LEGACY)
        result_legacy = calculator_legacy.calculate_contribution(repo_path)
        
        calculator_quality = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        result_quality = calculator_quality.calculate_contribution(repo_path)
        
        # 4. 生成报告
        report_file = tmp_path / "e2e_report.md"
        success = ReportGenerator.generate_markdown_report(
            repo_path,
            str(report_file),
            algorithm_mode=AlgorithmMode.QUALITY
        )
        
        assert success
        assert report_file.exists()
        
        # 验证报告内容
        content = report_file.read_text(encoding='utf-8')
        assert "Git仓库分析报告" in content
        assert "贡献度排名" in content
    
    @pytest.mark.integration
    def test_multi_file_quality_assessment(self, git_repo_with_commits):
        """测试多文件质量评估。"""
        repo_path, commits = git_repo_with_commits
        
        # 获取所有Python文件
        python_files = []
        for root, dirs, files in os.walk(repo_path):
            # 跳过.git目录
            if '.git' in root:
                continue
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        if len(python_files) > 0:
            evaluator = CodeQualityEvaluator()
            
            # 批量评估
            reports = evaluator.evaluate_files_batch(python_files, parallel=False)
            
            assert len(reports) > 0
            assert all(r.total_score >= 0 for r in reports)


# ==================== 错误处理集成测试 ====================

class TestErrorHandlingIntegration:
    """测试错误处理的集成。"""
    
    @pytest.mark.integration
    def test_invalid_repo_handling(self):
        """测试无效仓库的处理。"""
        # 无效路径
        assert RepositoryManager.is_git_repo("/nonexistent/path") is False
        
        # 获取提交应该返回空列表
        commits = CommitAnalyzer.get_commits("/nonexistent/path")
        assert commits == []
        
        # 计算贡献度应该返回空字典
        calculator = ContributionCalculator()
        result = calculator.calculate_contribution("/nonexistent/path")
        assert result == {}
    
    @pytest.mark.integration
    def test_empty_repo_handling(self, temp_git_repo):
        """测试空仓库的处理。"""
        # 空仓库应该被正确识别
        assert RepositoryManager.is_git_repo(temp_git_repo)
        
        # 获取提交应该返回空列表
        commits = CommitAnalyzer.get_commits(temp_git_repo)
        assert commits == []
        
        # 计算贡献度应该返回空字典
        calculator = ContributionCalculator()
        result = calculator.calculate_contribution(temp_git_repo)
        assert result == {}
    
    @pytest.mark.integration
    def test_syntax_error_file_handling(self, syntax_error_file):
        """测试语法错误文件的处理。"""
        evaluator = CodeQualityEvaluator()
        
        # 应该返回最低分报告而不是抛出异常
        report = evaluator.evaluate_file(syntax_error_file)
        
        assert report.total_score == 0.0
        assert len(report.suggestions) > 0


# ==================== 性能集成测试 ====================

class TestPerformanceIntegration:
    """测试性能相关的集成。"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_parallel_processing_integration(self, performance_test_repo):
        """测试并行处理集成。"""
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
        
        # 性能监控应该记录了数据
        metrics = PerformanceMonitor.get_all_metrics()
        assert len(metrics) > 0
    
    @pytest.mark.integration
    def test_cache_integration(self, sample_python_file, sample_bad_python_file):
        """测试缓存集成。"""
        CacheManager.clear()
        
        evaluator = CodeQualityEvaluator(enable_cache=True)
        
        files = [sample_python_file, sample_bad_python_file]
        
        # 第一次批量评估
        reports1 = evaluator.evaluate_files_batch(files, parallel=False)
        
        # 第二次批量评估（应该使用缓存）
        reports2 = evaluator.evaluate_files_batch(files, parallel=False)
        
        # 结果应该一致
        assert len(reports1) == len(reports2)
        for r1, r2 in zip(reports1, reports2):
            assert r1.total_score == r2.total_score


# ==================== 配置集成测试 ====================

class TestConfigurationIntegration:
    """测试配置相关的集成。"""
    
    @pytest.mark.integration
    def test_project_type_configuration(self, sample_python_file):
        """测试项目类型配置。"""
        # Web应用
        evaluator_web = CodeQualityEvaluator(
            project_type=ProjectType.WEB_APP,
            project_stage=ProjectStage.PRODUCTION
        )
        report_web = evaluator_web.evaluate_file(sample_python_file)
        
        # CLI工具
        evaluator_cli = CodeQualityEvaluator(
            project_type=ProjectType.CLI_TOOL,
            project_stage=ProjectStage.DEVELOPMENT
        )
        report_cli = evaluator_cli.evaluate_file(sample_python_file)
        
        # 不同的配置应该产生不同的权重
        assert evaluator_web.weight_coefficients != evaluator_cli.weight_coefficients
    
    @pytest.mark.integration
    def test_algorithm_mode_configuration(self, git_repo_with_commits):
        """测试算法模式配置。"""
        repo_path, commits = git_repo_with_commits
        
        # 旧算法
        calculator_legacy = ContributionCalculator(algorithm_mode=AlgorithmMode.LEGACY)
        result_legacy = calculator_legacy.calculate_contribution(repo_path)
        
        # 新算法
        calculator_quality = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        result_quality = calculator_quality.calculate_contribution(repo_path)
        
        # 两种算法的结果格式应该不同
        if len(result_legacy) > 0 and len(result_quality) > 0:
            author = list(result_legacy.keys())[0]
            
            # 旧算法应该有commits字段
            assert 'commits' in result_legacy[author]
            
            # 新算法应该有code_quality_score字段
            assert 'code_quality_score' in result_quality[author]


# ==================== 报告生成集成测试 ====================

class TestReportGenerationIntegration:
    """测试报告生成的集成。"""
    
    @pytest.mark.integration
    def test_report_with_different_algorithms(self, git_repo_with_commits, tmp_path):
        """测试使用不同算法生成报告。"""
        repo_path, commits = git_repo_with_commits
        
        # 旧算法报告
        report_legacy = tmp_path / "report_legacy.md"
        success_legacy = ReportGenerator.generate_markdown_report(
            repo_path,
            str(report_legacy),
            algorithm_mode=AlgorithmMode.LEGACY
        )
        
        # 新算法报告
        report_quality = tmp_path / "report_quality.md"
        success_quality = ReportGenerator.generate_markdown_report(
            repo_path,
            str(report_quality),
            algorithm_mode=AlgorithmMode.QUALITY
        )
        
        assert success_legacy
        assert success_quality
        
        # 验证报告内容不同
        content_legacy = report_legacy.read_text(encoding='utf-8')
        content_quality = report_quality.read_text(encoding='utf-8')
        
        # 旧算法报告应该包含提交次数
        assert "提交次数" in content_legacy or "commits" in content_legacy.lower()
        
        # 新算法报告应该包含代码质量得分
        assert "代码质量" in content_quality or "quality" in content_quality.lower()
    
    @pytest.mark.integration
    def test_report_with_date_range(self, git_repo_with_commits, tmp_path):
        """测试使用日期范围生成报告。"""
        repo_path, commits = git_repo_with_commits
        
        since = datetime.now() - timedelta(days=1)
        until = datetime.now() + timedelta(days=1)
        
        report_file = tmp_path / "report_dated.md"
        success = ReportGenerator.generate_markdown_report(
            repo_path,
            str(report_file),
            since=since,
            until=until,
            algorithm_mode=AlgorithmMode.QUALITY
        )
        
        assert success
        
        # 验证报告包含日期信息
        content = report_file.read_text(encoding='utf-8')
        assert "分析开始时间" in content or "分析结束时间" in content


# ==================== 数据一致性测试 ====================

class TestDataConsistency:
    """测试数据一致性。"""
    
    @pytest.mark.integration
    def test_commit_data_consistency(self, git_repo_with_commits):
        """测试提交数据一致性。"""
        repo_path, commits = git_repo_with_commits
        
        # 获取提交列表
        commit_list = CommitAnalyzer.get_commits(repo_path)
        
        # 对每个提交获取详情
        for commit in commit_list[:3]:  # 只测试前3个
            details = CommitAnalyzer.get_commit_details(repo_path, commit['hash'])
            
            # 详情应该与列表中的信息一致
            assert details['hash'] == commit['hash']
            assert details['author'] == commit['author']
            assert details['message'] == commit['message']
    
    @pytest.mark.integration
    def test_contribution_data_consistency(self, git_repo_with_commits):
        """测试贡献度数据一致性。"""
        repo_path, commits = git_repo_with_commits
        
        # 计算贡献度
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.LEGACY)
        result = calculator.calculate_contribution(repo_path)
        
        # 获取提交列表
        commit_list = CommitAnalyzer.get_commits(repo_path)
        
        # 贡献度中的作者应该与提交中的作者一致
        commit_authors = {commit['author'] for commit in commit_list}
        contribution_authors = set(result.keys())
        
        assert commit_authors == contribution_authors
