#!/usr/bin/env python3
"""
硬科幻章节生成器

用法：
  python3 generate_chapter.py "第1章：黑暗中的坐标"   # 生成单章
  python3 generate_chapter.py outline <world_setting> # 生成30章大纲

输出：
  ~/novel/chapters/ 或 ~/novel/outline/
"""

import json, os, sys, requests, re, subprocess
from pathlib import Path

NOVEL_DIR = Path.home() / "novel"
WORLD_FILE = NOVEL_DIR / "world" / "current-setting.md"
PROMPT_FILE = NOVEL_DIR / "pipeline" / "chapter-prompt.md"
CHAPTER_DIR = NOVEL_DIR / "chapters"

def get_api_key():
    """Try multiple sources for DEEPSEEK_API_KEY"""
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        result = subprocess.run(
            ['bash', '-ilc', 'echo $DEEPSEEK_API_KEY'],
            capture_output=True, text=True, timeout=5
        )
        key = result.stdout.strip()
        if key:
            return key
    except:
        pass
    return None

def load_context() -> str:
    parts = []
    if WORLD_FILE.exists():
        parts.append(f"## 世界观设定\n{WORLD_FILE.read_text(encoding='utf-8')}")
    summaries = []
    for f in sorted(CHAPTER_DIR.glob("*.md")):
        lines = f.read_text(encoding='utf-8').strip().split('\n')
        summary = '\n'.join(lines[:3]) if lines else ""
        if summary:
            summaries.append(f"- [{f.stem}]\n  {summary[:200]}")
    if summaries:
        parts.append("## 已有章节\n" + '\n'.join(summaries[-5:]))
    if PROMPT_FILE.exists():
        parts.append(f"## 写作风格\n{PROMPT_FILE.read_text(encoding='utf-8')}")
    return '\n\n'.join(parts)

def generate_chapter(chapter_title: str, outline: dict = None):
    api_key = get_api_key()
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found")
        return None

    system_prompt = f"""你是硬科幻小说作家，风格类似阿西莫夫和刘慈欣。\n\n{load_context()}"""
    user_prompt = f"请写出 {chapter_title}。\n\n" + (f"本章大纲：{json.dumps(outline, ensure_ascii=False, indent=2)}\n\n" if outline else "") + "要求：3000-5000字，包含核心科学概念，开头抓人，结尾留钩子。"

    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "deepseek/deepseek-chat", "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ], "temperature": 0.8, "max_tokens": 8000},
        timeout=120
    )
    if resp.status_code != 200:
        print(f"❌ API error: {resp.status_code}")
        return None

    content = resp.json()["choices"][0]["message"]["content"]
    safe_title = chapter_title.replace('/', '-').replace(':', '：')
    filepath = CHAPTER_DIR / f"{safe_title}.md"
    filepath.write_text(content, encoding='utf-8')
    print(f"✅ {filepath} ({len(content)}字)")
    return content

def generate_outline(world_setting: str):
    api_key = get_api_key()
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found")
        return None

    setting = Path(world_setting).read_text(encoding='utf-8') if Path(world_setting).exists() else world_setting
    prompt = f"""根据以下世界观设计30章硬科幻大纲，JSON输出。

世界观：{setting}

格式：{{"title":"","logline":"","core_concepts":[],"chapters":[{{"title":"","summary":"","science_concept":"","hook":""}}]}}"""

    resp = requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": "deepseek/deepseek-chat", "messages": [
            {"role": "system", "content": "你是专业科幻策划人，擅长宏大世界观和复杂情节。"},
            {"role": "user", "content": prompt}
        ], "temperature": 0.7, "max_tokens": 16000},
        timeout=180
    )
    if resp.status_code != 200:
        print(f"❌ API error: {resp.status_code}")
        return None

    text = resp.json()["choices"][0]["message"]["content"]
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    outline = json.loads(json_match.group(1)) if json_match else json.loads(text)

    outline_path = NOVEL_DIR / "outline" / f"{outline['title']}.json"
    outline_path.parent.mkdir(exist_ok=True)
    outline_path.write_text(json.dumps(outline, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"✅ 大纲已保存: {outline_path} ({len(outline['chapters'])}章)")
    return outline

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "outline":
        generate_outline(sys.argv[2] if len(sys.argv) > 2 else str(WORLD_FILE))
    else:
        outline_file = sys.argv[2] if len(sys.argv) > 2 else None
        outline_data = json.loads(Path(outline_file).read_text()) if outline_file and Path(outline_file).exists() else None
        generate_chapter(sys.argv[1], outline_data)
