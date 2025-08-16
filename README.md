# BizHub API

A RESTful API for small business operations, managing sales, inventory, payments, and notifications.

## Features
- User authentication with JWT (admin, staff, customer roles).
- Order and product management with inventory tracking.
- M-Pesa payment integration via Daraja API.
- SMS (Twilio) and email (SendGrid) notifications.
- Real-time order updates via Django Channels.
- Admin dashboards for analytics (sales, best-sellers, inventory, customers).
- Customer loyalty program (points for purchases).
- Product search and filtering by category, price, and stock availability.

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone <your-repo-url>
   cd bizhub_api
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` with:
     - `DJANGO_SECRET_KEY`: Generate a secure key.
     - `DEBUG`: Set to `True` for development, `False` for production.
     - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL credentials.
     - `MPESA_SHORTCODE`, `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_PASSKEY`, `MPESA_CALLBACK_URL`: M-Pesa Daraja credentials.
     - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`: Twilio credentials.
     - `SENDGRID_API_KEY`, `DEFAULT_FROM_EMAIL`: SendGrid credentials.
     - `REDIS_HOST`: Redis server (e.g., localhost or external service).

5. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```

8. **Access the API**:
   - Swagger documentation: `http://localhost:8000/swagger/`
   - Admin panel: `http://localhost:8000/admin/`

## Deployment on PythonAnywhere

1. **Create a PythonAnywhere Account**: Sign up at https://www.pythonanywhere.com.
2. **Clone the Repository**:
   - Go to the "Consoles" tab and open a Bash console.
   - Clone your repository:
     ```bash
     git clone <your-repo-url>
     cd bizhub_api
     ```

3. **Set Up Virtual Environment**:
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure PostgreSQL**:
   - Request a PostgreSQL database from PythonAnywhere support (free tier).
   - Update `.env` with the provided database credentials (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT).

5. **Set Up Environment Variables**:
   - Add environment variables in PythonAnywhere’s “Web” tab under “Environment Variables”:
     - `DJANGO_SECRET_KEY`, `MPESA_*`, `TWILIO_*`, `SENDGRID_*`.
     - `MPESA_CALLBACK_URL`: Set to `https://<your-username>.pythonanywhere.com/api/payments/mpesa/callback/`.
     - `REDIS_HOST`: Use an external Redis provider (e.g., Redis Labs free tier) as PythonAnywhere doesn’t provide Redis.

6. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Configure Web App**:
   - In the “Web” tab, create a new web app with Python 3.10.
   - Set the source code path to `/home/<your-username>/bizhub_api`.
   - Set the working directory to `/home/<your-username>/bizhub_api`.
   - Update the WSGI configuration file (`/var/www/<your-username>_pythonanywhere_com_wsgi.py`):
     ```python
     import os
     import sys
     path = '/home/<your-username>/bizhub_api'
     if path not in sys.path:
         sys.path.append(path)
     os.environ['DJANGO_SETTINGS_MODULE'] = 'bizhub.settings'
     from django.core.wsgi import get_wsgi_application
     from django.contrib.staticfiles.handlers import StaticFilesHandler
     application = StaticFilesHandler(get_wsgi_application())
     ```
   - Set static files:
     - URL: `/static/`, Path: `/home/<your-username>/bizhub_api/staticfiles`
   - Run `python manage.py collectstatic` in the console.

8. **Enable ASGI for Django Channels**:
   - PythonAnywhere doesn’t natively support ASGI, so use a separate worker process for Daphne:
     ```bash
     daphne -b 0.0.0.0 -p 8001 bizhub.asgi:application &
     ```
   - For WebSocket testing, use an external Redis provider and configure a reverse proxy (e.g., via ngrok or a custom domain).

9. **Reload the Web App**:
   - Click “Reload” in the PythonAnywhere “Web” tab.

10. **Test the Deployment**:
    - Access the API at `https://<your-username>.pythonanywhere.com/swagger/`.
    - Test endpoints with Postman.

## Testing
Run unit tests:
```bash
python manage.py test
```

## External APIs
- **M-Pesa Daraja**: Register at https://developer.safaricom.co.ke/ for sandbox credentials.
- **Twilio**: Sign up at https://www.twilio.com/ for SMS credentials.
- **SendGrid**: Sign up at https://sendgrid.com/ for email credentials.
- **Redis**: Use a free tier from Redis Labs (e.g., redis.io) for Channels.

## Notes
- Ensure environment variables are secure and not committed to Git.
- Test M-Pesa payments in the sandbox environment.
- WebSocket functionality requires an external Redis instance and may need ngrok for local testing.
- For production, secure `MPESA_CALLBACK_URL` with HTTPS.