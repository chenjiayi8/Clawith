# Upstream Main Integration Commit Map

## Baseline
- Working branch: `integration/upstream-main-2026-05-11`
- Fork remote: `origin`
- Upstream remote: `upstream`
- Local fork baseline SHA: `850b295cd17ef07c359d7e86e0ea293f277e6a8c`
- Upstream integration base SHA: `acf2a359ddeeb69239fbef7116e75d0fd3329bc5`
- Backup branch name: `backup/pre-upstream-main-integration-2026-05-11`
- Backup tag name: `pre-upstream-main-integration-2026-05-11`
- Integration branch: `integration/upstream-main-2026-05-11`
- Replay restore source of truth: restore work starts from the backup ref at the local `main` baseline SHA above, not from `origin/main`
- Published fork snapshot note: the divergence counts, ordered fork-only commit list, and fork-only file inventory below were captured from `origin/main` versus `upstream/main` to freeze the published fork delta being replayed
- Local-only baseline note: local `main` is clean and `ahead 1` of `origin/main`; that extra local-only commit stays preserved by the backup ref and is intentionally outside the `origin/main` snapshot sections below

## Divergence snapshot
- Command: `git rev-list --left-right --count origin/main...upstream/main`
- origin/main-only commits: 61
- upstream/main-only commits: 870

## Fork-only replay source commits
- Command: `git log --reverse --oneline upstream/main..origin/main`

30729dc fix(consultant): docker socket access and container name fixes
ec8e134 chore: add runtime data and infrastructure files to gitignore
a23acde feat(workspace): add WorkspaceProject and WorkspaceBugReport models
957aa28 feat(workspace): add deployment tools, index generator, and health checks
adc7c8c feat(workspace): add public bug report and container approve/reject API
d6adb91 feat(workspace): register 9 workspace tools for agents
03f7086 feat(workspace): wire models, routes, and health checks into app startup
03a664f feat: mobile responsive design for Dashboard, Chat, Plaza (#1)
9f7a5d7 fix: mobile tabs scroll and chat tab layout stacking
05efda5 feat(backend): add MCP Gateway tool sync on startup
8888a87 chore: add .worktrees/ to gitignore
20f8872 fix(mcp-client): preserve streamable error message across except blocks
105b59f fix(tools): show gateway MCP tools on agent tool pages
fa4070c Revert "fix(tools): show gateway MCP tools on agent tool pages"
1e71608 fix(startup): remove MCP Gateway auto-sync call
982013c fix(gateway): delete mcp_gateway sync module
cbcd659 fix(config): remove MCP_GATEWAY_URL setting
7fd8b3f fix(mcp-client): increase tools/call timeout to 210s
59e716a feat: add AGENCY_AGENTS_DIR config and is_hidden column to ChatMessage
2c22a8e feat: add build_role_reference script to generate reference.json from agency-agents
cf1d4e5 feat: add get_skill_map() service for skill autocomplete API
22357cb feat: expose skill_map in agent detail API response
e9d4f68 feat: expose message IDs in chat history, session messages, and WebSocket done events
d4e2ba9 feat: add skill injection and edit/retry handlers to WebSocket
6c6ca3d feat: add SkillAutocomplete component with slash-command autocomplete
944a257 feat: integrate SkillAutocomplete into both chat surfaces with skill_loaded indicator
f412233 feat: add message edit/retry with pencil icon and inline editing
adde77f fix: address code review — message IDs in AgentDetail, role-only fallback, onPaste forwarding
dc9bcd5 fix(security): add edit authorization and path traversal protection
27338f1 fix: use get_settings() instead of settings import in skill_map and websocket
7c66b20 fix: allow null in SkillAutocomplete inputRef type
cdd3821 chore: remove reference.json infrastructure (build script, AGENCY_AGENTS_DIR, shared volume)
b5952cc feat: rewrite get_skill_map() with recursive folder scanning and flat colon keys
0386cb1 feat: update agent API to return flat colon-keyed skill map
201c761 feat: simplify skill resolution to flat map lookup with single regex
f57becd feat: rewrite SkillAutocomplete with unlimited-depth prefix matching
7a736c7 feat: add zip preview and extract endpoints for skill package upload
15642d2 feat: add Import Skill Package button with zip preview modal
d80ee42 fix(security): add Form annotations for zip params and zip bomb protection
8ba305b fix: address code review — async skill read, zip validation DRY, autocomplete leaf+parent
48e648b fix: zip extract respects current folder path, chat input auto-expanding textarea
41c3aee fix: correct PADDING_Y constant and fire onPathChange on mount
3fccc9e fix: make chat textarea expand upward instead of downward
b3a507f feat: add title_edited and utility_model_id columns
f4474bf feat: expose hidden messages in messages API with is_hidden flag
f9280dd feat: set title_edited=True when session is renamed via PATCH
3468174 feat: expose utility_model_id in tenant-quotas GET/PATCH
11be274 feat: add session title generation service
ea1ca69 feat: add skill content to skill_loaded event and trigger LLM title generation
f98d300 feat: skill indicator debug drawer with hidden message content
b9a3928 feat: inline session title editing with double-click and long-press
f39a7fa feat: handle WebSocket session_title_updated for live title updates
ae80569 feat: utility model dropdown on LLM tab
e4bf6b1 feat: add i18n translations for utility model
7753ccc fix: use api_key_encrypted instead of api_key for utility model
37c8ae4 refactor: pass model object to generate_session_title instead of decomposed fields
fb807c3 fix: shorten migration revision ID to fit varchar(32)
0956255 fix: add hidden message handling and skill drawer to AgentDetail.tsx
05645bb chore: add .claude/ to .gitignore
6fd3e90 fix(frontend): prevent double-click rename from also selecting session
0858deb feat(frontend): make app name and logo configurable via .env


## Slice classification

### Backend product slice
- `backend/alembic/versions/5b0be8fbd941_add_chat_message_is_hidden_column.py`
- `backend/alembic/versions/add_title_edit_util_model.py`
- `backend/app/api/agents.py`
- `backend/app/api/chat_sessions.py`
- `backend/app/api/enterprise.py`
- `backend/app/api/files.py`
- `backend/app/api/websocket.py`
- `backend/app/api/workspace.py`
- `backend/app/config.py`
- `backend/app/main.py`
- `backend/app/models/audit.py`
- `backend/app/models/chat_session.py`
- `backend/app/models/tenant.py`
- `backend/app/models/workspace.py`
- `backend/app/scripts/__init__.py`
- `backend/app/services/agent_seeder.py`
- `backend/app/services/agent_tools.py`
- `backend/app/services/mcp_client.py`
- `backend/app/services/session_title.py`
- `backend/app/services/skill_map.py`
- `backend/app/services/tool_seeder.py`
- `backend/app/services/workspace_health.py`
- `backend/app/services/workspace_index.py`
- `backend/app/services/workspace_tools.py`
- `backend/entrypoint.sh`

### Frontend product slice
- `frontend/src/components/FileBrowser.tsx`
- `frontend/src/components/SkillAutocomplete.tsx`
- `frontend/src/i18n/en.json`
- `frontend/src/i18n/zh.json`
- `frontend/src/index.css`
- `frontend/src/pages/AgentDetail.tsx`
- `frontend/src/pages/Chat.tsx`
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/pages/EnterpriseSettings.tsx`
- `frontend/src/pages/Layout.tsx`
- `frontend/src/pages/Login.tsx`
- `frontend/src/pages/Plaza.tsx`
- `frontend/src/types/index.ts`

### Config / branding slice
- `.gitignore`
- `frontend/.env.example`
- `frontend/index.html`
- `frontend/nginx.conf`

## Skipped non-product artifacts
- `.claude/screenshots/01-login-page.png`
- `.claude/screenshots/02-after-login.png`
- Rationale: screenshots are intentionally excluded from replay because they are review artifacts, not product behavior.

## Fork-only file inventory
- Command: `git diff --name-only upstream/main...origin/main | sort`
.claude/screenshots/01-login-page.png
.claude/screenshots/02-after-login.png
.gitignore
backend/alembic/versions/5b0be8fbd941_add_chat_message_is_hidden_column.py
backend/alembic/versions/add_title_edit_util_model.py
backend/app/api/agents.py
backend/app/api/chat_sessions.py
backend/app/api/enterprise.py
backend/app/api/files.py
backend/app/api/websocket.py
backend/app/api/workspace.py
backend/app/config.py
backend/app/main.py
backend/app/models/audit.py
backend/app/models/chat_session.py
backend/app/models/tenant.py
backend/app/models/workspace.py
backend/app/scripts/__init__.py
backend/app/services/agent_seeder.py
backend/app/services/agent_tools.py
backend/app/services/mcp_client.py
backend/app/services/session_title.py
backend/app/services/skill_map.py
backend/app/services/tool_seeder.py
backend/app/services/workspace_health.py
backend/app/services/workspace_index.py
backend/app/services/workspace_tools.py
backend/entrypoint.sh
frontend/.env.example
frontend/index.html
frontend/nginx.conf
frontend/src/components/FileBrowser.tsx
frontend/src/components/SkillAutocomplete.tsx
frontend/src/i18n/en.json
frontend/src/i18n/zh.json
frontend/src/index.css
frontend/src/pages/AgentDetail.tsx
frontend/src/pages/Chat.tsx
frontend/src/pages/Dashboard.tsx
frontend/src/pages/EnterpriseSettings.tsx
frontend/src/pages/Layout.tsx
frontend/src/pages/Login.tsx
frontend/src/pages/Plaza.tsx
frontend/src/types/index.ts
