# Mailing List Validator

A Python application that collates and deduplicates contact information from multiple CSV and text files.

## Overview

This tool processes multiple contact data files of varying formats, intelligently maps fields to a standardized schema, and produces a single deduplicated output file.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Process Contact Files

1. Place your contact data files (CSV, XLSX, XLS, or TXT) in the `ingest/` directory
2. Run the processor:
```bash
python src/main.py
```
3. The application will:
   - Process all existing unprocessed files in the ingest directory
   - Watch the ingest directory for new files in real-time
   - Show progress as files are processed
4. Output will be saved to `output/contacts_consolidated.csv`

### Step 2: Validate Email Addresses (Optional)

After processing, you can validate email addresses to remove invalid entries:

#### DNS Validation (Recommended First)
Checks if domains exist and have MX records:
```bash
python src/validate_dns.py output/contacts_consolidated.csv
```

This will:
- Verify each email domain exists
- Confirm domain has MX (mail exchange) records
- Remove entries with invalid domains
- Create a backup before modifying the file

#### SMTP Mailbox Validation (Optional)
Connects to mail servers to verify mailbox existence:
```bash
python src/validate_smtp.py output/contacts_consolidated.csv
```

Options:
- `--timeout=N` - Set connection timeout in seconds (default: 10)
- `--no-fallback` - Only accept positively verified emails (more strict)

**Important Notes:**
- SMTP validation can take significant time for large lists
- Many mail servers block verification attempts to prevent harvesting
- False positives/negatives are common with SMTP validation
- Always run DNS validation first to catch obvious invalid domains
- Consider professional validation services for critical mailing lists

#### Example Workflow
```bash
# Step 1: Process all contact files
python src/main.py

# Step 2: Validate domains (fast, removes obviously invalid)
python src/validate_dns.py output/contacts_consolidated.csv

# Step 3 (optional): Validate mailboxes (slow, may have false positives)
python src/validate_smtp.py output/contacts_consolidated.csv --timeout=5
```

## Supported File Formats

- CSV files (`.csv`) - with automatic encoding detection
- Excel files (`.xlsx`, `.xls`)
- Text files (`.txt`) - one email address per line
- Files with various column names and formats are automatically mapped

## Output Schema

The application produces a standardized output with the following fields (EMAIL is the unique identifier):

- EMAIL (validated for correct format)
- FIRSTNAME
- LASTNAME
- FULLNAME
- COMPANYNAME
- SMS
- LANDLINE_NUMBER
- WHATSAPP
- INTERESTS
- LINKEDIN
- FACEBOOK
- WEBSITE
- ADDRESS1
- ADDRESS2
- CITY
- COUNTRY
- POSTCODE

## Data Quality Features

- **Email Validation**: Only records with valid email addresses are included
- **Garbage Filtering**: Automatically removes Excel errors (#VALUE!, #REF!, etc.) and invalid data
- **Deduplication**: EMAIL serves as the unique identifier - duplicate emails are merged
- **Data Merging**: When duplicates are found, combines data to create most complete record
- **Smart Field Mapping**: Automatically detects and maps various column names from different sources

## Important Notes

- Files in the `ingest/` directory are **never modified** - they remain read-only
- To reprocess data, delete files in `output/` and restart the application
- Only contacts with valid email addresses are included in the output
- All data is validated and cleaned during processing
