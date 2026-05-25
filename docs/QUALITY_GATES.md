# Quality Gates

- Startup checks: user is `fullcodex`, root is `/Users/fullcodex/CCTV_Project`, branch is `mac-port/fullcodex-autonomy`.
- Syntax checks: `py_compile` passes for `src/`, `scripts/`, and `touchdesigner/`.
- Import checks: safe imports do not start long-running loops.
- Diagnostics: `scripts/mac_diagnostics.py` runs with no required hardware.
- Git hygiene: generated logs/videos are not staged.
- Safety scan: changed scripts/docs do not introduce forbidden external paths except in safety rules.
- Git flow: commit small stable milestones, push normally, never force push.
