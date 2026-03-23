# /ship — Verify, Simplify, Security Review, and Auto-Commit

You are running the `/ship` workflow. This is a strict, sequential pipeline. Do NOT skip steps. Do NOT commit if any step fails.

## Step 1: Identify Changed Files

Run `git diff --name-only` and `git diff --cached --name-only` to get all changed files (staged + unstaged).
If there are no changes, stop and tell the user "Nothing to ship — no changes detected."

## Step 2: Type Verification

Run these checks based on which files changed:

- **If any `.ts` or `.tsx` files changed:** Run `cd frontend && npx tsc --noEmit` — STOP if errors. Report them and fix before continuing.
- **If any `.py` files under `backend/` changed:** Run `cd /Users/lsr/Documents/bitbucket/hybrid-image-search-demo && .venv/bin/pyright <changed_files>` — STOP if errors. Report them and fix before continuing.

If both stacks have changes, run both checks.

## Step 3: API Contract Sync Check

If BOTH `backend/src/schemas.py` AND `frontend/src/api.ts` are in the changed files, verify that:
- Every Pydantic model field in `schemas.py` has a matching TypeScript interface field in `api.ts`
- No new fields were added to one side without the other

If only ONE side changed and the change involves API response/request shapes, WARN the user:
> "⚠️ You changed `[file]` but not its counterpart. Verify the API contract is still in sync."

## Step 4: Simplify Review

For each changed file, review the code for:
- **Reuse opportunities:** Is there duplicated logic that could use an existing function?
- **Code quality:** Are there overly complex patterns that could be simplified?
- **Efficiency:** Are there unnecessary allocations, redundant loops, or N+1 patterns?
- **Dead code:** Are there unused imports, variables, or functions introduced by the changes?

If issues are found:
1. List each issue with file path and line number
2. Fix them automatically if the fix is safe and obvious
3. Ask the user if the fix is ambiguous

## Step 5: Security Review

For each changed file, check for:

### Python (backend/) files:
- SQL injection: raw string concatenation in queries (should use parameterized queries via SQLAlchemy)
- Path traversal: unsanitized user input in file paths (check `Path()` usage in image serving)
- Command injection: `os.system()`, `subprocess.call()` with `shell=True`
- Secrets in code: hardcoded API keys, tokens, or passwords
- Pickle deserialization of untrusted data
- Missing input validation on API endpoints

### TypeScript (frontend/) files:
- XSS: `dangerouslySetInnerHTML`, `innerHTML`, unescaped user input in JSX
- Sensitive data in localStorage/sessionStorage
- Insecure API calls (http:// instead of relative paths)
- Missing input sanitization before sending to backend

### General:
- `.env` files or secrets being staged for commit
- Debug/console.log statements left in production code
- Overly permissive CORS or authentication settings

If security issues are found:
1. **STOP** — do NOT proceed to commit
2. List each issue with severity (critical/warning/info)
3. Fix critical issues automatically
4. Ask user about warnings

## Step 6: Auto-Commit

Only reach this step if Steps 2-5 all pass.

1. Run `git add` on all changed files (excluding `.env`, `*.secret`, credentials)
2. Analyze the changes and generate a commit message:
   - Use conventional commit format: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`, `test:`
   - Summarize the "why" not the "what"
   - Keep under 72 characters for the first line
3. Create the commit with:
   ```
   Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
   ```
4. Show the commit hash and summary

## Failure Behavior

If ANY step fails:
- Report exactly what failed and why
- Do NOT proceed to later steps
- Do NOT commit partial work
- Suggest what the user should fix

## Output Format

After each step, print a status line:
```
✅ Step 1: 3 files changed (2 .tsx, 1 .py)
✅ Step 2: TypeScript compilation passed | Pyright passed
✅ Step 3: API contract in sync
✅ Step 4: Simplified 1 issue (removed unused import in App.tsx)
✅ Step 5: No security issues found
✅ Step 6: Committed as abc1234 — "feat: add thumbnail support to search results"
```
