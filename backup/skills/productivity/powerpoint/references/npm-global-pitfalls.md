# NPM Global Module Pitfalls

## Problem

When running `pptxgenjs` scripts from arbitrary directories (e.g. `/tmp/` or a project folder), Node.js cannot find globally-installed modules:

```
Error: Cannot find module 'pptxgenjs'
```

## Fix

Use `NODE_PATH` to point to the global npm root:

```bash
NODE_PATH=$(npm root -g) node script.js
```

Or run the script from within a project that has `pptxgenjs` as a local dependency.

## Verification

```bash
npm list -g pptxgenjs   # Should show version
npm root -g             # Shows global node_modules path
```
