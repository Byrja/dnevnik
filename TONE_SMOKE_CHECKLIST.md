# Tone Smoke Checklist

Date: __________
Tester: __________

## Target
Verify that selected tone materially affects UX and AI behavior.

## Modes to check
- [ ] warm
- [ ] neutral
- [ ] coach
- [ ] direct

## For each mode
1. [ ] `/settings` -> select tone -> explanation card matches selected mode
2. [ ] Start `/new` -> Step 1 prompt style matches mode
3. [ ] Complete Step 2/4/6 transitions -> tone style consistent
4. [ ] Step 7 `🤖 Помоги переформулировать` -> style differs by mode
5. [ ] Final card preface style differs by mode
6. [ ] `/history` summary labels/hints differ by mode
7. [ ] `/help` style differs by mode

## Pass criteria
- [ ] Clear and visible differences between all 4 modes
- [ ] No dead-ends or callback failures
- [ ] No extra spam from tone switching
