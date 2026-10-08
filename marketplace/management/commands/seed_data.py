import io
import os
import random
import urllib.request
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from marketplace.models import Listing, Category, ListingStatus, CampusLocation, SavedListing

User = get_user_model()

# Curated, verified high-resolution campus photos mapped per category
CATEGORY_PHOTO_URLS = {
    Category.TEXTBOOKS: [
        "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1568667256549-094345857637?w=700&auto=format&fit=crop&q=80",
    ],
    Category.ELECTRONICS: [
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=700&auto=format&fit=crop&q=80",
    ],
    Category.DORM_LIVING: [
        "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=700&auto=format&fit=crop&q=80",
    ],
    Category.STATIONERY: [
        "https://images.unsplash.com/photo-1586075010923-2dd4570fb338?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1596495578065-6e0763fa1178?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=700&auto=format&fit=crop&q=80",
    ],
    Category.FASHION: [
        "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=700&auto=format&fit=crop&q=80",
    ],
    Category.BICYCLES_COMMUTE: [
        "https://images.unsplash.com/photo-1485965120184-e220f721d03e?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1532298229144-0ec0c57515c7?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1558981403-c5f9899a28bc?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1507035895480-2b3156c31fc8?w=700&auto=format&fit=crop&q=80",
    ],
    Category.SPORTS_FITNESS: [
        "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1579952363873-27f3bade9f55?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1613918108466-292b78a8ef95?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=700&auto=format&fit=crop&q=80",
    ],
    Category.ENTERTAINMENT: [
        "https://images.unsplash.com/photo-1510915361894-db8b60106cb1?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1610890716171-6b1bb98ffd09?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=700&auto=format&fit=crop&q=80",
    ],
    Category.LOST_AND_FOUND: [
        "https://images.unsplash.com/photo-1544816155-12df9643f363?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1584820927498-cfe5211fd8bf?w=700&auto=format&fit=crop&q=80",
    ],
    Category.OTHER: [
        "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=700&auto=format&fit=crop&q=80",
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=700&auto=format&fit=crop&q=80",
    ],
}


class Command(BaseCommand):
    help = "Seeds database with ~100 realistic student marketplace listings complete with pictures, categories, and wishlist favorites."

    def handle(self, *args, **options):
        self.stdout.write("Creating student user accounts...")

        student_profiles = [
            {
                "username": "priya_sharma",
                "email": "priya.sharma@iitb.ac.in",
                "campus_name": "IIT Bombay (Hostel 15)",
                "phone_number": "+91 9820123456",
            },
            {
                "username": "rohit_kumar",
                "email": "rohit.k@du.ac.in",
                "campus_name": "Delhi University (North Campus)",
                "phone_number": "+91 9811234567",
            },
            {
                "username": "arjun_reddy",
                "email": "arjun.r@bits-pilani.ac.in",
                "campus_name": "BITS Pilani (Vyas Bhawan)",
                "phone_number": "+91 9701234568",
            },
            {
                "username": "ananya_iyer",
                "email": "ananya.iyer@iitm.ac.in",
                "campus_name": "IIT Madras (Sharavathi Hostel)",
                "phone_number": "+91 9840123789",
            },
            {
                "username": "sneha_patel",
                "email": "sneha.p@iitd.ac.in",
                "campus_name": "IIT Delhi (Kailash Hostel)",
                "phone_number": "+91 9979123890",
            },
            {
                "username": "vikram_singh",
                "email": "vikram.s@iitk.ac.in",
                "campus_name": "IIT Kanpur (Hall 4)",
                "phone_number": "+91 9839123450",
            },
            {
                "username": "kavya_nair",
                "email": "kavya.nair@iisc.ac.in",
                "campus_name": "IISc Bangalore (Main Campus)",
                "phone_number": "+91 9448123671",
            },
            {
                "username": "rahul_verma",
                "email": "rahul.v@nitk.edu.in",
                "campus_name": "NIT Surathkal (Hostel 7)",
                "phone_number": "+91 9886123902",
            },
            {
                "username": "divya_deshmukh",
                "email": "divya.d@vjti.ac.in",
                "campus_name": "VJTI Mumbai (Hostel A)",
                "phone_number": "+91 9769123401",
            },
            {
                "username": "tanmay_bhatia",
                "email": "tanmay.b@thapar.edu",
                "campus_name": "Thapar University (Hostel J)",
                "phone_number": "+91 9872123512",
            },
            {
                "username": "ishita_sen",
                "email": "ishita.sen@ju.ac.in",
                "campus_name": "Jadavpur University (Main Hostel)",
                "phone_number": "+91 9830123623",
            },
            {
                "username": "mohammed_faiz",
                "email": "m.faiz@amu.ac.in",
                "campus_name": "AMU Aligarh (Sir Syed Hall)",
                "phone_number": "+91 9412123734",
            },
        ]

        created_users = []
        for profile in student_profiles:
            u, created = User.objects.get_or_create(
                username=profile["username"],
                defaults={
                    "email": profile["email"],
                    "campus_name": profile["campus_name"],
                    "phone_number": profile["phone_number"],
                }
            )
            u.email = profile["email"]
            u.campus_name = profile["campus_name"]
            u.phone_number = profile["phone_number"]
            u.set_password("StudentPass123!")
            u.save()
            created_users.append(u)

        # Download & store curated photos in storage
        self.stdout.write("Ensuring category images are cached in storage...")
        stored_category_images = {}
        for category, urls in CATEGORY_PHOTO_URLS.items():
            stored_category_images[category] = []
            for idx, url in enumerate(urls):
                file_rel_path = f"listings/seed_{category.lower()}_{idx+1}.jpg"
                try:
                    if not default_storage.exists(file_rel_path):
                        self.stdout.write(f"  Fetching photo for {category} [{idx+1}/{len(urls)}]...")
                        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                        with urllib.request.urlopen(req, timeout=10) as resp:
                            img_data = resp.read()
                        saved_path = default_storage.save(file_rel_path, ContentFile(img_data))
                        stored_category_images[category].append(saved_path)
                    else:
                        stored_category_images[category].append(file_rel_path)
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  Could not download {url}: {e}"))
                    # Fallback path if already exists or empty
                    stored_category_images[category].append(file_rel_path)

        # Clear existing listings to re-seed clean dataset
        self.stdout.write("Refreshing marketplace listings...")
        Listing.objects.all().delete()

        # Database of 100 realistic student marketplace items (10 per category)
        raw_items = [
            # ==========================================
            # 1. TEXTBOOKS (10 items)
            # ==========================================
            (
                "Higher Engineering Mathematics - B.S. Grewal (44th Ed)",
                "Essential reference textbook for 1st & 2nd year Engineering Math. Clean pages with zero pen marks or tears. Meet at Central Library.",
                "450.00", Category.TEXTBOOKS, CampusLocation.CENTRAL_LIBRARY, "Central Library Ground Floor Reading Room", False
            ),
            (
                "Introduction to Algorithms (CLRS) 4th Edition",
                "The classic algorithms textbook. Hardcover in pristine condition. Highly recommended for Data Structures & Algorithms course.",
                "850.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "Computer Science Department Annex", True
            ),
            (
                "Operating System Concepts (Silberschatz & Galvin) - 10th Ed",
                "The Dinosaur OS book. Complete coverage of processes, threads, virtual memory, and distributed systems. Minor pencil highlights.",
                "480.00", Category.TEXTBOOKS, CampusLocation.STUDENT_UNION, "Student Union Food Court Entrance", False
            ),
            (
                "Database System Concepts - Korth, Sudarshan & Silberschatz 7th Ed",
                "Standard database management book for 5th semester DBMS lab. Includes relational algebra, SQL, indexing, and transaction processing.",
                "520.00", Category.TEXTBOOKS, CampusLocation.CENTRAL_LIBRARY, "Central Library Circulation Desk", False
            ),
            (
                "Digital Design With an Introduction to Verilog HDL - M. Morris Mano",
                "Required textbook for Digital Logic & Computer Organization course. Excellent condition with folded reference pinout charts.",
                "380.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "ECE Hardware Lab 102", True
            ),
            (
                "Thomas' Calculus (14th Edition in SI Units)",
                "Full calculus course text: multivariable calculus, vectors, line integrals, Stokes' Theorem. Binding intact with all page margins clean.",
                "600.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "Math Department Ground Floor", False
            ),
            (
                "Engineering Mechanics: Statics & Dynamics - Beer & Johnston (12th Ed)",
                "Mechanical and Civil engineering foundational mechanics textbook with step-by-step free-body diagrams and solved practice sets.",
                "550.00", Category.TEXTBOOKS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Main Gate", False
            ),
            (
                "Computer Networks: A Top-Down Approach - Kurose & Ross (8th Ed)",
                "Covers TCP/IP, DNS, socket programming, wireless networking, and network security. No missing pages, very neat condition.",
                "580.00", Category.TEXTBOOKS, CampusLocation.CENTRAL_LIBRARY, "Library Garden Benches", False
            ),
            (
                "Control Systems Engineering - I.J. Nagrath & M. Gopal",
                "Root locus, Bode plots, state-space equations, and Nyquist stability criteria. Perfect for Electrical and Instrumentation exams.",
                "400.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "Instrumentation Wing Lobby", False
            ),
            (
                "GATE Computer Science & IT Topic-wise Solved Papers (Made Easy)",
                "15 years topic-wise solved previous year question papers with detailed answer explanations. Perfect for final year GATE aspirants.",
                "490.00", Category.TEXTBOOKS, CampusLocation.STUDENT_UNION, "Student Union Atrium", False
            ),

            # ==========================================
            # 2. ELECTRONICS (10 items)
            # ==========================================
            (
                "Casio fx-991EX ClassWiz Scientific Calculator",
                "Original Casio calculator with high-res LCD and natural textbook display. Permitted in university semester exams and GATE.",
                "850.00", Category.ELECTRONICS, CampusLocation.CENTRAL_LIBRARY, "Central Library Security Desk", False
            ),
            (
                "boAt Rockerz 450 Wireless Bluetooth Headphones",
                "Matte black finish, 15 hours battery life, 40mm dynamic drivers. Ideal for library study sessions and video lectures.",
                "799.00", Category.ELECTRONICS, CampusLocation.STUDENT_UNION, "Student Union Cafeteria", False
            ),
            (
                "Raspberry Pi 4 Model B (4GB RAM) with Official Case & Heatsinks",
                "Includes 32GB Class 10 MicroSD card pre-installed with Raspberry Pi OS and 5V 3A USB-C power supply. Used for IoT semester project.",
                "3400.00", Category.ELECTRONICS, CampusLocation.SCIENCE_BLOCK, "Robotics Club Lab 304", False
            ),
            (
                "Arduino Uno Rev3 Starter Kit with 35+ Sensors & Jumper Wires",
                "Complete breadboard, ultrasonic sensor, LCD module, servo motor, LEDs, resistors, and USB cable. Used once for Mechatronics lab.",
                "950.00", Category.ELECTRONICS, CampusLocation.SCIENCE_BLOCK, "Makerspace Workbench 3", False
            ),
            (
                "SanDisk Ultra 128GB Dual Drive Go USB Type-C & Type-A",
                "High-speed USB 3.1 flash drive with dual swivel connectors for transferring project files between Android smartphone and laptop.",
                "650.00", Category.ELECTRONICS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Common Room", False
            ),
            (
                "Logitech B170 Wireless Mouse (Ambidextrous 2.4GHz)",
                "Reliable wireless optical mouse with 12-month battery life and mini USB nano receiver. Works smoothly on college dorm desks.",
                "380.00", Category.ELECTRONICS, CampusLocation.CENTRAL_LIBRARY, "Library Cyber Center Entrance", False
            ),
            (
                "Portronics 6-in-1 USB-C Hub with HDMI 4K & PD 100W",
                "Aluminum multi-port adapter with 4K HDMI, 3x USB 3.0 ports, SD card reader, and 100W Power Delivery pass-through.",
                "1100.00", Category.ELECTRONICS, CampusLocation.STUDENT_UNION, "Student Union Tech Zone", False
            ),
            (
                "Baseus 65W GaN3 Pro Desktop Fast Charger (2 USB-C + 2 USB-A)",
                "Compact Gallium Nitride wall charger that powers a laptop and smartphone simultaneously. Eliminates bulky OEM power bricks.",
                "1850.00", Category.ELECTRONICS, CampusLocation.SCIENCE_BLOCK, "Electrical Dept Gate", False
            ),
            (
                "Zebronics Zeb-Transformer Mechanical Feel Gaming Keyboard",
                "Braided cable, multi-color LED backlighting, integrated aluminum frame. Good tactile key travel.",
                "650.00", Category.ELECTRONICS, CampusLocation.STUDENT_UNION, "SAC Gaming Area", True
            ),
            (
                "Anker PowerCore 20000mAh Power Bank with Dual Output",
                "Ultra-high capacity portable charger with PowerIQ high-speed charging. Kept in backpack for long campus days and hackathons.",
                "1600.00", Category.ELECTRONICS, CampusLocation.MAIN_GATE, "Main Campus Bus Stop", False
            ),

            # ==========================================
            # 3. DORM_LIVING (10 items)
            # ==========================================
            (
                "Ergonomic Mesh Study Chair with Adjustable Lumbar Support",
                "Breathable mesh backrest, pneumatic height adjustment lever, and 360-degree swivel nylon caster wheels. Highly comfortable.",
                "1800.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Room 312 Pickup", False
            ),
            (
                "Foldable Bed Laptop Table with Cup Holder & iPad Groove",
                "Engineered wooden surface with non-slip curved metal legs. Perfect for studying on hostel beds or watching lectures.",
                "380.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Main Porch", False
            ),
            (
                "3-Tier Engineered Wood Bookshelf / Shoe Storage Rack",
                "Compact vertical shelf (90cm height) that fits neatly next to standard hostel cupboards. Clean teak finish.",
                "650.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "North Quad Quadrangle", False
            ),
            (
                "Havells 1200mm High-Speed Table Fan with 3-Speed Settings",
                "Aerodynamic PP blades, thermal overload protection, and smooth oscillation. A lifesaver during hot hostel summer months.",
                "1100.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Reception", False
            ),
            (
                "Pigeon 1.5-Liter Stainless Steel Electric Kettle",
                "Auto shut-off protection and 360-degree swivel base. Quick boiling for hostel coffee, tea, and cup noodles during late-night studies.",
                "420.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 14 Corridor", False
            ),
            (
                "Prestige 1200W Induction Cooktop with Indian Menu Presets",
                "Automatic voltage regulator, anti-magnetic wall, and timer function. Ideal for cooking Maggi, chai, and quick meals in hostel rooms.",
                "1350.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Wing A Pantry", False
            ),
            (
                "Wakefit Orthopedic Memory Foam Single Bed Mattress (72x36)",
                "High density foam with breathable removable zip cover. Fits standard hostel cot. Used for one semester, spotless and sanitized.",
                "2800.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 14 Wing B", True
            ),
            (
                "Heavy-Duty Canvas Laundry Hamper with Aluminum Handles",
                "Foldable 60L dirty clothes basket with water-resistant inner coating and padded handles. Great for weekly hostel laundry runs.",
                "320.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Staircase Landing", False
            ),
            (
                "Wipro 12W Smart LED Desk Lamp with 3 Color Temperatures",
                "Flexible gooseneck arm with touch sensor controls and warm/neutral/cool white light settings for eye-friendly midnight reading.",
                "680.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 11 Entrance", False
            ),
            (
                "Collapsible 4-Shelf Wardrobe Hanging Organizer",
                "Sturdy polyester fabric with reinforced fiberboards that hangs from any closet rod. Adds vertical storage for folded t-shirts.",
                "280.00", Category.DORM_LIVING, CampusLocation.STUDENT_UNION, "SAC Laundry Dropoff", False
            ),

            # ==========================================
            # 4. STATIONERY (10 items)
            # ==========================================
            (
                "Omega Deluxe Mini Drafter for Engineering Drawing",
                "Steel rods with unbreakable scale and clamp. Includes sturdy black canvas carrying bag. Mandatory for 1st-year graphics lab.",
                "380.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Drawing Hall 1 (Mechanical Dept)", False
            ),
            (
                "Set of 2 Standard White Cotton Lab Coats (Unisex Size M)",
                "100% thick white cotton with deep front pockets and durable buttons. Clean and freshly ironed. Approved for Chemistry and Bio labs.",
                "320.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Chemistry Lab 2 Entrance", False
            ),
            (
                "Medical Student Surgical Dissection Box Kit (14 Instruments)",
                "Stainless steel forceps, scalpel handles, disposable surgical blades, dissection scissors, and probe needles in a velvet zip case.",
                "450.00", Category.STATIONERY, CampusLocation.CENTRAL_LIBRARY, "Library Medical Section", False
            ),
            (
                "Mastech MAS830L Digital Multimeter with Backlight & Probes",
                "Measures DC/AC voltage, DC current, resistance, diode test, and transistor hFE. Essential for Electronics lab assignments.",
                "350.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "EE Hardware Workshop", False
            ),
            (
                "Rotary Cutter & A2 Self-Healing Cutting Mat for Architecture",
                "Professional 5-ply PVC double-sided cutting mat with grid lines and 45mm rotary cutter with spare blades for physical model making.",
                "480.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Architecture Studio 2", False
            ),
            (
                "Staedtler Mars 7-Piece Technical Drawing Compass Set",
                "Precision quick-setting compass with extension bar, universal adapter, and lead box. German engineered for engineering graphics.",
                "520.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Metrology Lab 104", False
            ),
            (
                "Classmate Pulse Spiral Binding Notebooks Pack of 6",
                "Pack of 6 unruled 300-page single subject notebooks with perforated paper and water-repellent poly covers. Brand new and sealed.",
                "340.00", Category.STATIONERY, CampusLocation.STUDENT_UNION, "SAC Stationery Counter", False
            ),
            (
                "Uni-ball Eye Rollerball Pens (Set of 5 - Blue & Black 0.5mm)",
                "Waterproof fade-proof Uni Super Ink with smooth stainless steel tip. Preferred pen for semester theory examination writing.",
                "260.00", Category.STATIONERY, CampusLocation.CENTRAL_LIBRARY, "Central Library Porch", False
            ),
            (
                "Clinical Thermometer & Stethoscope Combo (Nurse/Med Grade)",
                "Dual-head acoustic stethoscope with soft silicone ear tips and digital waterproof thermometer. Ideal for MBBS clinical postings.",
                "650.00", Category.STATIONERY, CampusLocation.MAIN_GATE, "Health Center Reception", False
            ),
            (
                "Koh-I-Noor Technical Drafting Pen Set 0.2 to 0.8mm",
                "Waterproof pigmented archival black ink technical drafting pens. Great for maps, architectural drawings, and detailed sketches.",
                "490.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Civil Engineering CAD Lab", True
            ),

            # ==========================================
            # 5. FASHION (10 items)
            # ==========================================
            (
                "Official College Techfest Heavyweight Fleece Hoodie (Unisex XL)",
                "Warm dark navy blue pullover hoodie with brushed fleece lining and kangaroo pocket. Only worn during winter fest.",
                "499.00", Category.FASHION, CampusLocation.STUDENT_UNION, "SAC Merch Counter", False
            ),
            (
                "Wildcraft 35L Water-Resistant College Laptop Backpack",
                "Triple compartments with padded 15.6-inch laptop sleeve, side bottle holders, and reinforced ergonomic shoulder straps.",
                "750.00", Category.FASHION, CampusLocation.STUDENT_UNION, "Student Union Main Entrance", False
            ),
            (
                "Men's Formal Slim-Fit Placement Blazer (Size 40 - Charcoal Grey)",
                "Single-breasted 2-button blazer tailored by Raymond. Worn twice for corporate campus placement interviews. Dry-cleaned.",
                "1500.00", Category.FASHION, CampusLocation.STUDENT_UNION, "Placement Cell Waiting Hall", False
            ),
            (
                "Women's Single-Breasted Navy Formal Interview Blazer (Size M)",
                "Crease-resistant formal jacket with notched lapel and structured shoulders. Ideal for placement drives and conference presentations.",
                "1400.00", Category.FASHION, CampusLocation.STUDENT_UNION, "SAC Placement Office", False
            ),
            (
                "Formal Silk Placement Tie & Silver Cufflinks Set",
                "Classic navy blue jacquard tie with stainless steel cufflinks and tie clip in hard gift box. Perfect for mock interviews.",
                "350.00", Category.FASHION, CampusLocation.CENTRAL_LIBRARY, "Library Main Porch", True
            ),
            (
                "Skybags 30L Dual-Compartment Campus Daypack with Rain Cover",
                "Durable polyester fabric with built-in rain cover tucked in bottom zip. Fits thick textbooks and lunchbox effortlessly.",
                "550.00", Category.FASHION, CampusLocation.MAIN_GATE, "Main Gate Metro Footbridge", False
            ),
            (
                "Traditional Embroidered Kurta Set for Cultural Fests (Size 38)",
                "Rich cotton silk fabric in maroon with subtle thread embroidery. Ideal for Diwali, ethnic day, and graduation celebrations.",
                "650.00", Category.FASHION, CampusLocation.STUDENT_UNION, "Cultural Club Room", False
            ),
            (
                "Campus Casual White Street Sneakers (UK 8 / EU 42)",
                "Classic low-top white sneakers with memory foam insole and vulcanized rubber sole. Worn casually around campus.",
                "790.00", Category.FASHION, CampusLocation.SPORTS_COMPLEX, "Sports Complex Main Gate", False
            ),
            (
                "Decathlon Quechua Windproof Water-Repellent Hiking Jacket (Size L)",
                "Breathable lightweight outdoor shell jacket with adjustable hood. Excellent for winter morning campus bicycle commutes.",
                "790.00", Category.FASHION, CampusLocation.SPORTS_COMPLEX, "Track & Field Bleachers", False
            ),
            (
                "American Tourister 20-inch Cabin Trolley Luggage (Hardcase)",
                "4-wheel 360 degree spinner suitcase with TSA lock. Perfect for carrying semester luggage on domestic flights and trains.",
                "1850.00", Category.FASHION, CampusLocation.MAIN_GATE, "Main Security Gate", False
            ),

            # ==========================================
            # 6. BICYCLES_COMMUTE (10 items)
            # ==========================================
            (
                "Hercules Roadeo Hardtail 26T Bicycle with Front Disc Brakes",
                "Sturdy steel frame, 26-inch wheels with wide tires, and comfortable saddle. Moving out after final semester, priced to sell.",
                "2900.00", Category.BICYCLES_COMMUTE, CampusLocation.MAIN_GATE, "Main Campus Bicycle Parking", False
            ),
            (
                "Hero Sprint Pro 21-Speed Hybrid Commuter Cycle (27.5T)",
                "Lightweight alloy frame, Shimano Tourney 21-speed gears, front suspension fork, and double-walled alloy rims. Smooth daily ride.",
                "3400.00", Category.BICYCLES_COMMUTE, CampusLocation.MAIN_GATE, "Hostel Cycle Stand Wing B", False
            ),
            (
                "Heavy Duty Hardened Steel U-Lock with 4-Digit Combination",
                "Thick 14mm cut-resistant shackle with dust cover. Zero risk of cycle theft from campus cycle stands. Reset code easily.",
                "450.00", Category.BICYCLES_COMMUTE, CampusLocation.CENTRAL_LIBRARY, "Central Library Bike Racks", False
            ),
            (
                "Oxford Coiled Bike Cable Lock with 2 Brass Keys",
                "1.8-meter flexible steel braided cable coated with protective vinyl. Long enough to lock both frame and front wheel to bike rail.",
                "280.00", Category.BICYCLES_COMMUTE, CampusLocation.SCIENCE_BLOCK, "Science Block Bicycle Shed", False
            ),
            (
                "Studds Urban Cycling Helmet with Adjustable Dial (Size M)",
                "Aerodynamic EPS foam shell with washable moisture-wicking pads and quick-release chin strap. Essential for campus main road riding.",
                "550.00", Category.BICYCLES_COMMUTE, CampusLocation.SPORTS_COMPLEX, "Gym Cycle Stand", False
            ),
            (
                "Rechargeable LED Bicycle Headlight & Taillight Set (USB-C)",
                "Super bright 400 lumens front light with 4 lighting modes and IPX4 waterproof silicone rear red strobe. USB-C rechargeable.",
                "380.00", Category.BICYCLES_COMMUTE, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Entrance", True
            ),
            (
                "Oxelo 28-inch Maple Wood Cruiser Skateboard with PU Wheels",
                "7-ply Canadian maple deck with 59mm 78A soft cruiser wheels and ABEC-7 bearings. Fast and fun way to get between hostel and lectures.",
                "1200.00", Category.BICYCLES_COMMUTE, CampusLocation.STUDENT_UNION, "SAC Open Plaza", False
            ),
            (
                "Detachable Wire Front Bicycle Basket with Quick-Release Mount",
                "Rust-proof black mesh basket with carry handle. Clicks off in one second to carry college bag or lunchbox into lecture halls.",
                "290.00", Category.BICYCLES_COMMUTE, CampusLocation.CENTRAL_LIBRARY, "Library East Porch", False
            ),
            (
                "Giyo High-Pressure Mini Bicycle Hand Pump with Gauge",
                "Compatible with both Presta and Schrader valves. Pumps up to 120 PSI with built-in pressure gauge. Mounts on bike water bottle cage.",
                "420.00", Category.BICYCLES_COMMUTE, CampusLocation.MAIN_GATE, "Campus Cycle Repair Kiosk", False
            ),
            (
                "Waterproof Bicycle Saddle Bag with Reflective Strip",
                "Compact under-seat wedge pouch with mesh compartments for keys, spare tube, multi-tool, and phone. Tear-resistant ripstop nylon.",
                "320.00", Category.BICYCLES_COMMUTE, CampusLocation.NORTH_QUAD_DORMS, "Hostel 14 Bike Shed", False
            ),

            # ==========================================
            # 7. SPORTS_FITNESS (10 items)
            # ==========================================
            (
                "Kore 20kg Adjustable Home/Hostel Dumbbell & Barbell Gym Kit",
                "Includes 4x 2kg, 4x 3kg plates, 2 dumbbell rods, spinlock collars, gym gloves, and skipping rope for room workouts.",
                "1150.00", Category.SPORTS_FITNESS, CampusLocation.SPORTS_COMPLEX, "Campus Gym Entrance", False
            ),
            (
                "SS Master 1000 Kashmir Willow Cricket Bat with Padded Cover",
                "Thick edges, curved blade, short cane handle with chevron rubber grip. Perfect for inter-department tape-ball and leather-ball matches.",
                "1250.00", Category.SPORTS_FITNESS, CampusLocation.SPORTS_COMPLEX, "Cricket Ground Pavilion", False
            ),
            (
                "Yonex Nanoray 18i Light Graphite Badminton Racket (77g)",
                "Isometric head shape with high-tension pre-strung BG65 string (24 lbs) and full racket cover. Ultra-light and speedy for court games.",
                "1400.00", Category.SPORTS_FITNESS, CampusLocation.SPORTS_COMPLEX, "Indoor Badminton Court 2", False
            ),
            (
                "Nivia Storm Football (Size 5 FIFA Standard) with Hand Pump",
                "Rubber molded outer shell suitable for rough campus ground and turf matches. Holds air pressure perfectly.",
                "320.00", Category.SPORTS_FITNESS, CampusLocation.SPORTS_COMPLEX, "Football Field Pavilions", False
            ),
            (
                "Nivia Heavy-Duty Basketball (Size 7 Rubber Composite)",
                "Deep channel design with durable pebbled grip for outdoor concrete campus basketball courts. Comes with needle and net.",
                "420.00", Category.SPORTS_FITNESS, CampusLocation.SPORTS_COMPLEX, "Basketball Court Bleachers", False
            ),
            (
                "Boldfit 6mm Non-Slip TPE Exercise & Yoga Mat with Carry Strap",
                "Dual-texture anti-skid surface with thick joint cushioning. Eco-friendly, sweat-resistant, and rolls up neatly for hostel storage.",
                "550.00", Category.SPORTS_FITNESS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Yoga Lawn", False
            ),
            (
                "Set of 5 Resistance Loop Bands with Door Anchor & Exercise Guide",
                "Latex resistance bands ranging from X-Light (5 lbs) to X-Heavy (30 lbs). Excellent for calisthenics, warmups, and hostel workouts.",
                "380.00", Category.SPORTS_FITNESS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Gym Room", True
            ),
            (
                "Cosco High-Bounce Tennis Balls (Pack of 3 Pressure Cans)",
                "Durable interlocked wool fiber cover suitable for campus tennis courts and hostel corridor cricket matches. Unopened fresh cans.",
                "280.00", Category.SPORTS_FITNESS, CampusLocation.SPORTS_COMPLEX, "Tennis Courts Gate", False
            ),
            (
                "Vector X Leather Gym Workout Gloves with Integrated Wrist Wraps",
                "Padded palm protection to prevent calluses during pull-ups and heavy bench presses. Breathable mesh back with velcro closure.",
                "260.00", Category.SPORTS_FITNESS, CampusLocation.SPORTS_COMPLEX, "Weightlifting Section", False
            ),
            (
                "Prolite 750ml Stainless Steel Protein Shaker Bottle with Wire Whisk",
                "BPA-free leakproof flip cap with surgical steel blender ball. Mixes whey protein, pre-workout, and electrolyte powders smoothly.",
                "320.00", Category.SPORTS_FITNESS, CampusLocation.STUDENT_UNION, "SAC Juice Bar", False
            ),

            # ==========================================
            # 8. ENTERTAINMENT (10 items)
            # ==========================================
            (
                "Yamaha F280 Acoustic Guitar with Padded Gig Bag & Capo",
                "Rosewood fretboard, natural gloss spruce top, warm resonant tone. New D'Addario strings fitted. Ideal for music club and hostel jams.",
                "4500.00", Category.ENTERTAINMENT, CampusLocation.STUDENT_UNION, "Music Club Room in SAC", False
            ),
            (
                "Juarez 21-inch Soprano Ukulele with Nylon Strings & Gig Bag",
                "Hawaiian solid linden wood body with geared tuning pegs. Easy to learn four-string instrument for relaxing between study sessions.",
                "1100.00", Category.ENTERTAINMENT, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Common Room", False
            ),
            (
                "Sony DualShock 4 Wireless Controller for PS4 & PC (Midnight Blue)",
                "Precision analog sticks, responsive triggers, and clickable touchpad. Connects via Bluetooth to gaming laptop or PlayStation console.",
                "1950.00", Category.ENTERTAINMENT, CampusLocation.STUDENT_UNION, "SAC Gaming Lounge", True
            ),
            (
                "International Tournament Wooden Chess Set with Weighted Pieces",
                "Solid sheesham wood folding board (14x14 inch) with carved Staunton pieces and green felt bottom. Great for hostel game nights.",
                "750.00", Category.ENTERTAINMENT, CampusLocation.STUDENT_UNION, "Chess Club Corner in SAC", False
            ),
            (
                "Catan Board Game (English 5th Edition Complete Box)",
                "The classic strategy trade-and-build board game. All 19 terrain hexes, dice, cards, and wooden settlements intact and organized.",
                "1600.00", Category.ENTERTAINMENT, CampusLocation.NORTH_QUAD_DORMS, "Hostel 14 Rec Room", False
            ),
            (
                "Scrabble Deluxe Edition with Rotating Turntable Grid",
                "Classic crossword word game with rotating board and raised tile lock grid. 100 letter tiles and wooden tile racks included.",
                "650.00", Category.ENTERTAINMENT, CampusLocation.CENTRAL_LIBRARY, "Library Discussion Room 3", False
            ),
            (
                "Monopoly Deal Card Game & UNO Flip Combo Pack",
                "Fast-paced 15-minute card versions of favorite family games. Perfect travel and hostel night entertainment. Cards in mint condition.",
                "240.00", Category.ENTERTAINMENT, CampusLocation.STUDENT_UNION, "SAC Cafeteria Benches", False
            ),
            (
                "Rubik's Connected 3x3 Smart Speed Cube (Bluetooth Tracker)",
                "Magnetic speed cube with motion sensors that syncs with free mobile app to teach algorithms, track solve speeds, and battle online.",
                "950.00", Category.ENTERTAINMENT, CampusLocation.SCIENCE_BLOCK, "CS Lounge", False
            ),
            (
                "Harry Potter 7-Book Complete Boxed Collection (Paperback)",
                "J.K. Rowling's full 7-volume series in decorative slipcase box. All books in clean readable condition with no torn spines.",
                "1250.00", Category.ENTERTAINMENT, CampusLocation.CENTRAL_LIBRARY, "Central Library Fiction Wing", False
            ),
            (
                "JBL Go 3 Portable Waterproof Bluetooth Speaker (Teal)",
                "Pro sound with punchy bass in an ultra-compact rugged fabric body. IP67 waterproof and dustproof with 5 hours continuous playback.",
                "1800.00", Category.ENTERTAINMENT, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Quadrangle", False
            ),

            # ==========================================
            # 9. LOST_AND_FOUND (10 items)
            # ==========================================
            (
                "[FOUND] Navy Blue Milton Thermosteel 1000ml Bottle at Library",
                "Found on 2nd floor study carrel desk #42 on Wednesday evening. Has a small NASA sticker on the side. Claim with librarian.",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.CENTRAL_LIBRARY, "Central Library Circulation Desk", False
            ),
            (
                "[LOST] Student ID Card with Blue College Lanyard & Hostel Key",
                "Lost near Student Union food court around 2 PM yesterday. Name on card is Priya Sharma, Roll #210103042. Reward for return!",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.STUDENT_UNION, "SAC Lost & Found Kiosk", False
            ),
            (
                "[FOUND] Casio Vintage Digital Watch (Silver Mesh Strap)",
                "Found in Science Block Lecture Hall 1 under row 4 seats after 11 AM Physics lecture. Clean working condition.",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.SCIENCE_BLOCK, "Physics Dept Office", False
            ),
            (
                "[FOUND] Black Automatic Folding Rain Umbrella in Room 204",
                "Sturdy windproof umbrella with wooden curved handle forgotten after rainy afternoon tutorial class. Deposited with room attender.",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.SCIENCE_BLOCK, "Lecture Hall 204 Podium", False
            ),
            (
                "[LOST] Ray-Ban Prescription Glasses in Black Hard Case",
                "Black rectangular metal frame spectacles left on library ground floor periodicals table. Greatly needed for upcoming exams.",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.CENTRAL_LIBRARY, "Library Reception Desk", False
            ),
            (
                "[FOUND] Set of 3 Keys with Royal Enfield Leather Keychain",
                "Found near Main Campus Gate cycle stand on concrete divider. Includes two bike keys and one small Godrej padlock key.",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.MAIN_GATE, "Main Security Checkpost", False
            ),
            (
                "[LOST] Blue Spiral Chemistry Lecture Notes Notebook",
                "Thick 200-page notebook with hand-drawn organic chemistry reaction mechanisms and lab diagrams. Left near Chemistry lab.",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.SCIENCE_BLOCK, "Chemistry Department Foyer", False
            ),
            (
                "[FOUND] boAt Airdopes Charging Case (Midnight Black) in Audi",
                "Found charging case on seat row F in the main auditorium after orientation session. Earbuds were missing inside.",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.STUDENT_UNION, "Auditorium Control Booth", False
            ),
            (
                "[FOUND] Scientific Calculator Casio fx-991CW left in LH-1",
                "Found on desktop in LH-1 following the morning Mathematics midterm test. Has initial 'A.K.' marked with silver marker on back.",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.SCIENCE_BLOCK, "Maths Department Notice Board", False
            ),
            (
                "[LOST] Red Titan Fastrack Leather Wallet near Main Gate",
                "Dropped between bus stop and campus entry gate. Contains college bus pass, metro smart card, and student photo ID.",
                "0.00", Category.LOST_AND_FOUND, CampusLocation.MAIN_GATE, "Main Gate Guard Room", False
            ),

            # ==========================================
            # 10. OTHER (10 items)
            # ==========================================
            (
                "Anchor 4-Socket Spike Guard Extension Board with 2m Cord",
                "Surge protected multi-plug extension strip with individual LED master switches. Essential for powering study setup in hostel.",
                "350.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Reception", False
            ),
            (
                "Milton Thermosteel 1000ml Insulated Water Bottle (24hr Hot/Cold)",
                "Durable 304 food-grade stainless steel with leak-proof lid. Keeps cold water chilled through long afternoon lab sessions.",
                "450.00", Category.OTHER, CampusLocation.CENTRAL_LIBRARY, "Central Library Water Cooler Area", False
            ),
            (
                "Wipro 3-in-1 Multi-Tool Rechargeable Emergency Study Lantern",
                "Bright emergency LED lantern with built-in USB power bank output and solar panel charging. Useful during power outages.",
                "420.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Gate", False
            ),
            (
                "Compact 2-Tier Stainless Steel Dish & Mug Drying Rack",
                "Rust-proof chrome finish wire rack with removable water drip tray. Organizes hostel plates, coffee mugs, and cutlery cleanly.",
                "380.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel Mess Courtyard", False
            ),
            (
                "Stanley 12-Piece Hand Tool & Screwdriver Repair Kit",
                "Includes magnetic bit screwdriver, precision jewelers screwdrivers, pliers, utility knife, and tape measure in durable blow mold case.",
                "550.00", Category.OTHER, CampusLocation.SCIENCE_BLOCK, "Makerspace Tool Wall", False
            ),
            (
                "Mosquito Bat Killer Racket with USB Charging Dock",
                "3-layer safety protective electric mesh net with built-in purple UV light attractant and rechargeable battery. Very effective in dorm.",
                "280.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel 14 Entrance", False
            ),
            (
                "Portable Compact Garment Steamer for Clothes (800W)",
                "Quick 30-second heat-up handheld steamer with 200ml water tank. Removes wrinkles from placement shirts and kurtas effortlessly.",
                "850.00", Category.OTHER, CampusLocation.STUDENT_UNION, "Placement Cell Foyer", False
            ),
            (
                "Multipurpose Storage Crates & Plastic Organizers (Set of 3)",
                "Heavy-duty stackable translucent plastic storage containers with clip-on lock lids. Great for organizing cables, notes, and snacks.",
                "320.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Wing C", False
            ),
            (
                "Water Filter Pitcher (3.5L) with 2 Activated Carbon Filters",
                "Reduces chlorine, odor, and heavy metals from campus tap water. Fits into mini fridge or dorm table. Clean and hygienic.",
                "750.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel 11 Wing A", False
            ),
            (
                "Heavy Duty Metal Clothes Drying Stand (Foldable Wing Style)",
                "Powder-coated steel drying rack with 45 feet of hanging line space. Folds flat to store behind hostel room door when not in use.",
                "890.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Roof Balcony", True
            ),
        ]

        # Populate listings with images and random distribution among students
        created_listings = []
        for i, (title, desc, price, category, location, campus_loc_text, is_sold) in enumerate(raw_items):
            seller = created_users[i % len(created_users)]
            status = ListingStatus.SOLD if is_sold else ListingStatus.AVAILABLE

            # Assign category-matched photo
            photo_choices = stored_category_images.get(category, [])
            assigned_photo = photo_choices[i % len(photo_choices)] if photo_choices else None

            listing = Listing.objects.create(
                seller=seller,
                title=title,
                description=desc,
                price=Decimal(price),
                category=category,
                image=assigned_photo,
                pickup_location=location,
                campus_pickup_location=campus_loc_text,
                status=status,
            )
            created_listings.append(listing)

        self.stdout.write(f"Created {len(created_listings)} listings across {len(Category.choices)} categories!")

        # Create realistic user bookmarks (Wishlist / Saved listings)
        self.stdout.write("Populating realistic Wishlist favorites...")
        saved_count = 0
        for listing in created_listings:
            other_users = [u for u in created_users if u != listing.seller]
            sample_favs = random.sample(other_users, k=random.choice([0, 1, 2, 3]))
            for user in sample_favs:
                SavedListing.objects.get_or_create(user=user, listing=listing)
                saved_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded database with {len(created_listings)} realistic campus listings with pictures, "
            f"{len(created_users)} verified student accounts, and {saved_count} wishlist bookmarks!"
        ))
