# Git Safety

This repository is isolated under `/Users/fullcodex/CCTV_Project`.

Codex must not work outside this folder. No `sudo` is allowed, and no global Git configuration should be changed.

Codex must not access the original user folder or any other user folder. In particular, `/Users/Donoyung` must not be accessed.

Large runtime outputs belong in `snapshots/` and `logs/`, which are ignored by Git.

Imported source files should be copied into `src/`, `models/`, `data/`, or `touchdesigner/`.

Before major refactors, create a Git commit.

Before deleting any file, move it to `.codex_trash/`.
