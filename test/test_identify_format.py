#!/usr/bin/env python3
"""Unit tests for identify_format.py"""

import unittest
import tempfile
import sys
from pathlib import Path
from io import StringIO

# Add parent directory to path to import modules from script/
sys.path.insert(0, str(Path(__file__).parent.parent / 'script'))

# Import the module to test
import identify_format


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
        """Should detect TAB delimiter (TSV format)"""
        content = "Name\tAge\tCity\nAlice\t30\tNY\nBob\t25\tLA\n"
        file_path = self.create_test_file("test.tsv", content)

        delim, name, confidence = identify_format.detect_delimiter(file_path)

        self.assertEqual(delim, '\t')
        self.assertEqual(name, 'TSV')
        self.assertGreater(confidence, 0.5)

    def test_detect_comma_delimiter(self):
        """Should detect comma delimiter (CSV format)"""
        content = "Name,Age,City\nAlice,30,NY\nBob,25,LA\n"
        file_path = self.create_test_file("test.csv", content)

        delim, name, confidence = identify_format.detect_delimiter(file_path)

        self.assertEqual(delim, ',')
        self.assertEqual(name, 'CSV')
        self.assertGreater(confidence, 0.5)

    def test_detect_pipe_delimiter(self):
        """Should detect pipe delimiter"""
        content = "Name|Age|City\nAlice|30|NY\nBob|25|LA\n"
        file_path = self.create_test_file("test.pipe", content)

        delim, name, confidence = identify_format.detect_delimiter(file_path)

        self.assertEqual(delim, '|')
        self.assertEqual(name, 'PIPE')
        self.assertGreater(confidence, 0.5)

    def test_detect_semicolon_delimiter(self):
        """Should detect semicolon delimiter"""
        content = "Name;Age;City\nAlice;30;NY\nBob;25;LA\n"
        file_path = self.create_test_file("test.semi", content)

        delim, name, confidence = identify_format.detect_delimiter(file_path)

        self.assertEqual(delim, ';')
        self.assertEqual(name, 'SEMICOLON')
        self.assertGreater(confidence, 0.5)

    def test_file_not_found(self):
        """Should raise FileNotFoundError for non-existent file"""
        file_path = self.temp_path / "nonexistent.txt"

        with self.assertRaises(FileNotFoundError):
            identify_format.detect_delimiter(file_path)

    def test_empty_file(self):
        """Should raise ValueError for empty file"""
        file_path = self.create_test_file("empty.txt", "")

        with self.assertRaises(ValueError):
            identify_format.detect_delimiter(file_path)

    def test_no_clear_delimiter(self):
        """Should raise ValueError when no delimiter detected"""
        content = "NoDelimitersHere\nJustPlainText\n"
        file_path = self.create_test_file("plain.txt", content)

        with self.assertRaises(ValueError):
            identify_format.detect_delimiter(file_path)

    def test_consistent_delimiter_counts(self):
        """Should have high confidence for consistent delimiters"""
        content = "A\tB\tC\nD\tE\tF\nG\tH\tI\n"
        file_path = self.create_test_file("consistent.tsv", content)

        delim, name, confidence = identify_format.detect_delimiter(file_path)

        self.assertEqual(confidence, 1.0)  # 100% consistent

    def test_inconsistent_delimiter_counts(self):
        """Should still pick best delimiter even if inconsistent"""
        # Mix of 2 and 3 tabs per line
        content = "A\tB\tC\nD\tE\nF\tG\tH\n"
        file_path = self.create_test_file("inconsistent.tsv", content)

        delim, name, confidence = identify_format.detect_delimiter(file_path)

        self.assertEqual(delim, '\t')
        # Confidence should be lower than 1.0 due to inconsistency
        self.assertLess(confidence, 1.0)

    def test_custom_sample_lines(self):
        """Should respect sample_lines parameter"""
        content = "A\tB\n" * 10  # 10 lines
        file_path = self.create_test_file("many_lines.tsv", content)

        # Should work with different sample sizes
        delim1, _, _ = identify_format.detect_delimiter(file_path, sample_lines=3)
        delim2, _, _ = identify_format.detect_delimiter(file_path, sample_lines=7)

        self.assertEqual(delim1, '\t')
        self.assertEqual(delim2, '\t')


class TestAnalyzeFileStructure(unittest.TestCase):
    """Test cases for analyze_file_structure function"""

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

    def test_analyze_tsv_structure(self):
        """Should correctly analyze TSV file structure"""
        content = "Name\tAge\tCity\nAlice\t30\tNY\nBob\t25\tLA\n"
        file_path = self.create_test_file("test.tsv", content)

        analysis = identify_format.analyze_file_structure(file_path, '\t', sample_lines=5)

        self.assertEqual(analysis['num_columns'], 3)
        self.assertEqual(analysis['headers'], ['Name', 'Age', 'City'])
        self.assertTrue(analysis['consistent_columns'])
        self.assertEqual(analysis['sample_rows'], 2)

    def test_count_columns_correctly(self):
        """Should count columns correctly"""
        content = "A\tB\tC\tD\tE\nF\tG\tH\tI\tJ\n"
        file_path = self.create_test_file("test.tsv", content)

        analysis = identify_format.analyze_file_structure(file_path, '\t')

        self.assertEqual(analysis['num_columns'], 5)

    def test_extract_headers_correctly(self):
        """Should extract headers with whitespace trimmed"""
        content = " Name \t Age \t City \nAlice\t30\tNY\n"
        file_path = self.create_test_file("test.tsv", content)

        analysis = identify_format.analyze_file_structure(file_path, '\t')

        self.assertEqual(analysis['headers'], ['Name', 'Age', 'City'])

    def test_detect_consistent_columns(self):
        """Should detect when all rows have same column count"""
        content = "A\tB\tC\nD\tE\tF\nG\tH\tI\n"
        file_path = self.create_test_file("test.tsv", content)

        analysis = identify_format.analyze_file_structure(file_path, '\t')

        self.assertTrue(analysis['consistent_columns'])

    def test_detect_inconsistent_columns(self):
        """Should detect when rows have different column counts"""
        content = "A\tB\tC\nD\tE\nF\tG\tH\tI\n"
        file_path = self.create_test_file("test.tsv", content)

        analysis = identify_format.analyze_file_structure(file_path, '\t')

        self.assertFalse(analysis['consistent_columns'])
        self.assertEqual(analysis['column_counts'], [2, 4])

    def test_empty_file(self):
        """Should return empty dict for empty file"""
        file_path = self.create_test_file("empty.txt", "")

        analysis = identify_format.analyze_file_structure(file_path, '\t')

        self.assertEqual(analysis, {})

    def test_only_headers(self):
        """Should handle file with only headers"""
        content = "Name\tAge\tCity\n"
        file_path = self.create_test_file("headers_only.tsv", content)

        analysis = identify_format.analyze_file_structure(file_path, '\t')

        self.assertEqual(analysis['num_columns'], 3)
        self.assertEqual(analysis['sample_rows'], 0)


class TestFormatOutput(unittest.TestCase):
    """Test cases for format_output function"""

    def test_normal_output(self):
        """Should include all info in normal mode"""
        output = identify_format.format_output(
            '\t', 'TSV', 0.95,
            Path('/test/file.txt'),
            quiet=False,
            verbose=False
        )

        self.assertIn('File:', output)
        self.assertIn('TSV', output)
        self.assertIn('95.0%', output)
        self.assertIn('Delimiter:', output)

    def test_quiet_mode(self):
        """Should only output delimiter name in quiet mode"""
        output = identify_format.format_output(
            '\t', 'TSV', 0.95,
            Path('/test/file.txt'),
            quiet=True,
            verbose=False
        )

        self.assertEqual(output, 'TSV')

    def test_verbose_mode(self):
        """Should include detailed analysis in verbose mode"""
        analysis = {
            'num_columns': 3,
            'headers': ['A', 'B', 'C'],
            'consistent_columns': True,
            'sample_rows': 5
        }

        output = identify_format.format_output(
            '\t', 'TSV', 0.95,
            Path('/test/file.txt'),
            analysis=analysis,
            quiet=False,
            verbose=True
        )

        self.assertIn('Detailed Analysis:', output)
        self.assertIn('Columns: 3', output)
        self.assertIn('A, B, C', output)
        self.assertIn('Consistent structure: Yes', output)

    def test_verbose_without_analysis(self):
        """Should handle verbose mode without analysis data"""
        output = identify_format.format_output(
            '\t', 'TSV', 0.95,
            Path('/test/file.txt'),
            analysis=None,
            quiet=False,
            verbose=True
        )

        # Should not crash, but won't have detailed analysis
        self.assertIn('TSV', output)
        self.assertNotIn('Detailed Analysis:', output)

    def test_many_headers_truncation(self):
        """Should truncate header list if too many"""
        analysis = {
            'num_columns': 8,
            'headers': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'],
            'consistent_columns': True,
            'sample_rows': 5
        }

        output = identify_format.format_output(
            '\t', 'TSV', 0.95,
            Path('/test/file.txt'),
            analysis=analysis,
            quiet=False,
            verbose=True
        )

        self.assertIn('...', output)  # Should show ellipsis for truncation


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
        content = "Name\tAge\nAlice\t30\n"
        file_path = self.create_test_file("test.tsv", content)

        args = {
            '<input_file>': str(file_path),
            '--quiet': True,
            '--verbose': False,
            '--sample-lines': '5'
        }

        exit_code = identify_format.main(args)

        self.assertEqual(exit_code, 0)

    def test_file_not_found(self):
        """Should return 1 when file not found"""
        args = {
            '<input_file>': str(self.temp_path / 'nonexistent.txt'),
            '--quiet': True,
            '--verbose': False,
            '--sample-lines': '5'
        }

        exit_code = identify_format.main(args)

        self.assertEqual(exit_code, 1)

    def test_quiet_flag(self):
        """Should suppress output with quiet flag"""
        content = "Name\tAge\nAlice\t30\n"
        file_path = self.create_test_file("test.tsv", content)

        args = {
            '<input_file>': str(file_path),
            '--quiet': True,
            '--verbose': False,
            '--sample-lines': '5'
        }

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        identify_format.main(args)
        output = sys.stdout.getvalue()

        sys.stdout = old_stdout

        # Should only output format name
        self.assertEqual(output.strip(), 'TSV')

    def test_verbose_flag(self):
        """Should show detailed analysis with verbose flag"""
        content = "Name\tAge\nAlice\t30\n"
        file_path = self.create_test_file("test.tsv", content)

        args = {
            '<input_file>': str(file_path),
            '--quiet': False,
            '--verbose': True,
            '--sample-lines': '5'
        }

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        identify_format.main(args)
        output = sys.stdout.getvalue()

        sys.stdout = old_stdout

        self.assertIn('Detailed Analysis:', output)

    def test_sample_lines_argument(self):
        """Should respect sample-lines argument"""
        content = "Name\tAge\n" + ("Alice\t30\n" * 10)
        file_path = self.create_test_file("test.tsv", content)

        args = {
            '<input_file>': str(file_path),
            '--quiet': True,
            '--verbose': False,
            '--sample-lines': '3'
        }

        exit_code = identify_format.main(args)

        self.assertEqual(exit_code, 0)

    def test_no_delimiter_error(self):
        """Should return 1 when no delimiter can be detected"""
        content = "NoDelimitersHere\nJustPlainText\n"
        file_path = self.create_test_file("plain.txt", content)

        args = {
            '<input_file>': str(file_path),
            '--quiet': True,
            '--verbose': False,
            '--sample-lines': '5'
        }

        exit_code = identify_format.main(args)

        self.assertEqual(exit_code, 1)


if __name__ == '__main__':
    unittest.main()
