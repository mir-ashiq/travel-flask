from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_babel import lazy_gettext as _l

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

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

class TourPackage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(200))  # Add image field for upload
    places = db.relationship('Place', secondary='package_places', backref='packages')

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
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date)

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
    logo = db.Column(db.String(200))
    phone = db.Column(db.String(30), default='+91-12345-67890')
    email = db.Column(db.String(120), default='info@jklgtravel.com')
    address = db.Column(db.String(200), default='Jammu, Kashmir, Ladakh & Gurez')
    facebook = db.Column(db.String(200))
    instagram = db.Column(db.String(200))
    twitter = db.Column(db.String(200))

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
