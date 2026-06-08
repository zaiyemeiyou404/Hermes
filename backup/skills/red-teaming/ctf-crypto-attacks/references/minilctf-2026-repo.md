# MiniL CTF 2026 — XDSEC Challenge Repo

**Source**: https://github.com/XDSEC/miniLCTF_2026

Official repository for the XDSEC (西电信息安全协会) Mini L-CTF 2026 competition.

## Repo Structure

```
miniLCTF_2026/
├── Challenges/              — Challenge source files
│   ├── Web/                 (6 challenges)
│   ├── misc/                (4 challenges)
│   ├── pwn/                 (6 challenges)
│   └── reverse/             (5 challenges)
├── OfficialWriteups/        — Official solution writeups
│   ├── CryptoWp/            (6 challenges)
│   │   ├── Noisyrsa/
│   │   ├── c0mplex_root/
│   │   ├── comp1ex_root/
│   │   ├── ecclcg/
│   │   ├── ezECDH/
│   │   └── 数独/             ← Source of the F_5² bilinear convolution Sudoku
│   ├── misc/                (4 challenges)
│   ├── pwn/                 (6 challenges)
│   ├── reverse/             (5 challenges)
│   └── web/                 (6 challenges)
└── Writeups/                — Participant-submitted writeups (PRs welcome)
```

## Challenge List

| Category | Challenges |
|----------|-----------|
| **Crypto** | Noisyrsa, c0mplex_root, comp1ex_root, ecclcg, ezECDH, 数独 |
| **Web** | EzJvav, EzOmniProbe, EzPing, Ezdomain, Ezff, Hdphp |
| **Pwn** | 1byte, EZarcade_hall, EZcs, level5, n4n0sleep, newletter |
| **Reverse** | GQuuuuuupX, Schrodinger's Env, VectorizedMirage-revenge, VectorizedMirage, ezbox |
| **Misc** | License_Recovery, Only_4-Bit_Depth, as_the_birds_say, Recovery_Pod |

## Relevant Skills

- The **「！？数独独数？！」** challenge (Crypto/数独) is the source of the F_5² bilinear convolution technique in `ctf-crypto-attacks` (Phase 6 — Sudoku). See that skill for the solve strategy: bijective linear maps over GF(5)², reusable witness across multiple rounds, gcd-α skip condition.

## How to Use

1. Clone: `git clone https://github.com/XDSEC/miniLCTF_2026.git`
2. Browse `OfficialWriteups/<category>/<challenge>/` for the official solve
3. For participant writeups, check `Writeups/` (may contain additional perspectives)
4. Challenge source files are in `Challenges/<category>/<challenge>/`
