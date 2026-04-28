#!/usr/bin/env python3
"""
Stitch multiple log files together by concatenating their headers and data.

Usage:
    python stitch_log_files.py file1.csv file2.csv file3.csv -o output.csv
    python stitch_log_files.py data/*.csv -o combined.csv
"""

import argparse
import sys
from pathlib import Path


def parse_file_sections(file_path):
    """
    Parse a log file into header section and data section.
    
    Header section: all lines until and including the "==========" delimiter line
    Data section: all data rows exactly as they appear in the file (preserved verbatim)
    
    Returns:
        tuple: (header_lines, data_lines, column_headers)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, None, None

    header_lines = []
    data_lines = []
    column_headers = None
    data_start_idx = None

    # Find the delimiter line with "==========" in column index 3
    for i, line in enumerate(lines):
        parts = line.strip().split('\t')
        if len(parts) >= 4 and parts[3].strip() == "==========":
            # Header section includes all lines up to and including delimiter
            header_lines = [l.rstrip('\n') for l in lines[:i+1]]
            # Next line contains column headers
            if i + 1 < len(lines):
                column_headers = lines[i + 1].strip()
                data_start_idx = i + 2
            break
    
    # If no delimiter found, treat whole file as data (unlikely for valid files)
    if data_start_idx is None:
        print(f"Warning: No delimiter found in {file_path}, treating all as data")
        data_lines = [l.rstrip('\n') for l in lines if l.strip()]
        return [], data_lines, None

    # Extract data lines - preserve exactly as in original (only skip comments and delimiters)
    for line in lines[data_start_idx:]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('[INFO]') or stripped.startswith('LTMControl'):
            continue
        if '==========' in stripped:
            continue
        # Keep the line exactly as is (preserving any internal formatting)
        data_lines.append(line.rstrip('\n'))

    return header_lines, data_lines, column_headers


def get_last_elapsed_time(data_lines):
    """Get the last elapsed time value from data lines."""
    if not data_lines:
        return 0.0
    for line in reversed(data_lines):
        parts = line.split('\t')
        if len(parts) >= 3:
            try:
                return float(parts[2].strip())
            except ValueError:
                continue
    return 0.0


def apply_elapsed_offset(line, offset):
    """Apply offset to the elapsed time (3rd column) of a data line."""
    if offset == 0:
        return line
    parts = line.split('\t')
    if len(parts) >= 3:
        try:
            elapsed = float(parts[2].strip())
            parts[2] = str(elapsed + offset)
            return '\t'.join(parts)
        except ValueError:
            pass
    return line


def stitch_files(file_paths, output_path):
    """
    Stitch multiple log files together.
    
    Headers from all files are concatenated with their '==========' delimiters
    replaced by '----------' so parse_data_file doesn't find them.
    A single valid data section with '==========' follows with all concatenated data.
    Elapsed time (3rd column) is offset so it continues increasing across files.
    All original lines are preserved unmodified (except the neutralized delimiters
    and the elapsed time offset).
    """
    all_headers = []  # List of (filename, header_lines, data_lines) tuples
    reference_columns = None
    skipped_files = []
    total_data_rows = 0

    print(f"Processing {len(file_paths)} file(s)...")

    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: File not found: {file_path}")
            skipped_files.append(file_path)
            continue

        print(f"  Processing: {path.name}")
        
        header_lines, data_lines, column_headers = parse_file_sections(file_path)
        
        if header_lines is None:
            skipped_files.append(file_path)
            continue

        # Store reference columns from first file
        if reference_columns is None and column_headers:
            reference_columns = column_headers

        # Store header and data for this file
        all_headers.append((path.name, header_lines, data_lines))
        total_data_rows += len(data_lines)

    if total_data_rows == 0:
        print("Error: No valid data found in any input files")
        return False

    # Write output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write each file's original header section (without the ========== lines)
            for filename, header_lines, _ in all_headers:
                for line in header_lines:
                    # Skip the ========== delimiter line
                    if '==========' in line:
                        continue
                    f.write(line + '\n')
            
            # Get timestamp from first data row for the separator
            separator_timestamp = "\t\t\t"
            for filename, _, data_lines in all_headers:
                if data_lines:
                    first_parts = data_lines[0].split('\t')
                    if len(first_parts) >= 3:
                        separator_timestamp = f"{first_parts[0]}\t{first_parts[1]}\t{first_parts[2]}\t"
                    break
            
            # Write single separator line
            f.write(f'{separator_timestamp}==========\n')
            
            # Write column headers
            expected_cols = 0
            if reference_columns:
                f.write(reference_columns + '\n')
                # Count non-empty columns (matching parse_data_file behavior)
                expected_cols = len([h for h in reference_columns.split('\t') if h.strip()])
            
            # Write data lines with cumulative elapsed time offset
            elapsed_offset = 0.0
            filtered_count = 0
            written_count = 0
            
            for filename, _, data_lines in all_headers:
                for line in data_lines:
                    # Filter rows with mismatched column count
                    if expected_cols > 0:
                        col_count = len([p for p in line.split('\t') if p.strip()])
                        if col_count != expected_cols:
                            filtered_count += 1
                            continue
                    
                    # Apply offset to elapsed time column
                    adjusted_line = apply_elapsed_offset(line, elapsed_offset)
                    f.write(adjusted_line + '\n')
                    written_count += 1
                
                # Update offset for next file
                if data_lines:
                    last_elapsed = get_last_elapsed_time(data_lines)
                    elapsed_offset += last_elapsed
            
            if filtered_count > 0:
                print(f"Filtered out {filtered_count} row(s) with mismatched column count")

        print(f"\nSuccessfully stitched {len(file_paths) - len(skipped_files)} file(s)")
        print(f"Output written to: {output_path}")
        print(f"Total data rows: {written_count}")
        
        if skipped_files:
            print(f"Skipped files: {', '.join(skipped_files)}")
            
        return True

    except Exception as e:
        print(f"Error writing output file: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Stitch multiple log files together by concatenating headers and data.'
    )
    parser.add_argument(
        'files',
        nargs='+',
        help='Input log files to stitch (supports wildcards)'
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output file path'
    )

    args = parser.parse_args()

    # Expand any wildcards in file paths
    import glob
    expanded_files = []
    for pattern in args.files:
        matches = glob.glob(pattern)
        if matches:
            expanded_files.extend(matches)
        else:
            expanded_files.append(pattern)  # Keep as-is if no matches (will fail gracefully)

    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in expanded_files:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)

    if not unique_files:
        print("Error: No input files specified")
        sys.exit(1)

    success = stitch_files(unique_files, args.output)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
