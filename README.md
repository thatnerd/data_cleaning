# Data Cleaning Tools

Python scripts for identifying and cleaning delimited data files for database ingestion.

## Scripts

### `script/identify_format.py`
Identifies the delimiter format of text files (TSV, CSV, pipe, semicolon).

```bash
./identify_format.py data.txt
./identify_format.py --verbose data.txt
./identify_format.py --quiet data.txt  # Output: TSV
```

### `script/clean_data.py`
Cleans delimited data for relational database import. Handles numeric suffixes (x, %), N/A values, and generates both CSV and SQL outputs.

```bash
./clean_data.py --tsv data.txt
./clean_data.py --csv -o output.csv -s output.sql data.txt
./clean_data.py --table-name metrics data.txt
```

**Transformations:**
- `20.8x` → `20.8`
- `29%` → `29.0`
- `N/A` → `NULL`
- Column names normalized for SQL

**Outputs:**
- Cleaned CSV file
- SQL CREATE TABLE + INSERT statements

## Pipeline Usage

```bash
# Identify format, then clean
FORMAT=$(./identify_format.py --quiet data.txt)
./clean_data.py --${FORMAT,,} data.txt
```

## Tests

Run comprehensive test suite (102 tests):

```bash
python -m pytest test/ -v
```

## Requirements

- Python 3.7+
- docopt
- pytest (for testing)
