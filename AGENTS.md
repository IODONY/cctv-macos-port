# Agent Notes

- Default to working inside `/Users/fullcodex/CCTV_Project`; modify files outside it only when the user explicitly authorizes that scope.
- Do not use `sudo`, global installs, or global Git config.
- Keep tracking behavior intact unless an active plan says otherwise.
- Preserve artwork outcomes: The previous pairwise matched/ambiguous/no_match evaluator is not the final target. It may be reused as an auxiliary score, but the main evaluation target is Top-K retrieval, especially OwnCount@9 and Recall@9.
- Run `scripts/agent_validate.sh` before committing code changes.
- Commit small milestones and push without force.
- Put runtime output in `logs/` or `snapshots/`; both are ignored.
