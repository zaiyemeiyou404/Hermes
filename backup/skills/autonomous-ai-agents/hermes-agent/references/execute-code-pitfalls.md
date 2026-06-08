# Execute Code Pitfalls

## `read_file` from `hermes_tools` adds line numbers — use `open()` instead

When writing file-transformation logic inside `execute_code`, **do not use the
`read_file` function from `hermes_tools` to read files.** It prepends
`LINE_NUMBER|` to every line of the returned content, which silently
corrupts HTML, CSS, JavaScript, and any structured text.

### Wrong (corrupts content)

```python
from hermes_tools import read_file

template = read_file("/path/to/file.html", limit=1000)
content = template["content"]  # ← every line starts with "123|"
content = content.replace("OLD", "NEW")
# Result: file now has line number artifacts like "488|", "489|" baked in
```

### Right (clean)

```python
with open("/path/to/file.html", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("OLD", "NEW")

with open("/path/to/file.html", "w", encoding="utf-8") as f:
    f.write(content)
```

### Symptoms when this bug hits

- HTML files with stray `488|`, `489|` strings inserted between elements
- JavaScript silently broken (syntax errors from injected numbers)
- CSS selectors stop matching
- Navigation, animations, and dynamic behavior all fail
- The file "looks fine" at a glance but nothing works

### Why it's hard to spot

The `read_file` output in chat displays line numbers for readability, so the
format is expected there. But in `execute_code`, the `"content"` key carries
the same decorated text — it's not stripped. The contamination is invisible
until you inspect the written file directly.
