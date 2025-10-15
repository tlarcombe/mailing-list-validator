#!/usr/bin/env python3
"""
Mailing List Validator - Main Entry Point

Watches the ingest directory for CSV and Excel files,
processes them, and outputs consolidated contact data.
"""

import sys
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from parser import FileParser
from processor import ContactProcessor


class IngestHandler(FileSystemEventHandler):
    """Handles file system events in the ingest directory."""

    def __init__(self, parser: FileParser, processor: ContactProcessor, ingest_dir: Path):
        self.parser = parser
        self.processor = processor
        self.ingest_dir = ingest_dir
        self.processing = set()  # Track files currently being processed

    def on_created(self, event):
        """Called when a file is created in the ingest directory."""
        if event.is_directory:
            return

        self.process_file(Path(event.src_path))

    def on_modified(self, event):
        """Called when a file is modified in the ingest directory."""
        if event.is_directory:
            return

        # Handle modifications (some programs create files by writing)
        self.process_file(Path(event.src_path))

    def process_file(self, file_path: Path):
        """
        Process a single file.

        Args:
            file_path: Path to the file to process
        """
        # Only process CSV, Excel, and TXT files
        if file_path.suffix.lower() not in ['.csv', '.xlsx', '.xls', '.txt']:
            return

        # Avoid processing the same file multiple times
        if file_path.name in self.processing:
            return

        # Check if already processed
        if file_path.name in self.processor.processed_files:
            return

        try:
            self.processing.add(file_path.name)

            # Small delay to ensure file is fully written
            time.sleep(0.5)

            # Parse the file
            records = self.parser.parse_file(file_path)

            if records:
                # Process records
                self.processor.process_records(records, file_path.name)

                # Save output
                self.processor.save_output()

        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")

        finally:
            self.processing.discard(file_path.name)


def process_existing_files(ingest_dir: Path, parser: FileParser, processor: ContactProcessor):
    """
    Process all existing files in the ingest directory.

    Args:
        ingest_dir: Path to ingest directory
        parser: File parser instance
        processor: Contact processor instance
    """
    print("🔍 Scanning for existing files in ingest directory...")

    files = []
    for ext in ['*.csv', '*.xlsx', '*.xls', '*.txt']:
        files.extend(ingest_dir.glob(ext))

    # Filter out already processed files
    files_to_process = [f for f in files if f.name not in processor.processed_files]

    if not files_to_process:
        print("✅ All existing files already processed")
        return

    print(f"📋 Found {len(files_to_process)} unprocessed files")

    for file_path in sorted(files_to_process):
        try:
            # Parse the file
            records = parser.parse_file(file_path)

            if records:
                # Process records
                processor.process_records(records, file_path.name)

        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")

    # Save consolidated output
    processor.save_output()


def main():
    """Main entry point."""
    print("=" * 60)
    print("📬 MAILING LIST VALIDATOR")
    print("=" * 60)

    # Setup paths
    project_dir = Path(__file__).parent.parent
    ingest_dir = project_dir / 'ingest'
    output_dir = project_dir / 'output'

    # Create directories if needed
    ingest_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    print(f"\n📁 Ingest directory: {ingest_dir}")
    print(f"📁 Output directory: {output_dir}")

    # Initialize parser and processor
    parser = FileParser()
    processor = ContactProcessor(output_dir)

    # Show current stats
    stats = processor.get_stats()
    print(f"\n📊 Current database stats:")
    print(f"   Total contacts: {stats['total_contacts']}")
    print(f"   With email: {stats['contacts_with_email']}")
    print(f"   Files processed: {stats['files_processed']}")

    # Process existing files
    print("\n" + "=" * 60)
    process_existing_files(ingest_dir, parser, processor)

    # Setup file watcher
    print("\n" + "=" * 60)
    print("👁️  Watching for new files...")
    print("   (Press Ctrl+C to stop)")
    print("=" * 60 + "\n")

    event_handler = IngestHandler(parser, processor, ingest_dir)
    observer = Observer()
    observer.schedule(event_handler, str(ingest_dir), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping...")
        observer.stop()

    observer.join()

    # Final stats
    stats = processor.get_stats()
    print("\n" + "=" * 60)
    print("📊 Final statistics:")
    print(f"   Total contacts: {stats['total_contacts']}")
    print(f"   With email: {stats['contacts_with_email']}")
    print(f"   Files processed: {stats['files_processed']}")
    print("=" * 60)
    print("\n✅ Done!")


if __name__ == '__main__':
    main()
