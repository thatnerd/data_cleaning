#!/usr/bin/env python3
"""Data Cleaner for Database Ingestion

This script cleans delimited data files for relational database ingestion.
It handles:
- Multiplier values (e.g., "20.8x" -> 20.8)
- Percentage values (e.g., "29%" -> 29.0)
- N/A values (converted to None/NULL)
- Negative values (e.g., "-6%" -> -6.0)

Usage:
    clean_data.py [options] <input_file>
    clean_data.py -h | --help
    clean_data.py --version

Arguments:
    <input_file>              Path to the file to process

Options:
    -h --help                 Show this help message and exit
    --version                 Show version information
    -o --output-csv=<path>    Output path for cleaned CSV file [default: cleaned_data.csv]
    -s --output-sql=<path>    Output path for SQL statements [default: insert_statements.sql]
    -t --table-name=<name>    Name for the database table [default: company_metrics]
    --tsv                     Force TSV format (tab-delimited)
    --csv                     Force CSV format (comma-delimited)
    --pipe                    Force pipe-delimited format
    --semicolon               Force semicolon-delimited format
    -d --delimiter=<delim>    Force custom delimiter character
    -q --quiet                Suppress informational output
    --no-csv                  Skip CSV output generation
    --no-sql                  Skip SQL output generation
    --sample-lines=<n>        Number of lines to sample for auto-detection [default: 5]

Examples:
    clean_data.py data.txt
    clean_data.py --tsv data.txt
    clean_data.py --csv -o output.csv -s output.sql data.txt
    clean_data.py --table-name metrics --delimiter "|" data.txt
    clean_data.py --quiet --no-csv data.txt
"""

import csv
import sys
from typing import Any, List, Dict, Optional, Tuple, Union
from pathlib import Path
from docopt import docopt


__version__ = "1.0.0"


CleanedRow = Dict[str, Union[str, Optional[float]]]
CleanedData = List[CleanedRow]
Headers = List[str]
SQLStatements = List[str]


# Format mappings
FORMAT_DELIMITERS: Dict[str, str] = {
    'tsv': '\t',
    'csv': ',',
    'pipe': '|',
    'semicolon': ';'
}


def detect_delimiter(
    file_path: Path,
    sample_lines: int = 5
) -> str:
    """
    Auto-detect the delimiter used in a file.

    Args:
        file_path: Path to the file
        sample_lines: Number of lines to sample for detection

    Returns:
        The detected delimiter character

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If no delimiter can be detected
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        sample: List[str] = [f.readline() for _ in range(sample_lines)]

    # Count delimiters
    delimiters: List[str] = ['\t', ',', '|', ';']
    delimiter_counts: Dict[str, int] = {
        delim: sum(line.count(delim) for line in sample)
        for delim in delimiters
    }

    # Find delimiter with highest count
    detected: str = max(delimiter_counts, key=lambda k: delimiter_counts[k])

    if delimiter_counts[detected] == 0:
        raise ValueError("Could not detect delimiter in file")

    return detected


def get_delimiter(
    arguments: Dict[str, Any],
    file_path: Path,
    quiet: bool = False
) -> Tuple[str, str]:
    """
    Determine the delimiter to use based on arguments.

    Args:
        arguments: Parsed command-line arguments
        file_path: Path to the input file
        quiet: If True, suppress output messages

    Returns:
        Tuple of (delimiter_char, format_name)

    Raises:
        ValueError: If conflicting format options are specified
    """
    # Check for format flags
    format_flags: List[str] = []
    if arguments['--tsv']:
        format_flags.append('tsv')
    if arguments['--csv']:
        format_flags.append('csv')
    if arguments['--pipe']:
        format_flags.append('pipe')
    if arguments['--semicolon']:
        format_flags.append('semicolon')

    # Check for conflicts
    if len(format_flags) > 1:
        raise ValueError(
            f"Multiple format flags specified: {', '.join(format_flags)}. "
            "Please specify only one."
        )

    # Custom delimiter takes precedence
    if arguments['--delimiter']:
        delimiter: str = arguments['--delimiter']
        # Handle escaped characters
        delimiter = delimiter.encode().decode('unicode_escape')
        format_name: str = 'CUSTOM'

        if not quiet:
            print(f"Using custom delimiter: {repr(delimiter)}")

        return delimiter, format_name

    # Use format flag if specified
    if format_flags:
        format_key: str = format_flags[0]
        delimiter = FORMAT_DELIMITERS[format_key]
        format_name = format_key.upper()

        if not quiet:
            print(f"Using {format_name} format (delimiter: {repr(delimiter)})")

        return delimiter, format_name

    # Auto-detect
    delimiter = detect_delimiter(file_path, sample_lines=int(arguments['--sample-lines']))

    # Determine format name
    format_name = 'UNKNOWN'
    for fmt, delim in FORMAT_DELIMITERS.items():
        if delim == delimiter:
            format_name = fmt.upper()
            break

    if not quiet:
        print(f"Auto-detected {format_name} format (delimiter: {repr(delimiter)})")

    return delimiter, format_name


def clean_numeric_value(value: str) -> Optional[float]:
    """
    Clean a numeric value by removing suffixes and converting to float.

    Args:
        value: The value to clean (e.g., "20.8x", "29%", "N/A", "-6%")

    Returns:
        Float value or None for N/A values

    Examples:
        >>> clean_numeric_value("20.8x")
        20.8
        >>> clean_numeric_value("29%")
        29.0
        >>> clean_numeric_value("N/A")
        None
        >>> clean_numeric_value("-6%")
        -6.0
    """
    if not value or value.strip().upper() == 'N/A':
        return None

    # Remove whitespace
    cleaned: str = value.strip()

    # Remove 'x' suffix (for multiples)
    if cleaned.endswith('x') or cleaned.endswith('X'):
        cleaned = cleaned[:-1]

    # Remove '%' suffix (for percentages)
    if cleaned.endswith('%'):
        cleaned = cleaned[:-1]

    # Convert to float
    try:
        return float(cleaned)
    except ValueError:
        return None


def normalize_column_name(name: str) -> str:
    """
    Normalize a column name for database use.

    Args:
        name: The column name to normalize

    Returns:
        Normalized column name (lowercase, underscores instead of spaces)

    Examples:
        >>> normalize_column_name("Current ARR Multiple")
        'current_arr_multiple'
        >>> normalize_column_name("2024 Stock Performance")
        '2024_stock_performance'
    """
    return name.lower().replace(' ', '_')


def read_and_clean_data(
    file_path: Path,
    delimiter: str,
    quiet: bool = False
) -> Tuple[Headers, CleanedData]:
    """
    Read and clean delimited data from file.

    Args:
        file_path: Path to the data file
        delimiter: The delimiter character to use
        quiet: If True, suppress informational output

    Returns:
        Tuple of (headers, cleaned_data)

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If no headers are found in the file
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    headers: Headers = []
    cleaned_data: CleanedData = []

    with open(file_path, 'r', encoding='utf-8') as f:
        reader: csv.reader = csv.reader(f, delimiter=delimiter)

        # Read headers
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError(f"No data found in file: {file_path}")

        headers = [h.strip() for h in headers]

        if not quiet:
            print(f"\nFound {len(headers)} columns")

        # Read and clean data rows
        row_num: int
        row: List[str]
        for row_num, row in enumerate(reader, start=2):
            if not any(row):  # Skip empty rows
                continue

            cleaned_row: CleanedRow = {}
            i: int
            header: str
            value: str

            for i, (header, value) in enumerate(zip(headers, row)):
                if i == 0:
                    # First column is typically a text identifier (keep as string)
                    cleaned_row[header] = value.strip()
                else:
                    # Other columns are numeric values
                    cleaned_row[header] = clean_numeric_value(value)

            cleaned_data.append(cleaned_row)

    if not quiet:
        print(f"Cleaned {len(cleaned_data)} data rows")

    return headers, cleaned_data


def export_to_csv(
    headers: Headers,
    data: CleanedData,
    output_path: Path,
    quiet: bool = False
) -> None:
    """
    Export cleaned data to CSV format suitable for database import.

    Args:
        headers: Column headers
        data: Cleaned data rows
        output_path: Path for output CSV file
        quiet: If True, suppress informational output

    Raises:
        IOError: If the file cannot be written
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer: csv.DictWriter = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        row: CleanedRow
        for row in data:
            # Convert None to empty string for CSV
            csv_row: Dict[str, Union[str, float]] = {
                k: ('' if v is None else v) for k, v in row.items()
            }
            writer.writerow(csv_row)

    if not quiet:
        print(f"\nExported cleaned data to: {output_path}")


def generate_sql_statements(
    headers: Headers,
    data: CleanedData,
    table_name: str = 'company_metrics'
) -> SQLStatements:
    """
    Generate SQL INSERT statements for database ingestion.

    Args:
        headers: Column headers
        data: Cleaned data rows
        table_name: Name of the database table

    Returns:
        List of SQL statements (CREATE TABLE followed by INSERT statements)

    Raises:
        ValueError: If headers list is empty
    """
    if not headers:
        raise ValueError("Headers list cannot be empty")

    sql_statements: SQLStatements = []

    # Generate CREATE TABLE statement
    create_table: str = f"CREATE TABLE {table_name} (\n"
    create_table += f"    {normalize_column_name(headers[0])} VARCHAR(255) PRIMARY KEY,\n"

    header: str
    for header in headers[1:]:
        col_name: str = normalize_column_name(header)
        create_table += f"    {col_name} DECIMAL(10, 2),\n"

    create_table = create_table.rstrip(',\n') + "\n);\n"
    sql_statements.append(create_table)

    # Generate INSERT statements
    row: CleanedRow
    for row in data:
        columns: str = ', '.join([normalize_column_name(h) for h in headers])
        values: List[str] = []

        for header in headers:
            value: Union[str, Optional[float]] = row[header]
            if value is None:
                values.append('NULL')
            elif isinstance(value, str):
                # Escape single quotes in strings
                escaped_value: str = value.replace("'", "''")
                values.append(f"'{escaped_value}'")
            else:
                values.append(str(value))

        values_str: str = ', '.join(values)
        insert: str = f"INSERT INTO {table_name} ({columns}) VALUES ({values_str});"
        sql_statements.append(insert)

    return sql_statements


def write_sql_file(
    sql_statements: SQLStatements,
    output_path: Path,
    quiet: bool = False
) -> None:
    """
    Write SQL statements to a file.

    Args:
        sql_statements: List of SQL statements to write
        output_path: Path for output SQL file
        quiet: If True, suppress informational output

    Raises:
        IOError: If the file cannot be written
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))

    if not quiet:
        print(f"Generated SQL statements: {output_path}")


def display_sample_data(
    data: CleanedData,
    num_rows: int = 3,
    quiet: bool = False
) -> None:
    """
    Display a sample of cleaned data.

    Args:
        data: Cleaned data rows
        num_rows: Number of rows to display
        quiet: If True, suppress output
    """
    if quiet or not data:
        return

    print(f"\nSample of cleaned data (first {min(num_rows, len(data))} rows):")
    print("-" * 60)

    i: int
    row: CleanedRow
    for i, row in enumerate(data[:num_rows], start=1):
        print(f"\nRow {i}:")
        key: str
        value: Union[str, Optional[float]]
        for key, value in row.items():
            print(f"  {key}: {value}")


def main(arguments: Optional[Dict[str, Any]] = None) -> int:
    """
    Main execution function.

    Args:
        arguments: Optional pre-parsed arguments (for testing)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if arguments is None:
        arguments = docopt(__doc__, version=f"Data Cleaner {__version__}")

    # Extract arguments
    input_file: Path = Path(arguments['<input_file>'])
    output_csv: Path = Path(arguments['--output-csv'])
    output_sql: Path = Path(arguments['--output-sql'])
    table_name: str = arguments['--table-name']
    quiet: bool = arguments['--quiet']
    no_csv: bool = arguments['--no-csv']
    no_sql: bool = arguments['--no-sql']

    # Check if input file exists
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        return 1

    if not quiet:
        print(f"Processing file: {input_file}")
        print("=" * 60)

    try:
        # Determine delimiter
        delimiter: str
        format_name: str
        delimiter, format_name = get_delimiter(arguments, input_file, quiet)

        # Read and clean data
        headers: Headers
        cleaned_data: CleanedData
        headers, cleaned_data = read_and_clean_data(
            input_file,
            delimiter=delimiter,
            quiet=quiet
        )

        # Display sample of cleaned data
        display_sample_data(cleaned_data, num_rows=3, quiet=quiet)

        # Export to CSV
        if not no_csv:
            export_to_csv(headers, cleaned_data, output_csv, quiet=quiet)

        # Generate and write SQL statements
        if not no_sql:
            sql_statements: SQLStatements = generate_sql_statements(
                headers,
                cleaned_data,
                table_name=table_name
            )
            write_sql_file(sql_statements, output_sql, quiet=quiet)

        if not quiet:
            print("\n" + "=" * 60)
            print("Data cleaning completed successfully!")
            if not no_csv or not no_sql:
                print("\nOutputs:")
                if not no_csv:
                    print(f"  - Cleaned CSV: {output_csv}")
                if not no_sql:
                    print(f"  - SQL statements: {output_sql}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
