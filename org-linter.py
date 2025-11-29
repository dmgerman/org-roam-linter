#!/usr/bin/env python3
"""Org-linter: Scan and lint org-mode files for compliance issues."""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Set
import orgparse
import logging


def setup_logging(debug: bool) -> None:
    """Configure logging for debug output."""
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr
    )


def find_org_files(directories: List[Path]) -> List[Path]:
    """Recursively find all .org files in given directories, following symlinks while avoiding cycles."""
    org_files = []
    visited = set()

    def _find_recursive(directory: Path) -> None:
        """Recursively traverse directory, following symlinks but avoiding infinite loops."""
        try:
            # Resolve to real path to detect cycles
            real_path = directory.resolve()
            if real_path in visited:
                return
            visited.add(real_path)
        except (OSError, RuntimeError):
            # Handle permission errors or broken symlinks
            return

        try:
            # Find .org files in current directory
            for item in directory.iterdir():
                if item.name.endswith('.org') and item.is_file(follow_symlinks=True):
                    org_files.append(item)
                elif item.is_dir(follow_symlinks=True):
                    # Recurse into subdirectories (follows symlinks)
                    _find_recursive(item)
        except (PermissionError, OSError):
            # Skip directories we can't read
            pass

    for directory in directories:
        _find_recursive(directory)

    return sorted(org_files)


def _traverse_nodes(node):
    """Recursively traverse org nodes."""
    yield node
    for child in node.children:
        yield from _traverse_nodes(child)


def _get_byte_offset_for_line(text_content: str, line_number: int) -> int:
    """Get byte offset at the start of a given line number (1-indexed)."""
    if line_number <= 1:
        return 0

    lines = text_content.split('\n')
    byte_offset = 0
    for i in range(min(line_number - 1, len(lines))):
        byte_offset += len(lines[i].encode('utf-8')) + 1  # +1 for newline
    return byte_offset


def parse_org_file(filepath: Path) -> Tuple[Dict[str, List[Tuple[int, Path]]], Set[str]]:
    """
    Parse an org file and extract org-ids and tags.

    Returns:
        Tuple of (org_ids_dict, tags_set) where:
        - org_ids_dict: {id: [(byte_offset, filepath), ...]}
        - tags_set: set of tags in this file
    """
    try:
        root = orgparse.load(str(filepath))
    except Exception as e:
        logging.warning(f"Failed to parse {filepath}: {e}")
        return {}, set()

    org_ids = {}
    tags = set()

    # Read file to get byte positions
    with open(filepath, 'rb') as f:
        content = f.read()

    text_content = content.decode('utf-8', errors='ignore')

    for node in _traverse_nodes(root):
        # Extract org-ids from PROPERTIES drawer or file-level properties
        if node.is_root():
            # For root node, try both file-level metadata and root PROPERTIES drawer
            org_id = node.get_file_property('ID')  # #+ID: metadata
            if not org_id:
                org_id = node.properties.get('ID')  # :PROPERTIES: drawer at file start
            id_type = 'file-level'
        else:
            # For heading nodes, use get_property to access PROPERTIES drawer ID
            org_id = node.get_property('ID')
            id_type = 'heading'

        if org_id:
            # Get byte offset of the header/heading location (not the ID property)
            if node.is_root():
                # For file-level IDs, find the :PROPERTIES: line at start of file
                # or use line 1 if it starts with #+ID:
                byte_offset = _get_byte_offset_for_line(text_content, node.linenumber or 1)
            else:
                # For heading IDs, use the heading's line number
                byte_offset = _get_byte_offset_for_line(text_content, node.linenumber or 1)

            if byte_offset >= 0:
                if org_id not in org_ids:
                    org_ids[org_id] = []
                org_ids[org_id].append((byte_offset, filepath))
                logging.debug(f"  Extracted {id_type} ID '{org_id}' at byte offset {byte_offset}")

        # Extract tags from headings
        node_tags = node.tags
        if node_tags:
            tags.update(node_tags)

    return org_ids, tags


def aggregate_org_ids(org_files: List[Path]) -> Tuple[Dict[str, List[Tuple[int, Path]]], Dict[str, Set[Path]]]:
    """
    Aggregate org-ids and tags from all files.

    Returns:
        Tuple of (all_org_ids, tag_files) where:
        - all_org_ids: {id: [(byte_offset, filepath), ...]}
        - tag_files: {tag: set(filepaths)}
    """
    all_org_ids: Dict[str, List[Tuple[int, Path]]] = {}
    tag_files: Dict[str, Set[Path]] = {}

    for filepath in org_files:
        logging.debug(f"Parsing {filepath}")
        org_ids, tags = parse_org_file(filepath)

        # Merge org-ids
        for org_id, locations in org_ids.items():
            if org_id not in all_org_ids:
                all_org_ids[org_id] = []
            all_org_ids[org_id].extend(locations)

        # Track which files have which tags
        for tag in tags:
            if tag not in tag_files:
                tag_files[tag] = set()
            tag_files[tag].add(filepath)

    return all_org_ids, tag_files


def format_org_table(headers: List[str], rows: List[List[str]]) -> str:
    """Format data as an org-mode table."""
    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    # Format header
    separator = '| ' + ' | '.join('-' * (w + 2) for w in col_widths) + ' |'
    header_row = '| ' + ' | '.join(
        h.ljust(col_widths[i]) for i, h in enumerate(headers)
    ) + ' |'

    # Format data rows
    data_rows = []
    for row in rows:
        formatted_cells = [
            str(cell).ljust(col_widths[i])
            for i, cell in enumerate(row)
        ]
        data_rows.append('| ' + ' | '.join(formatted_cells) + ' |')

    table = '\n'.join([separator, header_row, separator] + data_rows + [separator])
    return table


def get_timestamp() -> str:
    """Get current timestamp in org-mode format."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def generate_duplicate_ids_section(all_org_ids: Dict[str, List[Tuple[int, Path]]], base_directories: List[Path]) -> str:
    """Generate org-mode section for duplicate org-ids."""
    # Filter to only duplicates
    duplicates = {
        org_id: locations
        for org_id, locations in all_org_ids.items()
        if len(locations) > 1
    }

    if not duplicates:
        return ""

    # Build table with: id | No. Files | No. Instances | files (one row per id)
    headers = ['id', 'No. Files', 'No. Instances', 'files']
    rows = []

    for org_id in sorted(duplicates.keys()):
        locations = duplicates[org_id]
        # Count unique files
        unique_files = len(set(filepath for _, filepath in locations))
        # Count total instances
        total_instances = len(locations)

        # Format each occurrence separately: [[file:<filepath>::<offset>][<relative-path>::<offset>]]
        file_list = []
        for byte_offset, filepath in sorted(locations, key=lambda x: (str(x[1]), x[0])):
            # Find which base directory this file is under and calculate relative path
            rel_path_str = filepath.name  # Default to filename only

            for base_dir in base_directories:
                try:
                    # Use original (non-resolved) paths for relative_to comparison
                    # This preserves symlink directory names in the display
                    rel_path = filepath.relative_to(base_dir)
                    rel_path_str = str(rel_path)
                    break
                except ValueError:
                    # Not relative to this base_dir
                    continue

            file_list.append(f"[[file:{filepath}::{byte_offset}][{rel_path_str}::{byte_offset}]]")

        files_str = ', '.join(file_list)
        rows.append([org_id, str(unique_files), str(total_instances), files_str])

    table = format_org_table(headers, rows)
    timestamp = get_timestamp()

    section = f"""* Repeated IDs
:PROPERTIES:
:CREATED:  {timestamp}
:END:

{table}
"""
    return section


def generate_tags_summary_section(tag_files: Dict[str, Set[Path]]) -> str:
    """Generate org-mode section for tags summary."""
    if not tag_files:
        return ""

    # Filter to only tags that appear in multiple files
    repeated_tags = {
        tag: files
        for tag, files in tag_files.items()
        if len(files) > 1
    }

    if not repeated_tags:
        return ""

    headers = ['tag', 'No. Files']
    rows = [
        [tag, str(len(files))]
        for tag, files in sorted(repeated_tags.items())
    ]

    table = format_org_table(headers, rows)
    timestamp = get_timestamp()

    section = f"""* Tags summary
:PROPERTIES:
:CREATED:  {timestamp}
:END:

{table}
"""
    return section


def generate_output(
    org_files: List[Path],
    all_org_ids: Dict[str, List[Tuple[int, Path]]],
    tag_files: Dict[str, Set[Path]],
    enable_features: Dict[str, bool],
    base_directories: List[Path] = None
) -> str:
    """Generate final org-mode output."""
    if base_directories is None:
        base_directories = []

    lines = []
    lines.append(f"#+TITLE: Org-linter Results")
    lines.append(f"#+DATE: {get_timestamp()}")
    lines.append(f"")
    lines.append(f"Files scanned: {len(org_files)}")

    # Calculate ID statistics
    total_ids = len(all_org_ids)
    duplicate_ids = sum(1 for locations in all_org_ids.values() if len(locations) > 1)

    lines.append(f"IDs found: {total_ids}")
    lines.append(f"Duplicate IDs: {duplicate_ids}")
    lines.append(f"")

    if enable_features.get('duplicate-ids', False):
        dup_section = generate_duplicate_ids_section(all_org_ids, base_directories)
        if dup_section:
            lines.append(dup_section)

    if enable_features.get('tags-summary', False):
        tags_section = generate_tags_summary_section(tag_files)
        if tags_section:
            lines.append(tags_section)

    return '\n'.join(lines)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Scan and lint org-mode files for compliance issues',
        prog='org-linter'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    parser.add_argument(
        '--enable-duplicate-ids',
        action='store_true',
        dest='enable_duplicate_ids',
        help='Enable duplicate org-id detection'
    )

    parser.add_argument(
        '--enable-tags-summary',
        action='store_true',
        dest='enable_tags_summary',
        help='Enable tags summary generation'
    )

    parser.add_argument(
        'directories',
        nargs='+',
        type=Path,
        help='One or more directories to scan'
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_arguments()

    setup_logging(args.debug)

    logging.debug(f"Scanning directories: {args.directories}")

    # Validate directories exist
    for directory in args.directories:
        if not directory.is_dir():
            logging.error(f"Directory not found: {directory}")
            sys.exit(1)

    # Find and parse org files
    org_files = find_org_files(args.directories)
    logging.debug(f"Found {len(org_files)} org files")

    if not org_files:
        logging.warning("No .org files found in specified directories")

    # Aggregate data
    all_org_ids, tag_files = aggregate_org_ids(org_files)

    # Prepare enabled features
    enable_features = {
        'duplicate-ids': args.enable_duplicate_ids,
        'tags-summary': args.enable_tags_summary,
    }

    # Generate and output results
    output = generate_output(org_files, all_org_ids, tag_files, enable_features, args.directories)
    print(output)


if __name__ == '__main__':
    main()
