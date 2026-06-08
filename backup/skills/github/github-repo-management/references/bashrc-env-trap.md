# bashrc 环境变量获取陷阱

## 问题

`~/.bashrc` 常见开头：

```bash
# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac
```

这意味着 `source ~/.bashrc` 在非交互式 shell（如脚本、`bash -c`、`terminal` 工具）中**不会加载任何后续内容**，包括 `export GITHUB_TOKEN=...` 等环境变量设置。

## 症状

```bash
source ~/.bashrc
echo ${#GITHUB_TOKEN}   # → 0 （空！）
```

即使 token 实际存在文件中，`source` 也读不到。

## 绕过方法

### 方法 1：直接 grep 提取（推荐）

```bash
TOKEN=$(grep "^export GITHUB_TOKEN=" ~/.bashrc | sed 's/^export GITHUB_TOKEN="//;s/"$//')
echo "${#TOKEN}"   # → 93 （正常长度）
```

### 方法 2：使用 `bash --login -c`

```bash
bash --login -c 'echo ${#GITHUB_TOKEN}'   # 登录 shell 会读取 ~/.profile 等
```

不一定可靠，取决于 `.profile` 是否 `source .bashrc`。

### 方法 3：用 `env` 或 `.env` 文件（推荐长期方案）

将环境变量从 `.bashrc` 移到独立的 `.env` 文件，然后在需要的地方手动 source：

```bash
# ~/.env
GITHUB_TOKEN="ghp_xxx..."

# 使用时
set -a; source ~/.env; set +a
```

## 检查当前 shell 是否是交互式

```bash
case $- in *i*) echo "interactive" ;; *) echo "non-interactive" ;; esac
```

## 适用于

- `terminal` 工具中的 shell 命令
- cron job 脚本
- CI/CD pipeline
- 任何非登录、非交互式的 shell 环境
