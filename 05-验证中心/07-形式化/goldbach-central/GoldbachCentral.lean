import Mathlib.Data.Nat.Factorization.Basic
import Mathlib.Tactic

/-!
# 强哥德巴赫 · 中央筛核心引理的形式化（L4 候选）

本文件只形式化 PWCV 结构研究中**最干净、纯初等**的一条引理——定理 A 的逻辑内核：

  若偶数 E ≥ 4、整数 m 满足  √E < m ≤ E/2（写作 E < m² 与 2m ≤ E），
  并且对每个满足 p² ≤ E 的素数 p，p 既不整除 m，也不整除 E−m，
  那么 m 与 E−m 都必为素数。

它对应论文中“筛到 √E 后的存活位置即真正的 E = p+q 素对”的那一步。
注意：本引理是**条件式**：它说“若有幸存者，则是素对”。
它**不**断言幸存者一定存在（那正是强哥德巴赫本体，仍 OPEN）。
因此即使本文件 `lake build` 通过，也**不**构成哥德巴赫猜想的 L4 证明。

工具链：Lean 4 + Mathlib。唯一可能随 Mathlib 版本改名的引理是
`Nat.minFac_sq_le_self`（等价表述 `Nat.minFac_le_sqrt`），其余为稳定 API。
-/

namespace GoldbachCentral

/-- 若 1 < n < E，且 n 没有“平方不超过 E”的素因子，则 n 必为素数。

  证明：若 n 合数，其最小素因子 p = n.minFac 为素、整除 n，且 p² ≤ n < E，
  于是 p² ≤ E，与“没有这种素因子”矛盾。 -/
lemma no_small_prime_factor_then_prime (n E : ℕ)
    (hn_one : 1 < n) (hn_lt_E : n < E)
    (h : ∀ p : ℕ, Nat.Prime p → p^2 ≤ E → ¬ p ∣ n) :
    Nat.Prime n := by
  by_contra hnp
  set p := n.minFac with hpdef
  have hp_prime : Nat.Prime p := Nat.minFac_prime hn_one
  have hp_dvd : p ∣ n := Nat.minFac_dvd
  have hp2_le_n : p^2 ≤ n := Nat.minFac_sq_le_self hn_one hnp
  have hp2_le_E : p^2 ≤ E := le_trans hp2_le_n (le_of_lt hn_lt_E)
  exact h p hp_prime hp2_le_E hp_dvd

/-- **中央存活即双素（定理 A 内核）**。

  前提：
  - `hE4`  : E ≥ 4；
  - `h_lo` : E < m²，即 √E < m；
  - `h_hi` : 2*m ≤ E，即 m ≤ E/2，从而 m ≤ E−m 且 E−m ≥ m > 1；
  - `h_m`  : 每个 p² ≤ E 的素数都不整除 m；
  - `h_n`  : 每个 p² ≤ E 的素数都不整除 E−m。

  结论：m 与 E−m 均为素数，于是 E = m + (E−m) 是哥德巴赫分解。 -/
theorem central_survivors_are_prime (E m : ℕ)
    (hE4 : 4 ≤ E)
    (h_lo : E < m^2)
    (h_hi : 2 * m ≤ E)
    (h_m : ∀ p : ℕ, Nat.Prime p → p^2 ≤ E → ¬ p ∣ m)
    (h_n : ∀ p : ℕ, Nat.Prime p → p^2 ≤ E → ¬ p ∣ (E - m)) :
    Nat.Prime m ∧ Nat.Prime (E - m) := by
  have hm_one : 1 < m := by nlinarith
  have hm_lt_E : m < E := by nlinarith
  have h_prime_m := no_small_prime_factor_then_prime m E hm_one hm_lt_E h_m
  have h_n_ge_m : m ≤ E - m := by omega
  have hn_one : 1 < E - m := by omega
  have hn_lt_E : E - m < E := by omega
  have h_prime_n := no_small_prime_factor_then_prime (E - m) E hn_one hn_lt_E h_n
  exact ⟨h_prime_m, h_prime_n⟩

end GoldbachCentral
