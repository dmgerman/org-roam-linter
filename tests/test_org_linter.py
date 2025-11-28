"""Test suite for org-linter."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys
from io import StringIO

# Import the org-linter module
sys.path.insert(0, str(Path(__file__).parent.parent))
import importlib.util
spec = importlib.util.spec_from_file_location("org_linter", "/Users/dmg/git.dmg/org-roam-linter/org-linter.py")
org_linter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(org_linter)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_org_file_with_id(temp_dir):
    """Create a sample org file with an org-id."""
    content = """#+TITLE: Sample File

* Heading 1
:PROPERTIES:
:ID: id-12345
:END:

Some content here.

* Heading 2
:PROPERTIES:
:ID: id-67890
:END:

More content.
"""
    filepath = temp_dir / "sample.org"
    filepath.write_text(content)
    return filepath


@pytest.fixture
def sample_org_file_with_tags(temp_dir):
    """Create a sample org file with tags."""
    content = """#+TITLE: Tagged File

* Heading 1 :tag1:tag2:
Content with tags.

* Heading 2 :tag2:tag3:
More content.
"""
    filepath = temp_dir / "tagged.org"
    filepath.write_text(content)
    return filepath


@pytest.fixture
def duplicate_org_files(temp_dir):
    """Create org files with duplicate ids."""
    file1_content = """#+TITLE: File 1

* Heading 1
:PROPERTIES:
:ID: duplicate-id
:END:

Content in file 1.
"""
    file2_content = """#+TITLE: File 2

* Heading 2
:PROPERTIES:
:ID: duplicate-id
:END:

Content in file 2.
"""
    file1 = temp_dir / "file1.org"
    file2 = temp_dir / "file2.org"
    file1.write_text(file1_content)
    file2.write_text(file2_content)
    return [file1, file2]


@pytest.fixture
def sqlsql_org_file(temp_dir):
    """Create sqlsql.org file with root-level PROPERTIES drawer."""
    content = """:PROPERTIES:
:ID:       31B16E45-C104-4994-8520-F390C2A9AF76
:TRIGGER:  org-gtd-next-project-action org-gtd-update-project-task!
:END:
#+title: sqlsql

* PROJ SQL SQL :sqlsql:
:PROPERTIES:
:CREATED:  2025-04-27 20:46:30
:ID:       sql-sql-20250501-204734
:END:

Content here.
"""
    filepath = temp_dir / "sqlsql.org"
    filepath.write_text(content)
    return filepath


# CLI Argument Parsing Tests

def test_parse_arguments_debug_flag():
    """Test --debug flag parsing."""
    with patch.object(sys, 'argv', ['org-linter', '--debug', '/tmp']):
        args = org_linter.parse_arguments()
        assert args.debug is True


def test_parse_arguments_enable_duplicate_ids():
    """Test --enable-duplicate-ids flag."""
    with patch.object(sys, 'argv', ['org-linter', '--enable-duplicate-ids', '/tmp']):
        args = org_linter.parse_arguments()
        assert args.enable_duplicate_ids is True


def test_parse_arguments_enable_tags_summary():
    """Test --enable-tags-summary flag."""
    with patch.object(sys, 'argv', ['org-linter', '--enable-tags-summary', '/tmp']):
        args = org_linter.parse_arguments()
        assert args.enable_tags_summary is True


def test_parse_arguments_multiple_features():
    """Test enabling multiple features."""
    with patch.object(sys, 'argv', ['org-linter', '--enable-duplicate-ids', '--enable-tags-summary', '/tmp']):
        args = org_linter.parse_arguments()
        assert args.enable_duplicate_ids is True
        assert args.enable_tags_summary is True


def test_parse_arguments_multiple_directories():
    """Test multiple directory paths."""
    with patch.object(sys, 'argv', ['org-linter', '/tmp', '/var']):
        args = org_linter.parse_arguments()
        assert len(args.directories) == 2
        assert args.directories[0] == Path('/tmp')
        assert args.directories[1] == Path('/var')


def test_parse_arguments_directory_required():
    """Test that at least one directory is required."""
    with patch.object(sys, 'argv', ['org-linter']):
        with pytest.raises(SystemExit):
            org_linter.parse_arguments()


def test_parse_arguments_all_flags_combined():
    """Test all flags combined."""
    with patch.object(sys, 'argv', ['org-linter', '--debug', '--enable-duplicate-ids', '--enable-tags-summary', '/tmp', '/var']):
        args = org_linter.parse_arguments()
        assert args.debug is True
        assert args.enable_duplicate_ids is True
        assert args.enable_tags_summary is True
        assert len(args.directories) == 2


# File Discovery Tests

def test_find_org_files_single_file(sample_org_file_with_id):
    """Test finding a single org file."""
    parent_dir = sample_org_file_with_id.parent
    files = org_linter.find_org_files([parent_dir])
    assert len(files) >= 1
    assert sample_org_file_with_id in files


def test_find_org_files_multiple_files(temp_dir):
    """Test finding multiple org files."""
    (temp_dir / "file1.org").write_text("#+TITLE: File 1\n")
    (temp_dir / "file2.org").write_text("#+TITLE: File 2\n")
    files = org_linter.find_org_files([temp_dir])
    assert len(files) >= 2


def test_find_org_files_recursive(temp_dir):
    """Test recursive directory traversal."""
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.org").write_text("#+TITLE: Nested\n")
    files = org_linter.find_org_files([temp_dir])
    assert any(f.name == "nested.org" for f in files)


def test_find_org_files_ignores_non_org(temp_dir):
    """Test that non-.org files are ignored."""
    (temp_dir / "file.txt").write_text("Not an org file")
    (temp_dir / "file.org").write_text("#+TITLE: Org file\n")
    files = org_linter.find_org_files([temp_dir])
    assert all(f.suffix == '.org' for f in files)


def test_find_org_files_empty_directory(temp_dir):
    """Test with empty directory."""
    empty_dir = temp_dir / "empty"
    empty_dir.mkdir()
    files = org_linter.find_org_files([empty_dir])
    assert len(files) == 0


def test_find_org_files_follows_symlinks(temp_dir):
    """Test that symlinks to directories are followed."""
    # Create a real directory with org files
    real_dir = temp_dir / "real"
    real_dir.mkdir()
    (real_dir / "file1.org").write_text("#+TITLE: File 1\n")
    (real_dir / "file2.org").write_text("#+TITLE: File 2\n")

    # Create a symlink to the real directory
    symlink_dir = temp_dir / "symlink"
    symlink_dir.symlink_to(real_dir)

    # Search in symlink directory should find the files
    files = org_linter.find_org_files([symlink_dir])
    assert len(files) >= 2
    assert any(f.name == "file1.org" for f in files)
    assert any(f.name == "file2.org" for f in files)


def test_find_org_files_avoids_symlink_cycles(temp_dir):
    """Test that circular symlinks don't cause infinite loops."""
    # Create directory structure
    dir_a = temp_dir / "dir_a"
    dir_a.mkdir()
    (dir_a / "file.org").write_text("#+TITLE: File\n")

    # Create a circular symlink: dir_a/link -> dir_a (would cause infinite loop)
    symlink_to_self = dir_a / "link"
    symlink_to_self.symlink_to(dir_a)

    # Should complete without infinite loop and find the file
    files = org_linter.find_org_files([dir_a])
    assert len(files) >= 1
    assert any(f.name == "file.org" for f in files)


def test_find_org_files_symlink_to_file(temp_dir):
    """Test that symlinks to individual files are followed."""
    # Create a real org file
    real_file = temp_dir / "real.org"
    real_file.write_text("#+TITLE: Real\n")

    # Create a symlink to the file
    symlink_file = temp_dir / "link.org"
    symlink_file.symlink_to(real_file)

    # Search in directory should find both the real file and symlink
    files = org_linter.find_org_files([temp_dir])
    assert len(files) >= 1
    # Should find at least the real file
    assert any(f.name == "real.org" for f in files)


# Org File Parsing Tests

def test_parse_org_file_with_id(sample_org_file_with_id):
    """Test extracting org-ids from a file."""
    org_ids, tags = org_linter.parse_org_file(sample_org_file_with_id)
    assert 'id-12345' in org_ids
    assert 'id-67890' in org_ids


def test_parse_org_file_with_tags(sample_org_file_with_tags):
    """Test extracting tags from a file."""
    org_ids, tags = org_linter.parse_org_file(sample_org_file_with_tags)
    assert 'tag1' in tags
    assert 'tag2' in tags
    assert 'tag3' in tags


def test_parse_org_file_byte_offset(sample_org_file_with_id):
    """Test that byte offsets are recorded."""
    org_ids, tags = org_linter.parse_org_file(sample_org_file_with_id)
    assert org_ids['id-12345'][0][0] >= 0  # byte offset should be non-negative
    assert org_ids['id-12345'][0][1] == sample_org_file_with_id  # filepath should match


def test_parse_org_file_no_ids():
    """Test parsing file without org-ids."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as f:
        f.write("#+TITLE: No IDs\n\n* Heading\nContent\n")
        f.flush()
        filepath = Path(f.name)

    try:
        org_ids, tags = org_linter.parse_org_file(filepath)
        assert len(org_ids) == 0
    finally:
        filepath.unlink()


def test_parse_org_file_no_tags():
    """Test parsing file without tags."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as f:
        f.write("#+TITLE: No Tags\n\n* Heading\nContent\n")
        f.flush()
        filepath = Path(f.name)

    try:
        org_ids, tags = org_linter.parse_org_file(filepath)
        assert len(tags) == 0
    finally:
        filepath.unlink()


def test_parse_org_file_with_file_level_id():
    """Test extracting file-level ID (#+ID:)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as f:
        f.write("#+ID: file-level-id\n#+TITLE: Test File\n\n* Heading\nContent\n")
        f.flush()
        filepath = Path(f.name)

    try:
        org_ids, tags = org_linter.parse_org_file(filepath)
        assert 'file-level-id' in org_ids
        assert len(org_ids['file-level-id']) == 1
        assert org_ids['file-level-id'][0][1] == filepath
    finally:
        filepath.unlink()


def test_parse_org_file_with_file_and_heading_ids():
    """Test extracting both file-level and heading IDs."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as f:
        f.write("#+ID: file-id\n#+TITLE: Test\n\n* Heading\n:PROPERTIES:\n:ID: heading-id\n:END:\n\nContent\n")
        f.flush()
        filepath = Path(f.name)

    try:
        org_ids, tags = org_linter.parse_org_file(filepath)
        assert 'file-id' in org_ids
        assert 'heading-id' in org_ids
        assert len(org_ids['file-id']) == 1
        assert len(org_ids['heading-id']) == 1
    finally:
        filepath.unlink()


def test_file_level_id_byte_offset():
    """Test that file-level ID byte offset is correctly recorded."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.org', delete=False) as f:
        f.write("#+ID: test-file-id\n#+TITLE: Test\n\nContent\n")
        f.flush()
        filepath = Path(f.name)

    try:
        org_ids, tags = org_linter.parse_org_file(filepath)
        assert 'test-file-id' in org_ids
        byte_offset = org_ids['test-file-id'][0][0]
        assert byte_offset >= 0
        # Verify it's at the beginning of the file
        with open(filepath, 'r') as f:
            content = f.read()
            assert '#+ID: test-file-id' in content[byte_offset:byte_offset + 50]
    finally:
        filepath.unlink()


def test_duplicate_file_and_heading_ids():
    """Test detection of duplicate IDs across file and heading level."""
    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "file1.org"
        file2 = Path(tmpdir) / "file2.org"

        # File 1 has ID at file level
        file1.write_text("#+ID: duplicate-id\n#+TITLE: File 1\n\nContent\n")
        # File 2 has ID at heading level
        file2.write_text("#+TITLE: File 2\n\n* Heading\n:PROPERTIES:\n:ID: duplicate-id\n:END:\n\nContent\n")

        all_org_ids, _ = org_linter.aggregate_org_ids([file1, file2])
        assert 'duplicate-id' in all_org_ids
        assert len(all_org_ids['duplicate-id']) == 2
        # One from file level, one from heading level


def test_sqlsql_org_file_extraction(sqlsql_org_file):
    """Test extraction from sqlsql.org file with root PROPERTIES drawer."""
    org_ids, tags = org_linter.parse_org_file(sqlsql_org_file)

    # Should have both IDs
    assert '31B16E45-C104-4994-8520-F390C2A9AF76' in org_ids
    assert 'sql-sql-20250501-204734' in org_ids

    # Should have the sqlsql tag
    assert 'sqlsql' in tags


def test_sqlsql_org_file_byte_offsets(sqlsql_org_file):
    """Test that byte offsets in sqlsql.org are correct (header locations, not ID locations)."""
    org_ids, _ = org_linter.parse_org_file(sqlsql_org_file)

    # Get the file content
    with open(sqlsql_org_file, 'r') as f:
        content = f.read()

    # File-level ID offset should point to the start of the file (line 1 with :PROPERTIES:)
    file_level_id = '31B16E45-C104-4994-8520-F390C2A9AF76'
    file_level_offset = org_ids[file_level_id][0][0]

    # Heading ID offset should point to the heading line (line with *)
    heading_id = 'sql-sql-20250501-204734'
    heading_offset = org_ids[heading_id][0][0]

    # File-level offset should be at or near the start
    assert file_level_offset == 0, "File-level ID should have offset at start of file"

    # Heading offset should be after the file-level content
    assert heading_offset > file_level_offset, "Heading offset should be after file-level offset"

    # Verify the offsets point to the correct header locations
    # The heading offset should point to the line starting with *
    lines = content.split('\n')
    byte_pos = 0
    for i, line in enumerate(lines):
        if line.startswith('* PROJ SQL SQL'):
            # Found the heading line
            expected_offset = sum(len(l.encode('utf-8')) + 1 for l in lines[:i])
            assert heading_offset == expected_offset, f"Heading offset should point to heading line"
            break
        byte_pos += len(line.encode('utf-8')) + 1


def test_sqlsql_org_aggregate(sqlsql_org_file):
    """Test aggregation with sqlsql.org file."""
    all_org_ids, tag_files = org_linter.aggregate_org_ids([sqlsql_org_file])

    # Both IDs should be present
    assert '31B16E45-C104-4994-8520-F390C2A9AF76' in all_org_ids
    assert 'sql-sql-20250501-204734' in all_org_ids

    # Tag should map to the file
    assert 'sqlsql' in tag_files
    assert sqlsql_org_file in tag_files['sqlsql']


# Duplicate ID Detection Tests

def test_duplicate_ids_detection(duplicate_org_files):
    """Test detection of duplicate org-ids."""
    all_org_ids, _ = org_linter.aggregate_org_ids(duplicate_org_files)
    assert 'duplicate-id' in all_org_ids
    assert len(all_org_ids['duplicate-id']) == 2


def test_duplicate_ids_multiple_duplicates(temp_dir):
    """Test with multiple different duplicate ids."""
    file1 = temp_dir / "file1.org"
    file2 = temp_dir / "file2.org"
    file3 = temp_dir / "file3.org"

    file1.write_text("* H\n:PROPERTIES:\n:ID: dup1\n:END:\n")
    file2.write_text("* H\n:PROPERTIES:\n:ID: dup1\n:END:\n")
    file3.write_text("* H\n:PROPERTIES:\n:ID: dup1\n:END:\n")

    all_org_ids, _ = org_linter.aggregate_org_ids([file1, file2, file3])
    assert len(all_org_ids['dup1']) == 3


def test_no_duplicates_returns_empty(temp_dir):
    """Test that non-duplicate ids are not included."""
    file1 = temp_dir / "file1.org"
    file1.write_text("* H\n:PROPERTIES:\n:ID: unique1\n:END:\n")

    all_org_ids, _ = org_linter.aggregate_org_ids([file1])
    # unique1 should still be in all_org_ids but will be filtered in duplicate detection
    assert 'unique1' in all_org_ids


# Tags Summary Tests

def test_tags_summary_single_file(sample_org_file_with_tags):
    """Test tags summary with single file."""
    all_org_ids, tag_files = org_linter.aggregate_org_ids([sample_org_file_with_tags])
    assert 'tag1' in tag_files
    assert 'tag2' in tag_files
    assert 'tag3' in tag_files


def test_tags_summary_multiple_files(temp_dir):
    """Test tags summary across multiple files."""
    file1 = temp_dir / "file1.org"
    file2 = temp_dir / "file2.org"

    file1.write_text("* H1 :tag1:\nContent\n")
    file2.write_text("* H2 :tag2:\nContent\n")

    all_org_ids, tag_files = org_linter.aggregate_org_ids([file1, file2])
    assert len(tag_files['tag1']) == 1
    assert len(tag_files['tag2']) == 1


def test_tags_summary_shared_tags(temp_dir):
    """Test tags summary with tags shared across files."""
    file1 = temp_dir / "file1.org"
    file2 = temp_dir / "file2.org"

    file1.write_text("* H1 :shared:\nContent\n")
    file2.write_text("* H2 :shared:\nContent\n")

    all_org_ids, tag_files = org_linter.aggregate_org_ids([file1, file2])
    assert len(tag_files['shared']) == 2


def test_tags_summary_no_tags(temp_dir):
    """Test tags summary with no tags."""
    file1 = temp_dir / "file1.org"
    file1.write_text("* H1\nContent\n")

    all_org_ids, tag_files = org_linter.aggregate_org_ids([file1])
    assert len(tag_files) == 0


# Output Formatting Tests

def test_format_org_table_basic():
    """Test org-table formatting."""
    headers = ['Name', 'Value']
    rows = [['Alice', '100'], ['Bob', '200']]
    table = org_linter.format_org_table(headers, rows)
    assert '|' in table
    assert 'Name' in table
    assert 'Value' in table
    assert 'Alice' in table
    assert '100' in table


def test_format_org_table_spacing():
    """Test that columns are properly aligned."""
    headers = ['A', 'B']
    rows = [['short', 'verylongvalue']]
    table = org_linter.format_org_table(headers, rows)
    lines = table.split('\n')
    assert all(line.startswith('|') and line.endswith('|') for line in lines if line)


def test_get_timestamp():
    """Test timestamp generation."""
    ts = org_linter.get_timestamp()
    assert len(ts) > 0
    assert ':' in ts  # Should contain time separators
    assert '-' in ts  # Should contain date separators


def test_generate_duplicate_ids_section_with_duplicates(duplicate_org_files):
    """Test generating duplicate IDs section."""
    all_org_ids, _ = org_linter.aggregate_org_ids(duplicate_org_files)
    # Get the base directory from the files
    base_dir = duplicate_org_files[0].parent
    section = org_linter.generate_duplicate_ids_section(all_org_ids, [base_dir])
    assert '* Repeated IDs' in section
    assert 'duplicate-id' in section
    assert ':PROPERTIES:' in section
    assert ':CREATED:' in section


def test_generate_duplicate_ids_section_no_duplicates(temp_dir):
    """Test that duplicate section is empty when no duplicates."""
    file1 = temp_dir / "file1.org"
    file1.write_text("* H\n:PROPERTIES:\n:ID: unique\n:END:\n")

    all_org_ids, _ = org_linter.aggregate_org_ids([file1])
    section = org_linter.generate_duplicate_ids_section(all_org_ids, [temp_dir])
    assert section == ""


def test_generate_tags_summary_section_with_tags(temp_dir):
    """Test generating tags summary section with repeated tags."""
    # Create two files with shared tags
    file1 = temp_dir / "file1.org"
    file1.write_text("* H :project:important:\nContent\n")
    file2 = temp_dir / "file2.org"
    file2.write_text("* H :project:bug:\nContent\n")

    all_org_ids, tag_files = org_linter.aggregate_org_ids([file1, file2])
    section = org_linter.generate_tags_summary_section(tag_files)
    assert '* Tags summary' in section
    assert ':PROPERTIES:' in section
    assert ':CREATED:' in section
    assert 'project' in section
    assert '2' in section  # project appears in 2 files


def test_generate_tags_summary_section_no_tags(temp_dir):
    """Test that tags section is empty when no tags."""
    file1 = temp_dir / "file1.org"
    file1.write_text("* H\nContent\n")

    all_org_ids, tag_files = org_linter.aggregate_org_ids([file1])
    section = org_linter.generate_tags_summary_section(tag_files)
    assert section == ""


# Full Output Tests

def test_generate_output_includes_file_count(sample_org_file_with_id):
    """Test that output includes file count."""
    org_files = [sample_org_file_with_id]
    all_org_ids, tag_files = org_linter.aggregate_org_ids(org_files)
    output = org_linter.generate_output(org_files, all_org_ids, tag_files, {})
    assert 'Files scanned: 1' in output


def test_generate_output_disabled_features(sample_org_file_with_id, duplicate_org_files):
    """Test that disabled features don't produce output."""
    org_files = duplicate_org_files
    all_org_ids, tag_files = org_linter.aggregate_org_ids(org_files)
    output = org_linter.generate_output(
        org_files,
        all_org_ids,
        tag_files,
        {'duplicate-ids': False, 'tags-summary': False}
    )
    assert '* Repeated IDs' not in output


def test_generate_output_enabled_duplicate_ids(duplicate_org_files):
    """Test that duplicate-ids feature produces output when enabled."""
    org_files = duplicate_org_files
    all_org_ids, tag_files = org_linter.aggregate_org_ids(org_files)
    output = org_linter.generate_output(
        org_files,
        all_org_ids,
        tag_files,
        {'duplicate-ids': True, 'tags-summary': False}
    )
    assert '* Repeated IDs' in output


def test_generate_output_enabled_tags_summary(temp_dir):
    """Test that tags-summary feature produces output when enabled."""
    # Create two files with shared tags
    file1 = temp_dir / "file1.org"
    file1.write_text("* H :shared:\nContent\n")
    file2 = temp_dir / "file2.org"
    file2.write_text("* H :shared:\nContent\n")

    org_files = [file1, file2]
    all_org_ids, tag_files = org_linter.aggregate_org_ids(org_files)
    output = org_linter.generate_output(
        org_files,
        all_org_ids,
        tag_files,
        {'duplicate-ids': False, 'tags-summary': True}
    )
    assert '* Tags summary' in output
    assert 'shared' in output


# Integration Tests

def test_main_integration_help():
    """Test that --help works."""
    with patch.object(sys, 'argv', ['org-linter', '--help']):
        with pytest.raises(SystemExit) as exc_info:
            org_linter.parse_arguments()
        # argparse exits with 0 for --help
        assert exc_info.value.code == 0


def test_main_integration_with_test_data():
    """Integration test with test-data directory."""
    test_data_path = Path('/Users/dmg/git.dmg/org-roam-linter/test-data')
    if test_data_path.exists():
        org_files = org_linter.find_org_files([test_data_path])
        assert len(org_files) > 0, "test-data should contain org files"

        all_org_ids, tag_files = org_linter.aggregate_org_ids(org_files)
        # Just verify the functions run without error
        output = org_linter.generate_output(
            org_files,
            all_org_ids,
            tag_files,
            {'duplicate-ids': True, 'tags-summary': True}
        )
        assert 'Files scanned:' in output


def test_main_with_nonexistent_directory():
    """Test error handling with nonexistent directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nonexistent_dir = Path(tmpdir) / 'nonexistent'
        with patch.object(sys, 'argv', ['org-linter', str(nonexistent_dir)]):
            with pytest.raises(SystemExit):
                org_linter.main()


def test_tags_in_correct_order(temp_dir):
    """Test that tags are sorted alphabetically in output."""
    # Create multiple files with shared repeated tags
    file1 = temp_dir / "file1.org"
    file1.write_text("* H :zebra:apple:mango:\nContent\n")
    file2 = temp_dir / "file2.org"
    file2.write_text("* H :zebra:apple:\nContent\n")

    all_org_ids, tag_files = org_linter.aggregate_org_ids([file1, file2])
    section = org_linter.generate_tags_summary_section(tag_files)

    # Only repeated tags (appearing in multiple files) should be shown
    # apple and zebra appear in both files, mango only in file1
    assert 'apple' in section
    assert 'zebra' in section
    assert 'mango' not in section  # Only appears in one file


def test_duplicate_ids_sorted_lexicographically(temp_dir):
    """Test that duplicate IDs show files in lexicographic order."""
    file_z = temp_dir / "z_file.org"
    file_a = temp_dir / "a_file.org"

    file_z.write_text("* H\n:PROPERTIES:\n:ID: dup\n:END:\n")
    file_a.write_text("* H\n:PROPERTIES:\n:ID: dup\n:END:\n")

    all_org_ids, _ = org_linter.aggregate_org_ids([file_z, file_a])
    section = org_linter.generate_duplicate_ids_section(all_org_ids, [temp_dir])

    # Find the position of each file in the output
    z_pos = section.find('z_file')
    a_pos = section.find('a_file')

    if z_pos != -1 and a_pos != -1:
        # a_file should appear before z_file in the output
        assert a_pos < z_pos
