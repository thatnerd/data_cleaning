#!/usr/bin/env python3
"""Unit tests for clean_data.py"""

import unittest
import tempfile
import sys
from pathlib import Path
from io import StringIO

# Add parent directory to path to import modules from script/
sys.path.insert(0, str(Path(__file__).parent.parent / 'script'))

# Import the module to test
import clean_data


class TestDetectDelimiter(unittest.TestCase):
    """Test cases for detect_delimiter function"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def create_test_file(self, filename: str, content: str) -> Path:
        """Helper to create a test file"""
        file_path = self.temp_path / filename
        file_path.write_text(content)
        return file_path

    def test_detect_tab_delimiter(self):
        """Should detect TAB delimiter"""
        content = "Name\tAge\tCity\nAlice\t30\tNY\n"
        file_path = self.create_test_file("test.tsv", content)

        delim = clean_data.detect_delimiter(file_path)

        self.assertEqual(delim, '\t')

    def test_detect_comma_delimiter(self):
        """Should detect comma delimiter"""
        content = "Name,Age,City\nAlice,30,NY\n"
        file_path = self.create_test_file("test.csv", content)

        delim = clean_data.detect_delimiter(file_path)

        self.assertEqual(delim, ',')

    def test_detect_pipe_delimiter(self):
        """Should detect pipe delimiter"""
        content = "Name|Age|City\nAlice|30|NY\n"
        file_path = self.create_test_file("test.pipe", content)

        delim = clean_data.detect_delimiter(file_path)

        self.assertEqual(delim, '|')

    def test_detect_semicolon_delimiter(self):
        """Should detect semicolon delimiter"""
        content = "Name;Age;City\nAlice;30;NY\n"
        file_path = self.create_test_file("test.semi", content)

        delim = clean_data.detect_delimiter(file_path)

        self.assertEqual(delim, ';')

    def test_file_not_found(self):
        """Should raise FileNotFoundError for non-existent file"""
        file_path = self.temp_path / "nonexistent.txt"

        with self.assertRaises(FileNotFoundError):
            clean_data.detect_delimiter(file_path)

    def test_no_delimiter_found(self):
        """Should raise ValueError when no delimiter detected"""
        content = "NoDelimitersHere\nJustPlainText\n"
        file_path = self.create_test_file("plain.txt", content)

        with self.assertRaises(ValueError):
            clean_data.detect_delimiter(file_path)

    def test_choose_highest_count(self):
        """Should choose delimiter with highest count"""
        # More tabs than commas
        content = "A\tB\tC,extra\nD\tE\tF,extra\n"
        file_path = self.create_test_file("mixed.txt", content)

        delim = clean_data.detect_delimiter(file_path)

        self.assertEqual(delim, '\t')  # More tabs than commas

    def test_empty_file_error(self):
        """Should raise ValueError for empty file"""
        file_path = self.create_test_file("empty.txt", "")

        with self.assertRaises(ValueError):
            clean_data.detect_delimiter(file_path)


class TestGetDelimiter(unittest.TestCase):
    """Test cases for get_delimiter function"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def create_test_file(self, filename: str, content: str) -> Path:
        """Helper to create a test file"""
        file_path = self.temp_path / filename
        file_path.write_text(content)
        return file_path

    def test_tsv_flag(self):
        """Should use TAB delimiter with --tsv flag"""
        content = "Name\tAge\n"
        file_path = self.create_test_file("test.txt", content)

        args = {
            '--tsv': True,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--sample-lines': '5'
        }

        delim, format_name = clean_data.get_delimiter(args, file_path, quiet=True)

        self.assertEqual(delim, '\t')
        self.assertEqual(format_name, 'TSV')

    def test_csv_flag(self):
        """Should use comma delimiter with --csv flag"""
        content = "Name,Age\n"
        file_path = self.create_test_file("test.txt", content)

        args = {
            '--tsv': False,
            '--csv': True,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--sample-lines': '5'
        }

        delim, format_name = clean_data.get_delimiter(args, file_path, quiet=True)

        self.assertEqual(delim, ',')
        self.assertEqual(format_name, 'CSV')

    def test_pipe_flag(self):
        """Should use pipe delimiter with --pipe flag"""
        content = "Name|Age\n"
        file_path = self.create_test_file("test.txt", content)

        args = {
            '--tsv': False,
            '--csv': False,
            '--pipe': True,
            '--semicolon': False,
            '--delimiter': None,
            '--sample-lines': '5'
        }

        delim, format_name = clean_data.get_delimiter(args, file_path, quiet=True)

        self.assertEqual(delim, '|')
        self.assertEqual(format_name, 'PIPE')

    def test_semicolon_flag(self):
        """Should use semicolon delimiter with --semicolon flag"""
        content = "Name;Age\n"
        file_path = self.create_test_file("test.txt", content)

        args = {
            '--tsv': False,
            '--csv': False,
            '--pipe': False,
            '--semicolon': True,
            '--delimiter': None,
            '--sample-lines': '5'
        }

        delim, format_name = clean_data.get_delimiter(args, file_path, quiet=True)

        self.assertEqual(delim, ';')
        self.assertEqual(format_name, 'SEMICOLON')

    def test_custom_delimiter(self):
        """Should use custom delimiter with --delimiter flag"""
        content = "Name:Age\n"
        file_path = self.create_test_file("test.txt", content)

        args = {
            '--tsv': False,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': ':',
            '--sample-lines': '5'
        }

        delim, format_name = clean_data.get_delimiter(args, file_path, quiet=True)

        self.assertEqual(delim, ':')
        self.assertEqual(format_name, 'CUSTOM')

    def test_escaped_delimiter(self):
        """Should handle escaped delimiter characters"""
        content = "Name\tAge\n"
        file_path = self.create_test_file("test.txt", content)

        args = {
            '--tsv': False,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': '\\t',
            '--sample-lines': '5'
        }

        delim, format_name = clean_data.get_delimiter(args, file_path, quiet=True)

        self.assertEqual(delim, '\t')

    def test_auto_detect(self):
        """Should auto-detect when no flag specified"""
        content = "Name\tAge\nAlice\t30\n"
        file_path = self.create_test_file("test.txt", content)

        args = {
            '--tsv': False,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--sample-lines': '5'
        }

        delim, format_name = clean_data.get_delimiter(args, file_path, quiet=True)

        self.assertEqual(delim, '\t')
        self.assertEqual(format_name, 'TSV')

    def test_multiple_flags_conflict(self):
        """Should raise ValueError for multiple format flags"""
        content = "Name\tAge\n"
        file_path = self.create_test_file("test.txt", content)

        args = {
            '--tsv': True,
            '--csv': True,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--sample-lines': '5'
        }

        with self.assertRaises(ValueError) as context:
            clean_data.get_delimiter(args, file_path, quiet=True)

        self.assertIn('Multiple format flags', str(context.exception))

    def test_normal_mode_shows_output(self):
        """Should show output in normal (non-quiet) mode"""
        content = "Name\tAge\n"
        file_path = self.create_test_file("test.txt", content)

        args = {
            '--tsv': True,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--sample-lines': '5'
        }

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        clean_data.get_delimiter(args, file_path, quiet=False)
        output = sys.stdout.getvalue()

        sys.stdout = old_stdout

        # Should print format information
        self.assertIn('TSV', output)


class TestCleanNumericValue(unittest.TestCase):
    """Test cases for clean_numeric_value function"""

    def test_clean_multiplier_x(self):
        """Should clean '20.8x' -> 20.8"""
        result = clean_data.clean_numeric_value("20.8x")
        self.assertEqual(result, 20.8)

    def test_clean_percentage(self):
        """Should clean '29%' -> 29.0"""
        result = clean_data.clean_numeric_value("29%")
        self.assertEqual(result, 29.0)

    def test_clean_negative_percentage(self):
        """Should clean '-6%' -> -6.0"""
        result = clean_data.clean_numeric_value("-6%")
        self.assertEqual(result, -6.0)

    def test_clean_na_uppercase(self):
        """Should clean 'N/A' -> None"""
        result = clean_data.clean_numeric_value("N/A")
        self.assertIsNone(result)

    def test_clean_na_lowercase(self):
        """Should clean 'n/a' -> None (case insensitive)"""
        result = clean_data.clean_numeric_value("n/a")
        self.assertIsNone(result)

    def test_clean_na_with_whitespace(self):
        """Should clean '  N/A  ' -> None"""
        result = clean_data.clean_numeric_value("  N/A  ")
        self.assertIsNone(result)

    def test_clean_empty_string(self):
        """Should clean empty string -> None"""
        result = clean_data.clean_numeric_value("")
        self.assertIsNone(result)

    def test_clean_uppercase_x(self):
        """Should clean '15.5X' -> 15.5 (uppercase X)"""
        result = clean_data.clean_numeric_value("15.5X")
        self.assertEqual(result, 15.5)

    def test_clean_no_suffix(self):
        """Should clean '100.0' -> 100.0 (no suffix)"""
        result = clean_data.clean_numeric_value("100.0")
        self.assertEqual(result, 100.0)

    def test_clean_negative_multiplier(self):
        """Should clean '-10x' -> -10.0"""
        result = clean_data.clean_numeric_value("-10x")
        self.assertEqual(result, -10.0)

    def test_invalid_numeric_string(self):
        """Should return None for invalid numeric string"""
        result = clean_data.clean_numeric_value("invalid")
        self.assertIsNone(result)

    def test_clean_integer_percentage(self):
        """Should clean '50%' -> 50.0"""
        result = clean_data.clean_numeric_value("50%")
        self.assertEqual(result, 50.0)

    def test_clean_zero(self):
        """Should clean '0%' -> 0.0"""
        result = clean_data.clean_numeric_value("0%")
        self.assertEqual(result, 0.0)


class TestNormalizeColumnName(unittest.TestCase):
    """Test cases for normalize_column_name function"""

    def test_normalize_with_spaces(self):
        """Should normalize 'Current ARR Multiple' -> 'current_arr_multiple'"""
        result = clean_data.normalize_column_name("Current ARR Multiple")
        self.assertEqual(result, "current_arr_multiple")

    def test_normalize_with_year(self):
        """Should normalize '2024 Stock Performance' -> '2024_stock_performance'"""
        result = clean_data.normalize_column_name("2024 Stock Performance")
        self.assertEqual(result, "2024_stock_performance")

    def test_normalize_single_word(self):
        """Should normalize 'Company' -> 'company'"""
        result = clean_data.normalize_column_name("Company")
        self.assertEqual(result, "company")

    def test_normalize_all_caps(self):
        """Should normalize 'ALL CAPS TEXT' -> 'all_caps_text'"""
        result = clean_data.normalize_column_name("ALL CAPS TEXT")
        self.assertEqual(result, "all_caps_text")

    def test_normalize_multiple_spaces(self):
        """Should normalize 'Multiple   Spaces' -> 'multiple___spaces'"""
        result = clean_data.normalize_column_name("Multiple   Spaces")
        self.assertEqual(result, "multiple___spaces")


class TestReadAndCleanData(unittest.TestCase):
    """Test cases for read_and_clean_data function"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def create_test_file(self, filename: str, content: str) -> Path:
        """Helper to create a test file"""
        file_path = self.temp_path / filename
        file_path.write_text(content)
        return file_path

    def test_read_tsv_file(self):
        """Should read and clean TSV file"""
        content = "Company\tARR\tGrowth\nAcme\t20.5x\t30%\nBeta\t15.2x\t25%\n"
        file_path = self.create_test_file("test.tsv", content)

        headers, data = clean_data.read_and_clean_data(file_path, '\t', quiet=True)

        self.assertEqual(headers, ['Company', 'ARR', 'Growth'])
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['Company'], 'Acme')
        self.assertEqual(data[0]['ARR'], 20.5)
        self.assertEqual(data[0]['Growth'], 30.0)

    def test_read_csv_file(self):
        """Should read and clean CSV file"""
        content = "Company,ARR,Growth\nAcme,20.5x,30%\n"
        file_path = self.create_test_file("test.csv", content)

        headers, data = clean_data.read_and_clean_data(file_path, ',', quiet=True)

        self.assertEqual(headers, ['Company', 'ARR', 'Growth'])
        self.assertEqual(len(data), 1)

    def test_extract_headers(self):
        """Should extract headers correctly"""
        content = "Name\tAge\tCity\nAlice\t30\tNY\n"
        file_path = self.create_test_file("test.tsv", content)

        headers, _ = clean_data.read_and_clean_data(file_path, '\t', quiet=True)

        self.assertEqual(headers, ['Name', 'Age', 'City'])

    def test_clean_numeric_values(self):
        """Should clean numeric values in data rows"""
        content = "Company\tValue\nAcme\t50%\n"
        file_path = self.create_test_file("test.tsv", content)

        _, data = clean_data.read_and_clean_data(file_path, '\t', quiet=True)

        self.assertEqual(data[0]['Value'], 50.0)

    def test_keep_first_column_as_string(self):
        """Should keep first column as string"""
        content = "Company\tValue\nAcme Corp\t50%\n"
        file_path = self.create_test_file("test.tsv", content)

        _, data = clean_data.read_and_clean_data(file_path, '\t', quiet=True)

        self.assertEqual(data[0]['Company'], 'Acme Corp')
        self.assertIsInstance(data[0]['Company'], str)

    def test_skip_empty_rows(self):
        """Should skip empty rows"""
        content = "Company\tValue\nAcme\t50%\n\n\nBeta\t60%\n"
        file_path = self.create_test_file("test.tsv", content)

        _, data = clean_data.read_and_clean_data(file_path, '\t', quiet=True)

        self.assertEqual(len(data), 2)  # Should skip empty rows

    def test_file_not_found(self):
        """Should raise FileNotFoundError for non-existent file"""
        file_path = self.temp_path / "nonexistent.txt"

        with self.assertRaises(FileNotFoundError):
            clean_data.read_and_clean_data(file_path, '\t', quiet=True)

    def test_no_data_only_headers(self):
        """Should handle file with only headers"""
        content = "Company\tValue\n"
        file_path = self.create_test_file("test.tsv", content)

        headers, data = clean_data.read_and_clean_data(file_path, '\t', quiet=True)

        self.assertEqual(headers, ['Company', 'Value'])
        self.assertEqual(len(data), 0)

    def test_empty_file(self):
        """Should raise ValueError for empty file"""
        file_path = self.create_test_file("empty.txt", "")

        with self.assertRaises(ValueError):
            clean_data.read_and_clean_data(file_path, '\t', quiet=True)

    def test_handle_na_values(self):
        """Should convert N/A to None"""
        content = "Company\tValue\nAcme\tN/A\n"
        file_path = self.create_test_file("test.tsv", content)

        _, data = clean_data.read_and_clean_data(file_path, '\t', quiet=True)

        self.assertIsNone(data[0]['Value'])


class TestExportToCsv(unittest.TestCase):
    """Test cases for export_to_csv function"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def test_export_data_to_csv(self):
        """Should export data to CSV file"""
        headers = ['Company', 'Value']
        data = [
            {'Company': 'Acme', 'Value': 50.0},
            {'Company': 'Beta', 'Value': 60.0}
        ]
        output_path = self.temp_path / "output.csv"

        clean_data.export_to_csv(headers, data, output_path, quiet=True)

        self.assertTrue(output_path.exists())
        content = output_path.read_text()
        self.assertIn('Company,Value', content)
        self.assertIn('Acme,50.0', content)

    def test_write_headers(self):
        """Should write headers correctly"""
        headers = ['Name', 'Age', 'City']
        data = [{'Name': 'Alice', 'Age': 30.0, 'City': 'NY'}]
        output_path = self.temp_path / "output.csv"

        clean_data.export_to_csv(headers, data, output_path, quiet=True)

        content = output_path.read_text()
        lines = content.strip().split('\n')
        self.assertEqual(lines[0], 'Name,Age,City')

    def test_convert_none_to_empty(self):
        """Should convert None to empty string"""
        headers = ['Company', 'Value']
        data = [{'Company': 'Acme', 'Value': None}]
        output_path = self.temp_path / "output.csv"

        clean_data.export_to_csv(headers, data, output_path, quiet=True)

        content = output_path.read_text()
        self.assertIn('Acme,', content)  # Empty value after comma

    def test_keep_numeric_values(self):
        """Should keep numeric values as-is"""
        headers = ['Company', 'Value']
        data = [{'Company': 'Acme', 'Value': 50.5}]
        output_path = self.temp_path / "output.csv"

        clean_data.export_to_csv(headers, data, output_path, quiet=True)

        content = output_path.read_text()
        self.assertIn('50.5', content)

    def test_keep_string_values(self):
        """Should keep string values as-is"""
        headers = ['Company', 'Value']
        data = [{'Company': 'Acme Corp', 'Value': 50.0}]
        output_path = self.temp_path / "output.csv"

        clean_data.export_to_csv(headers, data, output_path, quiet=True)

        content = output_path.read_text()
        self.assertIn('Acme Corp', content)


class TestGenerateSqlStatements(unittest.TestCase):
    """Test cases for generate_sql_statements function"""

    def test_generate_create_table(self):
        """Should generate CREATE TABLE statement"""
        headers = ['Company', 'Value']
        data = [{'Company': 'Acme', 'Value': 50.0}]

        statements = clean_data.generate_sql_statements(headers, data)

        self.assertTrue(statements[0].startswith('CREATE TABLE'))
        self.assertIn('company VARCHAR(255) PRIMARY KEY', statements[0])

    def test_first_column_varchar_primary_key(self):
        """Should make first column VARCHAR PRIMARY KEY"""
        headers = ['Company', 'Value']
        data = [{'Company': 'Acme', 'Value': 50.0}]

        statements = clean_data.generate_sql_statements(headers, data)

        self.assertIn('company VARCHAR(255) PRIMARY KEY', statements[0])

    def test_other_columns_decimal(self):
        """Should make other columns DECIMAL(10, 2)"""
        headers = ['Company', 'Value', 'Growth']
        data = [{'Company': 'Acme', 'Value': 50.0, 'Growth': 25.0}]

        statements = clean_data.generate_sql_statements(headers, data)

        self.assertIn('value DECIMAL(10, 2)', statements[0])
        self.assertIn('growth DECIMAL(10, 2)', statements[0])

    def test_normalize_column_names_in_schema(self):
        """Should normalize column names in schema"""
        headers = ['Company Name', 'ARR Value']
        data = [{'Company Name': 'Acme', 'ARR Value': 50.0}]

        statements = clean_data.generate_sql_statements(headers, data)

        self.assertIn('company_name', statements[0])
        self.assertIn('arr_value', statements[0])

    def test_generate_insert_statements(self):
        """Should generate INSERT statements for all rows"""
        headers = ['Company', 'Value']
        data = [
            {'Company': 'Acme', 'Value': 50.0},
            {'Company': 'Beta', 'Value': 60.0}
        ]

        statements = clean_data.generate_sql_statements(headers, data)

        # Should have CREATE TABLE + 2 INSERT statements
        self.assertEqual(len(statements), 3)
        self.assertTrue(statements[1].startswith('INSERT INTO'))
        self.assertTrue(statements[2].startswith('INSERT INTO'))

    def test_handle_null_values(self):
        """Should convert None to NULL in SQL"""
        headers = ['Company', 'Value']
        data = [{'Company': 'Acme', 'Value': None}]

        statements = clean_data.generate_sql_statements(headers, data)

        self.assertIn("'Acme', NULL", statements[1])

    def test_handle_string_values(self):
        """Should quote string values"""
        headers = ['Company', 'Value']
        data = [{'Company': 'Acme Corp', 'Value': 50.0}]

        statements = clean_data.generate_sql_statements(headers, data)

        self.assertIn("'Acme Corp'", statements[1])

    def test_handle_numeric_values(self):
        """Should not quote numeric values"""
        headers = ['Company', 'Value']
        data = [{'Company': 'Acme', 'Value': 50.0}]

        statements = clean_data.generate_sql_statements(headers, data)

        self.assertIn("50.0", statements[1])
        # Should not have quotes around number
        self.assertNotIn("'50.0'", statements[1])

    def test_escape_single_quotes(self):
        """Should escape single quotes in strings"""
        headers = ['Company', 'Value']
        data = [{'Company': "O'Reilly", 'Value': 50.0}]

        statements = clean_data.generate_sql_statements(headers, data)

        self.assertIn("O''Reilly", statements[1])

    def test_custom_table_name(self):
        """Should use custom table name"""
        headers = ['Company', 'Value']
        data = [{'Company': 'Acme', 'Value': 50.0}]

        statements = clean_data.generate_sql_statements(
            headers, data, table_name='metrics'
        )

        self.assertIn('CREATE TABLE metrics', statements[0])
        self.assertIn('INSERT INTO metrics', statements[1])

    def test_empty_headers_error(self):
        """Should raise ValueError for empty headers"""
        with self.assertRaises(ValueError):
            clean_data.generate_sql_statements([], [])


class TestWriteSqlFile(unittest.TestCase):
    """Test cases for write_sql_file function"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def test_write_sql_statements(self):
        """Should write SQL statements to file"""
        statements = [
            "CREATE TABLE test (id INT);",
            "INSERT INTO test VALUES (1);"
        ]
        output_path = self.temp_path / "output.sql"

        clean_data.write_sql_file(statements, output_path, quiet=True)

        self.assertTrue(output_path.exists())
        content = output_path.read_text()
        self.assertIn("CREATE TABLE test", content)
        self.assertIn("INSERT INTO test", content)

    def test_join_with_newlines(self):
        """Should join statements with newlines"""
        statements = ["STATEMENT1;", "STATEMENT2;"]
        output_path = self.temp_path / "output.sql"

        clean_data.write_sql_file(statements, output_path, quiet=True)

        content = output_path.read_text()
        self.assertEqual(content, "STATEMENT1;\nSTATEMENT2;")


class TestDisplaySampleData(unittest.TestCase):
    """Test cases for display_sample_data function"""

    def test_display_specified_rows(self):
        """Should display specified number of rows"""
        data = [
            {'Company': 'A', 'Value': 10.0},
            {'Company': 'B', 'Value': 20.0},
            {'Company': 'C', 'Value': 30.0},
            {'Company': 'D', 'Value': 40.0}
        ]

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        clean_data.display_sample_data(data, num_rows=2, quiet=False)
        output = sys.stdout.getvalue()

        sys.stdout = old_stdout

        # Should show first 2 rows
        self.assertIn('Row 1:', output)
        self.assertIn('Row 2:', output)
        self.assertNotIn('Row 3:', output)

    def test_display_fewer_if_data_smaller(self):
        """Should display fewer rows if data has fewer"""
        data = [
            {'Company': 'A', 'Value': 10.0}
        ]

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        clean_data.display_sample_data(data, num_rows=5, quiet=False)
        output = sys.stdout.getvalue()

        sys.stdout = old_stdout

        self.assertIn('first 1 rows', output)

    def test_format_output(self):
        """Should format output correctly"""
        data = [{'Company': 'Acme', 'Value': 50.0}]

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        clean_data.display_sample_data(data, num_rows=1, quiet=False)
        output = sys.stdout.getvalue()

        sys.stdout = old_stdout

        self.assertIn('Company: Acme', output)
        self.assertIn('Value: 50.0', output)

    def test_quiet_mode(self):
        """Should suppress output in quiet mode"""
        data = [{'Company': 'Acme', 'Value': 50.0}]

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        clean_data.display_sample_data(data, num_rows=1, quiet=True)
        output = sys.stdout.getvalue()

        sys.stdout = old_stdout

        self.assertEqual(output, '')

    def test_empty_data(self):
        """Should handle empty data list"""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        clean_data.display_sample_data([], num_rows=3, quiet=False)
        output = sys.stdout.getvalue()

        sys.stdout = old_stdout

        self.assertEqual(output, '')


class TestMain(unittest.TestCase):
    """Test cases for main function"""

    def setUp(self):
        """Create temporary directory for test files"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temporary directory"""
        self.temp_dir.cleanup()

    def create_test_file(self, filename: str, content: str) -> Path:
        """Helper to create a test file"""
        file_path = self.temp_path / filename
        file_path.write_text(content)
        return file_path

    def test_successful_execution(self):
        """Should return 0 on successful execution"""
        content = "Company\tValue\nAcme\t50%\n"
        file_path = self.create_test_file("test.tsv", content)
        output_csv = self.temp_path / "output.csv"
        output_sql = self.temp_path / "output.sql"

        args = {
            '<input_file>': str(file_path),
            '--output-csv': str(output_csv),
            '--output-sql': str(output_sql),
            '--table-name': 'test',
            '--tsv': True,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--quiet': True,
            '--no-csv': False,
            '--no-sql': False,
            '--sample-lines': '5'
        }

        exit_code = clean_data.main(args)

        self.assertEqual(exit_code, 0)
        self.assertTrue(output_csv.exists())
        self.assertTrue(output_sql.exists())

    def test_file_not_found(self):
        """Should return 1 when file not found"""
        args = {
            '<input_file>': str(self.temp_path / 'nonexistent.txt'),
            '--output-csv': 'output.csv',
            '--output-sql': 'output.sql',
            '--table-name': 'test',
            '--tsv': False,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--quiet': True,
            '--no-csv': False,
            '--no-sql': False,
            '--sample-lines': '5'
        }

        exit_code = clean_data.main(args)

        self.assertEqual(exit_code, 1)

    def test_no_csv_flag(self):
        """Should skip CSV generation with --no-csv"""
        content = "Company\tValue\nAcme\t50%\n"
        file_path = self.create_test_file("test.tsv", content)
        output_csv = self.temp_path / "output.csv"
        output_sql = self.temp_path / "output.sql"

        args = {
            '<input_file>': str(file_path),
            '--output-csv': str(output_csv),
            '--output-sql': str(output_sql),
            '--table-name': 'test',
            '--tsv': True,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--quiet': True,
            '--no-csv': True,
            '--no-sql': False,
            '--sample-lines': '5'
        }

        clean_data.main(args)

        self.assertFalse(output_csv.exists())
        self.assertTrue(output_sql.exists())

    def test_no_sql_flag(self):
        """Should skip SQL generation with --no-sql"""
        content = "Company\tValue\nAcme\t50%\n"
        file_path = self.create_test_file("test.tsv", content)
        output_csv = self.temp_path / "output.csv"
        output_sql = self.temp_path / "output.sql"

        args = {
            '<input_file>': str(file_path),
            '--output-csv': str(output_csv),
            '--output-sql': str(output_sql),
            '--table-name': 'test',
            '--tsv': True,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--quiet': True,
            '--no-csv': False,
            '--no-sql': True,
            '--sample-lines': '5'
        }

        clean_data.main(args)

        self.assertTrue(output_csv.exists())
        self.assertFalse(output_sql.exists())

    def test_csv_flag(self):
        """Should handle --csv flag"""
        content = "Company,Value\nAcme,50%\n"
        file_path = self.create_test_file("test.csv", content)
        output_csv = self.temp_path / "output.csv"
        output_sql = self.temp_path / "output.sql"

        args = {
            '<input_file>': str(file_path),
            '--output-csv': str(output_csv),
            '--output-sql': str(output_sql),
            '--table-name': 'test',
            '--tsv': False,
            '--csv': True,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--quiet': True,
            '--no-csv': False,
            '--no-sql': False,
            '--sample-lines': '5'
        }

        exit_code = clean_data.main(args)

        self.assertEqual(exit_code, 0)
        self.assertTrue(output_csv.exists())

    def test_quiet_mode(self):
        """Should suppress output in quiet mode"""
        content = "Company\tValue\nAcme\t50%\n"
        file_path = self.create_test_file("test.tsv", content)
        output_csv = self.temp_path / "output.csv"
        output_sql = self.temp_path / "output.sql"

        args = {
            '<input_file>': str(file_path),
            '--output-csv': str(output_csv),
            '--output-sql': str(output_sql),
            '--table-name': 'test',
            '--tsv': True,
            '--csv': False,
            '--pipe': False,
            '--semicolon': False,
            '--delimiter': None,
            '--quiet': True,
            '--no-csv': False,
            '--no-sql': False,
            '--sample-lines': '5'
        }

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        clean_data.main(args)
        output = sys.stdout.getvalue()

        sys.stdout = old_stdout

        # Should have minimal or no output in quiet mode
        self.assertEqual(output, '')


if __name__ == '__main__':
    unittest.main()
