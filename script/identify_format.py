#!/usr/bin/env python3
"""File Format Identifier

This script identifies the delimiter format of delimited text files.
It detects common formats including TSV, CSV, pipe-delimited, and semicolon-delimited.

Usage:
    identify_format.py [options] <input_file>
    identify_format.py -h | --help
    identify_format.py --version

Arguments:
    <input_file>              Path to the file to analyze

Options:
    -h --help                 Show this help message and exit
    --version                 Show version information
    -q --quiet                Only output the delimiter name (for scripting)
    -s --sample-lines=<n>     Number of lines to sample [default: 5]
    -v --verbose              Show detailed analysis

Examples:
    identify_format.py data.txt
    identify_format.py --quiet data.txt
    identify_format.py --verbose --sample-lines 10 data.txt
"""

import sys
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from collections import Counter
from docopt import docopt


__version__ = "1.0.0"


DelimiterInfo = Dict[str, int]
DelimiterName = str
ConfidenceScore = float


# Delimiter mappings
DELIMITER_NAMES: Dict[str, str] = {
    '\t': 'TSV',
    ',': 'CSV',
    '|': 'PIPE',
    ';': 'SEMICOLON'
}

DELIMITER_CHARS: Dict[str, str] = {
    'TSV': '\t',
    'CSV': ',',
    'PIPE': '|',
    'SEMICOLON': ';'
}


def detect_delimiter(
    file_path: Path,
    sample_lines: int = 5
) -> Tuple[str, DelimiterName, ConfidenceScore]:
    """
    Detect the delimiter used in a file.

    Args:
        file_path: Path to the file to analyze
        sample_lines: Number of lines to sample for detection

    Returns:
        Tuple of (delimiter_char, delimiter_name, confidence_score)
        confidence_score is between 0.0 and 1.0

    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the file is empty or no delimiter can be detected
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read sample lines
    with open(file_path, 'r', encoding='utf-8') as f:
        lines: List[str] = []
        for _ in range(sample_lines):
            line: Optional[str] = f.readline()
            if not line:
                break
            lines.append(line)

    if not lines:
        raise ValueError(f"File is empty: {file_path}")

    # Count delimiters in each line
    delimiter_counts: Dict[str, List[int]] = {
        delim: [line.count(delim) for line in lines]
        for delim in DELIMITER_NAMES.keys()
    }

    # Calculate consistency and total counts
    scores: Dict[str, Tuple[int, float]] = {}

    delim: str
    counts: List[int]
    for delim, counts in delimiter_counts.items():
        total: int = sum(counts)
        if total == 0:
            continue

        # Check consistency (all lines should have same count)
        count_freq: Counter = Counter(counts)
        most_common_count: int
        frequency: int
        most_common_count, frequency = count_freq.most_common(1)[0]

        # Consistency score (0.0 to 1.0)
        consistency: float = frequency / len(lines)

        # Only consider if appears in most lines and has consistency
        if most_common_count > 0 and consistency >= 0.6:
            scores[delim] = (total, consistency)

    if not scores:
        raise ValueError(
            "Could not detect delimiter. File may not be a delimited format."
        )

    # Find best delimiter (highest total, then highest consistency)
    best_delim: str = max(
        scores.keys(),
        key=lambda d: (scores[d][0], scores[d][1])
    )

    total_count: int
    consistency_score: float
    total_count, consistency_score = scores[best_delim]
    delimiter_name: DelimiterName = DELIMITER_NAMES[best_delim]

    return best_delim, delimiter_name, consistency_score


def analyze_file_structure(
    file_path: Path,
    delimiter: str,
    sample_lines: int = 5
) -> Dict[str, any]:
    """
    Analyze the structure of a delimited file.

    Args:
        file_path: Path to the file to analyze
        delimiter: The delimiter character
        sample_lines: Number of lines to analyze

    Returns:
        Dictionary containing file structure information
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines: List[str] = [f.readline() for _ in range(sample_lines + 1)]

    # Remove empty lines
    lines = [line for line in lines if line.strip()]

    if not lines:
        return {}

    # Analyze structure
    header_line: str = lines[0]
    headers: List[str] = [h.strip() for h in header_line.split(delimiter)]
    num_columns: int = len(headers)

    # Check data rows
    data_lines: List[str] = lines[1:]
    column_counts: List[int] = [
        len(line.split(delimiter)) for line in data_lines
    ]

    consistent_columns: bool = all(count == num_columns for count in column_counts)

    analysis: Dict[str, any] = {
        'num_columns': num_columns,
        'headers': headers,
        'consistent_columns': consistent_columns,
        'sample_rows': len(data_lines),
        'column_counts': column_counts
    }

    return analysis


def format_output(
    delimiter_char: str,
    delimiter_name: DelimiterName,
    confidence: ConfidenceScore,
    file_path: Path,
    analysis: Optional[Dict[str, any]] = None,
    quiet: bool = False,
    verbose: bool = False
) -> str:
    """
    Format the output message.

    Args:
        delimiter_char: The detected delimiter character
        delimiter_name: Human-readable name of the delimiter
        confidence: Confidence score (0.0 to 1.0)
        file_path: Path to the analyzed file
        analysis: Optional detailed analysis
        quiet: If True, output only the delimiter name
        verbose: If True, include detailed analysis

    Returns:
        Formatted output string
    """
    if quiet:
        return delimiter_name

    output_lines: List[str] = []

    output_lines.append(f"File: {file_path}")
    output_lines.append(f"Format: {delimiter_name}")
    output_lines.append(f"Delimiter: {repr(delimiter_char)}")
    output_lines.append(f"Confidence: {confidence:.1%}")

    if verbose and analysis:
        output_lines.append("")
        output_lines.append("Detailed Analysis:")
        output_lines.append(f"  Columns: {analysis['num_columns']}")
        output_lines.append(f"  Headers: {', '.join(analysis['headers'][:5])}" +
                          ("..." if len(analysis['headers']) > 5 else ""))
        output_lines.append(f"  Consistent structure: " +
                          ("Yes" if analysis['consistent_columns'] else "No"))

        if not analysis['consistent_columns']:
            output_lines.append(f"  Column counts per row: {analysis['column_counts']}")

    return '\n'.join(output_lines)


def main(arguments: Optional[Dict[str, any]] = None) -> int:
    """
    Main execution function.

    Args:
        arguments: Optional pre-parsed arguments (for testing)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    if arguments is None:
        arguments = docopt(__doc__, version=f"Format Identifier {__version__}")

    # Extract arguments
    input_file: Path = Path(arguments['<input_file>'])
    quiet: bool = arguments['--quiet']
    verbose: bool = arguments['--verbose']
    sample_lines: int = int(arguments['--sample-lines'])

    try:
        # Detect delimiter
        delimiter_char: str
        delimiter_name: DelimiterName
        confidence: ConfidenceScore

        delimiter_char, delimiter_name, confidence = detect_delimiter(
            input_file,
            sample_lines=sample_lines
        )

        # Perform detailed analysis if verbose
        analysis: Optional[Dict[str, any]] = None
        if verbose:
            analysis = analyze_file_structure(
                input_file,
                delimiter_char,
                sample_lines=sample_lines
            )

        # Output results
        output: str = format_output(
            delimiter_char,
            delimiter_name,
            confidence,
            input_file,
            analysis=analysis,
            quiet=quiet,
            verbose=verbose
        )

        print(output)
        return 0

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
