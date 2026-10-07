# 🎓 Campus Marketplace

A production-ready, peer-to-peer campus commerce web application designed specifically for college students. Students can buy and sell textbooks, lab supplies, electronics, dorm furniture, and campus gear safely and locally with verified student accounts, Open Library ISBN auto-filling, campus pickup spot tags, saved wishlists, and instant HTMX inventory status toggles.

🌐 **Live Production URL Placeholder**: `https://campus-marketplace-demo.onrender.com`

---

## 🌟 Key Features

1. **Academic Textbook ISBN Auto-Fill**:
   - Integrated with the **Open Library Books API** (`https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data`).
   - Enter a 10- or 13-digit ISBN to instantly pull the book title, author(s), publication year, and cover image preview into the listing form.
2. **Object-Level Ownership Security**:
   - Strict security checks on all mutations (`edit`, `delete`, `toggle-sold`).
   - Unauthorized attempts by any non-owner trigger a strict `HTTP 403 Forbidden` (`PermissionDenied`).
3. **Email OTP Verification System (Gmail SMTP)**:
   - Registration creates inactive accounts (`is_active = False`) requiring verified student email access.
   - Generates cryptographically secure 6-digit numeric OTP codes (`100000`–`999999`) using Python's `secrets` module.
   - Dispatches branded HTML/plain-text emails via Gmail SMTP (`smtp.gmail.com:587` with TLS) with local console fallback.
   - 10-minute automatic expiration window and maximum 5 failed attempts limit.
   - 60-second rate-limited resend cooldown with interactive live countdown timer.
4. **Single-Click User Wishlist / Saved Listings (Bonus Feature)**:
   - One-click HTMX bookmarking on any card or detail page.
   - Dedicated "Wishlist" tab with saved item counts and direct access.
5. **Campus Pickup Location Tags (Bonus Feature)**:
   - Every listing specifies a designated campus meetup spot (e.g. *Student Union*, *Hostel 14*, *Central Library Gate*).
   - Searchable across feed queries.

5. **Dynamic Single-Click Status Management**:
   - Real-time HTMX status toggling between `AVAILABLE` and `SOLD` without full-page reloads.
6. **Rich Marketplace Discovery & Filters**:
   - Search across `title`, `description`, and `campus_pickup_location` (`icontains`).
   - Category filtering (`TEXTBOOKS`, `ELECTRONICS`, `LAB_SUPPLIES`, `FURNITURE`, `CLOTHING`, `HOUSING`, `OTHER`).
   - Status filtering (`Available`, `Sold`, or `All`).
   - Multi-mode sorting (Newest first, Price: Low to High, Price: High to Low).
7. **Visual Distinction for Sold Items**:
   - Grayscale image filters, contrast boost, bold "SOLD" badges, and disabled buyer contact triggers.
8. **Production-Ready Storage & Database Architecture**:
   - Supabase PostgreSQL database connected via `dj-database-url` and `psycopg` with persistent connection pooling.
   - Supabase Object Storage via S3 Protocol using `django-storages[s3]` and `boto3`, targeting the `'listing-images'` bucket with transparent local fallback.
   - WhiteNoise with `CompressedManifestStaticFilesStorage` for ultra-fast static file serving.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Django 6 LTS (Python 3.13) |
| **Frontend Templates** | Django Templates with HTML5 semantic markup |
| **Styling** | Tailwind CSS with custom branding & dark mode classes |
| **Dynamic Interactivity**| HTMX 1.9 + Vanilla JavaScript |
| **Persistent Database** | Supabase PostgreSQL (via `dj-database-url`, `psycopg2-binary`/`psycopg`) |
| **Media Storage** | Supabase Object Storage via S3 (`django-storages[s3]` + `boto3`) / Local Media |
| **Static File Serving** | WhiteNoise (`CompressedManifestStaticFilesStorage`) |
| **External API** | Open Library Books API (`https://openlibrary.org/api/books`) |
| **WSGI Server** | Gunicorn (configured in `Procfile`) |



---

## 📁 Project Directory Structure

```text
├── campus_marketplace/       # Project core configuration
│   ├── settings.py           # Hardened production settings
│   ├── urls.py               # Main URL router
│   ├── wsgi.py               # WSGI application entry
│   └── asgi.py               # ASGI application entry
├── accounts/                 # Custom Student User & Authentication
│   ├── models.py             # Custom User model (campus_name, phone)
│   ├── forms.py              # Student registration & login forms
│   ├── views.py              # Register, login, and logout controllers
│   ├── urls.py               # Authentication routes
│   ├── admin.py              # Admin registration for User
│   └── tests.py              # Authentication test suite
├── marketplace/              # Marketplace catalog & transactions
│   ├── models.py             # Listing, SavedListing, Category, ListingStatus
│   ├── forms.py              # ListingForm with ISBN helper & validators
│   ├── services.py           # Open Library ISBN lookup service
│   ├── views.py              # Discovery, CRUD, HTMX toggle, Wishlist
│   ├── urls.py               # Marketplace routes & /api/lookup-isbn/
│   ├── admin.py              # Admin configuration with custom actions
│   └── tests.py              # Unit & integration test suite (19 tests)
├── templates/                # Responsive HTML5 templates
│   ├── base.html             # Master layout with Tailwind & HTMX
│   ├── accounts/             # Login and register pages
│   └── marketplace/          # Feed, detail, wishlist, forms, and partials
├── static/                   # Static assets
├── media/                    # Local media uploads directory
├── Procfile                  # Gunicorn web server process configuration
├── requirements.txt          # Production dependencies
├── runtime.txt               # Python 3.13 runtime specification
├── .env.example              # Environment variables reference template
├── TECHNICAL_APPROACH.md     # In-depth architectural documentation
├── AI_DECLARATION.md         # Full AI tools & prompts disclosure
└── manage.py                 # Django command-line runner
```

---

## 🚀 Step-by-Step Local Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- `pip` package manager

### 2. Clone the Repository & Prepare Environment
```bash
git clone <repository_url>
cd campus_marketplace
```

Create and activate a virtual environment:
```bash
python -m venv venv

# On Linux / macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment file:
```bash
# On Linux / macOS:
cp .env.example .env

# On Windows:
copy .env.example .env
```
Ensure `.env` contains:
```ini
SECRET_KEY=local-dev-secret-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Seed Sample Campus Data
Populate the database with realistic campus listings, textbooks, and verified student accounts:
```bash
python manage.py seed_data
```

### 7. Launch Development Server
```bash
python manage.py runserver
```
Visit **`http://127.0.0.1:8000/`** in your browser.

---

## 🧪 Running the Test Suite

Execute the comprehensive automated test suite (including model validations, 403 Forbidden security assertions, Wishlist toggles, Open Library mocked lookups, and Indian phone validation):

```bash
python manage.py test
```

Result:
```text
Ran 16 tests in 19.121s — OK (All 16 tests passed)
```

---

## 🌐 Environment Variables Reference

| Variable | Description | Default / Example |
|---|---|---|
| `SECRET_KEY` | Django cryptographic signing key | Unique secret in production |
| `DEBUG` | Enables/disables debug mode | `True` (Dev) / `False` (Prod) |
| `ALLOWED_HOSTS` | Comma-separated list of allowed domains | `localhost,127.0.0.1` |
| `DATABASE_URL` | Supabase PostgreSQL connection URL | `postgresql://postgres:[PASS]@[HOST]:5432/postgres?sslmode=require` |
| `SUPABASE_S3_ACCESS_KEY` | Supabase Storage S3 Access Key | `your_supabase_s3_access_key` |
| `SUPABASE_S3_SECRET_KEY` | Supabase Storage S3 Secret Key | `your_supabase_s3_secret_key` |
| `SUPABASE_S3_BUCKET_NAME` | Supabase Storage S3 Bucket Name | `listing-images` |
| `SUPABASE_S3_ENDPOINT_URL` | Supabase Storage S3 Endpoint URL | `https://[PROJECT-REF].storage.supabase.co/v1/s3` |
| `SUPABASE_S3_REGION_NAME` | Supabase Storage S3 Region | `ap-southeast-2` |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF POST requests | `https://your-domain.com` |




---

## 📄 Additional Deliverables
- In-depth architectural blueprint: [`TECHNICAL_APPROACH.md`](file:///c:/Users/sridh/Desktop/gdg/TECHNICAL_APPROACH.md)
- Complete disclosure of AI tools & prompts: [`AI_DECLARATION.md`](file:///c:/Users/sridh/Desktop/gdg/AI_DECLARATION.md)
