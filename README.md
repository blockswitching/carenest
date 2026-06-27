# CareNest - Home Healthcare Platform

![CI](https://github.com/careforyou/carenest-backend/actions/workflows/ci.yml/badge.svg)

A comprehensive home healthcare platform built for India, enabling patients to connect with caregivers, nurses, and healthcare professionals for in-home medical services.

**Company:** CareForYou

## Tech Stack

- **Backend:** Django 5.2 LTS + Django REST Framework
- **Database:** PostgreSQL 15
- **Authentication:** JWT (djangorestframework-simplejwt)
- **API Docs:** drf-spectacular (Swagger/ReDoc)
- **Async Tasks:** Celery + Redis
- **Payments:** Razorpay Python SDK
- **Push Notifications:** Firebase Cloud Messaging (FCM)
- **Storage:** AWS S3 (optional) via django-storages
- **Monitoring:** Sentry
- **Deployment:** Docker + Nginx + Gunicorn
- **CI:** GitHub Actions

## Quick Start (Docker)

```bash
cp .env.example .env
# Edit .env with your credentials
docker-compose up --build
```

Services will be available at:
- API: http://localhost/api/v1/
- Admin: http://localhost/admin/
- Swagger: http://localhost/api/docs/

## Local Development Setup

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Redis 7+

### Setup

```bash
# Clone and enter project
git clone <repository-url>
cd carenest

# Virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Database
createdb carenest_db
python manage.py migrate

# Seed data
python manage.py seed_services
python manage.py seed_admin

# Run server
python manage.py runserver
```

### Celery (separate terminals)

```bash
celery -A config worker -l info
celery -A config beat -l info
```

## Project Structure

```
carenest/
├── apps/
│   ├── users/           # Auth, profiles, caregivers
│   ├── services/        # Service catalog
│   ├── bookings/        # Booking lifecycle, tracking, family dashboard
│   ├── health_records/  # Vitals, medications, reports
│   ├── payments/        # Razorpay integration, subscriptions
│   └── notifications/   # Push, in-app, emergency alerts
├── config/
│   └── settings/        # base, development, production
├── core/                # Base models, middleware, permissions
├── templates/admin/     # Custom admin dashboard
├── nginx.conf
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## API Documentation

| URL | Description |
|-----|-------------|
| `/api/docs/` | Swagger UI (interactive, JWT Authorize button) |
| `/api/redoc/` | ReDoc |
| `/api/schema/?format=json` | OpenAPI JSON (import to Postman) |
| `/api/health/` | Health check: `{"status": "ok", "version": "1.0.0"}` |

## API Response Format

All responses use a consistent envelope:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "message": ""
}
```

**Error:**
```json
{
  "success": false,
  "errors": {"field": ["error message"]},
  "message": "Validation failed."
}
```

## Endpoints Summary

### Authentication
| Method | Path | Access |
|--------|------|--------|
| POST | `/api/v1/auth/register/` | Anonymous |
| POST | `/api/v1/auth/login/` | Anonymous |
| POST | `/api/v1/auth/token/refresh/` | Anonymous |
| POST | `/api/v1/auth/logout/` | Authenticated |

### Users & Caregivers
| Method | Path | Access |
|--------|------|--------|
| GET/PUT | `/api/v1/users/me/` | Authenticated |
| GET | `/api/v1/caregivers/` | Authenticated |
| GET | `/api/v1/caregivers/{id}/` | Authenticated |
| POST | `/api/v1/caregivers/{id}/upload-document/` | Caregiver (own) |

### Services
| Method | Path | Access |
|--------|------|--------|
| GET | `/api/v1/services/` | Authenticated |
| GET | `/api/v1/services/categories/` | Authenticated |

### Bookings
| Method | Path | Access |
|--------|------|--------|
| POST | `/api/v1/bookings/` | Patient |
| GET | `/api/v1/bookings/` | Role-filtered |
| GET | `/api/v1/bookings/{id}/` | Owner/Assigned/Admin |
| PATCH | `/api/v1/bookings/{id}/cancel/` | Patient |
| POST | `/api/v1/bookings/{id}/assign-caregiver/` | Admin |
| PATCH | `/api/v1/bookings/{id}/update-status/` | Caregiver |
| PATCH | `/api/v1/bookings/{id}/update-location/` | Caregiver |
| GET | `/api/v1/bookings/{id}/tracking/` | Authenticated |
| GET | `/api/v1/family/dashboard/` | Patient/Caregiver/Admin |

### Health Records
| Method | Path | Access |
|--------|------|--------|
| GET/POST | `/api/v1/health/records/` | Patient/Caregiver |
| GET | `/api/v1/health/records/{patient_id}/history/` | Admin/Caregiver/Self |
| GET/POST | `/api/v1/health/medications/` | Patient/Admin |
| GET/POST | `/api/v1/health/reports/` | Patient/Caregiver |

### Payments
| Method | Path | Access |
|--------|------|--------|
| POST | `/api/v1/payments/create-order/` | Authenticated |
| POST | `/api/v1/payments/verify/` | Authenticated |
| GET | `/api/v1/payments/history/` | Patient/Admin |
| POST | `/api/v1/subscriptions/create/` | Authenticated |
| GET | `/api/v1/subscriptions/me/` | Authenticated |

### Notifications
| Method | Path | Access |
|--------|------|--------|
| GET | `/api/v1/notifications/` | Authenticated |
| PATCH | `/api/v1/notifications/{id}/read/` | Authenticated |
| POST | `/api/v1/notifications/register-device/` | Authenticated |
| POST | `/api/v1/notifications/emergency/` | Patient |

## Permissions Matrix

| Role | Access |
|------|--------|
| **Anonymous** | Register, Login only |
| **Patient** | Own bookings, health records, payments, notifications, emergency alerts, family dashboard |
| **Caregiver** | Assigned bookings, update status/location, record vitals, upload documents |
| **Admin** | Everything + Django admin panel + assign caregivers + verify documents |

## Management Commands

| Command | Description |
|---------|-------------|
| `python manage.py seed_services` | Seed 6 categories + ~19 healthcare services |
| `python manage.py seed_admin` | Create superuser from env vars |

## Mobile App Integration

- All list endpoints support: `?page=`, `?page_size=` (max 50), `?search=`, `?ordering=`
- Image URLs are always absolute (full domain)
- Datetimes are ISO 8601, timezone-aware (Asia/Kolkata)
- Deep link scheme: `carenest://booking/{id}`
- Live tracking via `PATCH /update-location/` + `GET /tracking/`
- FCM push via `POST /notifications/register-device/`

## Django Admin

Access at `/admin/` — features:
- Dashboard with real-time stats
- CSV export for bookings and payments
- Auto-assign caregiver (matches by city)
- Caregiver document verification workflow
- Bulk actions: mark completed, send test notification

## License

Proprietary - CareForYou
