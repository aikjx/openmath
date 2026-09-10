# 02-运行时

> 负责**派发、隔离、缓存、资源限制**。验证中心的执行层。

## 一、职责

| 职责 | 说明 |
| --- | --- |
| **发现** | 扫描仓库中的全部记录（`OM-*.yaml`） |
| **派发** | 按层级 + 域 + 能力声明选择引擎 |
| **隔离** | 子进程沙箱、资源限制、无网络 |
| **缓存** | 按「记录哈希 + 引擎版本 + 参数」缓存结果 |
| **并发** | 默认 N-1 进程并行；L4 串行（构建系统不适合并发） |
| **汇总** | 生成报告与看板数据 |

## 二、执行模型

```
openmath verify --level L2 [--domain NT] [--id OM-F-AN-0002] [--all]
        │
        ├─ 1. 发现目标记录（默认：全部；可过滤）
        │
        ├─ 2. 计算 record_hash（内容指纹）
        │
        ├─ 3. 查缓存：hash + engine_version + params 命中？
        │         └─ 命中 → 复用（标记 cached: true）
        │
        ├─ 4. 选引擎：engines.yaml → 能力匹配 → priority 排序
        │
        ├─ 5. 沙箱执行（超时/内存/网络限制）
        │
        ├─ 6. 收集 Result，写 03-结果/
        │
        └─ 7. 对比 04-基线/，生成回归报告
```

## 三、沙箱策略

| 层级 | 隔离方式 | 理由 |
| --- | --- | --- |
| L0–L1 | 进程内（快） | 纯标准库，无副作用 |
| L2–L3 | 子进程 + 超时 | 可能耗尽内存/死循环 |
| L4 | 子进程 + 独立工作目录 | 构建系统需要文件 IO |
| L5 | 子进程 + 严格超时 | 搜索可能爆炸 |
| L6 | CI 环境 | 定期任务 |

**限制**：

- 默认超时：L2 60s / L3 120s / L4 600s / L5 300s
- 内存：默认 2 GB（可配）
- 网络：**默认禁止**（L4 若需下载依赖，走预置缓存）
- 文件：只读，除 `03-结果/` 与临时目录

## 四、缓存策略

**缓存键**：

```
sha256(record_bytes) + engine_name + engine_version + json(params)
```

**失效条件**：

- 记录内容变化（哈希变）
- 引擎版本变化
- 参数变化（精度、种子、采样数）

**缓存存放**：`.openmath-cache/`（gitignore），或可选的远程缓存。

**重要**：缓存结果必须保留原始的 `environment` 与 `duration`，并标 `cached: true`，以便追溯。

## 五、确定性要求

| 要求 | 说明 |
| --- | --- |
| **随机种子必须固定** | L2/L5 的随机采样必须记录种子，可复现 |
| **排序稳定** | 遍历顺序必须确定（按 ID 排序，不依赖文件系统顺序） |
| **浮点确定性** | 使用 mpmath 而非原生浮点；跨平台的差异应记录 |
| **时间不参与判定** | 除性能回归外，执行时间不影响验证结论 |

## 六、并行与资源

```bash
python -m openmath verify --level L2 --jobs 4     # 并发数
python -m openmath verify --level L2 --timeout 120
python -m openmath verify --level L4 --no-parallel # 构建系统串行
```

**L4 默认串行**的原因：`lake build` / `isabelle build` 有自己的并发管理，外层并发会争抢资源并产生错误。

## 七、失败与重试

| 情形 | 处理 |
| --- | --- |
| 引擎超时 | `UNKNOWN` + 记录；**不重试**（可能确实慢） |
| 引擎崩溃 | `ERROR` + 记录 traceback；重试 1 次（排除偶发） |
| 依赖缺失 | `SKIP` + 记录原因 |
| 内存溢出 | `ERROR` + 建议降低 `sample_count` |

**禁止**：把 `ERROR` 静默转成 `PASS`。

## 八、CI 集成

```yaml
# 建议的 GitHub Actions 流程
- run: python -m openmath lint                  # L0，必须过
- run: python -m openmath verify --level L2     # 有 mpmath 时
- run: python -m openmath verify --level L3     # 有 sympy 时
- run: python -m openmath status --check        # 看板无回归
```

**CI 门禁**：

- L0 失败 → **阻止合并**（硬性）
- L2/L3 失败 → 阻止合并（除非条目标 `DISPUTED`/`FALSIFIED`）
- L4 失败 → 提示，不阻止（形式化成本高）

## 九、待办

- [ ] 实现沙箱（目前为进程内 + 超时信号）
- [ ] 实现缓存
- [ ] 实现并发调度
- [ ] 实现远程/分布式执行（大规模 L4 需要）
