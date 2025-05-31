# CFCJ 文件组织说明

## 文件保存位置修复

### 问题描述
之前CFCJ模块的测试脚本将采集结果文件保存到了项目根目录，而不是 `wz/cfcj/` 目录下。这不符合模块化的设计原则。

### 修复内容

#### 1. 修复的脚本文件
- `test_logged_in.py` - 已登录状态测试脚本
- `auto_login_test.py` - 自动登录测试脚本  
- `simple_login_test.py` - 简单登录测试脚本
- `main.py` - 主程序的save_result函数

#### 2. 修复的输出文件
- `logged_in_result.json` - 已移动到 `wz/cfcj/` 目录
- `auto_login_result.json` - 现在保存到 `wz/cfcj/` 目录
- `simple_login_result.json` - 现在保存到 `wz/cfcj/` 目录
- `cookie_reuse_result.json` - 现在保存到 `wz/cfcj/` 目录

#### 3. 修复方法
所有脚本现在使用以下模式来确保文件保存到正确位置：

```python
# 保存结果到cfcj目录
cfcj_dir = Path(__file__).parent
output_file = cfcj_dir / "result_file.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
```

### 当前文件结构

```
wz/cfcj/
├── logged_in_result.json          # 采集结果文件
├── auto_login_result.json         # 自动登录采集结果（运行后生成）
├── simple_login_result.json       # 简单登录采集结果（运行后生成）
├── cookie_reuse_result.json       # Cookie复用采集结果（运行后生成）
├── data/
│   ├── cfcj_config.json          # 配置文件
│   └── cookies.json              # 保存的Cookie
├── core/                         # 核心模块
├── auth/                         # 认证模块
├── utils/                        # 工具模块
├── tests/                        # 测试模块
└── config/                       # 配置模块
```

### 使用说明

#### 运行测试脚本
所有测试脚本现在都会将结果文件保存到 `wz/cfcj/` 目录：

```bash
# 进入cfcj目录
cd wz/cfcj

# 运行测试（结果文件会保存在当前目录）
python test_logged_in.py
python auto_login_test.py
python simple_login_test.py
```

#### 使用main.py
主程序也会将结果保存到cfcj目录：

```bash
cd wz/cfcj
python main.py https://linux.do/t/topic/690688/48
# 结果文件会保存在 wz/cfcj/ 目录下
```

#### 指定输出路径
如果需要保存到其他位置，可以使用绝对路径：

```bash
python main.py --output /path/to/custom/result.json https://example.com
```

### 优势

1. **模块化**: 所有相关文件都在模块目录内
2. **清洁**: 不会污染项目根目录
3. **组织性**: 便于管理和查找采集结果
4. **一致性**: 所有脚本使用统一的文件保存策略

### 注意事项

- 所有采集结果文件现在都保存在 `wz/cfcj/` 目录下
- Cookie和配置文件保存在 `wz/cfcj/data/` 目录下
- 如果需要在其他位置运行脚本，请使用绝对路径指定输出文件
- 建议在 `wz/cfcj/` 目录下运行所有CFCJ相关的脚本
