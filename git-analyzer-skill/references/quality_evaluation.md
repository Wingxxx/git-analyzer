# 代码质量评估指南

本文档详细介绍Git-Analyzer的代码质量评估体系，包括五维度评估标准、评分机制和使用方法。

## 目录

1. [概述](#概述)
2. [五维度评估体系](#五维度评估体系)
3. [评分标准详解](#评分标准详解)
4. [权重系数配置](#权重系数配置)
5. [使用方法](#使用方法)
6. [最佳实践](#最佳实践)
7. [常见问题解答](#常见问题解答)

---

## 概述

### 功能说明

代码质量评估器通过五维度评估体系，对代码进行全面的质量分析，生成客观的质量评分和改进建议。

### 评估维度

| 维度 | 满分 | 权重 | 说明 |
|------|------|------|------|
| 可读性 | 25分 | 25% | 代码的可理解程度 |
| 可维护性 | 25分 | 25% | 代码的维护难易程度 |
| 性能效率 | 20分 | 20% | 代码的运行效率 |
| 错误处理 | 15分 | 15% | 异常处理和边界检查 |
| 安全性 | 15分 | 15% | 安全编码实践 |

### 质量等级

| 等级 | 分数范围 | 说明 |
|------|---------|------|
| 优秀 | >= 80分 | 高质量代码，值得推广 |
| 良好 | >= 60分 | 合格代码，有改进空间 |
| 合格 | >= 40分 | 基本可用，需要优化 |
| 不合格 | < 40分 | 质量较差，需要重构 |

---

## 五维度评估体系

### 1. 可读性评估（0-25分）

可读性评估关注代码的可理解程度，包括命名规范、注释质量、代码格式等方面。

#### 1.1 命名规范（0-5分）

**评估内容**：
- 变量名是否符合PEP 8规范（小写+下划线）
- 函数名是否符合PEP 8规范（小写+下划线）
- 类名是否符合PEP 8规范（大驼峰）
- 命名是否具有描述性

**评分标准**：
| 得分 | 标准 |
|------|------|
| 5分 | 所有命名符合规范，具有良好描述性 |
| 4分 | 大部分命名符合规范 |
| 3分 | 存在一些命名不规范 |
| 2分 | 较多命名不规范 |
| 1分 | 命名严重不规范 |
| 0分 | 使用无意义命名（如a, b, x） |

**最佳实践**：
```python
# 好的命名
user_name = "John"
calculate_total_price = lambda items: sum(item.price for item in items)
class UserManager:
    pass

# 不好的命名
n = "John"
calc = lambda x: sum(x)
class manager:
    pass
```

#### 1.2 注释质量（0-5分）

**评估内容**：
- 注释密度（注释行数/总行数）
- 注释位置（行首注释、行内注释）
- 注释内容质量

**评分标准**：
| 注释密度 | 得分 |
|---------|------|
| >= 15% | 5分 |
| >= 10% | 4分 |
| >= 5% | 3分 |
| >= 2% | 2分 |
| > 0% | 1分 |
| 0% | 0分 |

**最佳实践**：
```python
# 好的注释
# 计算用户购物车的总价，包括折扣和税费
def calculate_total(cart_items, discount_rate=0.0, tax_rate=0.1):
    subtotal = sum(item.price * item.quantity for item in cart_items)
    discount = subtotal * discount_rate  # 应用折扣
    tax = (subtotal - discount) * tax_rate  # 计算税费
    return subtotal - discount + tax
```

#### 1.3 代码格式（0-5分）

**评估内容**：
- 缩进一致性（推荐4空格）
- 行长度（推荐不超过100字符）
- 空行使用（避免过多连续空行）

**评分标准**：
- 基础分：5分
- 行长度超过100字符：每行扣0.1分（最多扣2分）
- 缩进不一致：每处扣0.1分（最多扣1.5分）
- 连续空行超过2行：每超过一行扣0.5分（最多扣1.5分）

**最佳实践**：
```python
# 好的格式
def process_data(data):
    """处理数据并返回结果。"""
    if not data:
        return None
    
    result = []
    for item in data:
        processed = transform(item)
        result.append(processed)
    
    return result


# 不好的格式
def process_data(data):
    """处理数据并返回结果。"""
    if not data:
        return None
    result = []
    for item in data:
        processed = transform(item)
        result.append(processed)
    return result
```

#### 1.4 代码复杂度（0-5分）

**评估内容**：
- 函数长度（推荐不超过50行）
- 嵌套深度（推荐不超过4层）
- 圈复杂度（推荐不超过10）

**评分标准**：
- 基础分：5分
- 函数长度超过50行：每超过20行扣1分
- 嵌套深度超过4层：每超过1层扣0.5分
- 圈复杂度超过10：每超过5扣1分

**最佳实践**：
```python
# 好的复杂度
def validate_user(user):
    """验证用户数据。"""
    if not user:
        return False
    
    if not user.email:
        return False
    
    if not user.password:
        return False
    
    return True


# 不好的复杂度（嵌套过深）
def validate_user(user):
    if user:
        if user.email:
            if user.password:
                if len(user.password) >= 8:
                    if has_uppercase(user.password):
                        if has_lowercase(user.password):
                            return True
    return False
```

#### 1.5 文档字符串（0-5分）

**评估内容**：
- 模块文档字符串
- 类文档字符串
- 函数文档字符串

**评分标准**：
| 文档覆盖率 | 得分 |
|-----------|------|
| >= 80% | 5分 |
| >= 60% | 4分 |
| >= 40% | 3分 |
| >= 20% | 2分 |
| > 0% | 1分 |
| 0% | 0分 |

**最佳实践**：
```python
"""
用户管理模块。

提供用户注册、登录、权限管理等功能。
"""

class UserManager:
    """用户管理器，处理用户相关操作。"""
    
    def create_user(self, username, email, password):
        """
        创建新用户。
        
        Args:
            username: 用户名，长度3-20字符
            email: 邮箱地址
            password: 密码，长度至少8字符
        
        Returns:
            User: 新创建的用户对象
        
        Raises:
            ValueError: 参数无效时抛出
        """
        pass
```

---

### 2. 可维护性评估（0-25分）

可维护性评估关注代码的维护难易程度，包括模块化程度、代码重复度、依赖管理等方面。

#### 2.1 模块化程度（0-5分）

**评估内容**：
- 函数和类的组织
- 平均函数长度
- 功能划分合理性

**评分标准**：
| 平均函数长度 | 得分 |
|-------------|------|
| 10-30行 | 5分 |
| 5-10行或30-50行 | 4分 |
| 其他 | 3分 |
| 无函数或类 | 2分 |

**最佳实践**：
```python
# 好的模块化
class DataProcessor:
    """数据处理器。"""
    
    def load_data(self, file_path):
        """加载数据。"""
        pass
    
    def validate_data(self, data):
        """验证数据。"""
        pass
    
    def transform_data(self, data):
        """转换数据。"""
        pass
    
    def save_data(self, data, output_path):
        """保存数据。"""
        pass
```

#### 2.2 代码重复度（0-5分）

**评估内容**：
- 连续相同代码行
- 重复代码块

**评分标准**：
| 重复率 | 得分 |
|-------|------|
| < 5% | 5分 |
| < 10% | 4分 |
| < 15% | 3分 |
| < 20% | 2分 |
| >= 20% | 1分 |

**最佳实践**：
```python
# 不好：重复代码
def calculate_circle_area(radius):
    pi = 3.14159
    return pi * radius * radius

def calculate_cylinder_volume(radius, height):
    pi = 3.14159
    return pi * radius * radius * height


# 好：提取公共逻辑
PI = 3.14159

def calculate_circle_area(radius):
    return PI * radius * radius

def calculate_cylinder_volume(radius, height):
    return calculate_circle_area(radius) * height
```

#### 2.3 依赖管理（0-5分）

**评估内容**：
- 导入语句数量
- 导入语句组织

**评分标准**：
| 导入数量 | 得分 |
|---------|------|
| <= 10 | 5分 |
| <= 20 | 4分 |
| <= 30 | 3分 |
| > 30 | 2分 |

**最佳实践**：
```python
# 好的导入组织
# 标准库
import os
import sys
from datetime import datetime

# 第三方库
import numpy as np
import pandas as pd

# 本地模块
from utils import helper
from config import settings
```

#### 2.4 函数长度（0-5分）

**评估内容**：
- 函数行数统计
- 过长函数识别

**评分标准**：
| 违规次数 | 得分 |
|---------|------|
| 0次 | 5分 |
| <= 2次 | 4分 |
| <= 4次 | 3分 |
| > 4次 | 2分 |

**违规定义**：函数超过50行记1次，超过100行记2次

**最佳实践**：
```python
# 好：函数职责单一
def process_order(order):
    """处理订单。"""
    validate_order(order)
    calculate_total(order)
    apply_discount(order)
    save_order(order)
    send_confirmation(order)


# 不好：函数过长
def process_order(order):
    # 100多行代码...
    pass
```

#### 2.5 类设计（0-5分）

**评估内容**：
- 类的方法数量
- 类的属性数量
- 单一职责原则

**评分标准**：
- 基础分：5分
- 方法数量超过20：扣0.5分
- 属性数量超过15：扣0.3分

**最佳实践**：
```python
# 好：单一职责
class UserValidator:
    """用户验证器。"""
    
    def validate_email(self, email):
        pass
    
    def validate_password(self, password):
        pass


class UserRepository:
    """用户存储库。"""
    
    def save(self, user):
        pass
    
    def find_by_id(self, user_id):
        pass
```

---

### 3. 性能效率评估（0-20分）

性能效率评估关注代码的运行效率，包括算法复杂度、资源使用、数据结构选择等方面。

#### 3.1 算法复杂度（0-5分）

**评估内容**：
- 嵌套循环检测
- 时间复杂度分析

**评分标准**：
- 基础分：5分
- 每个嵌套循环扣0.5分（最多扣3分）

**最佳实践**：
```python
# 不好：O(n^2)复杂度
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates


# 好：O(n)复杂度
def find_duplicates(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)
    return list(duplicates)
```

#### 3.2 资源使用（0-5分）

**评估内容**：
- 文件句柄管理
- 数据库连接管理
- 资源释放

**评分标准**：
- 使用with语句管理资源：5分
- 有open调用但未使用with：3分
- 无资源操作：5分

**最佳实践**：
```python
# 好：使用with语句
def read_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()


# 不好：未使用with语句
def read_file(file_path):
    f = open(file_path, 'r')
    content = f.read()
    f.close()  # 可能不会执行
    return content
```

#### 3.3 数据结构选择（0-5分）

**评估内容**：
- 数据结构合理性
- 查找效率

**最佳实践**：
```python
# 不好：使用列表进行成员检查
def is_valid_user(user_id, valid_users):
    return user_id in valid_users  # O(n)复杂度


# 好：使用集合进行成员检查
def is_valid_user(user_id, valid_users):
    valid_set = set(valid_users)
    return user_id in valid_set  # O(1)复杂度
```

#### 3.4 循环优化（0-5分）

**评估内容**：
- 循环内重复计算
- 循环内函数调用

**最佳实践**：
```python
# 不好：循环内重复计算
def process_items(items):
    results = []
    for item in items:
        # 每次循环都重新计算
        threshold = calculate_threshold()
        if item.value > threshold:
            results.append(item)
    return results


# 好：将计算移出循环
def process_items(items):
    threshold = calculate_threshold()  # 只计算一次
    results = []
    for item in items:
        if item.value > threshold:
            results.append(item)
    return results
```

---

### 4. 错误处理评估（0-15分）

错误处理评估关注代码的健壮性，包括异常捕获、错误日志、边界检查等方面。

#### 4.1 异常捕获（0-5分）

**评估内容**：
- try-except块使用
- 危险操作识别

**评分标准**：
| 情况 | 得分 |
|------|------|
| 有危险操作且有try块 | 5分 |
| 无危险操作 | 4分 |
| 有危险操作但无try块 | 2分 |

**危险操作**：open, int, float, eval, exec等

**最佳实践**：
```python
# 好：完善的异常处理
def read_config(file_path):
    """读取配置文件。"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
        return {}
```

#### 4.2 错误日志（0-5分）

**评估内容**：
- logging模块使用
- 日志级别使用

**评分标准**：
| 情况 | 得分 |
|------|------|
| 使用logging模块且有日志调用 | 5分 |
| 导入logging但无日志调用 | 3分 |
| 未使用logging | 2分 |

**最佳实践**：
```python
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    """处理数据。"""
    try:
        result = transform(data)
        logger.info(f"数据处理成功: {len(result)}条记录")
        return result
    except Exception as e:
        logger.error(f"数据处理失败: {e}", exc_info=True)
        raise
```

#### 4.3 边界检查（0-5分）

**评估内容**：
- None值检查
- 空值检查
- 索引边界检查

**评分标准**：
- 有None检查：5分
- 无None检查：4分

**最佳实践**：
```python
# 好：完善的边界检查
def get_user_name(user):
    """获取用户名。"""
    if user is None:
        return "Unknown"
    
    if not hasattr(user, 'name'):
        return "Unnamed"
    
    return user.name if user.name else "Unnamed"
```

---

### 5. 安全性评估（0-15分）

安全性评估关注代码的安全性，包括输入验证、敏感数据处理、安全编码实践等方面。

#### 5.1 输入验证（0-5分）

**评估内容**：
- input函数使用
- 输入验证逻辑

**评分标准**：
| 情况 | 得分 |
|------|------|
| 有input函数且有验证逻辑 | 5分 |
| 有input函数但无验证逻辑 | 3分 |
| 无input函数 | 5分 |

**最佳实践**：
```python
# 好：输入验证
def get_user_age():
    """获取用户年龄。"""
    while True:
        age_str = input("请输入年龄: ")
        try:
            age = int(age_str)
            if 0 <= age <= 150:
                return age
            else:
                print("年龄必须在0-150之间")
        except ValueError:
            print("请输入有效的数字")
```

#### 5.2 敏感数据处理（0-5分）

**评估内容**：
- 硬编码敏感信息检测
- 敏感关键词识别

**敏感关键词**：
- password, secret, key, token, api_key
- private_key, credential, auth, session

**评分标准**：
- 无硬编码敏感信息：5分
- 发现硬编码敏感信息：每处扣2分

**最佳实践**：
```python
# 不好：硬编码密码
password = "my_password_123"
api_key = "sk-1234567890abcdef"


# 好：使用环境变量
import os

password = os.environ.get('DB_PASSWORD')
api_key = os.environ.get('API_KEY')
```

#### 5.3 安全编码实践（0-5分）

**评估内容**：
- 危险函数使用检测

**危险函数**：
- 代码执行：eval, exec, compile
- 命令执行：os.system, subprocess.call
- 反序列化：pickle.loads, marshal.loads
- YAML解析：yaml.load
- SQL执行：sql, execute, raw

**评分标准**：
- 无危险函数使用：5分
- 使用危险函数：每处扣1分

**最佳实践**：
```python
# 不好：使用危险函数
user_input = input("请输入表达式: ")
result = eval(user_input)  # 危险！


# 好：安全的替代方案
import ast

user_input = input("请输入数字: ")
try:
    result = ast.literal_eval(user_input)  # 安全
except (ValueError, SyntaxError):
    print("输入无效")
```

---

## 权重系数配置

### 默认权重

```python
DIMENSION_WEIGHTS = {
    'readability': 0.25,      # 可读性权重
    'maintainability': 0.25,  # 可维护性权重
    'performance': 0.20,      # 性能效率权重
    'error_handling': 0.15,   # 错误处理权重
    'security': 0.15          # 安全性权重
}
```

### 项目类型权重调整

| 项目类型 | 权重调整 |
|---------|---------|
| Web应用 | 安全性×1.2, 性能×1.1, 错误处理×1.1 |
| CLI工具 | 错误处理×1.2, 可读性×1.1 |
| 类库 | 可读性×1.2, 可维护性×1.1 |
| 数据科学 | 性能×1.2, 可读性×1.1 |

### 项目阶段权重调整

| 项目阶段 | 权重调整 |
|---------|---------|
| 开发阶段 | 可读性×1.1, 可维护性×1.1 |
| 测试阶段 | 错误处理×1.2, 安全性×1.1 |
| 生产阶段 | 安全性×1.3, 性能×1.2, 错误处理×1.2 |

### 团队规模权重调整

| 团队规模 | 权重调整 |
|---------|---------|
| > 5人 | 可读性×1.1, 可维护性×1.1 |
| > 10人 | 可读性×1.2, 可维护性×1.2 |

### 代码规模权重调整

| 代码行数 | 权重调整 |
|---------|---------|
| > 10000行 | 可维护性×1.15, 性能×1.1 |
| > 50000行 | 可维护性×1.25, 性能×1.2 |

---

## 使用方法

### 命令行使用

```bash
# 评估单个文件
python scripts/code_quality_evaluator.py path/to/file.py

# 通过git_analyzer使用
python scripts/git_analyzer.py analyze --algorithm quality
```

### 代码中使用

```python
from code_quality_evaluator import CodeQualityEvaluator, ProjectType, ProjectStage

# 创建评估器
evaluator = CodeQualityEvaluator(
    project_type=ProjectType.WEB_APP,
    project_stage=ProjectStage.PRODUCTION,
    team_size=5,
    code_lines=20000
)

# 评估文件
report = evaluator.evaluate_file('path/to/file.py')

# 查看结果
print(f"总分: {report.total_score}")
print(f"等级: {report.level.value}")

# 生成Markdown报告
markdown = evaluator.generate_report_markdown(report)
print(markdown)
```

### 批量评估

```python
# 批量评估多个文件
file_paths = ['file1.py', 'file2.py', 'file3.py']
reports = evaluator.evaluate_files_batch(file_paths, parallel=True)

# 统计平均分
avg_score = sum(r.total_score for r in reports) / len(reports)
print(f"平均分: {avg_score:.2f}")
```

---

## 最佳实践

### 1. 提高可读性

- 使用有意义的变量名和函数名
- 添加必要的注释和文档字符串
- 保持代码格式统一
- 避免过深的嵌套

### 2. 提高可维护性

- 模块化设计，单一职责
- 减少代码重复
- 合理管理依赖
- 控制函数长度

### 3. 提高性能效率

- 选择合适的算法和数据结构
- 避免嵌套循环
- 使用with语句管理资源
- 优化循环内计算

### 4. 完善错误处理

- 使用try-except捕获异常
- 记录错误日志
- 添加边界检查
- 提供友好的错误信息

### 5. 增强安全性

- 验证所有输入
- 避免硬编码敏感信息
- 使用安全的函数和库
- 遵循安全编码规范

---

## 常见问题解答

### Q1: 如何提高代码质量得分？

**建议**：
1. **可读性**：使用有意义的命名、添加注释、保持格式统一
2. **可维护性**：模块化设计、减少重复、控制函数长度
3. **性能效率**：优化算法、选择合适数据结构、管理资源
4. **错误处理**：捕获异常、记录日志、检查边界
5. **安全性**：验证输入、保护敏感数据、安全编码

### Q2: 为什么我的代码得分很低？

**可能原因**：
1. 命名不规范或无意义
2. 缺少注释和文档字符串
3. 函数过长或嵌套过深
4. 缺少异常处理
5. 存在安全隐患

### Q3: 如何查看详细的评估结果？

**方法**：
1. 使用`generate_report_markdown()`生成详细报告
2. 查看各维度的得分和改进建议
3. 关注得分较低的维度

### Q4: 权重系数如何影响评分？

**说明**：
- 权重系数根据项目类型、阶段、团队规模动态调整
- 不同场景下各维度的重要性不同
- 生产环境更重视安全性和性能
- 开发阶段更重视可读性和可维护性

### Q5: 如何处理AST解析失败？

**原因**：
- 代码存在语法错误
- 文件编码不支持
- 文件过大

**解决方案**：
1. 修复语法错误
2. 转换文件编码为UTF-8
3. 拆分大文件

### Q6: 评估结果可以作为绩效考核依据吗？

**建议**：
- 评估结果仅供参考
- 应结合定性分析
- 关注改进趋势而非单点数据
- 不同项目类型和阶段应区别对待

---

## 相关文档

- [贡献度分析详细指南](./contribution_analysis.md)
- [仓库管理详细指南](./repository_management.md)
- [报告生成详细指南](./report_generation.md)
- [算法对比报告](../algorithm_comparison_report.md)
