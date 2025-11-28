# DO NOT READ any files in tests-data

# Code Quality and Style

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

# Project Overview

## Purpose
Org-linter scans and analyzes org-mode files to detect issues like duplicate IDs and generate tag summaries across a knowledge base. It's designed to help users maintain consistency in org-roam and other org-mode note systems.

## Key Files
- **org-linter.py**: Main executable script containing all functionality
- **tests/test_org_linter.py**: Test suite for the tool
- **README.org**: User-facing documentation in org-mode format
- **test-data/**: Test fixtures (do not read)
- **specs/**: Implementation specifications and documentation

## Core Data Structures
- **all_org_ids**: `Dict[str, List[Tuple[int, Path]]]` - Maps org-id strings to list of (byte_offset, filepath) tuples where they appear
- **tag_files**: `Dict[str, Set[Path]]` - Maps tag names to set of filepaths containing that tag
- **enable_features**: `Dict[str, bool]` - Feature toggles for duplicate-ids and tags-summary

## Main Functions

### Parsing & Discovery
- **find_org_files(directories)**: Recursively finds .org files with symlink support and cycle detection
- **parse_org_file(filepath)**: Parses single file, extracts org-ids and tags with byte offsets
- **aggregate_org_ids(org_files)**: Combines data from all files into unified structures

### Reporting
- **generate_duplicate_ids_section()**: Creates table of duplicate IDs with file locations
- **generate_tags_summary_section()**: Creates table of tags appearing in multiple files
- **generate_output()**: Orchestrates all output generation with org-mode formatting
- **format_org_table()**: Formats tabular data as org-mode tables

### Utilities
- **_traverse_nodes(node)**: Recursive generator for traversing org node tree
- **_get_byte_offset_for_line()**: Calculates byte position for linking to specific lines
- **setup_logging()**: Configures logging based on debug flag

## Command-Line Interface
Main entry point is `parse_arguments()` which sets up:
- `--debug`: Enable detailed logging to stderr
- `--enable-duplicate-ids`: Show duplicate ID detection report
- `--enable-tags-summary`: Show tag distribution report
- `directories`: Positional arguments, one or more paths to scan

## Testing
Tests are in `tests/test_org_linter.py`. Run with:
```bash
python -m pytest tests/test_org_linter.py
```

## Important Implementation Notes
- File parsing uses orgparse library which handles org-mode syntax
- Both file-level IDs (#+ID:) and heading-level IDs (:PROPERTIES: drawer) are supported
- Byte offsets are used for precise file linking in org-mode output
- The tool is resilient: permission errors and parse errors don't halt execution
- All functions should follow functional programming style with immutable returns
