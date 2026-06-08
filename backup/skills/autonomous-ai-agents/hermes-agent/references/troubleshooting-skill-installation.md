# Troubleshooting External Skill Installation

## When `hermes skills install <url>` fails

External skills hosted on GitHub often need an extra step beyond the basic `hermes skills install <url>` command.

### Pattern 1: Direct GitHub repo URL doesn't resolve

```bash
# This often fails
hermes skills install https://github.com/op7418/guizang-ppt-skill
# Error: Could not fetch ... from any source.
```

**Fix: use the raw SKILL.md URL instead.**

```bash
hermes skills install https://raw.githubusercontent.com/op7418/guizang-ppt-skill/main/SKILL.md --yes --category creative
```

### Pattern 2: SKILL.md location isn't obvious

When you don't know where the SKILL.md lives in the repo, probe with curl:

```bash
for branch in main master; do
  for path in SKILL.md subdir/SKILL.md; do
    code=$(curl -sL -o /dev/null -w '%{http_code}' \
      "https://raw.githubusercontent.com/OWNER/REPO/$branch/$path")
    echo "$branch/$path -> $code"
  done
done
```

Then use the working path:
```bash
hermes skills install https://raw.githubusercontent.com/alchaincyf/huashu-skills/master/huashu-design/SKILL.md --yes --category creative
```

### Pattern 3: GitHub API rate limit

```
Error: GitHub API rate limit exhausted (unauthenticated: 60 requests/hour)
```

**Workarounds:**
1. Set `GITHUB_TOKEN` in `~/.hermes/.env`
2. Install and auth `gh` CLI: `gh auth login`
3. Use `curl` to probe paths directly (no API call)

### Non-interactive install (`--yes` flag)

When running in agent context (TUI, gateway), use `--yes` to skip confirmation:
```bash
hermes skills install <url> --yes --category <category>
```

If the SKILL.md frontmatter has no `name:` field, override with:
```bash
hermes skills install <url> --yes --name <skill-name> --category <category>
```

### Pattern 4: Supporting files (assets, references, scripts) are NOT included

**`hermes skills install <url>` only downloads SKILL.md.** Templates, scripts, theme files, and other supporting assets are NOT fetched — even when the install succeeds. The installed skill directory will contain only SKILL.md.

**Symptoms:** You installed a skill, `skill_view(name)` shows the SKILL.md content and `linked_files` is empty, but the SKILL.md references `assets/template.html` or `references/themes.md` that aren't present.

**Fix: manually download supporting files from the GitHub raw URL.**

```bash
# After install, fetch missing assets from the upstream repo
curl -sL 'https://raw.githubusercontent.com/op7418/guizang-ppt-skill/main/assets/template.html' \
  -o ~/.hermes/skills/creative/guizang-ppt-skill/assets/template.html
curl -sL 'https://raw.githubusercontent.com/op7418/guizang-ppt-skill/main/references/themes.md' \
  -o ~/.hermes/skills/creative/guizang-ppt-skill/references/themes.md
```

**Better approach for skills that need supporting files:** download the assets directly into your project workspace rather than patching the installed skill directory, which may get overwritten on update.

```bash
mkdir -p projects/my-ppt/ppt/images
curl -sL 'https://raw.githubusercontent.com/op7418/guizang-ppt-skill/main/assets/template.html' \
  -o projects/my-ppt/ppt/index.html
curl -sL 'https://raw.githubusercontent.com/op7418/guizang-ppt-skill/main/references/themes.md' \
  -o /tmp/guizang_themes.md
```

This keeps the installed skill clean and project files separate from skill internals.

### Note: `hermes skills tap add` is not a prerequisite

Tapping a repo (`hermes skills tap add <url>`) registers it as a skill source for browsing/searching, but does NOT make individual skills installable. For direct installation, always use the raw SKILL.md URL.
