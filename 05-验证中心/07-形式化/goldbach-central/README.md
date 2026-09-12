# goldbach-central · 中央存活即双素（Lean 4 + Mathlib）

## 状态：`NOT_BUILT` —— 尚未构成 L4 证据

| 项 | 值 |
| --- | --- |
| 目标条目 | OM-P-NT-0003（强哥德巴赫） |
| 形式化对象 | **仅**定理 A 的逻辑内核 `central_survivors_are_prime`（中央区间幸存者必为双素） |
| 工具链 | Lean 4 + Mathlib |
| 本机工具链 | **未安装**（elan/lean/lake 均缺，2026-09-12 探测） |
| 构建状态 | **`NOT_BUILT`：未执行 `lake build`，无 `sorry`/`admit`，但也未经编译器核验** |
| 证据等级 | **不是 L4**。构建通过（exit 0、无 sorry）后，仅该引理升 L4；强哥德巴赫本体仍 `OPEN` |

> 诚实说明：源文件中唯一可能随 Mathlib 版本改名的引理是
> `Nat.minFac_sq_le_self`（旧名/等价 `Nat.minFac_le_sqrt`）。未实际构建前，
> 不对 API 是否与当前 Mathlib 完全匹配作保证。

## 这条引理为什么不等于“证明了哥德巴赫”

`central_survivors_are_prime` 是**条件式**：

> **若**存在满足条件的幸存者 m（√E < m ≤ E/2 且逃过所有 p²≤E 的素数），**则** m、E−m 皆素。

它**不**证明幸存者一定存在。而“对每个偶数 E 都至少有一个幸存者”恰恰就是强哥德巴赫本体，
被 Selberg parity barrier 挡住、仍 `OPEN`。因此本引理即使机器核验通过，也只升级这一条结构引理，
不会、也不得被解读为哥德巴赫猜想获证。

## 构建步骤（在装好工具链的机器上）

```powershell
# 方式 A：用 Mathlib 官方模板（自动对齐 lean-toolchain，最稳）
lake +leanprover/lean4:stable new goldbach-central math
#   然后用本目录的 GoldbachCentral.lean 覆盖生成的同名库文件，lake build

# 方式 B：直接在本目录构建（首次会下载 Lean 工具链 + Mathlib，数 GB，编译较久）
curl -sSfL https://elan-init.sh | sh -s -- -y   # Windows 用 elan-init.ps1
lake exe cache get                              # 拉 Mathlib 预编译 oleans，大幅缩短时间
lake build
```

通过判据（对应验证协议 L4）：

1. `lake build` 退出码 0；
2. 全文无 `sorry` / `admit` / 未授权公理；
3. 把结果记录为
   `05-验证中心/03-结果/2026/09/OM-P-NT-0003-L4-<date>.json`，`level: L4, status: PASS`，
   并把 OM-P-NT-0003 第八节中本引理的标注由“形式化候选/NOT_BUILT”改为“L4 PASS”。
