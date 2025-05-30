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
- **Bulk import/export for users and packages (CSV)**
- **PDF export for bookings and packages**
- **Admin quick actions (approve/reject/confirm/cancel) for bookings, testimonials, and packages**
- **User impersonation by admin**
- **Real-time admin notifications**
- **Dark mode toggle for admin panel**
- **Inline editing and tooltips in admin**
- **Advanced analytics widgets (bookings by region, revenue, ticket status)**
- **Custom Jinja filter: `from_json` for template JSON parsing**

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
- Flask-Limiter (rate limiting)
- Flask-CKEditor (rich text editing)
- Flask-WTF (forms & CSRF)
- Flask-Migrate (database migrations)
- WTForms/WTForms-Alchemy
- xhtml2pdf (PDF export)

---

## Getting Started

### 1. Clone the repository
```powershell
git clone https://github.com/mir-ashiq/travel-flask
cd travel-flask
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
  - **Gallery:** Upload and manage images and videos (with validation).
  - **Users:** Manage user accounts and permissions. Reset passwords and impersonate users.
  - **Site Settings:** Update site name, contact info, branding, hero slides, and social links.
  - **Email Templates:** Edit email content for all notifications.
  - **Support Tickets:** Respond to user queries and update ticket status.
  - **Import/Export:** Download bookings/packages/testimonials/users as CSV or PDF. Import users/packages from CSV.
- **Logs:** View email logs and activity logs for auditing.
- **Quick Actions:** Approve/reject/confirm/cancel directly from the list view with one click.
- **Inline Editing:** Edit key fields directly in the list view.
- **Details Modal:** View record details in a modal popup.
- **Dark Mode:** Toggle dark mode in the admin panel.
- **Notifications:** See real-time counts of new bookings and tickets.
- **Analytics:** View bookings by region, revenue, and ticket status charts.

---

## Booking & Email Flow
1. **User submits a booking** via the website.
2. **User receives a confirmation email** with a secure link (`/booking/confirm?verify=...`).
3. **User clicks the link** to confirm the booking. The booking status is updated and a confirmation page is shown.
4. **Admin reviews bookings** in the admin panel and can approve/reject as needed.
5. **All status changes** (bookings, testimonials, tickets) trigger automatic email notifications to users.
6. **All emails** use dynamic site branding and are logged in the EmailLog table.

---

## Advanced Admin Features

### Quick Actions & Inline Editing
- Approve/reject testimonials, confirm/cancel bookings, publish/unpublish/duplicate packages with one click.
- Edit fields inline in the admin list view for faster management.

### Import/Export & PDF
- Export bookings, testimonials, users, and packages as CSV or PDF from the admin panel.
- Import users and packages in bulk from CSV files.

### User Impersonation
- Admins can impersonate any user for troubleshooting or support.

### Notifications
- Real-time polling for new bookings and support tickets in the admin panel.

### Dashboard Analytics
- Visual widgets for bookings by region, revenue, and ticket status.

### File Validation
- Images and videos are validated for type and size on upload (20MB for images, 150MB for videos).

### Custom Jinja Filter
- `from_json`: Use `{{ value|from_json }}` in templates to parse JSON strings (see `app.py`).

### Error Handling
- Custom 404 and 500 error pages with site branding.

---

## Customization
- **Site Branding:** Update site name, logo, contact info, and social links in the admin Site Settings.
- **Hero Slides:** Manage homepage hero slides (images, text, animations) in Site Settings.
- **Email Templates:** Edit email content in the admin panel or directly in `templates/emails/`.
- **Add Content:** Use the admin panel to add new destinations, packages, gallery images, and more.
- **Languages:** Add new translations using Flask-Babel if needed.
- **Admin Templates:**
  - `admin/list_with_actions.html`: Quick actions, details modal, inline editing
  - `admin/import_users.html`, `admin/import_packages.html`: Bulk import forms
  - `admin/bookings_pdf.html`, `admin/packages_pdf.html`: PDF export
  - `admin/base.html`: Dark mode toggle, notifications

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

**Q: How do I impersonate a user?**
- Use the "Impersonate" link in the admin panel next to a user account.

**Q: How do I use the dark mode toggle?**
- Click the dark mode button in the admin panel header.

---

## License
This project is for demonstration and educational purposes. For production use, review and update security, email, and deployment settings as needed.

---
For questions or support, contact the JKLG Travel team via the website contact form.
