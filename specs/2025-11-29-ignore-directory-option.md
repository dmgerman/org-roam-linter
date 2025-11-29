# Chore: Add --ignore-directory Command-Line Option

## Chore Description

Add a new command-line option `--ignore-directory` to allow users to exclude specific directories from being scanned. This option:
- Can be specified multiple times to ignore multiple directories
- Accepts both relative paths (relative to base directory) and absolute/full paths
- Should efficiently filter directories during the recursive scan to avoid unnecessary traversal
- Should handle both symlinked and real paths consistently
- Should work correctly with the existing symlink cycle detection

## Relevant Files

### Core Implementation Files
- **org-linter.py** - Main script requiring modifications:
  - `parse_arguments()` (line 331-365): Add new argument definition
  - `find_org_files()` (line 23-55): Modify to accept and filter ignore directories
  - `_find_recursive()` (line 28-50): Implement filtering logic
  - `main()` (line 368-400): Pass ignore directories through the pipeline

### Test Files
- **tests/test_org_linter.py** - Test suite requiring new tests:
  - Add tests for argument parsing with `--ignore-directory`
  - Add tests for single ignored directory filtering
  - Add tests for multiple ignored directories
  - Add tests for relative path matching
  - Add tests for absolute path matching
  - Add tests for symlink handling with ignored directories
  - Add tests for nested directory filtering
  - Add integration tests with ignore functionality

### New Files
None required - all changes are to existing files

## Step by Step Tasks

### Step 1: Update Argument Parser
- Modify `parse_arguments()` function to add `--ignore-directory` argument
- Use `action='append'` to allow multiple specifications
- Set default to empty list
- Add help text explaining relative and absolute path support

### Step 2: Update find_org_files() Function Signature
- Add `ignore_directories: List[Path] = None` parameter
- Initialize to empty list if None provided
- Pass parameter to `_find_recursive()` internal function

### Step 3: Implement Ignore Directory Logic in _find_recursive()
- Normalize ignore paths (convert relative paths to absolute based on base directory)
- Create a helper function `_should_ignore_directory(directory: Path, ignore_directories: List[Path]) -> bool`:
  - Resolve both the current directory AND each ignore directory to their real paths using `.resolve()`
  - Check for matches in BOTH forms:
    - Match resolved real paths: `directory.resolve() == ignore_dir.resolve()`
    - Match path components: handle cases where user specified symlink path vs actual path
  - Handle the scenario where user provides a symlink path to ignore: check if resolving it matches any current path
  - Handle the scenario where user provides an actual path: check if it matches the resolved form of current path
- Before traversing each directory in `_find_recursive()`, call `_should_ignore_directory()` and skip if True
- Log ignored directories when debug mode is enabled, showing both the provided path and resolved real path

### Step 4: Update main() Function
- Parse the `--ignore-directory` arguments into Path objects
- Resolve relative paths using `.resolve()` (relative to current working directory, not base directories)
- Pass ignore_directories list to `find_org_files()` call

### Step 5: Create Comprehensive Tests
Create the following test functions in tests/test_org_linter.py:

#### Argument Parsing Tests
- `test_parse_arguments_ignore_directory_single()` - Single ignore directory
- `test_parse_arguments_ignore_directory_multiple()` - Multiple ignore directories
- `test_parse_arguments_ignore_directory_with_other_flags()` - Combination with other flags

#### File Discovery with Ignore Tests
- `test_find_org_files_ignores_directory()` - Verify directory is skipped
- `test_find_org_files_ignores_multiple_directories()` - Multiple ignored directories
- `test_find_org_files_ignores_nested_directory()` - Nested directory filtering
- `test_find_org_files_absolute_path_ignore()` - Absolute path matching
- `test_find_org_files_relative_path_ignore()` - Relative path matching
- `test_find_org_files_ignores_symlink_by_symlink_path()` - Ignore when specifying the symlink path itself (--ignore-directory /path/to/symlink)
- `test_find_org_files_ignores_symlink_by_target_path()` - Ignore when specifying the target directory path (--ignore-directory /path/to/actual/target)
- `test_find_org_files_ignores_target_when_accessed_via_symlink()` - Directory ignored when accessed through symlink even if ignore path was the real path
- `test_find_org_files_ignores_symlink_path_when_accessed_as_real()` - Directory ignored when accessed as real path even if ignore path was the symlink
- `test_find_org_files_partial_path_no_match()` - Ensure partial paths don't match
- `test_find_org_files_ignore_doesnt_affect_base_dir()` - Base directory still scanned

#### Integration Tests
- `test_main_with_ignore_directory()` - Full integration test with main()
- `test_main_with_multiple_base_dirs_and_ignore()` - Multiple base directories with ignore

### Step 6: Validation Commands
Execute the following commands to validate the implementation:

```bash
# Run all tests to ensure no regressions
python -m pytest tests/test_org_linter.py -v

# Test specific test functions
python -m pytest tests/test_org_linter.py::test_parse_arguments_ignore_directory_single -v
python -m pytest tests/test_org_linter.py::test_find_org_files_ignores_directory -v
python -m pytest tests/test_org_linter.py::test_find_org_files_ignores_multiple_directories -v
python -m pytest tests/test_org_linter.py::test_main_with_ignore_directory -v

# Verify code follows functional programming style and DRY principle
python -m pytest tests/test_org_linter.py -v --tb=short

# Check that original functionality still works (no regressions)
python -m pytest tests/test_org_linter.py::test_find_org_files_recursive -v
python -m pytest tests/test_org_linter.py::test_find_org_files_follows_symlinks -v
python -m pytest tests/test_org_linter.py::test_find_org_files_avoids_symlink_cycles -v
```

## Document Changes

Update README.org to document the new `--ignore-directory` feature:

1. Add section under "Features" describing the ignore functionality
2. Add usage example showing single ignore directory: `./org-linter.py --ignore-directory .git ~/notes`
3. Add example showing multiple ignore directories
4. Add note about relative vs absolute path behavior
5. Add tips section note about common directories to ignore (`.git`, `.obsidian`, `node_modules`, etc.)

## Git Log

```
Add --ignore-directory command-line option for filtering directories

Users can now exclude specific directories from scanning using the
--ignore-directory flag (can appear multiple times). Supports both
relative paths (relative to base directory) and absolute paths.
Implements efficient directory filtering during traversal to avoid
unnecessary recursion. Includes comprehensive tests for argument parsing,
single/multiple directory filtering, and symlink handling.
```

## Notes

### Implementation Considerations

1. **Bidirectional Symlink Matching**: Handle symlinks in both directions:
   - **User specifies symlink path** (e.g., `--ignore-directory /scan/symlink_link`): Must ignore when directory is accessed via that symlink
   - **User specifies actual/target path** (e.g., `--ignore-directory /real/actual/path`): Must ignore when directory is accessed as real path OR via any symlink pointing to it
   - **Solution**: Always resolve to real path using `.resolve()` for matching. Compare resolved real paths of both the current traversal directory and all ignore directories

2. **Relative Path Behavior**: Relative paths are resolved relative to the current working directory (using `.resolve()`). Each `--ignore-directory` is an independent path specification that applies globally across all base directories being scanned.

3. **Efficiency**: Filter directories before recursing to avoid unnecessary traversal

4. **Symlink Safety**: Ensure ignore functionality doesn't interfere with existing cycle detection (already handled by `.resolve()` and visited set)

5. **Case Sensitivity**: Respect OS conventions (case-insensitive on macOS/Windows, case-sensitive on Linux)

### Testing Strategy

- Test both relative and absolute paths
- Test comprehensive symlink scenarios:
  - Ignore a symlink path itself (--ignore-directory /path/to/symlink) and verify it's ignored whether accessed as symlink or real path
  - Ignore the actual target path (--ignore-directory /real/target) and verify it's ignored whether accessed as real path or via symlink
  - Verify that if a directory is ignored via its real path, ALL symlinks to it are also ignored
  - Verify that if a directory is ignored via a symlink path, the actual target is also ignored
- Test nested directories (child of ignored parent should also be ignored)
- Test that ignore doesn't break cycle detection
- Test that ignore works correctly with the existing `visited` set and `.resolve()` logic
- Test integration with existing features (duplicate detection, tags summary)
- Ensure no org files are found in ignored directories regardless of access method
- Verify that ignoring a parent directory excludes all children

### Functional Programming Approach

- Keep filtering logic pure - separate path matching from side effects
  - The `_should_ignore_directory()` helper should be a pure function: same inputs always produce same output
  - No side effects in the matching logic (only logging is acceptable for debug purposes)
- Use immutable data structures for ignore paths list
- Avoid mutations in traversal loop
- Return early from recursion rather than using conditional nesting
- Symlink resolution via `.resolve()` is pure and deterministic for path matching
