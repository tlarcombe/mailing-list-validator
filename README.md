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

1. Place your contact data files (CSV, XLSX, or XLS) in the `ingest/` directory
2. Run the processor:
```bash
python src/main.py
```
3. The application will:
   - Process all existing unprocessed files in the ingest directory
   - Watch the ingest directory for new files in real-time
   - Show progress as files are processed
4. Output will be saved to `output/contacts_consolidated.csv`

## Supported File Formats

- CSV files (`.csv`) - with automatic encoding detection
- Excel files (`.xlsx`, `.xls`)
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
