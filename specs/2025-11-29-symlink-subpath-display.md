# Chore: Fix symlink subpath display in duplicate IDs report

## Chore Description

When scanning directories that contain symlinks, the duplicate IDs report doesn't display relative subpaths correctly.

**Current behavior:** When a symlinked directory contains nested files (e.g., `/Users/dmg/tmDropbox/org/roam/links/.emacs.d/modules/yt-playlist/index.org`), the report displays only the filename (`index.org`) instead of the relative path from the scan root (`links/.emacs.d/modules/yt-playlist/index.org`).

**Expected behavior:** The display text in org-mode links should show the relative path from the base scan directory for all files, whether they are behind symlinks or not. For example:
- Current (incorrect): `[[file:/Users/dmg/tmDropbox/org/roam/links/.emacs.d/modules/yt-playlist/index.org::0][index.org::0]]`
- Expected (correct): `[[file:/Users/dmg/tmDropbox/org/roam/links/.emacs.d/modules/yt-playlist/index.org::0][links/.emacs.d/modules/yt-playlist/index.org::0]]`

## Root Cause Analysis

The issue is in the `generate_duplicate_ids_section()` function at lines 226-241 in `org-linter.py`. The current logic:

1. Resolves both the filepath and base directory to their canonical paths
2. Tries to calculate the relative path using `relative_to()`
3. Falls back to using only `filepath.name` (just the filename) when resolution fails

The problem occurs because:
- When a parent directory is a symlink, the `filepath.resolve()` returns the real path through the symlink
- The comparison with `abs_base_dir.resolve()` may not match properly due to how symlinks are resolved
- The fallback to `filepath.name` loses all directory context

The fix should preserve the relative path calculation from the original (non-resolved) filepath relative to the original (non-resolved) base directory, following the actual directory structure as traversed.

## Relevant Files

- **org-linter.py** (lines 201-257): Contains `generate_duplicate_ids_section()` function where relative path calculation and org-mode link formatting occurs
- **tests/test_org_linter.py**: Existing test suite for validation

### New Files
- A new test case needs to be added to verify symlink subpath handling works correctly

## Step by Step Tasks

### 1. Understand the current file discovery and storage mechanism

- **What we know:** The `find_org_files()` function already handles symlinks correctly and returns `Path` objects representing the actual paths as traversed (not resolved)
- **Key insight:** The filepath stored in `all_org_ids` during `parse_org_file()` and `aggregate_org_ids()` is already the non-resolved path from the traversal
- The issue is only in the display/formatting step, not in file discovery

### 2. Fix the relative path calculation in `generate_duplicate_ids_section()`

The fix involves changing the approach at lines 226-241:

- **Remove the `.resolve()` calls** that convert symlinked paths to real paths
- **Use the original (non-resolved) filepath** directly for relative path calculation
- **Compare against the original (non-resolved) base directory**
- **Keep the fallback behavior** but make it a true fallback only for edge cases

The logic should be:
1. For each location (byte_offset, filepath):
   - Try to compute relative path from each base_dir (without resolving)
   - If successful, use that relative path for display
   - Only if all base_dirs fail, use the filename only as fallback

### 3. Update the relative path calculation logic

- Change line 229: Remove `.resolve()` from `abs_filepath`
- Change line 232: Remove `.resolve()` from `abs_base_dir`
- The comparison at line 235 will then work with the original paths as traversed
- This preserves the directory structure as the user provided it, including symlink names

### 4. Create a test case for symlink subpath display

Add a test to `tests/test_org_linter.py` that:
- Creates a real directory with nested org files
- Creates a symlink to that directory
- Adds files to the symlink path to create deeper nesting
- Calls `aggregate_org_ids()` and `generate_duplicate_ids_section()`
- Verifies that the displayed relative path includes the symlink directory name and subdirectories
- Example: For path `symlink_dir/subdir/file.org`, the display should be `symlink_dir/subdir/file.org`, not just `file.org`

### 5. Validation

Run the following commands to ensure the fix works with zero regressions:

```bash
# Run all existing tests to ensure no regressions
python -m pytest tests/test_org_linter.py -v

# Specifically test the new symlink test case
python -m pytest tests/test_org_linter.py::test_duplicate_ids_symlink_subpath_display -v

# Optional: Manual test with actual symlinked directories if possible
# (This would require the actual org-roam directory structure)
```

## Validation Commands

Execute every command to validate with 100% confidence the chore is complete with zero regressions:

```bash
# 1. Run all tests - must pass with no failures
python -m pytest tests/test_org_linter.py -v

# 2. Verify test output includes the new symlink test
python -m pytest tests/test_org_linter.py::test_duplicate_ids_symlink_subpath_display -v

# 3. Check that all existing duplicate ID tests still pass
python -m pytest tests/test_org_linter.py -k duplicate -v

# 4. Verify the fix with debug output (optional, for manual inspection)
python -m pytest tests/test_org_linter.py::test_duplicate_ids_symlink_subpath_display -v -s
```

## Document changes

No documentation changes needed. The functionality remains the same; only the display format is corrected to show the proper relative paths.

## Git log

Fix symlink subpath display in duplicate IDs report

When scanning directories containing symlinks, the relative path display in
the duplicate IDs report now correctly shows the full subpath from the scan
directory instead of just the filename. For example, files accessed through
`links/.emacs.d/modules/yt-playlist/index.org` now display the full path
instead of just `index.org`.

The fix removes unnecessary path resolution (`.resolve()`) that was converting
symlinked paths to their canonical forms, which prevented proper relative path
calculation. The relative path is now computed against the original traversed
path, preserving the directory structure as provided by the user.

## Notes

- The fix is minimal and surgical - it only changes path resolution behavior in the display function
- The core file discovery and ID aggregation already work correctly with symlinks
- This change respects the principle of displaying paths as the user encountered them (via symlinks), not their canonical real paths
- The fallback to filename-only still exists for edge cases, but should rarely be needed now
- All existing tests should continue to pass as the core logic is unchanged
