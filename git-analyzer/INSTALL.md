# Git Analyzer Skill 安装指南

## 快速安装

将整个 `git-analyzer` 目录复制到您的技能目录：

```powershell
# Windows PowerShell
Copy-Item -Recurse -Path ".\git-analyzer" -Destination "C:\Users\<用户名>\.trae-cn\skills\"
```

```bash
# Linux/macOS
cp -r ./git-analyzer ~/.trae-cn/skills/
```

## 目录结构

```
git-analyzer/
├── SKILL.md                    # 技能说明文档
├── scripts/                    # Python脚本
│   ├── git_analyzer.py         # 主程序入口
│   ├── code_quality_evaluator.py
│   ├── performance_optimizer.py
│   ├── quality_report_generator.py
│   ├── exceptions.py
│   └── validators.py
└── references/                 # 参考文档
    ├── contribution_analysis.md
    ├── quality_evaluation.md
    ├── report_generation.md
    └── repository_management.md
```

## 依赖安装

```bash
pip install GitPython
```

可选依赖（用于性能监控）：
```bash
pip install psutil
```

## 验证安装

```bash
cd git-analyzer/scripts
python git_analyzer.py --help
```

## 功能概述

- **仓库管理**: 克隆、更新、切换分支
- **提交分析**: 获取提交记录、统计变更
- **贡献度计算**: 多算法模式支持
- **代码质量评估**: 五维度质量分析
- **报告生成**: Markdown格式报告

---
**作者**: WING
