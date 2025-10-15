"""
Contact processing and deduplication logic.
"""

import pandas as pd
import hashlib
import uuid
from typing import List, Dict, Set
from pathlib import Path
from schema import OUTPUT_FIELDS


class ContactProcessor:
    """Handles contact deduplication and consolidation."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_file = output_dir / 'contacts_consolidated.csv'
        self.processed_files_log = output_dir / 'processed_files.txt'
        self.contacts_db: Dict[str, Dict] = {}  # Keyed by dedup key
        self.email_to_key: Dict[str, str] = {}  # Email to dedup key mapping
        self.processed_files: Set[str] = set()

        # Load existing data if it exists
        self._load_existing_data()

    def _load_existing_data(self):
        """Load existing contacts and processed files log."""
        # Load processed files log
        if self.processed_files_log.exists():
            with open(self.processed_files_log, 'r') as f:
                self.processed_files = set(line.strip() for line in f if line.strip())

        # Load existing contacts
        if self.output_file.exists():
            try:
                df = pd.read_csv(self.output_file)
                print(f"📂 Loaded {len(df)} existing contacts from {self.output_file.name}")

                for _, row in df.iterrows():
                    record = row.to_dict()
                    email = record.get('EMAIL', '').strip().lower()

                    if email:
                        # Reconstruct dedup key
                        dedup_key = self._generate_dedup_key(record)
                        self.contacts_db[dedup_key] = record

                        # Index by email
                        self.email_to_key[email] = dedup_key

            except Exception as e:
                print(f"⚠️  Error loading existing data: {e}")

    def _generate_dedup_key(self, record: Dict) -> str:
        """
        Generate a deduplication key for a contact.
        Uses email as primary key, falls back to name + other fields.

        Args:
            record: Contact record

        Returns:
            Deduplication key string
        """
        email = record.get('EMAIL', '').strip().lower()

        if email:
            # Email is the strongest identifier
            return f"email:{email}"

        # Fallback to name-based key
        fullname = record.get('FULLNAME', '').strip().lower()
        firstname = record.get('FIRSTNAME', '').strip().lower()
        lastname = record.get('LASTNAME', '').strip().lower()

        name_key = fullname or f"{firstname} {lastname}".strip()

        if name_key:
            # Add some additional context to avoid false positives
            company_hint = ''
            for field in ['WEBSITE', 'LINKEDIN']:
                value = record.get(field, '').strip().lower()
                if value:
                    company_hint = value[:50]  # First 50 chars
                    break

            if company_hint:
                return f"name:{name_key}::{company_hint}"
            else:
                return f"name:{name_key}"

        # Last resort: generate a unique ID (won't match anything)
        return f"unique:{uuid.uuid4()}"

    def _merge_records(self, existing: Dict, new: Dict) -> Dict:
        """
        Merge two contact records, preferring non-empty values.

        Args:
            existing: Existing contact record
            new: New contact record

        Returns:
            Merged record
        """
        merged = existing.copy()

        for field in OUTPUT_FIELDS:
            existing_value = str(existing.get(field, '')).strip()
            new_value = str(new.get(field, '')).strip()

            # Prefer longer/more complete value
            if not existing_value and new_value:
                merged[field] = new_value
            elif existing_value and new_value:
                # If both exist, prefer longer one or combine interests
                if field == 'INTERESTS':
                    # Combine interests
                    interests = set()
                    for val in [existing_value, new_value]:
                        interests.update([i.strip() for i in val.split(',') if i.strip()])
                    merged[field] = ', '.join(sorted(interests))
                elif len(new_value) > len(existing_value):
                    merged[field] = new_value

        return merged

    def process_records(self, records: List[Dict], source_file: str) -> int:
        """
        Process a list of contact records, deduplicating and merging.

        Args:
            records: List of contact records
            source_file: Source filename

        Returns:
            Number of new contacts added
        """
        new_count = 0
        updated_count = 0

        for record in records:
            dedup_key = self._generate_dedup_key(record)

            if dedup_key in self.contacts_db:
                # Merge with existing
                self.contacts_db[dedup_key] = self._merge_records(
                    self.contacts_db[dedup_key],
                    record
                )
                updated_count += 1
            else:
                # New contact
                self.contacts_db[dedup_key] = record

                # Index by email
                email = record.get('EMAIL', '').strip().lower()
                if email:
                    self.email_to_key[email] = dedup_key

                new_count += 1

        # Mark file as processed
        self.processed_files.add(source_file)

        print(f"  📈 Added {new_count} new contacts, updated {updated_count} existing")
        return new_count

    def save_output(self):
        """Save the consolidated contacts to CSV."""
        try:
            # Convert to DataFrame
            records_list = list(self.contacts_db.values())

            if not records_list:
                print("⚠️  No contacts to save")
                return

            df = pd.DataFrame(records_list, columns=OUTPUT_FIELDS)

            # Sort by email, then name
            df = df.sort_values(
                by=['EMAIL', 'LASTNAME', 'FIRSTNAME'],
                na_position='last'
            )

            # Save to CSV
            self.output_dir.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.output_file, index=False, encoding='utf-8')

            # Save processed files log
            with open(self.processed_files_log, 'w') as f:
                for filename in sorted(self.processed_files):
                    f.write(f"{filename}\n")

            print(f"\n💾 Saved {len(df)} total contacts to {self.output_file}")
            print(f"   📋 Email addresses: {df['EMAIL'].notna().sum()}")
            print(f"   👤 Named contacts: {df['FULLNAME'].notna().sum()}")

        except Exception as e:
            print(f"❌ Error saving output: {e}")

    def get_stats(self) -> Dict:
        """Get current statistics."""
        return {
            'total_contacts': len(self.contacts_db),
            'files_processed': len(self.processed_files),
            'contacts_with_email': sum(1 for r in self.contacts_db.values() if r.get('EMAIL'))
        }
