#!/usr/bin/env python3
"""
DNS Validation Script

This script validates email addresses in the consolidated contact list by checking:
1. Domain exists (has DNS records)
2. Domain has MX (Mail Exchange) records

Emails that fail validation are removed from the output file.
A backup of the original file is created before modification.
"""

import csv
import dns.resolver
import sys
from pathlib import Path
from datetime import datetime


def extract_domain(email):
    """Extract domain from email address."""
    if not email or '@' not in email:
        return None
    return email.split('@')[1].strip().lower()


def validate_domain_dns(domain):
    """
    Check if domain has DNS records.

    Args:
        domain: Domain name to check

    Returns:
        bool: True if domain has DNS records, False otherwise
    """
    try:
        dns.resolver.resolve(domain, 'A')
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        return False
    except Exception as e:
        print(f"  Warning: Unexpected error checking DNS for {domain}: {e}")
        return False


def validate_domain_mx(domain):
    """
    Check if domain has MX records.

    Args:
        domain: Domain name to check

    Returns:
        bool: True if domain has MX records, False otherwise
    """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return len(mx_records) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        return False
    except Exception as e:
        print(f"  Warning: Unexpected error checking MX for {domain}: {e}")
        return False


def validate_email_dns(email):
    """
    Validate email by checking domain DNS and MX records.

    Args:
        email: Email address to validate

    Returns:
        tuple: (is_valid, reason)
    """
    domain = extract_domain(email)

    if not domain:
        return False, "Invalid email format"

    # Check if domain exists
    if not validate_domain_dns(domain):
        return False, "Domain does not exist"

    # Check if domain has MX records
    if not validate_domain_mx(domain):
        return False, "No MX records found"

    return True, "Valid"


def process_contacts_file(input_file, output_file=None, create_backup=True):
    """
    Process contacts file and remove entries with invalid email addresses.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (defaults to overwriting input)
        create_backup: Whether to create a backup of the original file
    """
    input_path = Path(input_file)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}")
        return

    # Default output to input file (overwrite)
    if output_file is None:
        output_file = input_file

    output_path = Path(output_file)

    # Create backup if requested
    if create_backup:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = input_path.parent / f"{input_path.stem}_backup_{timestamp}{input_path.suffix}"
        print(f"Creating backup: {backup_path}")

        with open(input_path, 'r', encoding='utf-8') as src, \
             open(backup_path, 'w', encoding='utf-8', newline='') as dst:
            dst.write(src.read())

    # Read all contacts
    print(f"\nReading contacts from: {input_file}")

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        contacts = list(reader)

    print(f"Total contacts: {len(contacts)}")

    # Validate each contact
    valid_contacts = []
    invalid_contacts = []

    print("\nValidating email addresses...")

    for i, contact in enumerate(contacts, 1):
        email = contact.get('EMAIL', '').strip()

        if not email:
            print(f"{i}/{len(contacts)}: Skipping row with no email")
            invalid_contacts.append((contact, "No email address"))
            continue

        is_valid, reason = validate_email_dns(email)

        if is_valid:
            valid_contacts.append(contact)
            print(f"{i}/{len(contacts)}: ✓ {email}")
        else:
            invalid_contacts.append((contact, reason))
            print(f"{i}/{len(contacts)}: ✗ {email} - {reason}")

    # Write valid contacts to output file
    print(f"\nWriting {len(valid_contacts)} valid contacts to: {output_file}")

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(valid_contacts)

    # Summary
    print("\n" + "="*70)
    print("DNS VALIDATION SUMMARY")
    print("="*70)
    print(f"Total contacts processed: {len(contacts)}")
    print(f"Valid emails: {len(valid_contacts)}")
    print(f"Invalid emails: {len(invalid_contacts)}")
    print(f"Removal rate: {len(invalid_contacts)/len(contacts)*100:.1f}%")

    if invalid_contacts:
        print("\nInvalid emails by reason:")
        reasons = {}
        for _, reason in invalid_contacts:
            reasons[reason] = reasons.get(reason, 0) + 1

        for reason, count in sorted(reasons.items(), key=lambda x: x[1], reverse=True):
            print(f"  {reason}: {count}")

    print("="*70)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_dns.py <input_file> [output_file]")
        print("\nExample:")
        print("  python src/validate_dns.py output/contacts_consolidated.csv")
        print("  python src/validate_dns.py output/contacts_consolidated.csv output/contacts_dns_validated.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    print("="*70)
    print("DNS VALIDATION")
    print("="*70)

    process_contacts_file(input_file, output_file)


if __name__ == '__main__':
    main()
