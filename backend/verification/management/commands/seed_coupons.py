"""
Usage:
  python manage.py seed_coupons --codes STU-10,STU-20,STU-30
  python manage.py seed_coupons --generate 20   # auto-generate N codes
"""
import random
import string
from django.core.management.base import BaseCommand
from verification.models import Coupon


def _random_code(prefix="STU", length=5):
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choices(chars, k=length))
    return f"{prefix}-{suffix}"


class Command(BaseCommand):
    help = "Seed coupon codes into the database"

    def add_arguments(self, parser):
        parser.add_argument("--codes", type=str, help="Comma-separated list of codes")
        parser.add_argument("--generate", type=int, help="Auto-generate N random codes")
        parser.add_argument("--prefix", type=str, default="STU", help="Prefix for generated codes")

    def handle(self, *args, **options):
        codes = []

        if options["codes"]:
            codes = [c.strip() for c in options["codes"].split(",") if c.strip()]
        elif options["generate"]:
            n = options["generate"]
            prefix = options["prefix"]
            codes = [_random_code(prefix) for _ in range(n)]
        else:
            self.stderr.write("Provide --codes or --generate. Run --help for usage.")
            return

        created, skipped = 0, 0
        for code in codes:
            _, was_created = Coupon.objects.get_or_create(code=code)
            if was_created:
                created += 1
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done: {created} coupon(s) added, {skipped} already existed."
            )
        )
