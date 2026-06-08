---
name: ctf-crypto-attacks
description: "Crypto CTF techniques — LLL lattice reduction (RSA with noisy samples, BDD), supersingular ECDH with Pohlig-Hellman, shared RSA exponent joint lattice attack, Gaussian integer Coppersmith, LCG/EC-LCG prediction, Sudoku bilinear convolution over F_5²."
---

# CTF Crypto — Attack Techniques

## Trigger

When a CTF challenge provides:
- RSA with many "noisy" samples of the same plaintext → lattice / LLL
- Elliptic curve with given points + noise → BDD / CVP lattice
- ECDH with `j=1728` supersingular curve → Pohlig-Hellman
- Multiple RSA instances with different `e`, `n` but same `d` → joint lattice
- Linear Congruential Generator (LCG) output → prediction / parameter recovery
- Elliptic-curve LCG with noisy coordinates → collinearity + lattice

## Workflow

### Phase 1 — Lattice Attacks (LLL / BDD)

#### RSA with Noisy Samples

**Signal**: 10-30 ciphertext samples of the same plaintext bit-sliced with hidden multipliers.

```python
# Each sample: sample_i = s × (a_i + M·b_i) × (1 + k_i·p) mod n
# Recover: construct a dimension-N lattice where the short vector is [x_1, ..., x_N]
# where x_i = a_i + M·b_i

# Step 1: Build lattice
# Use the samples to create a matrix where LLL finds the short x_i vector
# Dimension typically equals number of samples

# Step 2: Recover hidden prime p from GCD of cross-differences
# GCD(x_i - a_i) reveals multiples of p

# Step 3: Once p is known, reduce RSA modulus
# Remaining modulus is much smaller → Wiener / continued fractions for small d
```

#### Small-d Lattice Variant (ed ≡ b mod φ(n))

**Signal**: Multiple RSA instances (e_i, n_i) sharing a common small exponent d, where noisy relations e_i·d ≡ b_i mod φ(n_i) are observed.

```python
# Step 1: Construct 2D lattice from two samples
#   L = [[2^512, e_1],
#        [0,    n_inner]]
# where n_inner is derived from the two moduli via GCD manipulation
from sage.all import matrix, ZZ

def recover_small_d(e1, e2, n1, n2, bits=512):
    """
    2D lattice attack for shared small d.
    Uses the relation: e1·d = 1 + k1·φ(n1), e2·d = 1 + k2·φ(n2)
    """
    # Build lattice: short vector contains d
    n_inner = n1 * n2 // gcd(n1, n2)  # combined modulus bound
    M = matrix(ZZ, [[2^bits, e1],
                    [0,      n_inner]])
    short = M.LLL()[0]
    d_candidate = abs(short[0]) // 2^bits
    return d_candidate

# Step 2: Recover p from GCD of cross-differences of z_i = e_i·d - 1
# Each z_i = k_i · φ(n_i) → GCD(z_i - z_j) reveals multiples of p
from math import gcd as math_gcd

def recover_p_from_z(z_list, n_list):
    """Recover p from z_i = e_i·d - 1 via GCD cross-differences."""
    g = 0
    for i in range(len(z_list)):
        for j in range(i+1, len(z_list)):
            diff = abs(z_list[i] - z_list[j])
            if diff:
                g = math_gcd(g, diff)
    # g contains p (or its multiple) — match against n values
    for n in n_list:
        p_candidate = math_gcd(g, n)
        if 1 < p_candidate < n:
            return p_candidate
    return None
```

**Key insight**: The 2D lattice works when d < 2^256 with ~1024-bit moduli. Cross-difference GCD exploits shared φ(n) structure across samples.

#### BDD (Bounded Distance Decoding) for EC-LCG

**Signal**: Point coordinates with low-noise perturbations.

```python
# If P_{i+1} = P_i + G on unknown curve, with noisy coordinates:
# Collinearity condition: (P_i, G, -P_{i+1}) are collinear regardless of a,b

# Build matrix from collinearity constraints
# Convert to HNF (Hermite Normal Form) then LLL
# Recover noise vectors; dimension = 3 × number of points
```

**Verification**: After LLL, verify recovered values produce integer points on a valid elliptic curve.

### Phase 2 — Supersingular ECDH (Pohlig-Hellman)

**Signal**: Curve `y² = x³ + x` over GF(p) where p ≡ 3 mod 4 → j=1728 → supersingular.

```python
# Supersingular curve: order = p + 1
# Factor the group order
from sage.all import factor

p = ...
E = EllipticCurve(GF(p), [1, 0])  # y² = x³ + x
order = p + 1
factors = factor(order)

# Pohlig-Hellman on small factors
partial_dlog = discrete_log(P, Q, operation='+')

# If a ~44-bit factor remains, use BSGS on remainder:
# t = (secret - partial_result) / small_factor_product
# BSGS search space ≈ 2^36 (practical with optimized code)
```

**Key insight**: Only x-coordinates of public keys are given → try both ±y for each point.

#### MOV Attack (Weil Pairing)

**Signal**: Supersingular curve with embedding degree ≤ 6. For `y² = x³ + x` over GF(p) with `p ≡ 3 mod 4`, the embedding degree k = 2.

```python
# The MOV attack transfers ECDLP from E(F_p) to F_p^k via Weil pairing.
# For supersingular curves, the embedding degree is small (k ∈ {1,2,3,4,6}).

# Step 1: Check embedding degree
# y² = x³ + x, p ≡ 3 mod 4 → k = 2 (works in F_p²)
from sage.all import GF, EllipticCurve, weil_pairing

p = ...
E = EllipticCurve(GF(p), [1, 0])  # y² = x³ + x

# Verify supersingularity
assert E.order() == p + 1
# Embedding degree k satisfies: p^k ≡ 1 mod order (smallest such k)
# For p ≡ 3 mod 4, k = 2

# Step 2: Construct extension field F_p²
Fp2 = GF(p^2, 'w')
E_ext = E.change_ring(Fp2)

# Step 3: Pick a torsion point R (order dividing the subgroup)
# Typically use a point of maximal order
P, Q = E_ext(P), E_ext(Q)  # map points to extension

# Step 4: Compute Weil pairing to transfer to F_p²
R = E_ext.random_point()
# Need R linearly independent from P
while R.order() != P.order() or weil_pairing(P, R, P.order()) == 1:
    R = E_ext.random_point()

pair_P = weil_pairing(P, R, P.order())
pair_Q = weil_pairing(Q, R, P.order())

# Step 5: Solve discrete log in F_p²
# In F_p², use small subgroup + BSGS or index calculus
# discrete_log(pair_Q, pair_P) gives the secret
from sage.all import discrete_log as dlog
secret = dlog(pair_Q, pair_P)
```

**Key insight**: The Weil pairing e(P, Q) is bilinear and non-degenerate. For supersingular curves, ECDLP reduces to DLP in a small extension field where sub-exponential algorithms apply.

**When MOV fails**: If embedding degree k > 6, the extension field is too large for practical discrete log. Check k before attempting.

### Phase 3 — Shared RSA Exponent Joint Lattice

**Signal**: Two RSA instances with different `(e, n)` but same unknown `d`.

```python
# e₁ × d = 1 + k₁ × φ(n₁)
# e₂ × d = 1 + k₂ × φ(n₂)
# Create joint lattice of dimension ~4

# Build matrix:
# [ e₁   1   0   0 ]
# [ e₂   0   1   0 ]
# [ n₁   0   0   0 ]
# [ n₂   0   0   -1 ]

# LLL reduction yields short vector containing (d, k₁, k₂)
# Recover d, then factor each n via ed-1 method
```

### Phase 4 — Gaussian Integer Coppersmith

**Signal**: AES key mask derived from a Gaussian integer root `x₀ = a + b·i` satisfying `f(x₀) ≡ 0 mod (p + q·i)`.

```python
# Given: mask = SHA256(a || b)[:16] where x₀ is Gaussian integer
# f(x) degree-4 polynomial mod Gaussian modulus

# Step 1: Factor n = p·q (classical RSA) via Boneh-Durfee if d is small
# Boneh-Durfee: when d < n^0.292, use Coppersmith on f(x) = e·d - k·φ(n)
from sage.all import var, ZZ, solve_mod

def boneh_durfee(n, e, delta=0.292):
    """
    Boneh-Durfee attack for small d RSA.
    Uses Coppersmith to solve f(x,y) = 1 + x·(n+1) - y·e ≡ 0 mod e.
    When |x| < n^δ and δ < 0.292, the solution is found by lattice reduction.
    """
    # Standard implementation: build lattice of dimension (1+2m) with m ~ 5-7
    # x = k (unknown multiplier), y = d (small secret)
    # The lattice short vector reveals (k, d) → recover φ(n) → factor n
    return None  # placeholder — requires Sage's small_roots()

# Step 2: Map Gaussian modulus to integer: N(M) = p² + q²
# Use CRT: the condition splits via i ≡ -p·q⁻¹ mod (p²+q²)
# For Gaussian integer factorization, factor N(M) = p² + q² via ECM

# Step 3: ECM on p²+q² for extracting Gaussian divisors
# The norm N(M) = p² + q² may have small factors → ECM to extract them
# This enables dimension reduction: z = z₀ + D·w
from sage.all import ECM, factor

def ecm_factor_gaussian_norm(N):
    """
    Factor the integer N = p² + q² using ECM.
    ECM is effective for factors up to ~80 digits.
    Returns the prime factors of N.
    """
    # Use Sage's ECM implementation
    # ecm = ECM()
    # ecm.run(N)  # finds a non-trivial factor
    return factor(N)

# Step 4: Dimension reduction via z = z₀ + D·w
# Once a factor D of N(M) is found, the search space reduces:
# Gaussian root x₀ = a + b·i where a, b ~ 128 bits
# After ECM: z ≡ z₀ mod D for some known z₀, unknown w
# New lattice dimension is much smaller

# Step 5: Gaussian → integer mapping + CRT + 2D CVP
# Map the Gaussian integer problem to a 2D closest vector problem
def gaussian_to_integer_cvp(a_approx, b_approx, N, D, modulus_bits=128):
    """
    Convert Gaussian root finding to 2D CVP.
    a_approx, b_approx: initial approximations (~128 bits)
    N = p² + q² (Gaussian modulus norm)
    D = known divisor from ECM

    The short vector in the lattice corresponds to (a, b).
    Use Babai's nearest plane or embedding technique.
    """
    # Build 2D lattice basis from the CRT-split condition
    # L = [[D,  0],
    #      [0,  D],
    #      [a0, b0]]  # embedding for CVP
    # Find lattice point closest to (a0, b0)
    from sage.all import matrix, ZZ, vector
    basis = matrix(ZZ, [[D, 0],
                        [0, D],
                        [a_approx, b_approx]])
    # LLL + Babai or direct CVP solver
    # Reduced basis = basis.LLL()
    # closest = Babai_closest_vector(reduced_basis, vector([a_approx, b_approx]))
    return None

# Step 6: Full pipeline — recover a, b and verify
def recover_gaussian_root(f, N, modulus_bits=128):
    """
    Full recovery pipeline:
    1. Factor N(M) = p² + q² via ECM
    2. Dimension reduction: z = z₀ + D·w
    3. 2D CVP on the reduced lattice
    4. CRT to combine partial solutions
    5. Verify f(a + b·i) ≡ 0 mod (p + q·i)
    """
    # facets = ecm_factor_gaussian_norm(N)
    # For each prime power factor, build partial lattice
    # Use CRT to combine results
    # Verify the final (a, b) produces the correct mask
    pass
```

**Key insights from c0mplex_root**:
- CRT splits the Gaussian congruence into two integer congruences
- ECM on p²+q² reveals small factors enabling dimension reduction
- The 2D CVP formulation: find (a, b) close to approximation such that a + b·i ≡ root mod Gaussian modulus
- Boneh-Durfee pre-factorization: when d is small, factor n before attempting Gaussian Coppersmith
- The mapping z = z₀ + D·w reduces effective dimension from ~8 to ~2

### Phase 5 — LCG Parameter Recovery

**Signal**: Consecutive outputs from a linear congruential generator.

```python
# LCG: X_{n+1} = a·X_n + c mod m
# Given consecutive outputs: recover modulus m first
# Using the "difference method": t_n = X_{n+1} - X_n
# Then t_{n+2}·t_n - t_{n+1}² ≡ 0 mod m
# GCD of multiple such terms reveals m
```

### Phase 6 — Sudoku Bilinear Convolution over F_5²

**Signal**: Challenge asks to construct two `N × N` Sudoku matrices `A, B` where `C[i][j] = sum_k (α·A[i][k]·B[k][j] + β·A[i][k] + γ·B[k][j] + δ) mod M + 1` is also a valid Sudoku. Parameters `α, β, γ, δ` vary per round, repeated across multiple rounds.

**Example**: Mini L-CTF 2026 "！？数独独数？！" — 25×25 Sudoku, `M=25`, 16 rounds, reusable witness.

#### Step 1 — Eliminate Redundant Terms

```
If A rows and B columns are permutations of 1..M:
  sum_k A[i][k] ≡ sum_k B[k][j] ≡ 0 (mod M)  [when M = 25, 25→0]
  M · δ ≡ 0 (mod M)

Therefore: C[i][j] = α · sum_k (A[i][k] · B[k][j]) mod M
β, γ, δ drop out entirely.
```

#### Step 2 — Detect Unsolvable Rounds

```
If gcd(α, M) ≠ 1:
  α · z mod M can only take M/gcd(α,M) distinct values
  → Not enough distinct values to fill a Sudoku row/column
  → Submit "-1" (skip)

For M=25: α divisible by 5 → {0,5,10,15,20} → impossible
```

**Only rounds with `gcd(α, 25) = 1` are solvable**.

#### Step 3 — Map Index Space to F_5²

Map `0..24` to 2D coordinates over GF(5):

```python
def pair_of_index(i):
    return (i // 5, i % 5)

def idx(p):
    return p[0] * 5 + p[1]
```

Define two linear transformations:

```python
S = lambda x: (x[1], x[0])        # swap
T = lambda x: ((x[0] + x[1]) % 5, x[1])  # shear
```

#### Step 4 — Construct Core Permutations AA, BB

Find two length-25 permutations `AA, BB` such that:

```python
F[z] = sum_u AA[u] * BB[u + z] mod 25
```

produces another permutation of `0..24`.

**Strategy**: Brute-force search over `S_25` candidate pairs, testing the convolution property (compute-time: seconds with backtracking + pruning). For the original challenge, these worked:

```python
AA = [24, 6, 19, 18, 8, 20, 11, 22, 17, 16, 3, 5, 21, 10, 2, 9, 14, 13, 15, 0, 4, 12, 23, 1, 7]
BB = [13, 2, 1, 5, 14, 18, 12, 0, 22, 8, 6, 10, 20, 3, 11, 21, 9, 4, 23, 19, 16, 24, 7, 17, 15]
```

#### Step 5 — Embed AA, BB into 25×25 Sudoku

Construct witness matrices:

```python
def generate_witness():
    A, B = [], []
    for i in range(25):
        x = pair_of_index(i)
        row = []
        for k in range(25):
            t = pair_of_index(k)
            u = (x[0] + t[1]) % 5, (x[1] + t[0]) % 5  # x + S(t)
            row.append(to_input(AA[idx(u)]))
        A.append(row)

    for k in range(25):
        t = pair_of_index(k)
        row = []
        for j in range(25):
            y = pair_of_index(j)
            u = ((t[1] + y[0] + y[1]) % 5, (t[0] + y[1]) % 5)  # S(t) + T(y)
            row.append(to_input(BB[idx(u)]))
        B.append(row)
    return A, B
```

Where `to_input(v)` maps residue `0` → `25`, and `1..24` stays as-is.

#### Step 6 — Verify and Submit

```python
for each round (α, β, γ, δ):
    if gcd(α, 25) != 1:
        send("-1")
    else:
        send(generate_witness())
```

Run self-test locally first:

```bash
python3 solve.py --self-test
# Expected: "self-test OK" + list of unsolvable round indices
```

### Mathematical Proof (Summary)

1. **A is a valid Sudoku**: `A[i][k] = AA[x + S(t)]`. Fixed row: `x` fixed, `t` varies over F_5² → `x + S(t)` is bijective since `S` is invertible. Same for columns and 5×5 sub-boxes.

2. **B is a valid Sudoku**: `B[k][j] = BB[S(t) + T(y)]`. `S` and `T` are both invertible, so fixed row/column/sub-box arguments hold.

3. **D = A · B mod 25 is a valid Sudoku**:
   - `D[x][y] = sum_z AA[x+z] · BB[z+T(y)] = F[T(y) - x]`
   - `Z[x][y] = T(y) - x` maps each row, column, and 5×5 sub-box bijectively onto F_5²
   - Therefore `F[Z]` is a valid permutation matrix

4. **When gcd(α, 25)=1**: multiplication by `α` permutes residues → `C = α·D + 1` is a valid Sudoku.

### Key Insight

The problem reduces from "construct 16 unique Sudoku pairs" to:
- 2 rounds: alpha divisible by 5 → skip
- 14 rounds: reuse the same A, B witness

The algebraic structure (F_5² → linear maps → convolution) ensures the witness works for all coprime α simultaneously.

> **Source repo**: This technique comes from the MiniL CTF 2026 challenge by XDSEC. The full challenge materials (source code, Dockerfile, solver) are at `references/minilctf-2026-repo.md`.

## Pitfalls

1. **LLL dimension** — low dimension (< 50) is fast; high dimension (> 80) may need BKZ or progressive BKZ
2. **Noise magnitude** — BDD lattice works when noise < modulus^(1/dimension). Larger noise = larger lattice dimension needed
3. **Supersingular ≠ vulnerable** — also need smooth-ish group order. Check factorization first
4. **Shared d attack** — only works if both φ(n) structures are unknown but d is shared. Won't work if d is different
5. **Gaussian Coppersmith** — the Gaussian modulus N(M) must be partially factorable. If it's prime, the attack fails
6. **BSGS scope** — bounded BSGS works when partial Pohlig-Hellman leaves < 2^40 search space
7. **SageMath dependency** — most crypto challenges expect SageMath. Fall back to Python + small-dimension LLL via flint/fpylll
