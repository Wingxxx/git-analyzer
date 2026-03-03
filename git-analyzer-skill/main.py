#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git仓库分析工具 - OpenClaw Skill
功能：
1. 本地仓库检测
2. Git仓库克隆
3. 仓库更新
4. 提交记录分析
   - 按时间范围过滤提交
   - 分支检测和切换
   - 提取提交详细信息
5. 贡献度计算
6. 报告生成

此脚本作为OpenClaw skill运行，提供Git仓库分析功能。
"""

# OpenClaw Skill入口点
def skill_entrypoint(args):
    """
    OpenClaw skill入口函数
    :param args: 命令行参数
    :return: 执行结果
    """
    import sys
    sys.argv = ['git-analyzer'] + args.split()
    main()
    return "Git-Analyzer命令执行完成"

import os
import git
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError
from datetime import datetime, timedelta
import argparse

def is_git_repo(path):
    """
    检测本地路径是否为Git仓库
    :param path: 本地路径
    :return: bool - 是否为Git仓库
    """
    try:
        Repo(path)
        return True
    except InvalidGitRepositoryError:
        return False
    except Exception:
        return False

def clone_repo(repo_url, local_path):
    """
    克隆Git仓库
    :param repo_url: 仓库URL
    :param local_path: 本地路径
    :return: bool - 克隆是否成功
    """
    try:
        print(f"正在克隆仓库: {repo_url} 到 {local_path}")
        Repo.clone_from(repo_url, local_path)
        print("克隆成功！")
        return True
    except GitCommandError as e:
        print(f"克隆失败: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

def update_repo(local_path):
    """
    更新本地Git仓库
    :param local_path: 本地仓库路径
    :return: bool - 更新是否成功
    """
    try:
        if not is_git_repo(local_path):
            print(f"错误: {local_path} 不是Git仓库")
            return False
        
        repo = Repo(local_path)
        print(f"正在更新仓库: {local_path}")
        
        # 获取当前分支
        current_branch = repo.active_branch
        print(f"当前分支: {current_branch.name}")
        
        # 拉取最新代码
        origin = repo.remotes.origin
        origin.pull()
        
        print("更新成功！")
        return True
    except GitCommandError as e:
        print(f"更新失败: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

def list_branches(local_path):
    """
    列出仓库所有分支
    :param local_path: 本地仓库路径
    :return: list - 分支列表
    """
    try:
        if not is_git_repo(local_path):
            print(f"错误: {local_path} 不是Git仓库")
            return []
        
        repo = Repo(local_path)
        branches = [branch.name for branch in repo.branches]
        print("分支列表:")
        for branch in branches:
            print(f"  - {branch}")
        return branches
    except Exception as e:
        print(f"发生错误: {e}")
        return []

def switch_branch(local_path, branch_name):
    """
    切换分支
    :param local_path: 本地仓库路径
    :param branch_name: 分支名称
    :return: bool - 切换是否成功
    """
    try:
        if not is_git_repo(local_path):
            print(f"错误: {local_path} 不是Git仓库")
            return False
        
        repo = Repo(local_path)
        print(f"正在切换到分支: {branch_name}")
        repo.git.checkout(branch_name)
        print(f"成功切换到分支: {branch_name}")
        return True
    except GitCommandError as e:
        print(f"切换分支失败: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False

def get_commits(local_path, since=None, until=None):
    """
    获取提交记录，支持按时间范围过滤
    :param local_path: 本地仓库路径
    :param since: 开始时间（datetime对象）
    :param until: 结束时间（datetime对象）
    :return: list - 提交记录列表
    """
    try:
        if not is_git_repo(local_path):
            print(f"错误: {local_path} 不是Git仓库")
            return []
        
        repo = Repo(local_path)
        commits = []
        
        # 构建查询参数
        kwargs = {}
        if since:
            kwargs['since'] = since
        if until:
            kwargs['until'] = until
        
        # 获取提交记录
        for commit in repo.iter_commits(**kwargs):
            commits.append({
                'hash': commit.hexsha,
                'author': commit.author.name,
                'email': commit.author.email,
                'date': commit.committed_datetime,
                'message': commit.message.strip()
            })
        
        print(f"获取到 {len(commits)} 条提交记录")
        return commits
    except Exception as e:
        print(f"发生错误: {e}")
        return []

def get_commit_details(local_path, commit_hash):
    """
    获取提交详细信息
    :param local_path: 本地仓库路径
    :param commit_hash: 提交哈希值
    :return: dict - 提交详细信息
    """
    try:
        if not is_git_repo(local_path):
            print(f"错误: {local_path} 不是Git仓库")
            return {}
        
        repo = Repo(local_path)
        commit = repo.commit(commit_hash)
        
        # 获取文件变更
        changed_files = []
        if commit.parents:
            parent = commit.parents[0]
            diff = parent.diff(commit)
            for item in diff:
                changed_files.append({
                    'path': item.a_path or item.b_path,
                    'change_type': 'A' if item.new_file else 'D' if item.deleted_file else 'M'
                })
        
        details = {
            'hash': commit.hexsha,
            'author': commit.author.name,
            'email': commit.author.email,
            'date': commit.committed_datetime,
            'message': commit.message.strip(),
            'changed_files': changed_files,
            'stats': commit.stats.total
        }
        
        print(f"提交详情: {commit.hexsha}")
        print(f"作者: {details['author']} <{details['email']}>")
        print(f"日期: {details['date']}")
        print(f"提交信息: {details['message']}")
        print(f"文件变更: {len(details['changed_files'])} 个文件")
        print(f"统计信息: {details['stats']}")
        
        return details
    except GitCommandError as e:
        print(f"获取提交详情失败: {e}")
        return {}
    except Exception as e:
        print(f"发生错误: {e}")
        return {}

def calculate_contribution(local_path, since=None, until=None):
    """
    计算贡献度
    :param local_path: 本地仓库路径
    :param since: 开始时间（datetime对象）
    :param until: 结束时间（datetime对象）
    :return: dict - 贡献度分析结果
    """
    try:
        if not is_git_repo(local_path):
            print(f"错误: {local_path} 不是Git仓库")
            return {}
        
        repo = Repo(local_path)
        author_stats = {}
        
        # 构建查询参数
        kwargs = {}
        if since:
            kwargs['since'] = since
        if until:
            kwargs['until'] = until
        
        # 遍历提交记录
        for commit in repo.iter_commits(**kwargs):
            author = commit.author.name
            
            # 初始化作者统计信息
            if author not in author_stats:
                author_stats[author] = {
                    'commits': 0,
                    'files_changed': 0,
                    'insertions': 0,
                    'deletions': 0,
                    'total_changes': 0,
                    'value_score': 0
                }
            
            # 统计提交次数
            author_stats[author]['commits'] += 1
            
            # 统计文件变更和代码行数变更
            if commit.parents:
                parent = commit.parents[0]
                diff = parent.diff(commit)
                
                # 统计文件变更数
                files_changed = len(diff)
                author_stats[author]['files_changed'] += files_changed
                
                # 统计代码行数变更
                insertions = 0
                deletions = 0
                for item in diff:
                    # 尝试获取统计信息
                    try:
                        stats = item.diff.split('\n')
                        for line in stats:
                            if line.startswith('+') and not line.startswith('+++'):
                                insertions += 1
                            elif line.startswith('-') and not line.startswith('---'):
                                deletions += 1
                    except:
                        pass
                
                author_stats[author]['insertions'] += insertions
                author_stats[author]['deletions'] += deletions
                author_stats[author]['total_changes'] += insertions + deletions
            
            # 评估提交价值
            value_score = 0
            
            # 基于提交消息质量的评估
            message = commit.message.strip()
            if len(message) > 10:
                value_score += 1
            if any(keyword in message.lower() for keyword in ['fix', 'bug', 'feature', 'improve', 'optimize']):
                value_score += 1
            
            # 基于变更大小的评估
            if author_stats[author]['total_changes'] > 100:
                value_score += 2
            elif author_stats[author]['total_changes'] > 10:
                value_score += 1
            
            # 基于文件类型的评估（简单实现）
            if commit.parents:
                parent = commit.parents[0]
                diff = parent.diff(commit)
                for item in diff:
                    path = item.a_path or item.b_path
                    if path:
                        if any(ext in path for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c']):
                            value_score += 1
                        elif any(ext in path for ext in ['.md', '.txt', '.json', '.xml']):
                            value_score += 0.5
            
            author_stats[author]['value_score'] += value_score
        
        # 计算最终贡献度分数
        for author, stats in author_stats.items():
            # 综合得分计算
            commits_score = stats['commits'] * 2
            files_score = stats['files_changed'] * 1.5
            changes_score = stats['total_changes'] * 0.5
            value_score = stats['value_score'] * 3
            
            total_score = commits_score + files_score + changes_score + value_score
            author_stats[author]['total_score'] = total_score
        
        # 按总得分排序
        sorted_authors = sorted(author_stats.items(), key=lambda x: x[1]['total_score'], reverse=True)
        
        # 打印贡献度分析结果
        print("\n贡献度分析结果:")
        print("=" * 80)
        print(f"{'作者':<20} {'提交次数':<10} {'文件变更':<10} {'代码变更':<10} {'价值得分':<10} {'总得分':<10}")
        print("-" * 80)
        
        for author, stats in sorted_authors:
            print(f"{author:<20} {stats['commits']:<10} {stats['files_changed']:<10} {stats['total_changes']:<10} {stats['value_score']:<10.1f} {stats['total_score']:<10.1f}")
        
        print("=" * 80)
        
        return author_stats
    except Exception as e:
        print(f"发生错误: {e}")
        return {}

def generate_markdown_report(local_path, output_file="git_analysis_report.md", since=None, until=None):
    """
    生成Markdown格式的分析报告
    :param local_path: 本地仓库路径
    :param output_file: 输出文件路径
    :param since: 开始时间（datetime对象）
    :param until: 结束时间（datetime对象）
    :return: bool - 报告生成是否成功
    """
    try:
        if not is_git_repo(local_path):
            print(f"错误: {local_path} 不是Git仓库")
            return False
        
        # 获取数据
        contribution_data = calculate_contribution(local_path, since, until)
        commits = get_commits(local_path, since, until)
        
        # 生成Markdown内容
        markdown_content = "# Git仓库分析报告\n\n"
        
        # 添加报告生成时间
        markdown_content += f"## 报告信息\n"
        markdown_content += f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        markdown_content += f"- 分析仓库: {local_path}\n"
        if since:
            markdown_content += f"- 分析开始时间: {since.strftime('%Y-%m-%d')}\n"
        if until:
            markdown_content += f"- 分析结束时间: {until.strftime('%Y-%m-%d')}\n"
        markdown_content += "\n"
        
        # 添加贡献度排名
        markdown_content += "## 贡献度排名\n"
        if contribution_data:
            # 按总得分排序
            sorted_authors = sorted(contribution_data.items(), key=lambda x: x[1]['total_score'], reverse=True)
            markdown_content += "| 排名 | 作者 | 提交次数 | 文件变更 | 代码变更 | 价值得分 | 总得分 |\n"
            markdown_content += "|------|------|----------|----------|----------|----------|--------|\n"
            
            for i, (author, stats) in enumerate(sorted_authors, 1):
                markdown_content += f"| {i} | {author} | {stats['commits']} | {stats['files_changed']} | {stats['total_changes']} | {stats['value_score']:.1f} | {stats['total_score']:.1f} |\n"
        else:
            markdown_content += "暂无贡献数据\n"
        markdown_content += "\n"
        
        # 添加最近提交记录
        markdown_content += "## 最近提交记录\n"
        if commits:
            for i, commit in enumerate(commits[:10], 1):  # 显示最近10条提交
                markdown_content += f"### {i}. {commit['hash'][:7]}\n"
                markdown_content += f"- 作者: {commit['author']} <{commit['email']}>\n"
                markdown_content += f"- 日期: {commit['date'].strftime('%Y-%m-%d %H:%M:%S')}\n"
                markdown_content += f"- 提交信息: {commit['message']}\n\n"
        else:
            markdown_content += "暂无提交记录\n"
        markdown_content += "\n"
        
        # 添加团队整体分析
        markdown_content += "## 团队整体分析\n"
        if contribution_data:
            total_commits = sum(stats['commits'] for stats in contribution_data.values())
            total_files_changed = sum(stats['files_changed'] for stats in contribution_data.values())
            total_changes = sum(stats['total_changes'] for stats in contribution_data.values())
            total_authors = len(contribution_data)
            
            markdown_content += f"- 参与开发者: {total_authors} 人\n"
            markdown_content += f"- 总提交次数: {total_commits} 次\n"
            markdown_content += f"- 总文件变更: {total_files_changed} 个\n"
            markdown_content += f"- 总代码变更: {total_changes} 行\n\n"
            
            # 分析最活跃的开发者
            if sorted_authors:
                most_active = sorted_authors[0]
                markdown_content += f"### 最活跃开发者\n"
                markdown_content += f"- 姓名: {most_active[0]}\n"
                markdown_content += f"- 提交次数: {most_active[1]['commits']} 次\n"
                markdown_content += f"- 贡献度: {most_active[1]['total_score']:.1f} 分\n"
        else:
            markdown_content += "暂无团队分析数据\n"
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"报告生成成功！文件保存至: {output_file}")
        return True
    except Exception as e:
        print(f"生成报告失败: {e}")
        return False

def parse_date(date_str):
    """
    解析日期字符串
    :param date_str: 日期字符串，格式为YYYY-MM-DD
    :return: datetime对象或None
    """
    if date_str:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            print(f"日期格式错误: {date_str}，应为YYYY-MM-DD")
            return None
    return None

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(
        prog='git-analyzer',
        description='Git仓库分析工具',
        epilog='更多信息请访问: https://openclaw.dev'
    )
    
    # 创建子命令解析器
    subparsers = parser.add_subparsers(
        dest='command',
        help='可用命令'
    )
    
    # status命令
    status_parser = subparsers.add_parser('status', help='检查仓库状态')
    status_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
    
    # clone命令
    clone_parser = subparsers.add_parser('clone', help='克隆仓库')
    clone_parser.add_argument('url', help='仓库URL')
    clone_parser.add_argument('path', help='本地路径')
    
    # update命令
    update_parser = subparsers.add_parser('update', help='更新仓库')
    update_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
    
    # branches命令
    branches_parser = subparsers.add_parser('branches', help='列出分支')
    branches_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
    
    # switch命令
    switch_parser = subparsers.add_parser('switch', help='切换分支')
    switch_parser.add_argument('branch', help='分支名称')
    switch_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
    
    # commits命令
    commits_parser = subparsers.add_parser('commits', help='查看提交记录')
    commits_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
    commits_parser.add_argument('--since', help='开始时间 (YYYY-MM-DD)')
    commits_parser.add_argument('--until', help='结束时间 (YYYY-MM-DD)')
    
    # analyze命令
    analyze_parser = subparsers.add_parser('analyze', help='分析贡献度')
    analyze_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
    analyze_parser.add_argument('--since', help='开始时间 (YYYY-MM-DD)')
    analyze_parser.add_argument('--until', help='结束时间 (YYYY-MM-DD)')
    
    # report命令
    report_parser = subparsers.add_parser('report', help='生成分析报告')
    report_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
    report_parser.add_argument('--output', default='git_analysis_report.md', help='输出文件路径')
    report_parser.add_argument('--since', help='开始时间 (YYYY-MM-DD)')
    report_parser.add_argument('--until', help='结束时间 (YYYY-MM-DD)')
    
    # 解析参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 处理路径参数
    path = os.path.abspath(args.path)
    
    if args.command == 'status':
        is_repo = is_git_repo(path)
        print(f"{path} {'是' if is_repo else '不是'} Git仓库")
    
    elif args.command == 'clone':
        clone_repo(args.url, path)
    
    elif args.command == 'update':
        update_repo(path)
    
    elif args.command == 'branches':
        list_branches(path)
    
    elif args.command == 'switch':
        switch_branch(path, args.branch)
    
    elif args.command == 'commits':
        since = parse_date(args.since)
        until = parse_date(args.until)
        get_commits(path, since, until)
    
    elif args.command == 'analyze':
        since = parse_date(args.since)
        until = parse_date(args.until)
        calculate_contribution(path, since, until)
    
    elif args.command == 'report':
        since = parse_date(args.since)
        until = parse_date(args.until)
        generate_markdown_report(path, args.output, since, until)

if __name__ == '__main__':
    main()
