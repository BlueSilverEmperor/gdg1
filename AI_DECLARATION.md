# 🤖 AI Tools & Prompts Declaration

**Project**: Campus Marketplace  
**Date**: October 2026  
**Developer / Agentic System**: Antigravity AI Engineer (Powered by Google DeepMind)  
**Operating Environment**: Windows / Python 3.13 / Django 6

---

## 1. AI Tools Utilized
During the design, implementation, and testing of the **Campus Marketplace** application, the following AI tools and foundational model architectures were utilized:

1. **Google DeepMind Antigravity Coding Agent**:
   - Primary agentic system responsible for architectural design, Django codebase generation, template authoring, test suite implementation, and production configuration.
2. **Gemini 3.8 Flash (Medium)**:
   - Reasoning model providing code synthesis, database schema optimization, security validation, and automated test generation.
3. **Automated IDE Tooling & Shell Integration**:
   - Automated file editing (`replace_file_content`, `write_to_file`), execution environment validation (`manage.py test`, `makemigrations`), and browser validation.

---

## 2. Prompts Used During Development

### Primary Prompt (Architecture & Cloud Service Mapping Loop)
```text
You are an expert full-stack Django engineer. Your goal is to build, test, and prepare a production-ready "Campus Marketplace" web application adhering to the specifications below.

### ARCHITECTURE & CLOUD SERVICE MAPPING
- Backend Framework: Django (LTS) with Django Templates, Tailwind CSS (via CDN), and HTMX.
- Persistent Database: Supabase PostgreSQL (connected via dj-database-url, psycopg2-binary, and transaction-pooling URI).
- Media Storage: Firebase Cloud Storage (Google Cloud Storage engine via django-storages[google] and google-auth).
- Static File Serving: WhiteNoise (with CompressedManifestStaticFilesStorage).
- External API: Open Library Books API (auto-fills textbook listings using ISBN).
- Security: Strict object-level ownership checks (HTTP 403 Forbidden for unauthorized mutative actions).
- Bonus Feature: Saved Listings / Wishlist and Campus Pickup Location tagging.

Execute this build systematically across 6 sequential iterations. Do not skip iterations or leave stub code. Implement each file completely.
```

### Secondary Prompt (Regional Localization & Standards)
```text
Convert all data to Indian standards: use INR (₹) currency, +91 and 10 digits for mobile number formatting and validation, and Indian university campus context.
```

### Tertiary Prompt (Supabase Credentials & Pooler Configuration)
```text
postgresql://postgres:[YOUR-PASSWORD]@db.xlcmrhqhvulypglyxtov.supabase.co:5432/postgres
Password: [Provided with URL-encoded '%' character (%25)]
```
*(Result: Configured `psycopg[binary]`, `dj-database-url`, and pooler URI in `.env` with SSL validation and migrated schema directly to Supabase PostgreSQL).*


---

## 3. Human Oversight & Code Integrity
- **Zero Placeholders**: All controllers, models, templates, and tests were fully implemented without any stub comments, placeholder blocks, or mock passes.
- **Verification**: All generated tests (19 tests) were executed against the Django test runner and passed with zero errors or warnings.
- **Security Vetting**: Ownership checks (`PermissionDenied` 403), CSRF headers for HTMX, and SQL injection protections through Django ORM were audited and verified.
