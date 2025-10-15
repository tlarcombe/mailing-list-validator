# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a contact information collation and deduplication application. It processes multiple CSV and text files containing investor contact data, intelligently maps varying formats to a standardized schema, and produces a single deduplicated output file.

## Project Structure

```
mailing_list_validator/
├── ingest/          # Input directory for CSV/text files (READ-ONLY)
├── output/          # Processed output files
├── src/             # Source code
│   ├── main.py      # Entry point with file watching
│   ├── parser.py    # Field detection and mapping logic
│   ├── processor.py # Data processing and deduplication
│   └── schema.py    # Output schema definition
├── requirements.txt
└── README.md
```

## Core Architecture

### Immutable Input Principle
Files in `ingest/` directory are NEVER modified. This allows reprocessing by deleting output files and restarting. All processing is non-destructive to source data.

### Output Schema
Standardized fields: CONTACTID, EMAIL, FULLNAME, FIRSTNAME, LASTNAME, SMS, LANDLINE_NUMBER, WHATSAPP, INTERESTS, LINKEDIN, FACEBOOK, WEBSITE, ADDRESS1, ADDRESS2, CITY, COUNTRY, POSTCODE

### Processing Pipeline
1. **File Watching**: Uses watchdog to monitor `ingest/` directory
2. **Format Detection**: Intelligently analyzes input file structure and field names
3. **Field Mapping**: Maps various input formats to standardized schema
4. **Deduplication**: Identifies and merges duplicate contacts
5. **Output Generation**: Writes consolidated data to `output/contacts_consolidated.csv`

## Development Commands

### Setup
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Run the application
```bash
python src/main.py
```

### Testing with sample files
Place test CSV/text files in `ingest/` directory and observe real-time processing output.

### Reset and reprocess
```bash
rm output/*
python src/main.py
```
- Always update github after making changes to the code.