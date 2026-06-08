Archived source skill: web-auth-reversing

This reference preserves the absorbed frontend-reversing patterns:
- use DevTools Network first, not only Sources
- trace dynamic HTML → injected script → API chain
- search for atob/charCodeAt/encrypt/sign helpers
- distinguish multiple contexts that reuse one crypto helper with different keys/purposes
- independently verify reproduced signing/encryption logic

The original full skill and case-study references were archived, not deleted.