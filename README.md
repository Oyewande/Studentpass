# StudentPass

A student discount verification platform for Nigerian universities. Authors and creators running campaigns on platforms like Selar, Gumroad, or Payhip can offer exclusive discount codes to verified students — without needing any integration with those platforms.

## How It Works

1. An author creates a campaign in the StudentPass admin, sets the allowed school domains, and imports their discount codes from their store.
2. Students visit the campaign link (e.g. `https://studentpass.ng/?c=covenant-book-sale`).
3. They enter their university email address. StudentPass validates the domain against the campaign's allowed schools.
4. A 6-digit OTP is sent to their school email via Brevo SMTP.
5. They verify the OTP. StudentPass issues one unique discount code from the campaign pool.
6. The student copies the code and is redirected to the product page to apply it at checkout.

Each student gets one code per campaign. Codes are valid for 24 hours. The same student can participate in multiple campaigns.

## Tech Stack

- **Backend:** Django 5.2 + Django REST Framework, PostgreSQL, Gunicorn
- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Email:** Brevo SMTP
- **Hosting:** Railway (backend) + Vercel (frontend)

## Project Structure

```
studentpass/
├── backend/          # Django API
│   ├── config/       # Settings, URLs, WSGI
│   ├── verification/ # Core app — models, views, serializers, throttles
│   └── manage.py
└── frontend/         # React app
    └── src/
        ├── components/   # EmailForm, OTPForm, Success
        ├── pages/        # VerifyPage
        └── services/     # API client
```

## Running Locally

**Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Campaign Setup

1. Go to `http://localhost:8000/admin/` → **Campaigns** → Add Campaign
2. Set the name, slug, allowed school domains, and product URL
3. Import discount codes: `python manage.py import_coupons codes.csv --campaign your-campaign-slug`
4. Share the campaign link: `https://your-domain.com/?c=your-campaign-slug`

## Environment Variables

See `backend/.env.example` for the full list of required backend variables.
