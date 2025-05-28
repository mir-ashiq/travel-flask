from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_babel import lazy_gettext as _l
from datetime import datetime

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64))
    action = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(32), default='admin')  # 'admin', 'staff', 'superadmin', etc.

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class Place(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    region = db.Column(db.String(50), nullable=False)  # Jammu, Kashmir, Ladakh, Gurez
    image = db.Column(db.String(200))
    featured_home = db.Column(db.Boolean, default=False)  # Show on homepage
    featured_order = db.Column(db.Integer, default=0)     # Order on homepage

class TourPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200))  # Add image field for upload
    places = db.relationship('Place', secondary='package_places', backref='packages')
    itinerary = db.Column(db.Text)
    accommodations = db.Column(db.Text)
    included = db.Column(db.Text)
    excluded = db.Column(db.Text)
    custom_destinations = db.Column(db.String(500))  # New field for manual destinations
    published = db.Column(db.Boolean, default=False)  # New field for published status

class PackagePlaces(db.Model):
    __tablename__ = 'package_places'
    package_id = db.Column(db.Integer, db.ForeignKey('tour_package.id'), primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey('place.id'), primary_key=True)

class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(200))
    caption = db.Column(db.String(200))
    video = db.Column(db.String(200))  # New field for video

class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)  # New field for user email
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.status is None:
            self.status = 'Pending'

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    package = db.Column(db.String(120))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, server_default=db.func.now())
    status = db.Column(db.String(20), default='Pending')  # New field

class SiteSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    site_name = db.Column(db.String(120), default='JKLG Travel')
    site_title = db.Column(db.String(200), default='JKLG Travel - Explore Jammu, Kashmir, Ladakh & Gurez')
    logo = db.Column(db.String(200))
    phone = db.Column(db.String(30), default='+91-12345-67890')
    email = db.Column(db.String(120), default='info@jklgtravel.com')
    address = db.Column(db.String(200), default='Jammu, Kashmir, Ladakh & Gurez')
    facebook = db.Column(db.String(120))  # Username only
    instagram = db.Column(db.String(120))  # Username only
    twitter = db.Column(db.String(120))  # Username only
    linkedin = db.Column(db.String(120))  # Username only
    youtube = db.Column(db.String(120))  # Channel/user ID only
    whatsapp = db.Column(db.String(30))  # Number only
    telegram = db.Column(db.String(120))  # Username only
    meta_description = db.Column(db.String(300))
    about = db.Column(db.Text)
    google_analytics_id = db.Column(db.String(32))
    show_facebook = db.Column(db.Boolean, default=True)
    show_instagram = db.Column(db.Boolean, default=True)
    show_twitter = db.Column(db.Boolean, default=True)
    show_linkedin = db.Column(db.Boolean, default=True)
    show_youtube = db.Column(db.Boolean, default=True)
    show_whatsapp = db.Column(db.Boolean, default=True)
    show_telegram = db.Column(db.Boolean, default=True)
    hero_title = db.Column(db.String(200), default='Discover Jammu, Kashmir, Ladakh & Gurez')
    hero_subtitle = db.Column(db.String(300), default='Unforgettable journeys, breathtaking landscapes, and curated experiences await you.')
    hero_bg_image = db.Column(db.String(200), default='hero_default.jpg')  # New field for background image
    hero_slides = db.Column(db.Text)  # JSON: [{"title":..., "subtitle":..., "image":..., "animation_title":..., "animation_subtitle":...}, ...]
    hero_slide_interval = db.Column(db.Integer, default=5)  # Interval in seconds for hero carousel

    def __str__(self):
        return self.site_name or f"SiteSettings #{self.id}"

    # Helper for admin: pretty print slides
    def hero_slides_pretty(self):
        import json
        try:
            slides = json.loads(self.hero_slides) if self.hero_slides else []
            return '\n'.join([
                f"{i+1}. {slide.get('title','')} | {slide.get('subtitle','')} | {slide.get('image','')} | {slide.get('animation_title','')} | {slide.get('animation_subtitle','')}"
                for i, slide in enumerate(slides)
            ])
        except Exception:
            return self.hero_slides or ''

    @property
    def hero_slides_list(self):
        import json
        try:
            slides = json.loads(self.hero_slides) if self.hero_slides else []
            # Ensure all keys exist for each slide and add robust defaults
            for slide in slides:
                slide.setdefault('enabled', True)
                slide.setdefault('title', '')
                slide.setdefault('subtitle', '')
                slide.setdefault('image', '')
                slide.setdefault('alt', '')
                slide.setdefault('animation_title', 'animate__fadeInLeft')
                slide.setdefault('animation_subtitle', 'animate__fadeInRight')
                slide.setdefault('cta_text', '')
                slide.setdefault('cta_link', '')
            return slides
        except Exception:
            return []

class EmailSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(120), default='smtp.gmail.com')
    smtp_port = db.Column(db.Integer, default=587)
    use_tls = db.Column(db.Boolean, default=True)
    use_ssl = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(120))
    password = db.Column(db.String(120))
    default_sender = db.Column(db.String(120), default='noreply@jklgtravel.com')

class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    to = db.Column(db.String(200))
    subject = db.Column(db.String(200))
    body = db.Column(db.Text)
    status = db.Column(db.String(20))
    error = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, server_default=db.func.now())

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    published = db.Column(db.Boolean, default=False)

class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(300), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    response = db.Column(db.Text)
    responded_at = db.Column(db.DateTime)

class ItineraryDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    package_id = db.Column(db.Integer, db.ForeignKey('tour_package.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    package = db.relationship('TourPackage', backref=db.backref('itinerary_days', cascade='all, delete-orphan', order_by='ItineraryDay.day_number'))

class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # e.g. 'booking_confirmation'
    subject = db.Column(db.String(200), nullable=False, default='')
    html_content = db.Column(db.Text, nullable=False, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
