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
│   ├── settings.py           # Hardened production settings (Render, Whitenoise, S3)
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
│   └── tests.py              # Unit & integration test suite (16+ tests)
├── templates/                # Responsive HTML5 templates
│   ├── base.html             # Master layout with Tailwind & HTMX
│   ├── accounts/             # Login, register, and OTP verification pages
│   └── marketplace/          # Feed, detail, wishlist, forms, and partials
├── static/                   # Static assets (CSS, JS, branding)
├── media/                    # Local media uploads directory (fallback)
├── build.sh                  # Render deployment build script (collectstatic + migrate)
├── render.yaml               # Render Infrastructure-as-Code Blueprint configuration
├── Procfile                  # Gunicorn web server process configuration
├── requirements.txt          # Production dependencies
├── .python-version           # Render runtime version specification (Python 3.12.8)
├── runtime.txt               # Fallback runtime specification
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

## ☁️ Production Deployment on Render

This project is pre-configured for automated continuous deployment on [Render](https://render.com).

### Option A: Standard Web Service Setup (Recommended)

1. **Push your code to GitHub**:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
   git push -u origin main
   ```
2. **Create New Web Service**:
   - Go to [dashboard.render.com](https://dashboard.render.com/) and click **New + > Web Service**.
   - Connect your GitHub repository.
3. **Configure Service Settings**:
   - **Name**: `campus-marketplace`
   - **Language**: `Python 3`
   - **Region**: Closest to your database (e.g. *Singapore* or *Frankfurt*)
   - **Branch**: `main`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn campus_marketplace.wsgi:application --log-file -`
   - **Instance Type**: `Free`
4. **Configure Environment Variables**:
   Add the following variables in the **Environment** tab:
   - `PYTHON_VERSION`: `3.12.8`
   - `DEBUG`: `False`
   - `SECRET_KEY`: *(Generate or use a strong random string)*
   - `DATABASE_URL`: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres?sslmode=require` (From Supabase)
   - `SUPABASE_S3_ACCESS_KEY`: *(From Supabase Storage settings)*
   - `SUPABASE_S3_SECRET_KEY`: *(From Supabase Storage settings)*
   - `SUPABASE_S3_BUCKET_NAME`: `listing_images`
   - `SUPABASE_S3_ENDPOINT_URL`: `https://[PROJECT-REF].supabase.co/storage/v1/s3`
   - `SUPABASE_S3_REGION_NAME`: `ap-southeast-2`
   - `EMAIL_HOST_USER`: *(Optional: Gmail address for live student OTP verification)*
   - `EMAIL_HOST_PASSWORD`: *(Optional: 16-character Google App Password)*
5. **Deploy**:
   - Click **Deploy Web Service**.
   - Render automatically executes `build.sh` (`pip install`, `collectstatic`, `migrate`) and starts Gunicorn.
   - Your live app is available at `https://<service-name>.onrender.com`.

### Option B: Render Blueprint (`render.yaml`)
Alternatively, deploy using Infrastructure-as-Code:
1. In the Render Dashboard, select **New + > Blueprint**.
2. Connect this repository; Render will automatically detect [`render.yaml`](file:///c:/Users/sridh/Desktop/gdg/render.yaml) and configure the build command, start command, and environment variable requirements.

---

## 🌐 Environment Variables Reference

| Variable | Required | Description | Example / Default |
|---|:---:|---|---|
| `SECRET_KEY` | Yes | Django cryptographic signing key | Unique 50+ character random secret |
| `DEBUG` | Yes | Toggles development debug output & toolbar | `False` (Prod) / `True` (Dev) |
| `ALLOWED_HOSTS` | No | Comma-separated domains allowed to serve requests | `.onrender.com,localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | No | Origins trusted for CSRF form validation | `https://*.onrender.com` |
| `DATABASE_URL` | Yes (Prod) | PostgreSQL connection URI (Supabase) | `postgresql://postgres:pass@host:5432/postgres?sslmode=require` |
| `SUPABASE_S3_ACCESS_KEY` | Optional | Supabase Object Storage S3 Access Key | `211a84...` |
| `SUPABASE_S3_SECRET_KEY` | Optional | Supabase Object Storage S3 Secret Key | `eb0aa2...` |
| `SUPABASE_S3_BUCKET_NAME` | Optional | Supabase S3 storage bucket name | `listing_images` |
| `SUPABASE_S3_ENDPOINT_URL` | Optional | Supabase S3 API endpoint URL | `https://[REF].supabase.co/storage/v1/s3` |
| `SUPABASE_S3_REGION_NAME` | Optional | Supabase storage region identifier | `ap-southeast-2` |
| `EMAIL_HOST_USER` | Optional | Gmail address for OTP email dispatch | `your-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Optional | 16-character Google App Password | `abcd efgh ijkl mnop` |
| `EMAIL_HOST` | Optional | SMTP host for email delivery | `smtp.gmail.com` |
| `EMAIL_PORT` | Optional | SMTP port | `587` |
| `EMAIL_USE_TLS` | Optional | TLS encryption toggle | `True` |

---

## 📄 Additional Deliverables
- In-depth architectural blueprint: [`TECHNICAL_APPROACH.md`](file:///c:/Users/sridh/Desktop/gdg/TECHNICAL_APPROACH.md)
- Complete disclosure of AI tools & prompts: [`AI_DECLARATION.md`](file:///c:/Users/sridh/Desktop/gdg/AI_DECLARATION.md)
- Render Blueprint Configuration: [`render.yaml`](file:///c:/Users/sridh/Desktop/gdg/render.yaml)

