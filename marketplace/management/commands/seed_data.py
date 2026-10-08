from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from marketplace.models import Listing, Category, ListingStatus, CampusLocation, SavedListing
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database with ~100 realistic Indian campus student marketplace listings"

    def handle(self, *args, **options):
        self.stdout.write("Creating student user accounts...")

        # 12 Diverse Indian University Student Profiles
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
                "username": "aditya_sen",
                "email": "aditya.sen@iitkgp.ac.in",
                "campus_name": "IIT Kharagpur (Nehru Hall)",
                "phone_number": "+91 9830123562",
            },
            {
                "username": "pooja_deshmukh",
                "email": "pooja.d@coep.ac.in",
                "campus_name": "COEP Pune (Girls Hostel)",
                "phone_number": "+91 9850123783",
            },
            {
                "username": "rahul_verma",
                "email": "rahul.v@nitt.edu",
                "campus_name": "NIT Trichy (Amber Hostel)",
                "phone_number": "+91 9443123894",
            },
            {
                "username": "tanvi_joshi",
                "email": "tanvi.j@iiit.ac.in",
                "campus_name": "IIIT Hyderabad (Old Boys/Girls)",
                "phone_number": "+91 9849123015",
            },
            {
                "username": "dev_mukherjee",
                "email": "dev.m@vit.ac.in",
                "campus_name": "VIT Vellore (Block D)",
                "phone_number": "+91 9790123456",
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

        # Clear existing listings to re-seed clean dataset
        self.stdout.write("Refreshing marketplace listings...")
        Listing.objects.all().delete()

        # Database of 105 realistic student marketplace items
        raw_items = [
            # 1-25: TEXTBOOKS
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
                "Fundamentals of Database Systems - Elmasri & Navathe (7th Ed)",
                "Standard DBMS syllabus textbook. Includes SQL and relational algebra practice sets with solution appendix. Excellent condition.",
                "520.00", Category.TEXTBOOKS, CampusLocation.CENTRAL_LIBRARY, "Central Library Circulation Desk", False
            ),
            (
                "Computer Networking: A Top-Down Approach - Kurose & Ross",
                "Used for Computer Networks course. Clear explanations of TCP/IP stack, DNS, socket programming, and security protocols.",
                "550.00", Category.TEXTBOOKS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Main Gate", False
            ),
            (
                "Concepts of Physics (Vol 1 & 2 Bundle) - Dr. H.C. Verma",
                "Legendary physics books with solved conceptual questions. Perfect for engineering foundation and competitive exam revision.",
                "380.00", Category.TEXTBOOKS, CampusLocation.MAIN_GATE, "Main Security Checkpost", False
            ),
            (
                "Advanced Engineering Mathematics - Erwin Kreyszig (10th Ed)",
                "Covers ODEs, linear algebra, vector calculus, Fourier analysis, and complex variables. International student edition.",
                "600.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "Math Department Ground Floor", False
            ),
            (
                "Signals and Systems - Alan V. Oppenheim & Alan S. Willsky",
                "Required text for EE and ECE branches. Continuous-time and discrete-time signals, Fourier transforms, and Laplace domains.",
                "490.00", Category.TEXTBOOKS, CampusLocation.CENTRAL_LIBRARY, "Central Library Periodicals Section", False
            ),
            (
                "Electronic Devices and Circuit Theory - Boylestad & Nashelsky",
                "11th Edition. Ideal for Analog Electronics labs and theory exams. Crisp binding with CD included.",
                "420.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "ECE Hardware Lab 102", True
            ),
            (
                "Modern Physical Metallurgy - R.E. Smallman & A.H.W. Ngan",
                "Metallurgy & Materials Science core course book. Covers crystal structures, dislocations, phase diagrams, and heat treatment.",
                "390.00", Category.TEXTBOOKS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Common Room", False
            ),
            (
                "Indian Polity for Civil Services - M. Laxmikanth (7th Ed)",
                "Latest updated edition with recent constitutional amendments. Bought for UPSC prep club. Neat marginal notes in pencil.",
                "580.00", Category.TEXTBOOKS, CampusLocation.CENTRAL_LIBRARY, "Library Garden Benches", False
            ),
            (
                "Principles of Microeconomics - N. Gregory Mankiw (8th Ed)",
                "Standard introductory economics textbook for MBA, B.Com, and Engineering Economics electives. Crisp condition.",
                "460.00", Category.TEXTBOOKS, CampusLocation.STUDENT_UNION, "Student Union Atrium", False
            ),
            (
                "Organic Chemistry - Morrison & Boyd (7th Edition)",
                "Comprehensive reaction mechanisms and stereochemistry. Essential for Chemistry majors and chemical engineering.",
                "490.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "Chemistry Department Foyer", False
            ),
            (
                "Mechanical Engineering Design - Joseph Shigley (11th Metric Ed)",
                "Classic machine design manual. Covers stress analysis, fatigue strength, shafts, gears, bearings, and fasteners.",
                "650.00", Category.TEXTBOOKS, CampusLocation.MAIN_GATE, "Main Gate Bus Stop", False
            ),
            (
                "Principles of Compiler Design (Dragon Book) - Aho, Lam, Sethi, Ullman",
                "Compilers 2nd Edition. Lexical analysis, parsing techniques, intermediate code generation, and optimization algorithms.",
                "540.00", Category.TEXTBOOKS, CampusLocation.CENTRAL_LIBRARY, "Central Library 1st Floor Study Cubicles", False
            ),
            (
                "Data Communications and Networking - Behrouz A. Forouzan",
                "Fifth edition. Comprehensive diagrams explaining OSI model, Ethernet standards, and routing protocols. Brand new feel.",
                "510.00", Category.TEXTBOOKS, CampusLocation.NORTH_QUAD_DORMS, "North Quad Mess Entrance", False
            ),
            (
                "University Physics with Modern Physics - Young & Freedman (14th Ed)",
                "Massive hardcover volume. Covers mechanics, thermodynamics, waves, optics, and quantum physics with end-of-chapter problems.",
                "750.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "Physics Lecture Hall Complex", False
            ),
            (
                "Campbell Biology - Urry, Cain, Wasserman (12th Edition)",
                "Authoritative reference for Biotechnology, Life Sciences, and pre-med courses. Full-color plates, zero damages.",
                "890.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "Biotechnology Block Porch", True
            ),
            (
                "Structural Analysis - R.C. Hibbeler (9th SI Edition)",
                "Civil Engineering must-have. Trusses, cables, shear moment diagrams, influence lines, and deflection calculation methods.",
                "530.00", Category.TEXTBOOKS, CampusLocation.CENTRAL_LIBRARY, "Central Library Porch", False
            ),
            (
                "Design and Analysis of Algorithms - Sartaj Sahni",
                "Computer algorithms in C++/Java. Divide-and-conquer, dynamic programming, greedy algorithms, and NP-completeness.",
                "370.00", Category.TEXTBOOKS, CampusLocation.STUDENT_UNION, "SAC Amphitheatre", False
            ),
            (
                "Engineering Electromagnetics - William Hayt & John Buck",
                "8th Edition. Electrostatic fields, Maxwell's equations, plane waves, and transmission lines. Great for ECE 3rd semester.",
                "420.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "Electrical Machines Lab Foyer", False
            ),
            (
                "Microelectronic Circuits - Sedra & Smith (7th International Ed)",
                "MOSFETs, BJTs, operational amplifiers, and IC design. Bound with sturdy plastic protective jacket.",
                "590.00", Category.TEXTBOOKS, CampusLocation.CENTRAL_LIBRARY, "Library Coffee Stall", False
            ),
            (
                "A Modern Approach to Verbal & Non-Verbal Reasoning - R.S. Aggarwal",
                "Popular aptitude and campus placement preparation book. Covers coding-decoding, blood relations, and syllogisms.",
                "320.00", Category.TEXTBOOKS, CampusLocation.STUDENT_UNION, "Student Union 2nd Floor Lounge", False
            ),
            (
                "Quantitative Aptitude for Competitive Examinations - R.S. Aggarwal",
                "Indispensable guide for placement tests, CAT, and bank PO exams. All shortcuts and sample papers intact.",
                "350.00", Category.TEXTBOOKS, CampusLocation.MAIN_GATE, "Main Security Checkpost", True
            ),
            (
                "Control Systems Engineering - I.J. Nagrath & M. Gopal",
                "Root locus, Bode plots, state-space equations, and Nyquist stability criteria. Perfect for Electrical and Instrumentation exams.",
                "400.00", Category.TEXTBOOKS, CampusLocation.SCIENCE_BLOCK, "Instrumentation Wing Lobby", False
            ),

            # 26-47: ELECTRONICS
            (
                "Casio fx-991EX ClassWiz Scientific Calculator",
                "Original Casio calculator with high-res LCD and natural textbook display. Permitted in university semester exams and GATE.",
                "850.00", Category.ELECTRONICS, CampusLocation.CENTRAL_LIBRARY, "Central Library Security Desk", False
            ),
            (
                "Casio fx-991CW Advanced Non-Programmable Calculator",
                "Latest updated model with intuitive 4-gradation menu display and QR code function. 6 months old with protective slider case.",
                "950.00", Category.ELECTRONICS, CampusLocation.SCIENCE_BLOCK, "Science Block Main Stairs", False
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
                "950.00", Category.ELECTRONICS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Porch", False
            ),
            (
                "Dell 24-inch Full HD IPS Monitor (75Hz, HDMI & VGA)",
                "Crisp anti-glare display with ultra-thin bezels. Perfect secondary screen for coding and hostel room setup. Includes HDMI cable.",
                "5200.00", Category.ELECTRONICS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Room 218 Pickup", False
            ),
            (
                "Cosmic Byte CB-GK-16 Firefly Tenkeyless Mechanical Keyboard",
                "RGB backlighting with Outemu Blue tactile switches. Great clicky feedback for long programming sessions. Well cleaned.",
                "1250.00", Category.ELECTRONICS, CampusLocation.STUDENT_UNION, "Student Activity Center Lounge", True
            ),
            (
                "Logitech Pebble M350 Wireless Bluetooth Mouse (Silent Click)",
                "Ultra-slim and quiet click buttons for silent study in library reading rooms. Dual connectivity via Bluetooth and 2.4GHz USB dongle.",
                "750.00", Category.ELECTRONICS, CampusLocation.CENTRAL_LIBRARY, "Central Library Porch", False
            ),
            (
                "SanDisk 1TB Extreme Portable External SSD (USB 3.2 Gen 2)",
                "Read speeds up to 1050MB/s. Rugged water and dust-resistant casing. Used for backing up project datasets and virtual machines.",
                "4800.00", Category.ELECTRONICS, CampusLocation.SCIENCE_BLOCK, "Computer Center Reception", False
            ),
            (
                "Portronics 6-in-1 USB-C Hub (4K HDMI, 3x USB 3.0, PD 100W)",
                "Aluminum unibody adapter compatible with MacBook, Dell XPS, and ThinkPad. Plug and play for classroom presentation projectors.",
                "890.00", Category.ELECTRONICS, CampusLocation.STUDENT_UNION, "SAC Entrance", False
            ),
            (
                "Mi 20000mAh 18W Fast Charging Power Bank 3i",
                "Triple output ports with dual-way fast charging. Keeps phone and tablet charged during full-day campus classes.",
                "1100.00", Category.ELECTRONICS, CampusLocation.MAIN_GATE, "Main Gate Auto Stand", False
            ),
            (
                "Sony WH-CH520 Wireless Bluetooth Headphones (50-Hour Battery)",
                "Beige color. DSEE sound enhancement and multi-point Bluetooth pairing. Lightest headphones for extended study playlists.",
                "2400.00", Category.ELECTRONICS, CampusLocation.CENTRAL_LIBRARY, "Central Library Cyber Cafe", False
            ),
            (
                "TP-Link Archer C6 AC1200 Dual-Band Gigabit Wi-Fi Router",
                "4 external antennas with MU-MIMO technology. Ideal for sharing high-speed hostel LAN connection across multiple room devices.",
                "1350.00", Category.ELECTRONICS, CampusLocation.NORTH_QUAD_DORMS, "Hostel Corridor 3rd Floor", False
            ),
            (
                "One by Wacom Small Digital Pen Graphics Tablet (CTL-472)",
                "Pressure-sensitive battery-free stylus. Perfect for taking handwritten digital notes in OneNote and drawing circuit schematics.",
                "1600.00", Category.ELECTRONICS, CampusLocation.SCIENCE_BLOCK, "Design Lab Entrance", True
            ),
            (
                "Logitech C270 HD 720p Webcam with Noise-Reducing Mic",
                "Clear video and built-in microphone for virtual campus placement interviews, online viva exams, and hackathons.",
                "1050.00", Category.ELECTRONICS, CampusLocation.STUDENT_UNION, "Student Union Meeting Room", False
            ),
            (
                "Belkin 4-Socket Surge Protector Extension Board (2-Meter Cord)",
                "Heavy-duty spike buster with master switch. Essential for charging laptop, monitor, and phone safely in old hostel wall sockets.",
                "650.00", Category.ELECTRONICS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Warden Office Steps", False
            ),
            (
                "Noise ColorFit Pulse Grand Smartwatch (1.69-inch Display)",
                "Heart rate monitor, SpO2 sensor, IP68 water resistant, and 60 sports modes. Includes original magnetic charging cable.",
                "850.00", Category.ELECTRONICS, CampusLocation.SPORTS_COMPLEX, "Sports Complex Pavilion", False
            ),
            (
                "Anker PowerLine+ USB-C to USB-C Fast Charging Cable (6ft Braided)",
                "Durable double-braided nylon cable supporting 60W USB-PD charging and high-speed data transfer. No fraying.",
                "450.00", Category.ELECTRONICS, CampusLocation.CENTRAL_LIBRARY, "Library Lawn Entrance", False
            ),
            (
                "Amazon Echo Dot (4th Gen) Smart Speaker with Alexa",
                "Glacier white spherical design. Great for setting study timers, reminders, alarms, and playing study music in hostel rooms.",
                "1700.00", Category.ELECTRONICS, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Gate", False
            ),
            (
                "Seagate One Touch 2TB External Hard Drive (USB 3.0)",
                "Compact brushed metal enclosure. Pre-formatted for Windows and Mac with password protection. Stores course lecture archives.",
                "3600.00", Category.ELECTRONICS, CampusLocation.CENTRAL_LIBRARY, "Central Library Front Stairs", False
            ),
            (
                "Zebronics Zeb-Transformer Gaming Keyboard & Mouse Combo",
                "Braided cable, multi-color LED backlighting, integrated aluminum frame. Good tactile key travel.",
                "650.00", Category.ELECTRONICS, CampusLocation.STUDENT_UNION, "SAC Gaming Area", True
            ),
            (
                "Baseus 65W GaN3 Pro Desktop Fast Charger (2 USB-C + 2 USB-A)",
                "Compact Gallium Nitride wall charger that powers a laptop and smartphone simultaneously. Eliminates bulky OEM power bricks.",
                "1850.00", Category.ELECTRONICS, CampusLocation.SCIENCE_BLOCK, "Electrical Dept Gate", False
            ),

            # 48-63: LAB SUPPLIES & ENGINEERING EQUIPMENT
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
                "Engineering Drawing Instrument Box (Compass, Divider, Leads)",
                "Camlin high-precision technical drawing compass set with extension arm and ink attachments. Clean metal joints.",
                "220.00", Category.STATIONERY, CampusLocation.CENTRAL_LIBRARY, "Central Library Porch", False
            ),
            (
                "Borosil Borosilicate Chemistry Lab Glassware Assortment",
                "Includes 250ml conical flask, 500ml beaker, 100ml measuring cylinder, and 2 watch glasses. Heat-resistant borosilicate glass.",
                "400.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Chemical Engineering Workshop", False
            ),
            (
                "Soldering Iron Kit (60W Adjustable Temp with Stand & Solder Wire)",
                "Features ceramic heating core (200°C to 450°C), desoldering pump, tweezers, and lead-free solder wire spool.",
                "480.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Electronics Club Workshop", True
            ),
            (
                "Roller Scale & French Curves Set for Engineering Graphics",
                "30cm rolling ruler with built-in protractor and 3-piece acrylic French curves set. Essential for smooth curve plotting.",
                "120.00", Category.STATIONERY, CampusLocation.STUDENT_UNION, "SAC Stationery Counter", False
            ),
            (
                "Mitutoyo Style 150mm Stainless Steel Vernier Caliper (0.02mm Accuracy)",
                "Precision dual-scale metric and imperial vernier caliper with locking screw for Mechanical workshop measurements.",
                "390.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Mechanical Workshop Fitting Shop", False
            ),
            (
                "Pack of 3 Solderless Breadboards (830 Tie-Points Each) + 130 Jumpers",
                "High quality breadboards with power rails and multi-colored male-to-male and male-to-female flexible jumper cables.",
                "300.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Digital Electronics Lab", False
            ),
            (
                "Chemical Splash Protective Safety Goggles (Anti-Fog, Clear)",
                "Soft PVC frame with indirect ventilation and adjustable head strap. Meets OSHA lab safety requirements.",
                "140.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Safety Office Lobby", False
            ),
            (
                "A2 Size Technical Drafting Board with Stand Clamps",
                "Smooth pine wood drawing board (65cm x 47cm) with beveled working edge. Great for drafting practice in hostel rooms.",
                "480.00", Category.STATIONERY, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Ground Floor", False
            ),
            (
                "Digital Vernier Height Gauge & Micrometer Screw Gauge (0-25mm)",
                "Workshop practice tools with ratchet stop and carbide tipped measuring faces. Includes wooden storage case.",
                "520.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Metrology Lab 104", False
            ),
            (
                "Microscope Prepared Slides Box (50 Botanical & Zoology Specimens)",
                "Optically clear glass slides with cedarwood oil immersion covers. Covers mitosis, plant tissues, and bacterial cultures.",
                "420.00", Category.STATIONERY, CampusLocation.SCIENCE_BLOCK, "Bio Sciences Building Atrium", False
            ),
            (
                "Component Storage Organizer Box (30 Transparent Drawers)",
                "Plastic cabinet for sorting resistors, capacitors, ICs, and small screws on project desks. Clean and crack-free.",
                "380.00", Category.STATIONERY, CampusLocation.STUDENT_UNION, "SAC Makerspace", True
            ),
            (
                "Clinical Thermometer & Stethoscope Combo (Nurse/Med Student Grade)",
                "Dual-head acoustic stethoscope with soft silicone ear tips and digital waterproof thermometer. Ideal for MBBS clinical postings.",
                "650.00", Category.STATIONERY, CampusLocation.MAIN_GATE, "Health Center Reception", False
            ),

            # 64-77: FURNITURE & HOSTEL LIVING
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
                "Sleepwell 4-inch Single Bed Foam Mattress (6x3 ft)",
                "High density orthopedic foam mattress. Kept inside waterproof protective cover since day one. Must be picked up from hostel room.",
                "1400.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 14 Wing B", True
            ),
            (
                "Nilkamal Heavy Duty Plastic Armchair (Set of 2)",
                "Sturdy weather-proof brown plastic chairs. Great for extra hostel room seating during group study sessions.",
                "550.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel Mess Courtyard", False
            ),
            (
                "Clip-On LED Desk Lamp with 3 Color Modes & Touch Dimmer",
                "Flexible gooseneck clamp light with USB rechargeable battery. Clamp it to bed rail or desk for late-night exam prep.",
                "340.00", Category.DORM_LIVING, CampusLocation.CENTRAL_LIBRARY, "Central Library Gate", False
            ),
            (
                "Havells 400mm 3-Blade High-Speed Table Fan",
                "Powerful air delivery with smooth oscillation and copper motor. Saves you during hot summer semester exam months.",
                "1100.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Reception", False
            ),
            (
                "Collapsible Wardrobe Clothes Organizer with Dust Cover",
                "Steel pipe frame with non-woven fabric zipped cover and side shoe pockets. Disassembles easily into a compact box.",
                "680.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 11 Entrance", False
            ),
            (
                "Floor Standing Full-Length Mirror with Wooden Easel Stand",
                "Crisp distortion-free 150cm mirror. Great for getting ready for campus presentations and placement interviews.",
                "650.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Front Desk", False
            ),
            (
                "Heavy-Duty Metal 4-Tier Shoe Rack (Holds 12 Pairs)",
                "Rust-resistant black powder-coated steel tubes. Keeps room footwear organized outside hostel room doorway.",
                "320.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Staircase Landing", False
            ),
            (
                "Single Bed Cotton Mattress Topper & Bedcover Set",
                "Quilted microfiber mattress topper with 2 fitted cotton bedsheets and 2 matching pillowcases. Freshly laundered.",
                "450.00", Category.DORM_LIVING, CampusLocation.STUDENT_UNION, "SAC Laundry Dropoff", False
            ),
            (
                "Adjustable Height Laptop Riser / Stand (Aluminum Foldable)",
                "Ergonomic angled laptop stand with silicone grips and ventilation hollows to prevent laptop overheating during compiling.",
                "420.00", Category.DORM_LIVING, CampusLocation.CENTRAL_LIBRARY, "Central Library Atrium", False
            ),
            (
                "Cushioned Hostel Bean Bag (Size XXL - Black Leatherette)",
                "Comfortable filled bean bag for reading and relaxing in hostel rooms. Double stitched with child-safe safety zipper.",
                "850.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 14 Common Room", True
            ),
            (
                "Multi-Tier Rolling Utility Cart with Lockable Wheels",
                "Mesh metal baskets for storing textbooks, stationery, snacks, and toiletries next to study table.",
                "750.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Wing C", False
            ),

            # 78-87: CLOTHING & ACCESSORIES
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
                "Decathlon Quechua Windproof Water-Repellent Hiking Jacket (Size L)",
                "Breathable lightweight outdoor shell jacket with adjustable hood. Excellent for winter morning campus bicycle commutes.",
                "790.00", Category.FASHION, CampusLocation.SPORTS_COMPLEX, "Sports Complex Main Gate", False
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
                "Woodland Waterproof Leather Outdoor Boots (UK Size 8)",
                "Rugged nubuck leather with rubber lug soles. Great for college trips, monsoons, and rough terrain.",
                "1400.00", Category.FASHION, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Gate", False
            ),
            (
                "Traditional Embroidered Kurta Set for Cultural Fests (Size 38)",
                "Rich cotton silk fabric in maroon with subtle thread embroidery. Ideal for Diwali, ethnic day, and graduation celebrations.",
                "650.00", Category.FASHION, CampusLocation.STUDENT_UNION, "Cultural Club Room", False
            ),
            (
                "American Tourister 20-inch Cabin Trolley Luggage (Hardcase)",
                "4-wheel 360 degree spinner suitcase with TSA lock. Perfect for carrying semester luggage on domestic flights and trains.",
                "1850.00", Category.FASHION, CampusLocation.MAIN_GATE, "Main Security Gate", False
            ),
            (
                "Campus Sports Tracksuit (Jacket & Track Pants - Size M)",
                "Quick-dry moisture-wicking fabric with zippered pockets. Worn for inter-hostel football tournament practices.",
                "500.00", Category.FASHION, CampusLocation.SPORTS_COMPLEX, "Track & Field Bleachers", False
            ),

            # 88-95: HOUSING & SUBLETS
            (
                "Single Occupancy AC Room in 3BHK Flat near North Campus Metro Gate 2",
                "Fully furnished single bedroom with AC, wardrobe, study desk, 200Mbps Wi-Fi, washing machine, and maid service included. Sublet for spring semester.",
                "7500.00", Category.DORM_LIVING, CampusLocation.MAIN_GATE, "Metro Station Gate 2 Meetup", False
            ),
            (
                "Double Sharing Furnished PG Room with 3 Meals & Wi-Fi near South Campus",
                "Includes RO drinking water, power backup, daily housekeeping, and hot water geyser. Walking distance from university bus stop.",
                "5500.00", Category.DORM_LIVING, CampusLocation.STUDENT_UNION, "SAC Front Steps", False
            ),
            (
                "Summer Internship Sublet: Private Room in 2BHK Flat near Powai IIT Main Gate",
                "Available May to July for summer interns and research assistants. AC, modular kitchen, refrigerator, and gym access.",
                "8500.00", Category.DORM_LIVING, CampusLocation.MAIN_GATE, "IIT Powai Main Gate Checkpost", False
            ),
            (
                "Studio Apartment Sublet for Monsoon Semester (Fully Furnished, Power Backup)",
                "Private kitchenette, attached washroom, balcony with green campus view. Ideal for PhD scholars or final year project pairs.",
                "9500.00", Category.DORM_LIVING, CampusLocation.CENTRAL_LIBRARY, "Central Library Parking Area", True
            ),
            (
                "Shared 2BHK Flat Lease Transfer near Knowledge Park / Campus Outer Gate",
                "Spacious hall, 2 bathrooms, gated society with 24x7 security guards and grocery stores on campus boundary.",
                "6000.00", Category.DORM_LIVING, CampusLocation.MAIN_GATE, "Campus Outer Security Gate", False
            ),
            (
                "Furnished Master Bedroom Sublet in 3BHK with Attached Washroom & Balcony",
                "King bed, split AC, modular wardrobes, and high-speed fiber internet. Roommate is an easy-going 4th year student.",
                "8000.00", Category.DORM_LIVING, CampusLocation.NORTH_QUAD_DORMS, "Hostel Visitors Gate", False
            ),
            (
                "Single Bed in Air-Conditioned PG near Tech Park / College Campus",
                "Includes morning breakfast and dinner. Laundry facility available. Low deposit of 1 month only.",
                "4800.00", Category.DORM_LIVING, CampusLocation.MAIN_GATE, "Main Gate Visitors Desk", False
            ),
            (
                "Spacious 1RK Flat Sublet for Winter Semester near University Law Faculty",
                "Furnished with double bed, study table, refrigerator, and induction stove. Very quiet residential street.",
                "6200.00", Category.DORM_LIVING, CampusLocation.CENTRAL_LIBRARY, "Law Faculty Library Gate", False
            ),

            # 96-105: OTHER (SPORTS, INSTRUMENTS, APPLIANCES & HOSTEL GADGETS)
            (
                "Yonex Nanoray 7000I Badminton Racket with Full Cover & Shuttles",
                "Lightweight isometric graphite frame (77g) strung at 24 lbs. Includes 3 Mavis 350 nylon shuttlecocks. Used for hostel tournaments.",
                "1100.00", Category.OTHER, CampusLocation.SPORTS_COMPLEX, "Indoor Badminton Court 2", False
            ),
            (
                "Hero Sprint 21-Speed Mountain Bicycle with Lock & Helmet",
                "Dual disc brakes, front suspension fork, and Shimano gear shifters. Best way to commute between hostels and academic blocks.",
                "3600.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel 12 Bicycle Stand", False
            ),
            (
                "Yamaha F310 Acoustic Guitar with Padded Gig Bag & Capo",
                "Traditional Western body with spruce top and rosewood fretboard. Warm balanced tone, low action, newly strung with D'Addario strings.",
                "4500.00", Category.OTHER, CampusLocation.STUDENT_UNION, "Music Club Room", True
            ),
            (
                "Prestige PIC 20 1600W Induction Cooktop with Indian Menu Presets",
                "Automatic voltage regulator, anti-magnetic wall, and timer function. Ideal for cooking Maggi, chai, and quick meals in hostel rooms.",
                "1350.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel 15 Wing A Pantry", False
            ),
            (
                "Pigeon 1.5-Liter Stainless Steel Electric Kettle",
                "Auto shut-off protection and 360-degree swivel base. Quick boiling for hostel coffee, tea, and cup noodles during late-night studies.",
                "420.00", Category.OTHER, CampusLocation.NORTH_QUAD_DORMS, "Hostel 14 Corridor", False
            ),
            (
                "Nivia Storm Football (Size 5 FIFA Standard) with Hand Pump",
                "Rubber molded outer shell suitable for rough campus ground and turf matches. Holds air pressure perfectly.",
                "320.00", Category.OTHER, CampusLocation.SPORTS_COMPLEX, "Football Field Pavilions", False
            ),
            (
                "Kore 20kg Adjustable Home/Hostel Dumbbell & Barbell Gym Kit",
                "Includes 4x 2kg, 4x 3kg plates, 2 dumbbell rods, spinlock collars, gym gloves, and skipping rope for room workouts.",
                "1150.00", Category.OTHER, CampusLocation.SPORTS_COMPLEX, "Campus Gym Entrance", False
            ),
            (
                "Milton Thermosteel 1000ml Insulated Water Bottle (24hr Hot/Cold)",
                "Durable 304 food-grade stainless steel with leak-proof lid. Keeps cold water chilled through long afternoon lab sessions.",
                "450.00", Category.OTHER, CampusLocation.CENTRAL_LIBRARY, "Central Library Water Cooler Area", False
            ),
            (
                "International Tournament Wooden Chess Set with Weighted Pieces",
                "Solid sheesham wood folding board (14x14 inch) with carved Staunton pieces and green felt bottom. Great for hostel game nights.",
                "750.00", Category.OTHER, CampusLocation.STUDENT_UNION, "Chess Club Corner in SAC", False
            ),
            (
                "Hercules Roadeo Hardtail Bicycle with Front Disc Brakes",
                "Sturdy steel frame, 26-inch wheels with wide tires, and comfortable saddle. Moving out after final semester, priced to sell.",
                "2900.00", Category.OTHER, CampusLocation.MAIN_GATE, "Main Campus Bicycle Parking", False
            ),
        ]

        # Populate listings with random distribution among students
        created_listings = []
        for i, (title, desc, price, category, location, campus_loc_text, is_sold) in enumerate(raw_items):
            seller = created_users[i % len(created_users)]
            status = ListingStatus.SOLD if is_sold else ListingStatus.AVAILABLE
            listing = Listing.objects.create(
                seller=seller,
                title=title,
                description=desc,
                price=Decimal(price),
                category=category,
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
            # Randomly bookmark some listings by other students (exclude seller)
            other_users = [u for u in created_users if u != listing.seller]
            sample_favs = random.sample(other_users, k=random.choice([0, 1, 2, 3]))
            for user in sample_favs:
                SavedListing.objects.get_or_create(user=user, listing=listing)
                saved_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded database with {len(created_listings)} realistic campus listings, "
            f"{len(created_users)} verified student accounts, and {saved_count} wishlist bookmarks!"
        ))
