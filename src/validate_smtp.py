#!/usr/bin/env python3
"""
SMTP Mailbox Validation Script

This script validates email addresses by connecting to the mail server and checking
if the mailbox exists without actually sending an email. It uses the SMTP VRFY or
RCPT TO commands to verify mailbox existence.

WARNING: Many mail servers disable VRFY for security reasons or return false positives
to prevent email harvesting. Results should be interpreted carefully.

Emails that fail validation are removed from the output file.
A backup of the original file is created before modification.
"""

import csv
import smtplib
import dns.resolver
import sys
import socket
from pathlib import Path
from datetime import datetime
from email.utils import parseaddr


def extract_domain(email):
    """Extract domain from email address."""
    if not email or '@' not in email:
        return None
    return email.split('@')[1].strip().lower()


def get_mx_hosts(domain):
    """
    Get MX hosts for a domain, ordered by priority.

    Args:
        domain: Domain name

    Returns:
        list: List of MX host names ordered by priority
    """
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        # Sort by priority (lower is higher priority)
        mx_hosts = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in mx_records])
        return [host for _, host in mx_hosts]
    except Exception:
        return []


def validate_email_smtp(email, timeout=10, use_fallback=True):
    """
    Validate email by connecting to SMTP server and checking mailbox existence.

    Args:
        email: Email address to validate
        timeout: Connection timeout in seconds
        use_fallback: If True, assume valid if server doesn't support verification

    Returns:
        tuple: (is_valid, reason, details)
    """
    domain = extract_domain(email)

    if not domain:
        return False, "Invalid email format", ""

    # Get MX hosts
    mx_hosts = get_mx_hosts(domain)

    if not mx_hosts:
        return False, "No MX records found", ""

    # Try each MX host
    last_error = ""

    for mx_host in mx_hosts:
        try:
            # Connect to SMTP server
            with smtplib.SMTP(timeout=timeout) as smtp:
                smtp.connect(mx_host, 25)
                smtp.set_debuglevel(0)

                # Get server greeting
                code, message = smtp.helo('mail.validator.local')

                if code != 250:
                    last_error = f"HELO failed: {code}"
                    continue

                # Set a fake sender (required for RCPT TO)
                code, message = smtp.mail('validator@validator.local')

                if code != 250:
                    last_error = f"MAIL FROM failed: {code}"
                    continue

                # Try to verify recipient
                code, message = smtp.rcpt(email)

                # Response codes:
                # 250 = mailbox exists
                # 251 = user not local, will forward (accept as valid)
                # 252 = cannot verify, but will accept message (greylisting)
                # 450-451 = temporary failure
                # 550-551 = mailbox doesn't exist
                # 552-553 = exceeded storage / policy

                if code == 250:
                    return True, "Mailbox verified", f"{mx_host}: {code}"
                elif code == 251:
                    return True, "Will forward", f"{mx_host}: {code}"
                elif code == 252:
                    # Server won't verify but will accept
                    if use_fallback:
                        return True, "Cannot verify (accepting)", f"{mx_host}: {code}"
                    else:
                        return False, "Cannot verify", f"{mx_host}: {code}"
                elif code in [450, 451]:
                    # Temporary failure, try next MX
                    last_error = f"{mx_host}: Temporary failure ({code})"
                    continue
                elif code >= 550:
                    # Permanent failure
                    return False, "Mailbox does not exist", f"{mx_host}: {code}"
                else:
                    last_error = f"{mx_host}: Unexpected code {code}"
                    continue

        except smtplib.SMTPServerDisconnected:
            last_error = f"{mx_host}: Server disconnected"
            continue
        except smtplib.SMTPConnectError as e:
            last_error = f"{mx_host}: Connection failed"
            continue
        except socket.timeout:
            last_error = f"{mx_host}: Connection timeout"
            continue
        except socket.gaierror:
            last_error = f"{mx_host}: Cannot resolve hostname"
            continue
        except Exception as e:
            last_error = f"{mx_host}: {type(e).__name__}"
            continue

    # If we got here, all MX hosts failed
    if use_fallback:
        # Conservative approach: assume valid if we can't verify
        return True, "Cannot verify (accepting)", last_error
    else:
        return False, "All MX hosts failed", last_error


def process_contacts_file(input_file, output_file=None, create_backup=True,
                         timeout=10, use_fallback=True):
    """
    Process contacts file and remove entries with invalid email addresses.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (defaults to overwriting input)
        create_backup: Whether to create a backup of the original file
        timeout: SMTP connection timeout in seconds
        use_fallback: If True, assume valid if server doesn't support verification
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

    print("\nValidating email addresses via SMTP...")
    print(f"Settings: timeout={timeout}s, fallback={'enabled' if use_fallback else 'disabled'}")
    print("Note: This may take a while...\n")

    for i, contact in enumerate(contacts, 1):
        email = contact.get('EMAIL', '').strip()

        if not email:
            print(f"{i}/{len(contacts)}: Skipping row with no email")
            invalid_contacts.append((contact, "No email address"))
            continue

        is_valid, reason, details = validate_email_smtp(email, timeout, use_fallback)

        if is_valid:
            valid_contacts.append(contact)
            print(f"{i}/{len(contacts)}: ✓ {email} - {reason}")
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
    print("SMTP VALIDATION SUMMARY")
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

    print("\n" + "="*70)
    print("IMPORTANT NOTES:")
    print("  - Many mail servers block SMTP verification to prevent harvesting")
    print("  - False positives/negatives are common")
    print("  - Use DNS validation first to filter out obvious invalid domains")
    print("  - Consider using a professional email validation service for critical lists")
    print("="*70)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_smtp.py <input_file> [output_file] [--no-fallback] [--timeout=N]")
        print("\nOptions:")
        print("  --no-fallback    Only accept emails that are positively verified")
        print("  --timeout=N      Set connection timeout in seconds (default: 10)")
        print("\nExamples:")
        print("  python src/validate_smtp.py output/contacts_consolidated.csv")
        print("  python src/validate_smtp.py output/contacts_consolidated.csv output/contacts_smtp_validated.csv")
        print("  python src/validate_smtp.py output/contacts_consolidated.csv --timeout=5 --no-fallback")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = None
    use_fallback = True
    timeout = 10

    # Parse arguments
    for arg in sys.argv[2:]:
        if arg == '--no-fallback':
            use_fallback = False
        elif arg.startswith('--timeout='):
            timeout = int(arg.split('=')[1])
        elif not arg.startswith('--'):
            output_file = arg

    print("="*70)
    print("SMTP MAILBOX VALIDATION")
    print("="*70)

    process_contacts_file(input_file, output_file, timeout=timeout, use_fallback=use_fallback)


if __name__ == '__main__':
    main()
