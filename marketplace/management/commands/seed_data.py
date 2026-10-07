from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from marketplace.models import Listing, Category, ListingStatus
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database with Indian campus student marketplace test data"

    def handle(self, *args, **options):
        # Create Indian student accounts with +91 10-digit mobile numbers
        u1, _ = User.objects.get_or_create(
            username="priya_sharma",
            defaults={
                "email": "priya@iitb.ac.in",
                "campus_name": "IIT Bombay (Hostel 15)",
                "phone_number": "+91 9820123456"
            }
        )
        u1.phone_number = "+91 9820123456"
        u1.campus_name = "IIT Bombay (Hostel 15)"
        u1.set_password("StudentPass123!")
        u1.save()

        u2, _ = User.objects.get_or_create(
            username="rohit_kumar",
            defaults={
                "email": "rohit@du.ac.in",
                "campus_name": "Delhi University (North Campus)",
                "phone_number": "+91 9811234567"
            }
        )
        u2.phone_number = "+91 9811234567"
        u2.campus_name = "Delhi University (North Campus)"
        u2.set_password("StudentPass123!")
        u2.save()

        u3, _ = User.objects.get_or_create(
            username="arjun_reddy",
            defaults={
                "email": "arjun@bits.ac.in",
                "campus_name": "BITS Pilani (Vyas Bhawan)",
                "phone_number": "+91 9701234568"
            }
        )
        u3.phone_number = "+91 9701234568"
        u3.campus_name = "BITS Pilani (Vyas Bhawan)"
        u3.set_password("StudentPass123!")
        u3.save()

        # Clean old listings if any to re-populate with Indian standards
        Listing.objects.all().delete()

        # Create sample listings in INR (₹)
        sample_items = [
            {
                "seller": u1,
                "title": "Higher Engineering Mathematics - B.S. Grewal (44th Ed)",
                "description": "Essential for 1st & 2nd year Engineering Math. Clean pages with zero pen marks. Meet at Central Library entrance.",
                "price": Decimal("450.00"),
                "category": Category.TEXTBOOKS,
                "status": ListingStatus.AVAILABLE,
            },
            {
                "seller": u2,
                "title": "Casio fx-991EX ClassWiz Scientific Calculator",
                "description": "Original Casio calculator with solar backup. Approved for university semester exams and GATE. Includes protective hard case.",
                "price": Decimal("850.00"),
                "category": Category.ELECTRONICS,
                "status": ListingStatus.AVAILABLE,
            },
            {
                "seller": u3,
                "title": "Engineered Wood Study Desk with Book Rack",
                "description": "Sturdy hostel desk with built-in shelf. Perfect for laptop and books. Must pickup from Vyas Bhawan ground floor.",
                "price": Decimal("1500.00"),
                "category": Category.FURNITURE,
                "status": ListingStatus.AVAILABLE,
            },
            {
                "seller": u1,
                "title": "Introduction to Algorithms (CLRS) 4th Edition",
                "description": "The quintessential computer science textbook. Clean margins, hardcover. Already sold to a junior.",
                "price": Decimal("800.00"),
                "category": Category.TEXTBOOKS,
                "status": ListingStatus.SOLD,
            },
            {
                "seller": u2,
                "title": "boAt Rockerz 450 Wireless Bluetooth Headphones",
                "description": "Matte black finish, 15 hours battery life, extra bass. Ideal for online lectures and library study sessions.",
                "price": Decimal("999.00"),
                "category": Category.ELECTRONICS,
                "status": ListingStatus.AVAILABLE,
            },
            {
                "seller": u3,
                "title": "Campus Winter Heavyweight Hoodie (Size L)",
                "description": "Dark navy fleece hoodie with kangaroo pocket. Very warm and comfortable.",
                "price": Decimal("499.00"),
                "category": Category.CLOTHING,
                "status": ListingStatus.AVAILABLE,
            },
            {
                "seller": u2,
                "title": "Single Room PG / Flat Sublet near North Campus Metro",
                "description": "Furnished single room with AC, RO water, high-speed Wi-Fi, and 3 meals included. Available for next semester.",
                "price": Decimal("7500.00"),
                "category": Category.HOUSING,
                "status": ListingStatus.AVAILABLE,
            },
        ]

        for item in sample_items:
            Listing.objects.create(**item)

        self.stdout.write(self.style.SUCCESS(
            "Successfully seeded database with Indian campus data (INR and +91 10-digit mobile numbers)!"
        ))
