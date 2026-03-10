#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git分析器单元测试

测试仓库管理、提交分析和贡献度计算功能。

WING
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

# 添加scripts目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from git_analyzer import (
    RepositoryManager,
    CommitAnalyzer,
    ContributionCalculator,
    ReportGenerator,
    AlgorithmMode,
    CodeQualityScore,
    CollaborationScore,
    DocumentationScore,
    ContributionScore
)


# ==================== 数据类测试 ====================

class TestAlgorithmMode:
    """测试算法模式枚举。"""
    
    def test_algorithm_mode_values(self):
        """测试算法模式枚举值。"""
        assert AlgorithmMode.LEGACY.value == "legacy"
        assert AlgorithmMode.QUALITY.value == "quality"
    
    def test_algorithm_mode_comparison(self):
        """测试算法模式比较。"""
        assert AlgorithmMode.LEGACY == AlgorithmMode.LEGACY
        assert AlgorithmMode.QUALITY == AlgorithmMode.QUALITY
        assert AlgorithmMode.LEGACY != AlgorithmMode.QUALITY


class TestCodeQualityScore:
    """测试代码质量得分数据类。"""
    
    def test_default_values(self):
        """测试默认值。"""
        score = CodeQualityScore()
        
        assert score.total_score == 0.0
        assert score.max_score == 100.0
        assert score.file_count == 0
        assert score.avg_score == 0.0
        assert score.dimension_scores == {}
    
    def test_custom_values(self):
        """测试自定义值。"""
        score = CodeQualityScore(
            total_score=85.5,
            max_score=100.0,
            file_count=10,
            avg_score=8.55,
            dimension_scores={'readability': 20.0, 'maintainability': 18.0}
        )
        
        assert score.total_score == 85.5
        assert score.file_count == 10
        assert score.avg_score == 8.55
        assert score.dimension_scores['readability'] == 20.0


class TestCollaborationScore:
    """测试协作贡献得分数据类。"""
    
    def test_default_values(self):
        """测试默认值。"""
        score = CollaborationScore()
        
        assert score.code_review_score == 0.0
        assert score.issue_resolution_score == 0.0
        assert score.merge_score == 0.0
        assert score.total_score == 0.0
        assert score.review_count == 0
        assert score.issue_count == 0
        assert score.merge_count == 0


class TestDocumentationScore:
    """测试文档贡献得分数据类。"""
    
    def test_default_values(self):
        """测试默认值。"""
        score = DocumentationScore()
        
        assert score.doc_files_count == 0
        assert score.doc_lines_added == 0
        assert score.doc_lines_deleted == 0
        assert score.doc_quality_score == 0.0
        assert score.completeness_score == 0.0
        assert score.total_score == 0.0


class TestContributionScore:
    """测试综合贡献得分数据类。"""
    
    def test_default_values(self):
        """测试默认值。"""
        score = ContributionScore(author="test_user")
        
        assert score.author == "test_user"
        assert score.total_score == 0.0
        assert score.algorithm_mode == AlgorithmMode.QUALITY
    
    def test_custom_values(self):
        """测试自定义值。"""
        quality_score = CodeQualityScore(total_score=80.0)
        collab_score = CollaborationScore(total_score=20.0)
        doc_score = DocumentationScore(total_score=10.0)
        
        score = ContributionScore(
            author="test_user",
            code_quality_score=quality_score,
            collaboration_score=collab_score,
            documentation_score=doc_score,
            total_score=110.0,
            algorithm_mode=AlgorithmMode.LEGACY
        )
        
        assert score.author == "test_user"
        assert score.total_score == 110.0
        assert score.algorithm_mode == AlgorithmMode.LEGACY


# ==================== RepositoryManager测试 ====================

class TestRepositoryManager:
    """测试仓库管理器。"""
    
    def test_is_git_repo_valid(self, temp_git_repo):
        """测试检测有效的Git仓库。"""
        result = RepositoryManager.is_git_repo(temp_git_repo)
        
        assert result is True
    
    def test_is_git_repo_invalid(self, tmp_path):
        """测试检测无效的Git仓库。"""
        result = RepositoryManager.is_git_repo(str(tmp_path))
        
        assert result is False
    
    def test_is_git_repo_nonexistent(self):
        """测试检测不存在的路径。"""
        result = RepositoryManager.is_git_repo("/nonexistent/path")
        
        assert result is False
    
    def test_is_git_repo_empty_path(self):
        """测试检测空路径。"""
        result = RepositoryManager.is_git_repo("")
        
        assert result is False
    
    def test_is_git_repo_none(self):
        """测试检测None路径。"""
        result = RepositoryManager.is_git_repo(None)
        
        assert result is False
    
    def test_list_branches(self, git_repo_with_branches):
        """测试列出分支。"""
        repo_path, branches = git_repo_with_branches
        
        result = RepositoryManager.list_branches(repo_path)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'main' in result or 'master' in result
    
    def test_switch_branch(self, git_repo_with_branches):
        """测试切换分支。"""
        repo_path, branches = git_repo_with_branches
        
        # 切换到feature-1分支
        result = RepositoryManager.switch_branch(repo_path, 'feature-1')
        
        assert result is True
    
    def test_switch_branch_nonexistent(self, temp_git_repo):
        """测试切换到不存在的分支。"""
        result = RepositoryManager.switch_branch(temp_git_repo, 'nonexistent-branch')
        
        assert result is False


# ==================== CommitAnalyzer测试 ====================

class TestCommitAnalyzer:
    """测试提交分析器。"""
    
    def test_get_commits(self, git_repo_with_commits):
        """测试获取提交记录。"""
        repo_path, commits = git_repo_with_commits
        
        result = CommitAnalyzer.get_commits(repo_path)
        
        assert isinstance(result, list)
        assert len(result) == len(commits)
        
        # 检查提交记录格式
        if len(result) > 0:
            commit = result[0]
            assert 'hash' in commit
            assert 'author' in commit
            assert 'email' in commit
            assert 'date' in commit
            assert 'message' in commit
    
    def test_get_commits_with_date_filter(self, git_repo_with_commits):
        """测试使用日期过滤获取提交记录。"""
        repo_path, commits = git_repo_with_commits
        
        since = datetime.now() - timedelta(days=1)
        until = datetime.now() + timedelta(days=1)
        
        result = CommitAnalyzer.get_commits(repo_path, since=since, until=until)
        
        assert isinstance(result, list)
    
    def test_get_commits_invalid_path(self):
        """测试无效路径获取提交记录。"""
        result = CommitAnalyzer.get_commits("/nonexistent/path")
        
        assert result == []
    
    def test_get_commits_empty_path(self):
        """测试空路径获取提交记录。"""
        result = CommitAnalyzer.get_commits("")
        
        assert result == []
    
    def test_get_commit_details(self, git_repo_with_commits):
        """测试获取提交详情。"""
        repo_path, commits = git_repo_with_commits
        
        # 先获取提交列表
        commit_list = CommitAnalyzer.get_commits(repo_path)
        
        if len(commit_list) > 0:
            commit_hash = commit_list[0]['hash']
            
            result = CommitAnalyzer.get_commit_details(repo_path, commit_hash)
            
            assert isinstance(result, dict)
            assert 'hash' in result
            assert 'author' in result
            assert 'message' in result
            assert result['hash'] == commit_hash


# ==================== ContributionCalculator测试 ====================

class TestContributionCalculator:
    """测试贡献度计算器。"""
    
    def test_initialization_legacy(self):
        """测试旧算法初始化。"""
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.LEGACY)
        
        assert calculator.algorithm_mode == AlgorithmMode.LEGACY
    
    def test_initialization_quality(self):
        """测试新算法初始化。"""
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        
        assert calculator.algorithm_mode == AlgorithmMode.QUALITY
    
    def test_initialization_invalid_team_size(self):
        """测试无效团队规模初始化。"""
        calculator = ContributionCalculator(team_size=-1)
        
        # 应该使用默认值
        assert calculator.team_size == 1
    
    def test_initialization_invalid_batch_size(self):
        """测试无效批次大小初始化。"""
        calculator = ContributionCalculator(batch_size=-1)
        
        # 应该使用默认值
        assert calculator.batch_size == 50
    
    def test_calculate_contribution_legacy(self, git_repo_with_commits):
        """测试旧算法贡献度计算。"""
        repo_path, commits = git_repo_with_commits
        
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.LEGACY)
        result = calculator.calculate_contribution(repo_path)
        
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # 检查结果格式
        for author, stats in result.items():
            assert 'commits' in stats
            assert 'files_changed' in stats
            assert 'total_changes' in stats
            assert 'total_score' in stats
    
    def test_calculate_contribution_quality(self, git_repo_with_commits):
        """测试新算法贡献度计算。"""
        repo_path, commits = git_repo_with_commits
        
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        result = calculator.calculate_contribution(repo_path)
        
        assert isinstance(result, dict)
        assert len(result) > 0
        
        # 检查结果格式
        for author, stats in result.items():
            assert 'code_quality_score' in stats
            assert 'collaboration_score' in stats
            assert 'documentation_score' in stats
            assert 'total_score' in stats
            assert 'algorithm_mode' in stats
            assert stats['algorithm_mode'] == 'quality'
    
    def test_calculate_contribution_empty_repo(self, temp_git_repo):
        """测试空仓库贡献度计算。"""
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.LEGACY)
        result = calculator.calculate_contribution(temp_git_repo)
        
        # 空仓库应该返回空字典
        assert result == {}
    
    def test_calculate_contribution_invalid_path(self):
        """测试无效路径贡献度计算。"""
        calculator = ContributionCalculator()
        result = calculator.calculate_contribution("/nonexistent/path")
        
        assert result == {}
    
    def test_extract_commit_files(self):
        """测试提取提交文件。"""
        calculator = ContributionCalculator()
        
        # 创建模拟提交对象
        mock_commit = Mock()
        mock_parent = Mock()
        mock_commit.parents = [mock_parent]
        mock_commit.hexsha = "abc123"
        
        # 创建模拟diff
        mock_diff1 = Mock()
        mock_diff1.a_path = 'test.py'
        mock_diff1.b_path = 'test.py'
        mock_diff1.deleted_file = False
        
        mock_diff2 = Mock()
        mock_diff2.a_path = 'README.md'
        mock_diff2.b_path = 'README.md'
        mock_diff2.deleted_file = False
        
        mock_diff3 = Mock()
        mock_diff3.a_path = 'config.json'
        mock_diff3.b_path = 'config.json'
        mock_diff3.deleted_file = False
        
        mock_parent.diff.return_value = [mock_diff1, mock_diff2, mock_diff3]
        
        # 测试文件提取
        code_files, doc_files, config_files = calculator._extract_commit_files(mock_commit)
        
        assert len(code_files) == 1
        assert len(doc_files) == 1
        assert len(config_files) == 1
        assert 'test.py' in code_files
        assert 'README.md' in doc_files
        assert 'config.json' in config_files
    
    def test_analyze_collaboration(self):
        """测试协作贡献分析。"""
        calculator = ContributionCalculator()
        
        # 测试代码审查提交
        mock_commit = Mock()
        mock_commit.message = "review: approved the pull request"
        mock_commit.hexsha = "abc123"
        
        review_score, issue_score, merge_score = calculator._analyze_collaboration(mock_commit)
        assert review_score > 0
        
        # 测试问题解决提交
        mock_commit.message = "fix: resolve issue #123"
        review_score, issue_score, merge_score = calculator._analyze_collaboration(mock_commit)
        assert issue_score > 0
        
        # 测试合并提交
        mock_commit.message = "merge pull request #456"
        review_score, issue_score, merge_score = calculator._analyze_collaboration(mock_commit)
        assert merge_score > 0
    
    def test_calculate_documentation_score(self):
        """测试文档贡献得分计算。"""
        calculator = ContributionCalculator()
        
        # 测试新增文档
        score = calculator._calculate_documentation_score(
            doc_files_count=5,
            doc_lines_added=100,
            doc_lines_deleted=20
        )
        
        assert score.doc_files_count == 5
        assert score.doc_lines_added == 100
        assert score.doc_lines_deleted == 20
        assert score.total_score > 0
        
        # 测试零文档
        score = calculator._calculate_documentation_score(0, 0, 0)
        assert score.total_score == 0.0
    
    def test_quality_weights(self):
        """测试权重配置。"""
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        
        assert calculator.QUALITY_WEIGHT == 0.6
        assert calculator.COLLABORATION_WEIGHT == 0.25
        assert calculator.DOCUMENTATION_WEIGHT == 0.15
        
        # 权重总和应该为1.0
        total_weight = (
            calculator.QUALITY_WEIGHT +
            calculator.COLLABORATION_WEIGHT +
            calculator.DOCUMENTATION_WEIGHT
        )
        assert abs(total_weight - 1.0) < 0.01


# ==================== ReportGenerator测试 ====================

class TestReportGenerator:
    """测试报告生成器。"""
    
    def test_generate_markdown_report_legacy(self, git_repo_with_commits, tmp_path):
        """测试生成旧算法Markdown报告。"""
        repo_path, commits = git_repo_with_commits
        output_file = tmp_path / "report_legacy.md"
        
        result = ReportGenerator.generate_markdown_report(
            repo_path,
            str(output_file),
            algorithm_mode=AlgorithmMode.LEGACY
        )
        
        assert result is True
        assert output_file.exists()
        
        # 检查报告内容
        content = output_file.read_text(encoding='utf-8')
        assert "Git仓库分析报告" in content
        assert "贡献度排名" in content
    
    def test_generate_markdown_report_quality(self, git_repo_with_commits, tmp_path):
        """测试生成新算法Markdown报告。"""
        repo_path, commits = git_repo_with_commits
        output_file = tmp_path / "report_quality.md"
        
        result = ReportGenerator.generate_markdown_report(
            repo_path,
            str(output_file),
            algorithm_mode=AlgorithmMode.QUALITY
        )
        
        assert result is True
        assert output_file.exists()
        
        # 检查报告内容
        content = output_file.read_text(encoding='utf-8')
        assert "Git仓库分析报告" in content
        assert "贡献度排名" in content
    
    def test_generate_report_invalid_repo(self, tmp_path):
        """测试无效仓库生成报告。"""
        output_file = tmp_path / "report.md"
        
        result = ReportGenerator.generate_markdown_report(
            "/nonexistent/path",
            str(output_file)
        )
        
        assert result is False
    
    def test_generate_report_with_date_filter(self, git_repo_with_commits, tmp_path):
        """测试使用日期过滤生成报告。"""
        repo_path, commits = git_repo_with_commits
        output_file = tmp_path / "report_filtered.md"
        
        since = datetime.now() - timedelta(days=1)
        until = datetime.now() + timedelta(days=1)
        
        result = ReportGenerator.generate_markdown_report(
            repo_path,
            str(output_file),
            since=since,
            until=until
        )
        
        assert result is True
        assert output_file.exists()


# ==================== 边界条件测试 ====================

class TestEdgeCases:
    """测试边界条件。"""
    
    def test_empty_commit_message(self):
        """测试空提交消息。"""
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        
        mock_commit = Mock()
        mock_commit.message = ""
        mock_commit.hexsha = "abc123"
        
        review_score, issue_score, merge_score = calculator._analyze_collaboration(mock_commit)
        
        # 空消息应该得0分
        assert review_score == 0.0
        assert issue_score == 0.0
        assert merge_score == 0.0
    
    def test_no_parent_commit(self):
        """测试无父提交的情况。"""
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        
        mock_commit = Mock()
        mock_commit.parents = []
        mock_commit.hexsha = "abc123"
        
        # 测试文件提取
        code_files, doc_files, config_files = calculator._extract_commit_files(mock_commit)
        assert len(code_files) == 0
        assert len(doc_files) == 0
        assert len(config_files) == 0
    
    def test_deleted_files(self):
        """测试删除文件的处理。"""
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        
        mock_commit = Mock()
        mock_parent = Mock()
        mock_commit.parents = [mock_parent]
        mock_commit.hexsha = "abc123"
        
        # 创建删除文件的diff
        mock_diff = Mock()
        mock_diff.a_path = 'deleted.py'
        mock_diff.b_path = 'deleted.py'
        mock_diff.deleted_file = True
        
        mock_parent.diff.return_value = [mock_diff]
        
        # 测试文件提取
        code_files, doc_files, config_files = calculator._extract_commit_files(mock_commit)
        
        # 删除的文件不应该被包含
        assert len(code_files) == 0
    
    def test_large_documentation_score(self):
        """测试大文档贡献（验证上限）。"""
        calculator = ContributionCalculator(algorithm_mode=AlgorithmMode.QUALITY)
        
        score = calculator._calculate_documentation_score(
            doc_files_count=100,
            doc_lines_added=10000,
            doc_lines_deleted=0
        )
        
        # 验证得分有上限
        assert score.total_score > 0
        # 完整性得分应该有上限
        assert score.completeness_score <= 10.0
    
    def test_whitespace_parameters(self):
        """测试空白字符参数。"""
        result = RepositoryManager.is_git_repo("   ")
        assert result is False
        
        result = RepositoryManager.is_git_repo("\t\n")
        assert result is False


# ==================== 性能测试 ====================

class TestPerformance:
    """测试性能相关功能。"""
    
    @pytest.mark.slow
    def test_large_repo_performance(self, performance_test_repo):
        """测试大型仓库性能。"""
        import time
        
        calculator = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True,
            batch_size=50
        )
        
        start_time = time.time()
        result = calculator.calculate_contribution(performance_test_repo)
        elapsed_time = time.time() - start_time
        
        # 应该在合理时间内完成
        assert elapsed_time < 60  # 60秒内
        assert isinstance(result, dict)
    
    @pytest.mark.slow
    def test_parallel_vs_serial(self, git_repo_with_commits):
        """测试并行vs串行性能。"""
        import time
        
        repo_path, commits = git_repo_with_commits
        
        # 串行处理
        calculator_serial = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=False
        )
        start_time = time.time()
        result_serial = calculator_serial.calculate_contribution(repo_path)
        serial_time = time.time() - start_time
        
        # 并行处理
        calculator_parallel = ContributionCalculator(
            algorithm_mode=AlgorithmMode.QUALITY,
            enable_parallel=True
        )
        start_time = time.time()
        result_parallel = calculator_parallel.calculate_contribution(repo_path)
        parallel_time = time.time() - start_time
        
        # 结果应该一致
        assert len(result_serial) == len(result_parallel)
