# AI UX Backlog (requested)

Date: 2026-04-09
Status: planned

## New requested improvements
1. **Step 7 AI options in monospaced blocks**
   - Format each option as code block for one-tap copy in Telegram.
   - Keep numbering 1/2/3.

2. **Optional AI button on final card**
   - Add button like: `🤖 Краткое резюме ИИ`.
   - Generates compact summary from completed card.

3. **AI summary available from any card (optional)**
   - Add reusable callback action for “краткое резюме от ИИ”.
   - Scope control: start with final card only, then expand to history/user card if useful.

## Priority
- P1: Step 7 monospaced copy format (fast UX win)
- [x] P1: Final-card AI summary button (v1 local summary in place)
- P2: AI summary in other cards

## Constraints
- Preserve fallback to local mode if LLM unavailable.
- Avoid extra spam: prefer edit-in-place where possible.
- Keep output concise and copy-ready.
