---
name: dynamic-web-extraction
description: "Extract content and reverse engineer behavior from JavaScript-heavy, anti-bot, or dynamically loaded web pages. Covers DevTools tracing, dynamic script discovery, anti-verification detection, browser/curl fallback paths, and auth/content extraction workflows."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [web, extraction, reversing, devtools, anti-bot, wechat, auth, javascript]
    related_skills: [hermes-agent, blogwatcher]
---

# Dynamic Web Extraction

## Overview

Use this skill for the class of work where a target website is **not a simple static page**:
- content is hidden behind JavaScript execution,
- logic is split across dynamically loaded scripts,
- anti-bot or verification pages may replace the real content,
- or authentication/signing/encryption behavior must be traced from the frontend.

This umbrella absorbs narrower siblings that separately covered:
- extracting WeChat public-article content, and
- tracing frontend auth/captcha/encryption flows in DevTools.

Those are not separate top-level classes; they are both instances of **dynamic web extraction**.

## When to Use

Use this skill when the user asks to:
- fetch content from a JS-heavy or anti-bot page
- understand where a site's captcha/auth/encryption logic comes from
- find dynamically injected scripts that do not appear in the normal source tree
- determine whether a 200 response is real content or a verification/interstitial page
- reproduce or explain frontend-side encryption/signing steps

## Class-Level Workflow

### 1. Start with the lightest retrieval path
Prefer the simplest path first:
- direct HTTP fetch with appropriate headers / mobile UA
- then browser automation or JS evaluation if plain fetch is blocked
- then deeper DevTools/network tracing if behavior or logic must be reverse engineered

Do not jump straight to full browser automation when a simple request may already work.

### 2. Distinguish real content from interstitials
A `200 OK` response is not proof of success. Check for:
- expected content containers
- expected metadata fields (title, author, publish time, body)
- anti-bot markers such as verification language, abnormal-environment warnings, or empty content selectors

### 3. Use the Network panel, not only Sources
Dynamic sites often load the important code indirectly:
- XHR returns HTML
- that HTML injects a `<script src=...>`
- that script contains the real captcha/auth/content logic

If a file is missing from the Sources tree, search the **Network** panel, page scripts list, or open the direct script URL.

### 4. Trace the execution chain
Map the actual chain:
- page script / bootstrap script
- dynamic HTML fetch
- dynamic script injection
- API request for content/captcha/signature challenge
- verification or login endpoint consuming the derived payload

This execution chain is often the real answer to "how does this work?"

## Section A — Content Extraction from Anti-Bot Pages

### Retrieval ladder
1. direct request with realistic headers / mobile UA
2. browser navigation + DOM extraction
3. in-page JS evaluation to read DOM/local state directly
4. only then specialized workarounds for site-specific anti-bot behavior

### Output normalization
Extract into a stable contract:
- title
- author/source
- publish time
- normalized text body
- page type (`content`, `verification`, `unknown`, `request_error`)

### Heuristic rule
If the expected content container is absent, classify the result instead of pretending extraction succeeded.

## Section B — Frontend Auth / Captcha / Encryption Reversing

### What to look for
Search for:
- dynamic script loads
- `atob` / `btoa`
- byte extraction loops (`charCodeAt` patterns)
- encryption/signature helpers
- API calls returning HTML rather than JSON
- multiple call sites reusing one encryption function with different keys/IVs

### Reasoning model
Many systems reuse the same cryptographic helper for different purposes:
- captcha/sign challenge
- password encryption
- request signing

Do not assume the same function implies the same key source or payload semantics.

### Verification rule
Once you believe you found the frontend logic, reproduce it independently and verify against the target endpoint or an equivalent local test. Reading the JS is not enough; confirm the behavior.

## Section C — Browser Automation Caveats

Browser tools are useful, but not always the best first path.

Common caveats:
- browser automation may trigger anti-bot where curl does not
- JS-heavy SPAs may not respond to synthetic clicks reliably
- screenshots or automation endpoints may be unavailable or flaky on a given backend
- DOM extraction via evaluate/read-state is often more reliable than trying to click through complex UI flows

## Common Pitfalls

1. **Treating WeChat/article extraction and auth reversing as separate top-level classes.** Both are dynamic-web extraction problems.
2. **Assuming 200 means success.** Verification pages also return 200.
3. **Searching only the Sources tree.** Dynamic scripts frequently hide in Network-loaded HTML/script chains.
4. **Skipping the simplest fetch path.** A mobile-UA curl often succeeds where full browser automation fails.
5. **Confusing two uses of the same encryption helper.** Trace call sites and key inputs separately.
6. **Declaring extraction success with empty selectors.** Report page type accurately instead.

## Support files

Absorbed narrower historical notes are preserved in:
- `references/wechat-public-article-extraction.md`
- `references/web-auth-reversing.md`

## Verification Checklist

- [ ] The chosen path started with the lightest plausible retrieval method
- [ ] Real content was distinguished from verification/interstitial pages
- [ ] Dynamic scripts were traced through Network when needed
- [ ] Extraction output was normalized into stable fields
- [ ] Reversed auth/encryption logic was independently verified where possible
