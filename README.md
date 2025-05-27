# JKLG Travel Agency Website

A modern, feature-rich Flask-based website for a travel agency covering Jammu, Kashmir, Ladakh, and Gurez. This project is designed for real-world use by travel businesses, with a robust admin panel, modular code, and a beautiful, responsive UI.

## Features
- Destinations, places, and detailed tour packages
- Booking system with email confirmation and admin approval
- Gallery and testimonials (with admin moderation)
- Advanced admin panel (Flask-Admin) for all content
- User authentication and security best practices
- Responsive, modern Bootstrap UI
- Modular Flask blueprints for scalability
- SQLAlchemy ORM for database access
- Email notifications for bookings, testimonials, and support tickets
- Site settings and dynamic branding
- Support ticket/contact system
- Analytics dashboard for admins

## Technology Stack
- Python 3.8+
- Flask
- SQLAlchemy
- Flask-Admin
- Flask-Mail
- Flask-Login
- Flask-Babel (i18n)
- Bootstrap 5

## Getting Started
1. **Clone the repository**
   ```powershell
   git clone <your-repo-url>
   cd travel
   ```
2. **Create a virtual environment**
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```
4. **Initialize the database**
   ```powershell
   flask db upgrade
   python init_site_settings.py
   ```
5. **Run the app**
   ```powershell
   flask run
   ```
6. **Access the site**
   - User: http://127.0.0.1:5000/
   - Admin: http://127.0.0.1:5000/admin (default admin: admin/admin123)

## Project Structure
- `app.py` / `views.py` — Main Flask app, routes, admin logic
- `models.py` — SQLAlchemy models (Booking, Testimonial, SiteSettings, etc.)
- `templates/` — Jinja2 HTML templates (site, admin, emails)
- `static/` — CSS, JS, images, uploads
- `migrations/` — Alembic migration scripts
- `requirements.txt` — Python dependencies

## Booking & Email Flow
- Users submit bookings via the website.
- Users receive a confirmation email with a secure link.
- Clicking the link confirms the booking and shows a confirmation page.
- Admins can approve/reject bookings, testimonials, and support tickets from the admin panel.
- All status changes trigger automatic email notifications to users.

## Admin Panel
- Manage all content: places, packages, bookings, testimonials, gallery, users, site settings, email templates, and more.
- View analytics and logs.
- Import/export data (CSV, PDF).

## Customization
- Update site name, contact info, and branding in the admin Site Settings.
- Edit email templates in the admin or in `templates/emails/`.
- Add new destinations, packages, and gallery images via the admin panel.

## Security & Best Practices
- All admin routes require authentication.
- CSRF protection and rate limiting enabled.
- Passwords are securely hashed.
- Email sending is logged for audit.

## License
This project is for demonstration and educational purposes. For production use, review and update security, email, and deployment settings as needed.

---
For questions or support, contact the JKLG Travel team via the website contact form.
