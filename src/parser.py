"""
Field detection and mapping logic for various input formats.
"""

import re
import pandas as pd
import chardet
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from schema import FIELD_MAPPINGS, get_output_template


class FileParser:
    """Handles parsing and field mapping for various file formats."""

    def __init__(self):
        self.field_map_cache = {}

    def is_valid_email(self, email: str) -> bool:
        """
        Validate if a string is a valid email address.

        Args:
            email: String to validate

        Returns:
            True if valid email, False otherwise
        """
        if not email or pd.isna(email):
            return False

        email = str(email).strip()

        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

        return bool(re.match(pattern, email))

    def contains_garbage(self, value: str) -> bool:
        """
        Check if a value contains garbage data (Excel errors, etc).

        Args:
            value: String to check

        Returns:
            True if contains garbage, False otherwise
        """
        if not value or pd.isna(value):
            return False

        value = str(value).strip()

        # Check for common garbage patterns
        garbage_patterns = [
            '#VALUE!',
            '#REF!',
            '#DIV/0!',
            '#N/A',
            '#NAME?',
            '#NULL!',
            '#NUM!',
            '￼',  # Object replacement character
            '\ufffc',  # Object replacement character
        ]

        return any(pattern in value for pattern in garbage_patterns)

    def clean_value(self, value: str) -> str:
        """
        Clean a cell value, removing garbage characters.

        Args:
            value: Value to clean

        Returns:
            Cleaned value or empty string if garbage
        """
        if not value or pd.isna(value):
            return ''

        value = str(value).strip()

        # Return empty if contains garbage
        if self.contains_garbage(value):
            return ''

        return value

    def detect_encoding(self, file_path: Path) -> str:
        """
        Detect the encoding of a file.

        Args:
            file_path: Path to the file

        Returns:
            Detected encoding name
        """
        with open(file_path, 'rb') as f:
            raw_data = f.read(100000)  # Read first 100KB
            result = chardet.detect(raw_data)
            return result['encoding'] or 'utf-8'

    def read_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """
        Read a file (CSV, Excel, or TXT) and return a DataFrame.
        Handles encoding detection and skips header rows.

        Args:
            file_path: Path to the file

        Returns:
            DataFrame with the file contents, or None if error
        """
        try:
            file_ext = file_path.suffix.lower()

            if file_ext in ['.xlsx', '.xls']:
                # Read Excel file
                df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else 'xlrd')
            elif file_ext == '.csv':
                # Detect encoding
                encoding = self.detect_encoding(file_path)

                # Try to read, detecting the right starting row
                df = self._read_csv_smart(file_path, encoding)
            elif file_ext == '.txt':
                # Read text file (one email per line)
                encoding = self.detect_encoding(file_path)
                df = self._read_txt_file(file_path, encoding)
            else:
                print(f"  ⚠️  Unsupported file type: {file_ext}")
                return None

            if df is None or df.empty:
                print(f"  ⚠️  File is empty or could not be read")
                return None

            # Clean column names
            df.columns = df.columns.astype(str).str.strip()

            # Remove completely empty rows
            df = df.dropna(how='all')

            # Remove rows where all values are empty strings
            df = df[~(df.astype(str).apply(lambda x: x.str.strip()) == '').all(axis=1)]

            return df

        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
            return None

    def _read_txt_file(self, file_path: Path, encoding: str) -> Optional[pd.DataFrame]:
        """
        Read a text file with one email per line.

        Args:
            file_path: Path to text file
            encoding: Detected encoding

        Returns:
            DataFrame with email column or None
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()

            # Filter out empty lines and strip whitespace
            emails = [line.strip() for line in lines if line.strip()]

            # Create DataFrame with EMAIL column
            df = pd.DataFrame({'EMAIL': emails})

            return df

        except Exception as e:
            print(f"  ⚠️  Error reading text file: {e}")
            return None

    def _read_csv_smart(self, file_path: Path, encoding: str) -> Optional[pd.DataFrame]:
        """
        Intelligently read CSV, detecting header rows and skipping metadata.

        Args:
            file_path: Path to CSV file
            encoding: Detected encoding

        Returns:
            DataFrame or None
        """
        # Try reading with different strategies
        try:
            # First attempt: standard read
            df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')

            # Check if first few rows look like headers/metadata
            # Look for a row with multiple non-empty columns as the real header
            if len(df) > 0:
                for skip_rows in range(min(5, len(df))):
                    test_df = pd.read_csv(
                        file_path,
                        encoding=encoding,
                        skiprows=skip_rows,
                        on_bad_lines='skip'
                    )

                    if test_df is not None and not test_df.empty:
                        # Count non-empty column names
                        non_empty_cols = sum(1 for col in test_df.columns if str(col).strip() and not str(col).startswith('Unnamed'))

                        if non_empty_cols >= 2:  # At least 2 named columns
                            return test_df

            return df

        except Exception as e:
            print(f"  ⚠️  Error in smart CSV read: {e}")
            return None

    def map_fields(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Map input DataFrame columns to output schema fields.

        Args:
            df: Input DataFrame

        Returns:
            Dictionary mapping output field names to input column names
        """
        field_mapping = {}
        input_columns = {col.lower(): col for col in df.columns}

        # Try to map each output field to an input column
        for output_field, patterns in FIELD_MAPPINGS.items():
            for pattern in patterns:
                pattern_lower = pattern.lower()

                # Exact match
                if pattern_lower in input_columns:
                    field_mapping[output_field] = input_columns[pattern_lower]
                    break

                # Partial match (contains)
                for input_col_lower, input_col_original in input_columns.items():
                    if pattern_lower in input_col_lower or input_col_lower in pattern_lower:
                        if output_field not in field_mapping:  # Prefer first/best match
                            field_mapping[output_field] = input_col_original
                            break

        return field_mapping

    def extract_name_parts(self, fullname: str) -> Tuple[str, str]:
        """
        Extract first and last name from full name.

        Args:
            fullname: Full name string

        Returns:
            Tuple of (firstname, lastname)
        """
        if not fullname or pd.isna(fullname):
            return '', ''

        fullname = str(fullname).strip()
        parts = fullname.split()

        if len(parts) == 0:
            return '', ''
        elif len(parts) == 1:
            return parts[0], ''
        else:
            return parts[0], ' '.join(parts[1:])

    def parse_file(self, file_path: Path) -> List[Dict]:
        """
        Parse a file and return a list of contact records.

        Args:
            file_path: Path to the file

        Returns:
            List of dictionaries with standardized fields
        """
        print(f"\n📄 Processing: {file_path.name}")

        # Read the file
        df = self.read_file(file_path)
        if df is None or df.empty:
            return []

        print(f"  📊 Found {len(df)} rows, {len(df.columns)} columns")

        # Map fields
        field_mapping = self.map_fields(df)
        print(f"  🗺️  Mapped {len(field_mapping)} fields: {', '.join(field_mapping.keys())}")

        # Convert to standardized records
        records = []
        skipped_invalid_email = 0
        skipped_garbage = 0

        for idx, row in df.iterrows():
            record = get_output_template()

            # Map fields and clean values
            for output_field, input_column in field_mapping.items():
                value = row.get(input_column, '')
                if pd.notna(value):
                    cleaned_value = self.clean_value(str(value).strip())
                    record[output_field] = cleaned_value

            # Check if any field contains garbage
            has_garbage = any(self.contains_garbage(str(v)) for v in record.values() if v)
            if has_garbage:
                skipped_garbage += 1
                continue

            # Validate email address
            if not record['EMAIL'] or not self.is_valid_email(record['EMAIL']):
                skipped_invalid_email += 1
                continue

            # Handle name splitting if we have FULLNAME but not FIRSTNAME/LASTNAME
            if record['FULLNAME'] and (not record['FIRSTNAME'] or not record['LASTNAME']):
                firstname, lastname = self.extract_name_parts(record['FULLNAME'])
                if not record['FIRSTNAME']:
                    record['FIRSTNAME'] = firstname
                if not record['LASTNAME']:
                    record['LASTNAME'] = lastname

            # Create FULLNAME if we have FIRSTNAME and LASTNAME but not FULLNAME
            if not record['FULLNAME'] and (record['FIRSTNAME'] or record['LASTNAME']):
                record['FULLNAME'] = f"{record['FIRSTNAME']} {record['LASTNAME']}".strip()

            records.append(record)

        # Report validation results
        if skipped_invalid_email > 0:
            print(f"  ⚠️  Skipped {skipped_invalid_email} rows with invalid email addresses")
        if skipped_garbage > 0:
            print(f"  ⚠️  Skipped {skipped_garbage} rows with garbage data")

        print(f"  ✅ Extracted {len(records)} valid contact records")
        return records
