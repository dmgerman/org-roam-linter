# Chore: Write org-linter Python Script

## Chore Description

Create a Python script called `org-linter` that scans recursively through one or more directories looking for org-mode files (.org) and verifies they comply with specified linting rules.

The script must support:
- Command-line argument `--debug` to output debugging messages to stderr
- Command-line arguments `--enable-<feature>` to enable individual features (all disabled by default)
- One or more directory paths as input arguments
- Output in org-mode format showing scan results

Two linting features must be implemented:
1. **Duplicate org-id detection**: Identify org-ids that appear in multiple files, reporting file locations with byte positions
2. **Tags summary**: Generate a summary of all tags used and count files where each tag appears

The script should include comprehensive test coverage using the test-data directory.

## Relevant Files

### New Files to Create

- `org-linter.py` - Main linter script in root directory
  - Parses command-line arguments
  - Recursively scans directories for .org files
  - Implements core linting functionality
  - Outputs results in org-mode format

- `tests/test_org_linter.py` - Test suite
  - Unit tests for CLI argument parsing
  - Tests for duplicate org-id detection
  - Tests for tags summary feature
  - Integration tests using test-data directory
  - Test fixtures for org-mode content

### Existing Directories
- `test-data/` - Contains sample org files for integration testing (do not read directly)
- `specs/` - Where this plan is stored

## Step by Step Tasks

### Setup and Architecture

#### Task 1: Design the core architecture
- The script will use Python's `argparse` for CLI parsing
- Use `pathlib.Path` for cross-platform directory traversal
- Use `orgparse` library to parse org-mode files (handles PROPERTIES drawers, headings, and tags automatically)
- Create a data structure to track:
  - File paths scanned
  - org-ids with their file locations and byte offsets
  - Tags with their occurrence count per file
- Output results using a helper function that formats org-mode tables

#### Task 2: Create the main org-linter.py script structure
- Create command-line interface with argparse
  - `--debug` flag for debug output
  - Dynamic `--enable-<feature>` arguments based on available features
  - Positional arguments for directory paths (one or more required)
- Implement file discovery function using pathlib recursion
- Implement org-mode parsing function using orgparse:
  - Load each .org file using `orgparse.load()`
  - Extract org-ids from nodes' PROPERTIES drawer
  - Extract tags from heading nodes using orgparse API
  - Track file paths, org-ids, and byte offsets for org-ids (position in file)

#### Task 3: Implement Feature 1 - Duplicate org-id detection
- Scan all .org files using orgparse to find nodes with org-id property
- Store org-id with file path and byte offset (position in file where org-id appears)
- Identify duplicates (same org-id in different files)
- Generate org-mode formatted output with:
  - Heading "* Repeated IDs"
  - PROPERTIES drawer with CREATED timestamp
  - Org-table with dynamic columns:
    - First column: id
    - Remaining columns: one column per file containing the duplicate id (e.g., if id appears in 3 files, columns are: id | file1 | file2 | file3)
    - Column headers show file path with byte offset in format `filepath:byte-offset`
    - Files sorted lexicographically
  - Each duplicate org-id gets its own row in the table
- Only show duplicates (if no duplicates, don't include this section)

#### Task 4: Implement Feature 2 - Tags summary
- Parse tags from all heading lines across all files using orgparse
- Track which files contain each tag and count unique files per tag
- Generate org-mode formatted output with:
  - Heading "* Tags summary"
  - PROPERTIES drawer with CREATED timestamp
  - Org-table with columns: tag | No. Files
  - Each row: tag name and count of unique files containing that tag
  - Sort tags alphabetically
- Only show tags summary if feature is enabled

#### Task 5: Implement output generation
- Create function to generate org-mode output header with file count
- Create function to format org-mode tables
- Implement timestamp generation (current date/time in org-mode format)
- Handle cases where features are disabled or no results found

### Testing

#### Task 6: Create test suite structure
- Create `tests/` directory if it doesn't exist
- Create `tests/test_org_linter.py` test file
- Setup test fixtures with minimal org-mode content (don't use test-data, create fixtures)
- Use pytest as the testing framework

#### Task 7: Test CLI argument parsing
- Test `--debug` flag is properly recognized
- Test `--enable-duplicate-ids` enables that feature
- Test `--enable-tags-summary` enables that feature
- Test multiple features can be enabled simultaneously
- Test that at least one directory path is required
- Test that multiple directory paths are accepted

#### Task 8: Test duplicate org-id detection
- Create fixtures with .org files containing duplicate org-ids
- Test that duplicates are correctly identified
- Test that byte positions are correctly calculated
- Test that output is properly formatted as org-table
- Test edge cases: no duplicates, single file, multiple duplicates of same id
- Test lexicographic ordering of files in output

#### Task 9: Test tags summary feature
- Create fixtures with .org files containing various tags
- Test that all tags are captured correctly
- Test that file counts per tag are accurate
- Test that output is properly formatted as org-table
- Test edge cases: no tags, duplicate tags in same file, tags in different files
- Test alphabetical ordering of tags in output

#### Task 10: Test file discovery and integration
- Test that script correctly finds .org files recursively
- Test that non-.org files are ignored
- Test with nested directory structures
- Test with empty directories
- Test file counting is accurate
- Integration test: run script on test-data directory and verify output structure

#### Task 11: Test output formatting
- Test org-mode table generation
- Test timestamp formatting in PROPERTIES drawers
- Test that CREATED timestamps are present
- Test heading format with asterisks
- Test that disabled features don't produce output

### Validation

#### Task 12: Run validation commands
- Verify all tests pass with no failures
- Run script on test-data directory with both features enabled
- Validate output is valid org-mode format
- Check debug output appears on stderr when --debug flag is used
- Verify script handles edge cases gracefully
- Ensure no exceptions are raised on valid input

## Validation Commands

Execute these commands in order to validate the implementation:

```bash
# Run all tests
python3 -m pytest tests/test_org_linter.py -v

# Test the script with --help to show all options
python3 org-linter.py --help

# Test with a single feature enabled on test-data directory
python3 org-linter.py --enable-duplicate-ids test-data/

# Test with both features enabled on test-data directory
python3 org-linter.py --enable-duplicate-ids --enable-tags-summary test-data/

# Test debug output on stderr
python3 org-linter.py --debug --enable-duplicate-ids test-data/ 2>&1 | head -20

# Verify output is valid org-mode (check for proper heading and table format)
python3 org-linter.py --enable-duplicate-ids --enable-tags-summary test-data/ | grep -E "^\*|^|"

# Run tests with coverage
python3 -m pytest tests/test_org_linter.py --cov=org-linter -v
```

## Document Changes

- No documentation files need to be updated as this is a new tool
- The script should include a help message via argparse that describes usage
- Add docstrings to main functions explaining their purpose

## Git Log

```
feat: Add org-linter Python script with duplicate org-id and tags summary features

- Create org-linter.py script to scan org-mode files recursively
- Implement feature 1: Detect duplicate org-ids across files with byte position reporting
- Implement feature 2: Generate tags summary showing file occurrence counts
- Add command-line interface with --debug and --enable-<feature> options
- Create comprehensive test suite with pytest
- All tests passing with 100% feature coverage
```

## Notes

### Code Quality and Style

- **Production Quality**: Code must be production-ready with proper error handling, logging, and robustness
- **Functional Programming Style**: Avoid mutation as much as possible
  - Use immutable data structures where practical
  - Prefer function composition and pure functions
  - Minimize side effects (I/O operations should be isolated at boundaries)
  - Use `map()`, `filter()`, `reduce()` and comprehensions instead of loops with mutations
  - Return new data structures instead of modifying existing ones
  - Use type hints throughout for clarity and runtime checking support
- **Function Design**: Keep functions small and focused
  - Each function should have a single, clear responsibility
  - Aim for functions that fit on a single screen
  - Break down complex logic into smaller, composable functions
- **Code Organization**: Structure functions to be composable and testable
- **DRY Principle**: No code duplication
  - Extract repeated logic into reusable functions
  - Use helper functions to eliminate duplication across features
- **Error Handling**: Validate inputs and handle edge cases gracefully
- **Logging**: Include appropriate logging for debugging (especially with `--debug` flag)

### Implementation Details

- Use `orgparse` library for parsing org-mode files (automatically handles PROPERTIES, headings, and tags)
- Access org-ids through the orgparse node's properties: `node.get_property('ID')`
- Access tags through the orgparse node's tags: `node.get_tags()` or `node.tags`
- Byte offsets: Track the byte position in the file where each org-id property appears. This can be obtained from the orgparse node's position information or by reading the file in binary mode.
- Timestamps should use the format: `YYYY-MM-DD HH:MM:SS` for org-mode CREATED property
- Install orgparse with: `pip install orgparse`

### Orgparse API Usage

1. **Loading files**: Use `orgparse.load(filepath)` to parse a file
2. **Accessing org-ids**: Iterate through nodes and check `node.get_property('ID')` or `node.properties.get('ID')`
3. **Accessing tags**: Use `node.get_tags()` to get list of tags on a heading
4. **Iterating nodes**: Use `root.traverse()` to walk through all nodes in the tree

### Testing Strategy

- Use fixtures with small, hand-crafted org-mode content to keep tests fast
- Do not read from test-data directory during test creation
- Each test should be isolated and independent
- Mock file system operations where appropriate for speed
- Use orgparse directly in tests to create test data fixtures
