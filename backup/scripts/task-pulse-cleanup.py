#!/usr/bin/env python3
"""
task-pulse 每日任务分类整理脚本（5:00 定时运行）
- 修正 category 分类（PPT→ppt, 代码→coding, 聊天→chat）
- 统一 groupId（确保同组任务 groupId 一致）
- 补齐 repoLink（使 group 合并逻辑正常）
- 标记 waiting_review 已完成的过时任务
"""
import json, glob, os, re
from collections import defaultdict

DATA_DIR = os.path.expanduser("~/task-pulse/.task-pulse-data")
FIXES = []

def fix_task(filepath):
    with open(filepath) as f:
        d = json.load(f)
    t = d["task"]
    changed = False

    title = t.get("title", "")
    category = t.get("category", "coding")

    # === Fix category ===
    ppt_keywords = ["PPT", "ppt", "演示", "幻灯片", "slide", "deck", "slides", "展示"]
    chat_keywords = ["聊天", "对话", "chat", "消息", "通知", "审批"]
    design_keywords = ["设计", "design", "UI", "UX", "原型"]

    new_cat = category
    if any(k in title for k in ppt_keywords) and category != "ppt":
        new_cat = "ppt"
    elif any(k in title for k in chat_keywords) and category != "chat":
        new_cat = "chat"
    elif any(k in title for k in design_keywords) and category != "design":
        new_cat = "design"

    if new_cat != category:
        t["category"] = new_cat
        changed = True
        FIXES.append(f"  [{filepath}] category: {category} → {new_cat}")

    # === Fix groupId consistency ===
    gname = t.get("metadata", {}).get("groupName", "")
    repo = t.get("metadata", {}).get("repoLink", t.get("repoLink", ""))
    gid = t.get("groupId", "")

    # Generate expected groupId
    if repo:
        expected_seed = (gname + "::" + re.sub(r"^https?://", "", repo))
    else:
        expected_seed = gname
    expected_gid = "group_" + re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", expected_seed.lower()).strip("-")[:48]

    if expected_gid and gid != expected_gid:
        t["groupId"] = expected_gid
        if "metadata" in t:
            t["metadata"]["groupId"] = expected_gid
        changed = True
        FIXES.append(f"  [{filepath}] groupId: {gid} → {expected_gid}")

    # === Ensure repoLink for coding/ppt tasks ===
    if new_cat in ("coding", "ppt") and not repo:
        # Try to extract from title/prompt
        prompt = t.get("prompt", "")
        match = re.search(r"(https?://(?:github|gitlab|gitee)\.com/[\w.-]+/[\w.-]+)", title + " " + prompt)
        if match:
            t.setdefault("metadata", {})["repoLink"] = match.group(1)
            t["repoLink"] = match.group(1)
            changed = True
            FIXES.append(f"  [{filepath}] added repoLink: {match.group(1)}")

    # === Clear stale waiting_review ===
    if t.get("phase") == "waiting_review" and t.get("status") in ("done", "completed", "stopped"):
        t["phase"] = "completed"
        changed = True
        FIXES.append(f"  [{filepath}] phase: waiting_review → completed")

    if changed:
        with open(filepath, "w") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        return True
    return False


# Main
if not os.path.isdir(DATA_DIR):
    print(f"❌ Data dir not found: {DATA_DIR}")
    exit(1)

files = sorted(glob.glob(os.path.join(DATA_DIR, "task_*.json")))
fixed_count = 0
for fp in files:
    if fix_task(fp):
        fixed_count += 1

print(f"📊 Task Pulse 每日整理报告")
print(f"  检查: {len(files)} 个任务文件")
print(f"  修复: {fixed_count} 个文件")
if FIXES:
    print(f"\n  变更详情:")
    for f in FIXES:
        print(f)
else:
    print(f"\n  无需修复 ✅")
