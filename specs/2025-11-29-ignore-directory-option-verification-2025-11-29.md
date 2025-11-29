# Verification Log: Add --ignore-directory Command-Line Option

## Interaction History

### Initial Verification (2025-11-29)

**User Request**: Verify plan for implementing --ignore-directory command-line option

**Assistant Response**:
- Identified ambiguity regarding relative path resolution behavior
- Asked whether relative paths should resolve against first base directory or each base directory
- Flagged line 144 as unclear

**User Clarification (Round 1)**:
> The --ignore-directory=<dir> should be specified once per directory, thus they are independent of each other.

**User Clarification (Round 2)**:
> The option should be specified --ignore-directory=.git --ignore-directory=~/notes --ignore-directory=~/research. Only relative to base path, not relative to each other. In this case it will ignore only ~/.git ~/notes and ~/research (assuming it is run from directory ~)

**Final Interpretation**:
- Each `--ignore-directory` is an independent, complete path specification
- Paths are resolved relative to the **current working directory** (not to base directories being scanned)
- Can be absolute paths (e.g., `/path/to/ignore`) or relative to cwd (e.g., `.git`, `notes`)
- All ignore paths apply globally across all base directories being scanned
- Example: Running `./org-linter.py --ignore-directory=.git --ignore-directory=~/notes ~/notes ~/research` from `~` will ignore `~/.git` and `~/notes` when scanning both `~/notes` and `~/research`

**Plan Updates Made**:
- Updated Step 4 to clarify that relative paths are resolved relative to cwd using `.resolve()`
- Updated Note 2 (Relative Path Behavior) to remove ambiguity and document the final behavior

**Verification Status**: ✅ COMPLETE - All clarifications resolved and plan updated

---
