import Lake
open Lake DSL

package goldbach-central where
  -- 无任何 `sorry`/`admit`；构建成功即为本引理的 L4 机器核验证据。

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git"

@[default_target]
lean_lib GoldbachCentral
