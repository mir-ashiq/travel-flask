from app import app, db
from models import SiteSettings

with app.app_context():
    from models import User
    if not User.query.filter_by(username='admin').first():
        admin_user = User(username='admin', is_admin=True, role='superadmin')
        admin_user.set_password('admin123')  # Change this password after first login!
        db.session.add(admin_user)
    if not SiteSettings.query.first():
        settings = SiteSettings(site_name='JKLG Travel', phone='+91-12345-67890', email='info@jklgtravel.com', address='Jammu, Kashmir, Ladakh & Gurez')
        db.session.add(settings)
    db.session.commit()
    print("Default site settings and admin user ensured.")
