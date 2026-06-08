# tabler-filled Icon Name Gotchas (PPT Master SVG)

This environment's `tabler-filled` library (`skills/ppt-master/templates/icons/tabler-filled/`) does NOT have all intuitive icon names. Below are the mismatches discovered during usage — always `ls | grep <keyword>` before committing an icon.

## Common Mismatches

| Intuitive name | Actual name | Notes |
|---------------|-------------|-------|
| `server` | **does not exist** | Use `cloud-computing` or `device-imac` |
| `robot` | **does not exist** | Use `sparkles` (AI feel) or `code-circle-2` (tech/AI) |
| `terminal-2` | **does not exist** | Use `code-circle-2` |
| `users` (plural) | **does not exist** | Use `user` (singular only) |
| `tool` | **does not exist** | Use `settings` or `tools-kitchen-2` |
| `clock` | `clock` | Exists |
| `chart-bar` | varies | Check `ls | grep chart` |
| `settings` | `settings` | exists |
| `brand-github` | `brand-github` | exists |

## General Rule

Tabler libraries use plural/descriptive naming conventions:
- `cloud-computing` (not `cloud-server`)
- `code-circle-2` (not just `code`)
- `clipboard-list` (not `list`)
- `shield-check` (not `shield-verified`)

Always verify: `ls skills/ppt-master/templates/icons/tabler-filled/ | grep <keyword>`
