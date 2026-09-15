# CityFix

CityFix is an AI-assisted civic issue reporting platform. Citizens submit photos and locations, receive structured issue analysis and priority scoring, track report progress, and explore public city issues. Authorities manage the response queue and status history.

## Problem
Cities receive many civic complaints, but identifying, prioritizing, and tracking them can be slow and difficult.

## Solution
CityFix uses AI to transform photos of civic problems into structured, prioritized reports with location and tracking. It includes an offline Demo Mode so the full workflow works without an external AI key.

## Key Features

- AI civic issue detection
- Confidence and severity assessment
- Priority scoring and explanation
- Browser geolocation and manual map selection
- Interactive Leaflet/OpenStreetMap maps
- Citizen reporting and secure authentication
- Citizen dashboard and owned report details
- Report tracking and status timeline
- Authority dashboard, search, filters, and status notes
- Public Explore Issues map and safe public report details
- Demo Mode fallback
- Optional Gemini Vision integration

## Technology Stack

- Python 3.10+
- FastAPI and Uvicorn
- SQLAlchemy 2 with SQLite
- Pydantic v2 and pydantic-settings
- JWT authentication with Passlib/bcrypt
- HTML5, Tailwind CSS CDN, and Lucide icons
- Leaflet.js and OpenStreetMap
- Pillow for image validation
- Google Generative AI SDK for optional Gemini Vision

## How to Run

From the project root:

```powershell
pip install -r requirements.txt
python run.py
```

Open `http://127.0.0.1:8000`.

Useful URLs:

- `/` landing page
- `/report` citizen report workflow
- `/dashboard` citizen dashboard
- `/explore` public issue map
- `/authority` authority dashboard
- `/admin` authority report management
- `/docs` API documentation

## Environment Variables

Create a `.env` file in the project root when needed. Do not commit it.

```env
GEMINI_API_KEY=your_key_here
```

Without `GEMINI_API_KEY`, CityFix uses the clearly labeled Demo Mode analyzer. The key is read only by the backend and is never sent to frontend JavaScript.

## Demo Accounts

The default launcher seeds these accounts when the database is empty:

| Role | Email | Password |
|---|---|---|
| Citizen | `citizen@cityfix.org` | `password123` |
| Authority | `officer@cityfix.org` | `admin123` |

## Hackathon Demo

1. Open CityFix and choose **Report an Issue**.
2. Upload a pothole image and optionally enter `pothole` as the clue.
3. Run analysis and confirm confidence, severity, priority, explanation, and Demo Mode.
4. Choose a location with the map or enter coordinates manually.
5. Review and submit the report.
6. Open the citizen dashboard and report details to show the generated `CITYFIX-000001`-style ID and Submitted timeline entry.
7. Sign in as the authority and open `/authority` or `/admin`.
8. Find the report, add a note, and move it through Under Review, Assigned, In Progress, and Resolved.
9. Open `/explore` while logged out and show the public marker, filters, and public timeline.

## Database and Storage

SQLite is created in the project root. Startup applies additive schema updates and backfills initial status-history entries for existing reports. Reports are linked to their submitting user through `reported_by_id`. Validated images are stored under `uploads/` with generated filenames.

## Future Improvements

- Automatic authority assignment
- Duplicate issue detection
- Citizen notifications
- Predictive civic issue hotspots
- Multilingual reporting
- Operational analytics
- Integration with municipal systems

## Security Notes

Public report endpoints expose only safe civic fields. Citizens can only access their own private report details. Authority pages and status updates require an authority/admin role. Passwords are hashed, JWTs are used for API calls, and an HttpOnly session cookie supports protected page navigation.
