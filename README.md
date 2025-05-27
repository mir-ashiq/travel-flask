# JKLG Travel Agency Website

A modern, feature-rich Flask-based website for a travel agency covering Jammu, Kashmir, Ladakh, and Gurez. This project is designed for real-world use by travel businesses, with a robust admin panel, modular code, and a beautiful, responsive UI.

---

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
- Import/export data (CSV, PDF)
- Multi-language support (Flask-Babel)

---

## Technology Stack
- Python 3.8+
- Flask
- SQLAlchemy
- Flask-Admin
- Flask-Mail
- Flask-Login
- Flask-Babel (i18n)
- Bootstrap 5

---

## Getting Started

### 1. Clone the repository
```powershell
git clone <your-repo-url>
cd travel
```

### 2. Create a virtual environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install dependencies
```powershell
pip install -r requirements.txt
```

### 4. Initialize the database
```powershell
flask db upgrade
python init_site_settings.py
```

### 5. Run the app
```powershell
flask run
```

### 6. Access the site
- User: http://127.0.0.1:5000/
- Admin: http://127.0.0.1:5000/admin (default admin: admin/admin123)

---

## Project Structure
- `app.py` / `views.py` — Main Flask app, routes, admin logic
- `models.py` — SQLAlchemy models (Booking, Testimonial, SiteSettings, etc.)
- `templates/` — Jinja2 HTML templates (site, admin, emails)
- `static/` — CSS, JS, images, uploads
- `migrations/` — Alembic migration scripts
- `requirements.txt` — Python dependencies

---

## How to Use

### User Side
- **Browse Destinations & Packages:** Users can explore all destinations, packages, and gallery images.
- **Book a Tour:** Fill out the booking form. You will receive a confirmation email with a secure link.
- **Confirm Booking:** Click the link in your email to confirm your booking. You will see a confirmation page.
- **Submit Testimonials:** Share your experience. Testimonials are published after admin approval.
- **Contact Support:** Use the contact form for support tickets. You will receive updates via email.

### Admin Side
- **Login:** Go to `/admin` and log in with your admin credentials.
- **Dashboard:** View analytics, recent bookings, and quick stats.
- **Manage Content:**
  - **Places & Packages:** Add/edit/delete destinations and tour packages.
  - **Bookings:** View, confirm, or reject bookings. Status changes trigger email notifications.
  - **Testimonials:** Approve or reject testimonials before they appear on the site.
  - **Gallery:** Upload and manage images.
  - **Users:** Manage user accounts and permissions.
  - **Site Settings:** Update site name, contact info, branding, and social links.
  - **Email Templates:** Edit email content for all notifications.
  - **Support Tickets:** Respond to user queries and update ticket status.
  - **Import/Export:** Download bookings/packages as CSV or PDF. Import users/packages from CSV.
- **Logs:** View email logs and activity logs for auditing.

---

## Booking & Email Flow
1. **User submits a booking** via the website.
2. **User receives a confirmation email** with a secure link (`/booking/confirm?verify=...`).
3. **User clicks the link** to confirm the booking. The booking status is updated and a confirmation page is shown.
4. **Admin reviews bookings** in the admin panel and can approve/reject as needed.
5. **All status changes** (bookings, testimonials, tickets) trigger automatic email notifications to users.
6. **All emails** use dynamic site branding and are logged in the EmailLog table.

---

## Customization
- **Site Branding:** Update site name, logo, contact info, and social links in the admin Site Settings.
- **Email Templates:** Edit email content in the admin panel or directly in `templates/emails/`.
- **Add Content:** Use the admin panel to add new destinations, packages, gallery images, and more.
- **Languages:** Add new translations using Flask-Babel if needed.

---

## Security & Best Practices
- All admin routes require authentication.
- CSRF protection and rate limiting enabled.
- Passwords are securely hashed.
- Email sending is logged for audit.
- Use strong, unique passwords for admin accounts.
- For production, set up proper email (SMTP) and secure deployment (HTTPS, environment variables, etc.).

---

## Troubleshooting & FAQ

**Q: I can't log in to the admin panel.**
- Make sure you ran `python init_site_settings.py` to create the default admin user.
- Default admin: `admin` / `admin123` (change password after first login).

**Q: Emails are not being sent.**
- Check your email settings in the admin panel.
- Make sure your SMTP server is configured and reachable.
- Check the EmailLog in the admin for errors.

**Q: How do I reset a user's password?**
- Use the "Reset Password" feature in the admin panel.

**Q: How do I add new packages or destinations?**
- Log in to the admin panel and use the "Tour Packages" and "Places" sections.

**Q: How do I change the site name or logo?**
- Go to "Site Settings" in the admin panel.

**Q: How do I export bookings or packages?**
- Use the export links in the admin panel (CSV or PDF).

**Q: How do I translate the site?**
- Add new language files using Flask-Babel and update the templates as needed.

---

## License
This project is for demonstration and educational purposes. For production use, review and update security, email, and deployment settings as needed.

---
For questions or support, contact the JKLG Travel team via the website contact form.
