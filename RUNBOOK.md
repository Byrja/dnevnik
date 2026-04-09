# Clarity CBT — Runbook (Owner)

## 1) Check current funnel
```bash
# in Telegram bot chat
/funnel
```
What to watch:
- Sessions started/completed
- Completion rate
- A/B block (A vs B + Winner)

## 2) Manage A/B mode (owner-only)
```bash
/admin_ab status   # current mode
/admin_ab test     # regular A/B split
/admin_ab a        # force variant A
/admin_ab b        # force variant B
```
Inline admin panel is available from `/admin_ab` message.

## 3) Quick quality check after changes
```bash
cd /srv/openclaw-bus/cbt-clarity
./scripts/run_release_gate_p0.sh
```
Then review:
- `RELEASE_GATE_STATUS_2026-04-09.md`
- `scripts/smoke_checklist_p0.md`

## 4) Restart bot service
```bash
systemctl --user restart cbt-clarity.service
systemctl --user is-active cbt-clarity.service
```
Expected: `active`

## 5) Emergency rollback (git)
```bash
cd /srv/openclaw-bus/cbt-clarity
git log --oneline -n 10
git reset --hard <known_good_commit>
git push --force-with-lease origin main
systemctl --user restart cbt-clarity.service
```
Use only if production is broken.

## 6) Current key files
- Product status: `PROJECT_STATUS.md`
- UI lock: `UI_COPY_LOCK.md`
- Gate definition: `RELEASE_GATE_P0.md`
- Gate status: `RELEASE_GATE_STATUS_2026-04-09.md`
- Event map: `ANALYTICS_EVENT_MAP.md`
