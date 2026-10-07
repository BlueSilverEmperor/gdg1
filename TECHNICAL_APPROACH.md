# 🏗️ Technical Approach & Architecture Document
**Project**: Campus Marketplace  
**Framework**: Django 6 (Python 3.13) + Tailwind CSS + HTMX  
**Database**: SQLite (Local Development) / PostgreSQL & Supabase Compatible (Production)

---

## 1. Executive Summary
Campus Marketplace is a modern, responsive, and secure peer-to-peer web platform designed specifically for college students. The platform solves the perennial problems of high textbook prices, expensive dorm gear, and awkward logistics by enabling verified students to trade directly on campus with built-in ISBN auto-population, campus pickup location tags, wishlists, and strict object-level security.

---

## 2. Database Schema & Data Models

### 2.1 Custom User Model (`accounts.User`)
Inherits from Django's `AbstractUser` to support student-centric profile information:
- `campus_name` (`CharField`): Institutional campus or college affiliation (e.g. *IIT Delhi*, *BITS Pilani*, *Delhi University*).
- `phone_number` (`CharField`): Standardized 10-digit Indian mobile number prefixed with `+91`, thoroughly sanitized and validated on form submission.
- Inherited fields: `username`, `email` (student email validation), `password` (hashed with PBKDF2), `is_active`, `is_staff`, `date_joined`.

### 2.2 Marketplace Listing Model (`marketplace.Listing`)
The primary transactional entity:
- `seller` (`ForeignKey` to `User`, `on_delete=models.CASCADE`, `related_name='listings'`): Direct foreign key ownership.
- `title` (`CharField(max_length=120)`): Validated for non-empty string and min length.
- `description` (`TextField`): Item details, condition, markings.
- `price` (`DecimalField(max_digits=8, decimal_places=2)`): Validated strictly `> 0` and `<= 999,999.99`.
- `category` (`CharField`): Enum choices:
  - `TEXTBOOKS`
  - `ELECTRONICS`
  - `LAB_SUPPLIES`
  - `FURNITURE`
  - `CLOTHING`
  - `HOUSING`
  - `OTHER`
- `status` (`CharField`): Enum choices (`AVAILABLE`, `SOLD`). Defaults to `AVAILABLE`.
- `campus_pickup_location` (`CharField(max_length=150)`): Designated safe meeting point on campus (e.g. *Central Library Gate*, *Student Union*, *Hostel 14 Common Room*). Indexed via search queries.
- `image` (`ImageField`): Stored locally in `media/listings/` or remotely via Cloudinary.
- `created_at` (`DateTimeField(auto_now_add=True)`) & `updated_at` (`DateTimeField(auto_now=True)`).
- **Database Indexes**: Indexed on `['status', '-created_at']` and `['category']` for query performance.

### 2.3 User Wishlist / Saved Listings Model (`marketplace.SavedListing`)
The wishlist junction table:
- `user` (`ForeignKey` to `User`, `on_delete=models.CASCADE`, `related_name='saved_items'`)
- `listing` (`ForeignKey` to `Listing`, `on_delete=models.CASCADE`, `related_name='favorited_by'`)
- `created_at` (`DateTimeField(auto_now_add=True)`)
- **Constraints**: Enforces `models.UniqueConstraint(fields=['user', 'listing'], name='unique_user_saved_listing')` preventing duplicate bookmarks at the database layer.

---

## 3. Backend Architecture & Controller Logic

### 3.1 Modular App Separation
- **`accounts/`**: Encapsulates user registration, student email regex validation, phone number normalization, login session management, and logout flows.
- **`marketplace/`**: Encapsulates listing feeds, detail views, owner CRUD operations, ISBN API integrations, HTMX status toggle, and wishlist bookmarks.
- **`campus_marketplace/`**: Houses central settings, WSGI/ASGI configurations, and top-level route distribution.

### 3.2 Dynamic Interactivity via HTMX
Instead of heavy Single-Page Application (SPA) state management or full-page browser refreshes, the app utilizes **HTMX 1.9**:
1. **Single-Click Status Toggle**:
   - Owner clicks `Mark as Sold` or `Re-list Available`.
   - Sends `POST /<pk>/toggle-sold/` with `HX-Request: true`.
   - Django updates `listing.status` and returns only `templates/marketplace/partials/status_toggle_btn.html`.
   - The DOM swaps the target container smoothly without reloading.
2. **Instant Wishlist Toggle**:
   - User clicks the heart icon on any listing card or detail view.
   - Sends `POST /<pk>/toggle-wishlist/` with `HX-Request: true`.
   - Django creates or deletes `SavedListing` and returns `templates/marketplace/partials/wishlist_btn.html` with animated state change.

### 3.3 Search & Discovery Pipeline
- Search operates concurrently across `title`, `description`, and `campus_pickup_location` using `Q(title__icontains=...) | Q(description__icontains=...) | Q(campus_pickup_location__icontains=...)`.
- Multiple filter combinators: `category`, `status` (`AVAILABLE` vs `SOLD` vs `ALL`), and sorting order (`newest`, `price_asc`, `price_desc`).
- Efficient database queries using `select_related('seller')` to prevent $N+1$ query overhead.

---

## 4. External API Integration (Open Library Books API)

### 4.1 Specification & Endpoint
- Endpoint: `https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data`
- Service implementation: `marketplace/services.py` (`fetch_book_by_isbn`)
- Dedicated API Proxy: `GET /api/lookup-isbn/?isbn={isbn}`

### 4.2 Data Pipeline
1. Sanitizes ISBN (strips spaces, dashes, normalizes length to 10 or 13 characters).
2. Issues an HTTP request via Python `requests` with custom User-Agent and an 8-second timeout.
3. Extracts metadata:
   - Book title
   - Author names (concatenated)
   - Large or medium cover image URL from Open Library Covers CDN
   - Publication year parsed from `publish_date`
   - Generated description draft
4. The client-side form (`templates/marketplace/listing_form.html`) intercepts the response, updates the form fields (`#id_title`, `#id_category = 'TEXTBOOKS'`, `#id_description`), displays a live preview, and automatically downloads the remote cover image into Django `ImageField` if no manual photo is uploaded.

---

## 5. Security & Authorization Architecture

### 5.1 Object-Level Ownership Enforcement
- Strict authorization checks in `listing_update`, `listing_delete`, and `listing_toggle_sold`:
  ```python
  if listing.seller != request.user:
      raise PermissionDenied("You do not have permission to modify this listing.")
  ```
- Any unauthorized attempts by User B to alter User A's listing immediately terminate with an `HTTP 403 Forbidden` response.

### 5.2 CSRF Protection & HTMX Integration
- Global `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'` attribute bound to the `<body>` element in [`templates/base.html`](file:///c:/Users/sridh/Desktop/gdg/templates/base.html).
- All asynchronous POST calls from HTMX automatically convey the CSRF token.

### 5.3 Input Sanitization & Server-Side Validation
- Student email validation ensures valid institutional format.
- Mobile numbers normalized to Indian standard `+91 XXXXXXXXXX`.
- Negative and zero pricing values are rejected at the form layer (`clean_price`).

### 5.4 Email OTP Verification Lifecycle (Gmail SMTP)
- **Account Inactivation**: Students register with `is_active = False`, preventing unauthorized login or activity until email ownership is proven.
- **Cryptographic Security**: 6-digit numeric OTP tokens (`100000`–`999999`) generated via Python's `secrets` module.
- **Delivery Engine**: Gmail SMTP (`smtp.gmail.com:587`, TLS enabled) dispatching responsive branded HTML & plain-text templates. Seamless fallback to `console.EmailBackend` in development.
- **Expiration & Throttling**:
  - 10-minute lifetime (`is_valid()` checks `timezone.now() - created_at <= 10m`).
  - Strict 5-attempt limit per OTP to prevent brute-force attacks.
  - 60-second rate-limited resend cooldown with real-time browser countdown timer.
- **Activation & Session Handshake**: Once verified, deletes OTP record, sets `user.is_active = True`, logs user in directly via `django.contrib.auth.login`, and issues a success alert.

---


## 6. Cloud Services & Production Architecture

### 6.1 Persistent Database: Supabase PostgreSQL
- **Connection Architecture**:
  - Integrated via `dj-database-url` and `psycopg` / `psycopg2-binary`.
  - Configured with `conn_max_age=600` and `sslmode=require` for secure, persistent connections.
  - Compatible with Supabase Transaction-Pooling and Session-Pooling URIs (`port 5432` / `port 6543`).
  - Strict URL encoding of special characters in database credentials (e.g. `%` encoded as `%25`).
  - Seamless fallback to `sqlite:///db.sqlite3` for offline development when `DATABASE_URL` is omitted.

### 6.2 Media Storage: Supabase Object Storage via S3 Protocol
- **Engine**: S3-compatible object storage via `django-storages[s3]` and `boto3`.
- **Target Bucket**: Dedicated `'listing-images'` bucket on Supabase Storage.
- **Configuration & Connection**:
  - Activated conditionally when `SUPABASE_S3_ACCESS_KEY` is present in the environment.
  - S3 endpoint: `https://[PROJECT-REF].storage.supabase.co/v1/s3`
  - Addressing style: `path` (`AWS_S3_ADDRESSING_STYLE = 'path'`)
  - Region: Configurable, defaults to `ap-southeast-2`
  - Public URLs & Direct CDN access: `AWS_QUERYSTRING_AUTH = False`, `AWS_DEFAULT_ACL = None`.
- **Clean Fallback**:
  - Transparent fallback to local filesystem storage (`MEDIA_ROOT` / `media/`) for offline development when `SUPABASE_S3_ACCESS_KEY` is omitted.



### 6.3 Static File Serving: WhiteNoise
- Integrated using `whitenoise.middleware.WhiteNoiseMiddleware` positioned immediately below `SecurityMiddleware`.
- Uses `whitenoise.storage.CompressedManifestStaticFilesStorage` in production (`DEBUG=False`) for gzip/Brotli pre-compression, unique hash-based cache busting, and direct WSGI serving without needing a separate Nginx or S3 bucket for assets.

### 6.4 External API: Open Library Books Integration
- Integrated via `marketplace/services.py` with custom User-Agent and timeout controls.
- Asynchronous form autofill via HTMX and JavaScript lookup endpoints (`/api/lookup-isbn/`).
- Seamless remote cover image ingestion directly into Django's storage layer.

### 6.5 Production Deployment Ready
- `Procfile` configured for Gunicorn: `web: gunicorn campus_marketplace.wsgi:application`.
- `build.sh` script automating pip dependency installation, `collectstatic --noinput`, and `python manage.py migrate`.
- Comprehensive automated test suite (19 tests) verifying all critical paths, ownership security, and validations.

