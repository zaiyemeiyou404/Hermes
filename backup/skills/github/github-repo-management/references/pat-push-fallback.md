# GitHub PAT Push Fallback

## When to use

`git push origin <branch>` fails with:

```
fatal: could not read Username for 'https://github.com': No such device or address
```

or when the remote URL doesn't have credentials embedded and there's no credential helper configured.

## Root cause

The remote URL (`git remote get-url origin`) is a plain HTTPS URL without a token:
```
https://github.com/owner/repo.git
```

Running `git remote set-url origin` with the token-embedded URL **can time out** (the security scanner blocks it). Do not attempt to persist the token in the remote — use the inline URL approach below.

## The fix: Push with inline token URL

```bash
git push https://username:PAT@github.com/owner/repo.git HEAD:branch-name
```

Replace `PAT` with the actual token, `owner/repo` with the GitHub repo, and `branch-name` with the target branch.

This always works because the token is passed directly in the URL without touching `git remote`.

## Security note

The token is visible in the command and will trigger the agent's security scanner. It will require user approval. This is expected and unavoidable — the alternative (storing the token in the remote URL or credential helper) risks persisting it in git config on a shared machine.

## After the push

The remote URL remains unchanged (plain HTTPS). Subsequent pushes will still need the same pattern unless a credential helper is configured.

## One-time branch naming

When pushing to a new branch:

| Command | Result |
|---------|--------|
| `git push ... HEAD:task-pulse/improvements` | Creates/updates remote branch `task-pulse/improvements` |
| `git push ... opencode/local-branch:remote-branch` | Pushes local `opencode/local-branch` to remote `remote-branch` |

## Verifying success

Look for this in the output:

```
 * [new branch]      HEAD -> branch-name
To https://github.com/owner/repo.git
```

Or for an update:

```
   deadbeef..abc1234  HEAD -> branch-name
```
