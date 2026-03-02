#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw 主工具
功能：
1. 命令行参数解析
2. Git分析功能集成
3. 工具配置管理
"""

import argparse
import os
import sys
from datetime import datetime, timedelta



# 导入Git分析功能
from .tools.git_analyzer import (
    is_git_repo,
    clone_repo,
    update_repo,
    list_branches,
    switch_branch,
    get_commits,
    get_commit_details,
    calculate_contribution,
    generate_markdown_report
)

class OpenClaw:
    """OpenClaw主类"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog='openclaw',
            description='OpenClaw开发工具集',
            epilog='更多信息请访问: https://openclaw.dev'
        )
        self._setup_arguments()
    
    def _setup_arguments(self):
        """设置命令行参数"""
        # 创建子命令解析器
        subparsers = self.parser.add_subparsers(
            dest='command',
            help='可用命令'
        )
        
        # git-analyzer命令
        git_parser = subparsers.add_parser('git-analyzer', help='Git仓库分析工具')
        git_subparsers = git_parser.add_subparsers(
            dest='git_command',
            help='Git分析命令'
        )
        
        # git status命令
        status_parser = git_subparsers.add_parser('status', help='检查仓库状态')
        status_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        
        # git clone命令
        clone_parser = git_subparsers.add_parser('clone', help='克隆仓库')
        clone_parser.add_argument('url', help='仓库URL')
        clone_parser.add_argument('path', help='本地路径')
        
        # git update命令
        update_parser = git_subparsers.add_parser('update', help='更新仓库')
        update_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        
        # git branches命令
        branches_parser = git_subparsers.add_parser('branches', help='列出分支')
        branches_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        
        # git switch命令
        switch_parser = git_subparsers.add_parser('switch', help='切换分支')
        switch_parser.add_argument('branch', help='分支名称')
        switch_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        
        # git commits命令
        commits_parser = git_subparsers.add_parser('commits', help='查看提交记录')
        commits_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        commits_parser.add_argument('--since', help='开始时间 (YYYY-MM-DD)')
        commits_parser.add_argument('--until', help='结束时间 (YYYY-MM-DD)')
        
        # git analyze命令
        analyze_parser = git_subparsers.add_parser('analyze', help='分析贡献度')
        analyze_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        analyze_parser.add_argument('--since', help='开始时间 (YYYY-MM-DD)')
        analyze_parser.add_argument('--until', help='结束时间 (YYYY-MM-DD)')
        
        # git report命令
        report_parser = git_subparsers.add_parser('report', help='生成分析报告')
        report_parser.add_argument('path', nargs='?', default='.', help='仓库路径')
        report_parser.add_argument('--output', default='git_analysis_report.md', help='输出文件路径')
        report_parser.add_argument('--since', help='开始时间 (YYYY-MM-DD)')
        report_parser.add_argument('--until', help='结束时间 (YYYY-MM-DD)')
    
    def _parse_date(self, date_str):
        """解析日期字符串"""
        if date_str:
            return datetime.strptime(date_str, '%Y-%m-%d')
        return None
    
    def run(self):
        """运行命令"""
        args = self.parser.parse_args()
        
        if not args.command:
            self.parser.print_help()
            return
        
        if args.command == 'git-analyzer':
            self._run_git_command(args)
    
    def _run_git_command(self, args):
        """运行Git相关命令"""
        if not args.git_command:
            print("请指定Git子命令")
            return
        
        # 处理路径参数
        path = os.path.abspath(args.path)
        
        if args.git_command == 'status':
            is_repo = is_git_repo(path)
            print(f"{path} {'是' if is_repo else '不是'} Git仓库")
        
        elif args.git_command == 'clone':
            clone_repo(args.url, path)
        
        elif args.git_command == 'update':
            update_repo(path)
        
        elif args.git_command == 'branches':
            list_branches(path)
        
        elif args.git_command == 'switch':
            switch_branch(path, args.branch)
        
        elif args.git_command == 'commits':
            since = self._parse_date(args.since)
            until = self._parse_date(args.until)
            get_commits(path, since, until)
        
        elif args.git_command == 'analyze':
            since = self._parse_date(args.since)
            until = self._parse_date(args.until)
            calculate_contribution(path, since, until)
        
        elif args.git_command == 'report':
            since = self._parse_date(args.since)
            until = self._parse_date(args.until)
            generate_markdown_report(path, args.output, since, until)

def main():
    """主函数"""
    claw = OpenClaw()
    claw.run()

if __name__ == '__main__':
    main()
