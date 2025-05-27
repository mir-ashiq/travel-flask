"""
Initialize or update the SiteSettings table with default or latest values for branding, contact, and social links.
Run this script after migrations or when setting up a new instance.
"""

from extensions import db
from models import SiteSettings
from app import app

def init_site_settings():
    with app.app_context():
        settings = SiteSettings.query.first()
        if not settings:
            settings = SiteSettings(
                site_name='JKLG Travel',
                site_title='Travel Agency - Jammu, Kashmir, Ladakh, Gurez',
                logo='Ladakh.jpg',  # Default logo file in static/uploads/
                phone='+91-12345-67890',
                email='info@jklgtravel.com',
                address='Jammu, Kashmir, Ladakh & Gurez',
                facebook='https://facebook.com/jklgtravel',
                instagram='https://instagram.com/jklgtravel',
                twitter='https://twitter.com/jklgtravel',
                linkedin='',
                youtube='',
                whatsapp='',
                telegram='',
                meta_description='Book your dream trip to Jammu, Kashmir, Ladakh & Gurez with JKLG Travel. Explore destinations, packages, and more.',
                about='JKLG Travel is your trusted partner for exploring the beauty of Jammu, Kashmir, Ladakh, and Gurez. We offer curated packages, expert guides, and unforgettable experiences.',
                google_analytics_id=''
            )
            db.session.add(settings)
            db.session.commit()
            print('SiteSettings initialized.')
        else:
            # Update with latest fields if missing
            updated = False
            defaults = dict(
                site_name='JKLG Travel',
                site_title='Travel Agency - Jammu, Kashmir, Ladakh, Gurez',
                logo='Ladakh.jpg',
                phone='+91-12345-67890',
                email='info@jklgtravel.com',
                address='Jammu, Kashmir, Ladakh & Gurez',
                facebook='https://facebook.com/jklgtravel',
                instagram='https://instagram.com/jklgtravel',
                twitter='https://twitter.com/jklgtravel',
                linkedin='',
                youtube='',
                whatsapp='',
                telegram='',
                meta_description='Book your dream trip to Jammu, Kashmir, Ladakh & Gurez with JKLG Travel. Explore destinations, packages, and more.',
                about='JKLG Travel is your trusted partner for exploring the beauty of Jammu, Kashmir, Ladakh, and Gurez. We offer curated packages, expert guides, and unforgettable experiences.',
                google_analytics_id='',
                hero_title='Discover Jammu, Kashmir, Ladakh & Gurez',
                hero_subtitle='Unforgettable journeys, breathtaking landscapes, and curated experiences await you.'
            )
            for key, value in defaults.items():
                if not hasattr(settings, key) or getattr(settings, key) is None:
                    setattr(settings, key, value)
                    updated = True
            # Ensure new show/hide social fields are present and default to True
            for show_field in ['show_facebook', 'show_instagram', 'show_twitter', 'show_linkedin', 'show_youtube', 'show_whatsapp', 'show_telegram']:
                if not hasattr(settings, show_field) or getattr(settings, show_field) is None:
                    setattr(settings, show_field, True)
                    updated = True
            if updated:
                db.session.commit()
                print('SiteSettings updated with latest fields.')
            else:
                print('SiteSettings already up to date.')

if __name__ == '__main__':
    init_site_settings()
