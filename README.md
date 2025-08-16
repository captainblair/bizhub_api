# BizHub API

A RESTful API for small business operations, managing sales, inventory, payments, and notifications using MySQL.

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

4. **Set Up MySQL Database**:
   - Install MySQL locally or use PythonAnywhere’s MySQL.
   - Create a database named `bizhub`:
     ```sql
     CREATE DATABASE bizhub;
     ```

5. **Set Up Environment Variables**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` with:
     - `DJANGO_SECRET_KEY`: Generate a secure key (e.g., `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`).
     - `DEBUG`: Set to `True` for development, `False` for production.
     - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: MySQL credentials.
     - `MPESA_SHORTCODE`, `MPESA_CONSUMER_KEY`, `MPESA_CONSUMER_SECRET`, `MPESA_PASSKEY`, `MPESA_CALLBACK_URL`: M-Pesa Daraja credentials (from https://developer.safaricom.co.ke/).
     - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`: Twilio credentials (from https://www.twilio.com/).
     - `SENDGRID_API_KEY`, `DEFAULT_FROM_EMAIL`: SendGrid credentials (from https://sendgrid.com/).
     - `REDIS_HOST`: Redis server (e.g., redis://<host>:6379 from Redis Labs free tier).
     - `SAFARICOM_API`: Set to `https://sandbox.safaricom.co.ke` for testing.

6. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a Superuser**:
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the Development Server**:
   ```bash
   python manage.py runserver
   ```

9. **Access the API**:
   - Swagger documentation: `http://localhost:8000/swagger/`
   - Admin panel: `http://localhost:8000/admin/`

## Deployment on PythonAnywhere

1. **Create a PythonAnywhere Account**: Sign up at https://www.pythonanywhere.com.
2. **Clone the Repository**:
   - Open a Bash console in the “Consoles” tab.
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

4. **Configure MySQL**:
   - In the “Databases” tab, create a MySQL database.
   - Note the database name, username, password, and host (e.g., `<your-username>.mysql.pythonanywhere-services.com`).
   - Update `.env` with these credentials.

5. **Set Up Environment Variables**:
   - In the “Web” tab, under “Environment Variables”, add:
     - `DJANGO_SECRET_KEY`, `MPESA_*`, `TWILIO_*`, `SENDGRID_*`.
     - `MPESA_CALLBACK_URL`: Set to `https://<your-username>.pythonanywhere.com/api/payments/mpesa/callback/`.
     - `REDIS_HOST`: Use a free Redis instance (e.g., Redis Labs).
     - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: MySQL credentials from PythonAnywhere.
     - `SAFARICOM_API`: `https://sandbox.safaricom.co.ke`.

6. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Collect Static Files**:
   ```bash
   python manage.py collectstatic
   ```

8. **Configure Web App**:
   - In the “Web” tab, create a new web app with Python 3.10.
   - Set:
     - Source code: `/home/<your-username>/bizhub_api`
     - Working directory: `/home/<your-username>/bizhub_api`
     - Static files: URL `/static/`, Path `/home/<your-username>/bizhub_api/staticfiles`
   - Update the WSGI file (`/var/www/<your-username>_pythonanywhere_com_wsgi.py`):
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

9. **Enable ASGI for Django Channels**:
   - PythonAnywhere doesn’t natively support ASGI, so run Daphne as a separate process:
     ```bash
     daphne -b 0.0.0.0 -p 8001 bizhub.asgi:application &
     ```
   - For WebSocket testing, use an external Redis provider and consider ngrok for local testing or a custom domain for production.

10. **Reload the Web App**:
    - Click “Reload” in the “Web” tab.

11. **Test the Deployment**:
    - Access the API at `https://<your-username>.pythonanywhere.com/swagger/`.
    - Test endpoints with Postman.
    - Run tests: `python manage.py test`.

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