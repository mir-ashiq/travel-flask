from flask import Flask, render_template, send_file, request, flash
from extensions import db, mail, babel, limiter
from flask_login import LoginManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms.fields import PasswordField
from flask_admin.form import ImageUploadField, FileUploadField
from flask_wtf import CSRFProtect
from flask_mail import Mail, Message
import os
from flask_admin.menu import MenuLink
import imghdr
from datetime import datetime, timedelta
try:
    import magic  # python-magic for MIME type checking (add to requirements.txt)
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    # Video validation will be basic if python-magic is not installed

# Initialize extensions
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_agency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'  # Use a beautiful Bootstrap swatch

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@jklgtravel.com')

db.init_app(app)
mail.init_app(app)
babel.init_app(app)
limiter.init_app(app)

login_manager = LoginManager(app)
csrf = CSRFProtect(app)

from flask_admin import BaseView, expose
from flask_admin.base import AdminIndexView
from flask_login import current_user
from flask import redirect, url_for, render_template
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

class SecureModelView(ModelView):
    def is_accessible(self):
        from flask_login import current_user
        return current_user.is_authenticated and getattr(current_user, 'is_admin', False)
    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for
        return redirect(url_for('main.login'))

class CustomAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('main.login'))
        from models import Booking, TourPackage, Place, Testimonial, User, GalleryImage, SiteSettings
        from extensions import db
        total_bookings = Booking.query.count()
        total_packages = TourPackage.query.count()
        total_places = Place.query.count()
        total_testimonials = Testimonial.query.count()
        total_users = User.query.count()
        total_gallery = GalleryImage.query.count()
        settings = SiteSettings.query.first()
        recent_bookings = Booking.query.order_by(Booking.date.desc()).limit(5).all()
        popular_packages = db.session.query(Booking.package, db.func.count(Booking.package).label('count')).group_by(Booking.package).order_by(db.func.count(Booking.package).desc()).limit(5).all()
        # Bookings per month (last 12 months)
        now = datetime.now()
        months = [(now.replace(day=1) - timedelta(days=30*i)).strftime('%b %Y') for i in range(11, -1, -1)]
        bookings_per_month = []
        for i in range(11, -1, -1):
            start = (now.replace(day=1) - timedelta(days=30*i))
            end = (now.replace(day=1) - timedelta(days=30*(i-1))) if i > 0 else now
            count = Booking.query.filter(Booking.date >= start, Booking.date < end).count()
            bookings_per_month.append(count)
        return self.render('dashboard.html',
            total_bookings=total_bookings,
            total_packages=total_packages,
            total_places=total_places,
            total_testimonials=total_testimonials,
            total_users=total_users,
            total_gallery=total_gallery,
            site_settings=settings,
            recent_bookings=recent_bookings,
            popular_packages=popular_packages,
            months=months,
            bookings_per_month=bookings_per_month
        )

admin = Admin(app, name='Travel Admin', template_mode='bootstrap4', index_view=CustomAdminIndexView())

# Register blueprints (to be created)
from views import main
app.register_blueprint(main)

# from app.admin import admin_bp
# app.register_blueprint(admin_bp)

class UserAdmin(ModelView):
    form_excluded_columns = ['password']
    column_exclude_list = ['password']
    can_create = False
    can_edit = False
    can_view_details = True

# --- File Validation Helpers ---
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4'}
MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename, allowed_exts):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_exts

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return False
    if format.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        return False
    return True

def validate_video(stream):
    if HAS_MAGIC:
        mime = magic.from_buffer(stream.read(2048), mime=True)
        stream.seek(0)
        return mime == 'video/mp4'
    # Fallback: just check extension (less secure)
    return True

# --- Override admin upload fields for validation ---
class UniqueImageUploadField(ImageUploadField):
    def pre_validate(self, form):
        if self.data:
            if hasattr(self.data, 'filename'):
                if not allowed_file(self.data.filename, ALLOWED_IMAGE_EXTENSIONS):
                    raise ValueError('Invalid image file extension.')
                self.data.stream.seek(0, os.SEEK_END)
                size = self.data.stream.tell()
                self.data.stream.seek(0)
                if size > MAX_IMAGE_SIZE:
                    raise ValueError('Image file too large (max 2MB).')
                if not validate_image(self.data.stream):
                    raise ValueError('Invalid image file.')
        super().pre_validate(form)

class UniqueVideoUploadField(FileUploadField):
    def pre_validate(self, form):
        if self.data:
            if hasattr(self.data, 'filename'):
                if not allowed_file(self.data.filename, ALLOWED_VIDEO_EXTENSIONS):
                    raise ValueError('Invalid video file extension.')
                self.data.stream.seek(0, os.SEEK_END)
                size = self.data.stream.tell()
                self.data.stream.seek(0)
                if size > MAX_VIDEO_SIZE:
                    raise ValueError('Video file too large (max 50MB).')
                if not validate_video(self.data.stream):
                    raise ValueError('Invalid video file.')
        super().pre_validate(form)

class GalleryImageAdmin(ModelView):
    form_overrides = {'image': UniqueImageUploadField, 'video': UniqueVideoUploadField}
    form_args = {
        'image': {
            'label': 'Image',
            'base_path': os.path.join(os.path.dirname(__file__), 'static', 'gallery'),
            'allow_overwrite': True,
        },
        'video': {
            'label': 'Video (MP4, optional)',
            'base_path': os.path.join(os.path.dirname(__file__), 'static', 'gallery'),
            'allow_overwrite': True,
            'allowed_extensions': ['mp4']
        }
    }
    form_extra_fields = {
        'video': UniqueVideoUploadField('Video', base_path=os.path.join(os.path.dirname(__file__), 'static', 'gallery'), allowed_extensions=['mp4'], allow_overwrite=True)
    }

class PlaceAdmin(ModelView):
    form_overrides = {'image': UniqueImageUploadField}
    form_args = {
        'image': {
            'label': 'Image',
            'base_path': os.path.join(os.path.dirname(__file__), 'static', 'places'),
            'allow_overwrite': True,
        }
    }

class TourPackageAdmin(ModelView):
    form_overrides = {'image': UniqueImageUploadField}
    form_args = {
        'image': {
            'label': 'Image',
            'base_path': os.path.join(os.path.dirname(__file__), 'static', 'packages'),
            'allow_overwrite': True,
        }
    }

class SiteSettingsAdmin(ModelView):
    can_create = False  # Only one row
    can_delete = False
    form_overrides = {'logo': UniqueImageUploadField}
    form_args = {
        'logo': {
            'label': 'Logo',
            'base_path': os.path.join(os.path.dirname(__file__), 'static'),
            'allow_overwrite': True,
        }
    }

# Register models with Flask-Admin
from models import User, Place, TourPackage, GalleryImage, Testimonial, SiteSettings, Booking, EmailSettings, Blog, EmailLog

admin.add_view(SecureModelView(User, db.session, name='Users', endpoint='admin_user'))
admin.add_view(SecureModelView(Place, db.session, name='Places', endpoint='admin_place'))
admin.add_view(SecureModelView(TourPackage, db.session, name='Tour Packages', endpoint='admin_tourpackage'))
admin.add_view(SecureModelView(GalleryImage, db.session, name='Gallery Images', endpoint='admin_galleryimage'))
admin.add_view(SecureModelView(Testimonial, db.session, name='Testimonials', endpoint='admin_testimonial'))
admin.add_view(SecureModelView(SiteSettings, db.session, name='Site Settings', endpoint='admin_sitesettings'))
admin.add_view(SecureModelView(Booking, db.session, name='Bookings', endpoint='admin_booking'))
admin.add_view(SecureModelView(EmailSettings, db.session, name='Email Settings', endpoint='admin_emailsettings'))
admin.add_view(SecureModelView(Blog, db.session, name='Blog', endpoint='admin_blog'))
admin.add_view(SecureModelView(EmailLog, db.session, name='Email Logs', endpoint='admin_emaillog'))
admin.add_link(MenuLink(name='Logout', category='', url='/logout'))

# --- Export Bookings as CSV ---
from flask_login import login_required
import io
import csv
@app.route('/admin/export_bookings')
@login_required
def export_bookings():
    from models import Booking
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        return redirect(url_for('main.login'))
    bookings = Booking.query.order_by(Booking.date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Package', 'Date', 'Message'])
    for b in bookings:
        writer.writerow([
            b.id, b.name, b.email, b.phone, b.package, b.date.strftime('%Y-%m-%d %H:%M'), b.message
        ])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='bookings.csv')

# --- Add Export Link to Admin ---
admin.add_link(MenuLink(name='Export Bookings (CSV)', category='', url='/admin/export_bookings'))

# Payment integration placeholder (in booking route, to be implemented)

# Export endpoints for testimonials, users, packages
@app.route('/admin/export_testimonials')
@login_required
def export_testimonials():
    from models import Testimonial
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        return redirect(url_for('main.login'))
    testimonials = Testimonial.query.order_by(Testimonial.id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Content', 'Date'])
    for t in testimonials:
        writer.writerow([t.id, t.name, t.content, t.date])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='testimonials.csv')
@app.route('/admin/export_users')
@login_required
def export_users():
    from models import User
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        return redirect(url_for('main.login'))
    users = User.query.order_by(User.id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Username', 'Is Admin'])
    for u in users:
        writer.writerow([u.id, u.username, u.is_admin])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='users.csv')
@app.route('/admin/export_packages')
@login_required
def export_packages():
    from models import TourPackage
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        return redirect(url_for('main.login'))
    packages = TourPackage.query.order_by(TourPackage.id.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Title', 'Description', 'Price', 'Duration'])
    for p in packages:
        writer.writerow([p.id, p.title, p.description, p.price, p.duration])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True, download_name='packages.csv')
# Add export links to admin
admin.add_link(MenuLink(name='Export Testimonials (CSV)', category='', url='/admin/export_testimonials'))
admin.add_link(MenuLink(name='Export Users (CSV)', category='', url='/admin/export_users'))
admin.add_link(MenuLink(name='Export Packages (CSV)', category='', url='/admin/export_packages'))

# Flask-Babel for i18n
app.config['BABEL_DEFAULT_LOCALE'] = 'en'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

login_manager.login_view = 'main.login'  # Redirect to login page if not authenticated

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
