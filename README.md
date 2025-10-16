# Mailing List Validator

A Python application that collates and deduplicates contact information from multiple CSV and text files, with built-in DNS and SMTP email validation.

## Overview

This tool processes multiple contact data files of varying formats, intelligently maps fields to a standardized schema, and produces a single deduplicated output file. It includes advanced email validation capabilities to ensure your contact list contains only valid, deliverable email addresses.

## Features

- **Multi-format Support**: Process CSV, Excel (XLSX/XLS), and text files
- **Intelligent Field Mapping**: Automatically maps various column names to standardized schema
- **Deduplication**: Merges duplicate contacts based on email address
- **DNS Validation**: Verifies domain existence and MX records
- **SMTP Validation**: Checks mailbox existence via SMTP (optional)
- **Real-time Processing**: Monitors ingest directory for new files
- **Automatic Backups**: Creates backups before validation operations

## Installation

### Clone the Repository

```bash
git clone https://github.com/tlarcombe/mailing-list-validator.git
cd mailing-list-validator
```

### Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# On Windows: venv\Scripts\activate
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

Verifies that email domains exist and have proper MX (mail exchange) records:

```bash
python src/validate_dns.py output/contacts_consolidated.csv
```

**What it does:**
- ✅ Verifies each email domain exists in DNS
- ✅ Confirms domain has MX (mail exchange) records
- ✅ Creates automatic backup before modifying file
- ❌ Removes entries where domain doesn't exist
- ❌ Removes entries where domain has no MX records

**Performance:** Processes ~25,000 emails in 1-2 hours

#### SMTP Mailbox Validation (Optional)

Connects to mail servers to verify individual mailbox existence:

```bash
python src/validate_smtp.py output/contacts_consolidated.csv
```

**Default Behavior (Conservative - Recommended):**
- ✅ **Keeps emails** when server blocks verification (code 252)
- ✅ **Keeps emails** when connection fails/times out
- ✅ **Keeps emails** when server doesn't respond
- ❌ **Only removes** when server explicitly says "mailbox does not exist" (code 550+)

**Strict Mode (--no-fallback):**
```bash
python src/validate_smtp.py output/contacts_consolidated.csv --no-fallback
```
- ✅ **Only keeps** emails that are positively verified (codes 250, 251)
- ❌ **Removes** emails when verification is blocked or fails

**Options:**
- `--timeout=N` - Connection timeout in seconds (default: 10)
- `--no-fallback` - Enable strict mode (only keep verified emails)
- `--output=FILE` - Save to different file (preserves original)

**Important Considerations:**
- ⏱️ **Time:** Can take several hours for large lists (much slower than DNS)
- 🚫 **Blocking:** Many mail servers block verification to prevent email harvesting
- ⚠️ **Accuracy:** False positives/negatives are common
- 💡 **Best Practice:** Always run DNS validation first
- 🎯 **Use Case:** Best for final cleanup of critical mailing lists

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
