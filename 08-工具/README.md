# 08-工具

> `openmath` CLI 的使用说明与开发指南。

## 一、安装

```bash
pip install -e .                    # 核心功能，零第三方依赖
pip install -e ".[all]"             # 增加 mpmath / numpy / sympy（启用 L2/L3）
```

## 二、命令

| 命令 | 作用 | 依赖 |
| --- | --- | --- |
| `openmath doctor` | 环境体检（哪些层级可用） | 无 |
| `openmath lint` | **L0 结构校验** | 无 |
| `openmath verify --level L2` | L2 高精度数值 | sympy |
| `openmath verify --level L3` | L3 符号验证 | sympy |
| `openmath index` | 构建交叉引用索引 | 无 |
| `openmath index --search X` | 检索 | 无 |
| `openmath status` | 看板 | 无 |
| `openmath new F --domain NT --slug xxx` | 从模板创建记录 | 无 |

也可以不用安装：

```bash
python -m openmath doctor
python -m openmath lint
```

## 三、示例

```bash
# 全库结构校验
python -m openmath lint

# 只验证一条
python -m openmath verify --level L2 --id OM-F-AN-0002

# 提高精度与采样数
python -m openmath verify --level L2 --precision 80 --samples 100

# 建索引并检索
python -m openmath index
python -m openmath index --search zeta
python -m openmath index --domain NT

# 看板
python -m openmath status
python -m openmath status --format json
```

## 四、目录结构

```
08-工具/
├── README.md            本文件
├── examples/            独立可运行的验证脚本（被条目引用）
│   ├── verify_OM-F-AN-0001.py
│   └── verify_OM-F-AN-0002.py
└── tests/               自检
    └── test_core.py
```

Python 包本体位于仓库根的 `openmath/`：

```
openmath/
├── cli.py       命令行
├── ids.py       ID 解析与分配
├── record.py    记录加载与发现（PyYAML 优先，回退 yamlish）
├── yamlish.py   最小 YAML 子集解析器（零依赖）
├── schema.py    L0 校验
├── verify.py    L2/L3 引擎
├── index.py     索引
└── report.py    看板
```

## 五、为什么要自带 YAML 解析器

核心门禁（L0）必须在**任何环境**下可运行。若依赖 PyYAML，一台干净的机器在没有网络时就无法做最基本的结构校验。

因此 `openmath/yamlish.py` 实现了覆盖本库全部记录文件的最小 YAML 子集。已安装 PyYAML 时自动优先使用它。

**若你的记录文件使用了 yamlish 不支持的语法**（锚点、多文档等），请安装 PyYAML。

## 六、退出码

| 码 | 含义 |
| --- | --- |
| 0 | 通过 |
| 1 | 验证 FAIL 或 L0 错误 |
| 2 | 引擎 ERROR / 环境问题 |

## 七、待办

- [ ] L1 良构性引擎
- [ ] 量纲检查（物理条目）
- [ ] 阴性对照集
- [ ] L4 形式化绑定
- [ ] 并发与缓存（见 [05-验证中心/02-运行时](../05-验证中心/02-运行时/README.md)）
