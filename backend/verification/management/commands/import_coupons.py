"""
Import real Selar coupon codes from a CSV file into the database.

The CSV can have any of these formats — the command auto-detects the code column:

  1. Single column, no header:
       SELAR-ABC123
       SELAR-DEF456

  2. Single column, with header (any header name):
       code
       SELAR-ABC123

  3. Multi-column export from Selar (header required, 'code' column used):
       code,discount,uses
       SELAR-ABC123,30%,0

Usage:
  python manage.py import_coupons coupons.csv --campaign caleb-book-sale
  python manage.py import_coupons coupons.csv --campaign caleb-book-sale --dry-run
  python manage.py import_coupons coupons.csv --campaign caleb-book-sale --column discount_code
"""
import csv
import os
from django.core.management.base import BaseCommand, CommandError
from verification.models import Coupon, Campaign


class Command(BaseCommand):
    help = "Import Selar coupon codes from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the CSV file containing coupon codes",
        )
        parser.add_argument(
            "--campaign",
            type=str,
            required=True,
            help="Campaign slug to assign these codes to (e.g. caleb-book-sale)",
        )
        parser.add_argument(
            "--column",
            type=str,
            default=None,
            help='Header name of the code column (default: auto-detect — tries "code", "coupon", "coupon_code")',
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be imported without writing to the database",
        )

    def handle(self, *args, **options):
        path = options["csv_file"]
        campaign_slug = options["campaign"]
        dry_run = options["dry_run"]
        column_override = options["column"]

        try:
            campaign = Campaign.objects.get(slug=campaign_slug)
        except Campaign.DoesNotExist:
            raise CommandError(
                f"Campaign '{campaign_slug}' not found. "
                "Create it in the Django admin first, then re-run this command."
            )

        self.stdout.write(f"Importing into campaign: {campaign.name} ({campaign.slug})")

        if not os.path.exists(path):
            raise CommandError(f"File not found: {path}")

        codes = self._read_codes(path, column_override)

        if not codes:
            raise CommandError("No coupon codes found in the file. Check the format.")

        self.stdout.write(f"Found {len(codes)} code(s) in file.")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run — nothing will be saved.\n"))
            for code in codes:
                exists = Coupon.objects.filter(code=code).exists()
                status = "EXISTS" if exists else "NEW"
                self.stdout.write(f"  [{status}] {code}")
            return

        created, skipped = 0, 0
        for code in codes:
            _, was_created = Coupon.objects.get_or_create(
                code=code,
                defaults={"campaign": campaign},
            )
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {created} coupon(s) imported, {skipped} already existed."
            )
        )

        remaining = Coupon.objects.filter(is_used=False).count()
        self.stdout.write(f"Pool now has {remaining} unused coupon(s) available.")

    def _read_codes(self, path: str, column_override: str | None) -> list[str]:
        """
        Reads codes from CSV. Handles both header and no-header files.
        Returns a deduplicated list of non-empty stripped codes.
        """
        AUTO_DETECT_HEADERS = ["code", "coupon", "coupon_code", "discount_code"]

        with open(path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(1024)
            f.seek(0)

            has_header = csv.Sniffer().has_header(sample)
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return []

        codes = []

        if has_header:
            headers = [h.strip().lower() for h in rows[0]]

            # Determine which column to use
            if column_override:
                col_name = column_override.strip().lower()
                if col_name not in headers:
                    raise CommandError(
                        f"Column '{column_override}' not found. "
                        f"Available columns: {', '.join(rows[0])}"
                    )
                col_index = headers.index(col_name)
            else:
                col_index = None
                for candidate in AUTO_DETECT_HEADERS:
                    if candidate in headers:
                        col_index = headers.index(candidate)
                        self.stdout.write(f"Using column: '{rows[0][col_index].strip()}'")
                        break
                if col_index is None:
                    # Fall back to first column
                    col_index = 0
                    self.stdout.write(
                        self.style.WARNING(
                            f"No recognised header found ({', '.join(AUTO_DETECT_HEADERS)}). "
                            f"Using first column: '{rows[0][0].strip()}'"
                        )
                    )

            for row in rows[1:]:
                if row and len(row) > col_index:
                    code = row[col_index].strip()
                    if code:
                        codes.append(code)
        else:
            # No header — treat entire first column as codes
            for row in rows:
                if row:
                    code = row[0].strip()
                    if code:
                        codes.append(code)

        # Deduplicate while preserving order
        seen = set()
        unique = []
        for code in codes:
            if code not in seen:
                seen.add(code)
                unique.append(code)

        duplicates = len(codes) - len(unique)
        if duplicates:
            self.stdout.write(
                self.style.WARNING(f"Skipped {duplicates} duplicate(s) in the file.")
            )

        return unique
