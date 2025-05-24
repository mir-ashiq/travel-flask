from app import app, db
from models import SiteSettings

with app.app_context():
    if not SiteSettings.query.first():
        settings = SiteSettings(site_name='JKLG Travel', phone='+91-12345-67890', email='info@jklgtravel.com', address='Jammu, Kashmir, Ladakh & Gurez')
        db.session.add(settings)
        db.session.commit()
    print("Default site settings ensured.")
