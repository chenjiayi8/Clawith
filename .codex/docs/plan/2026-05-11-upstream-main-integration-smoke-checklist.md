# Upstream Main Integration Smoke Checklist

Environment used for smoke:
- Integrated branch app started from this worktree
- Isolated smoke database: `clawith_smoke_1778531390`
- Smoke user: platform admin created via `/api/auth/register`
- Smoke agent: `Smoke Agent`
- Smoke session: `Renamed Smoke Session`

Checks performed:
1. Start the app with `bash restart.sh --source` using the integration worktree `.env`
2. Confirm backend health at `http://localhost:8008/api/health`
3. Confirm frontend proxy health at `http://localhost:3008/api/health`
4. Browser smoke: Dashboard and Plaza shells load while authenticated
5. Browser smoke: Agent chat page shows renamed session and hidden-message indicator/content
6. Browser smoke: Enterprise Models tab shows Utility Model selector and Smoke Model
7. Browser smoke: Skills tab shows Import Skill Package affordance in `FileBrowser`
8. Live zip flow: `/preview-zip` and `/extract-zip` succeed against the smoke agent; extracted folder appears under `skills/`
9. Browser smoke: mobile viewport loads Plaza and Agent chat shells
10. Branding smoke: built `dist/index.html` renders concrete default title/meta (`Clawith`, `Clawith — 企业数字员工平台`)

Notes:
- Smoke ran against an isolated Postgres database to avoid mutating the shared consultant DB.
- The browser click-path for zip extraction was flaky under headless automation because the live chat page keeps websocket activity; the zip flow was therefore proven with browser-visible affordance + live backend preview/extract API execution.
