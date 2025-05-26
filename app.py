from flask import Flask, render_template, send_file, request, flash
from extensions import db, mail, babel, limiter
from flask_login import LoginManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from wtforms.fields import PasswordField, SelectField
from flask_admin.form import ImageUploadField, FileUploadField, Select2Widget
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
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

from flask_ckeditor import CKEditor, CKEditorField

# Initialize extensions
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_agency.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'  # Use a beautiful Bootstrap swatch

# Configure Flask-Mail
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'mail.lisexports.in')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 465))
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'test@lisexports.in')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'testEmail#123')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'test@lisexports.in')

db.init_app(app)
mail.init_app(app)
babel.init_app(app)
limiter.init_app(app)
ckeditor = CKEditor(app)

login_manager = LoginManager(app)
csrf = CSRFProtect(app)

from flask_admin import BaseView, expose
from flask_admin.base import AdminIndexView
from flask_login import current_user
from flask import redirect, url_for, render_template
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from models import (
    ActivityLog, User, Place, TourPackage, GalleryImage, Testimonial, Booking, SiteSettings, EmailSettings, Blog, EmailLog, FAQ, SupportTicket, ItineraryDay, EmailTemplate
)
from wtforms import TextAreaField
from flask_admin.actions import action

class SecureModelView(ModelView):
    def is_accessible(self):
        from flask_login import current_user
        return current_user.is_authenticated and getattr(current_user, 'role', 'admin') in ['admin', 'superadmin']
    def inaccessible_callback(self, name, **kwargs):
        from flask import redirect, url_for
        return redirect(url_for('main.login'))
    def log_activity(self, action):
        from flask_login import current_user
        from models import ActivityLog
        if current_user.is_authenticated:
            log = ActivityLog(user_id=current_user.id, username=current_user.username, action=action)
            db.session.add(log)
            db.session.commit()
    def on_model_change(self, form, model, is_created):
        action = f"{'Created' if is_created else 'Edited'} {self.model.__name__} (ID: {getattr(model, 'id', None)})"
        self.log_activity(action)
        return super().on_model_change(form, model, is_created)
    def on_model_delete(self, model):
        action = f"Deleted {self.model.__name__} (ID: {getattr(model, 'id', None)})"
        self.log_activity(action)
        return super().on_model_delete(model)

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
        total_faqs = FAQ.query.count()
        total_tickets = SupportTicket.query.count()
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
            bookings_per_month=bookings_per_month,
            total_faqs=total_faqs,
            total_tickets=total_tickets
        )

admin = Admin(app, name='Travel Admin', template_mode='bootstrap4', index_view=CustomAdminIndexView())

# Register blueprints (to be created)
from views import main
app.register_blueprint(main)

# from app.admin import admin_bp
# app.register_blueprint(admin_bp)

class UserAdmin(SecureModelView):
    form_columns = ['username', 'password', 'is_admin', 'role']
    form_overrides = {'password': PasswordField}
    column_searchable_list = ['username']
    column_filters = ['is_admin', 'role']
    column_exclude_list = ['password']
    can_view_details = True
    can_export = True
    can_create = True
    can_edit = True
    can_delete = True

    def on_model_change(self, form, model, is_created):
        # Hash password if set/changed
        if form.password.data:
            model.set_password(form.password.data)
        else:
            # Don't overwrite password if not set
            if not is_created:
                del form.password
        return super().on_model_change(form, model, is_created)

    @expose('/reset_password/', methods=['GET', 'POST'])
    def reset_password_view(self):
        from flask import request, redirect, url_for, flash, render_template
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            confirm = request.form.get('confirm')
            user = self.session.query(self.model).filter_by(username=username).first()
            if not user:
                flash('No user found with that username.', 'danger')
            elif password != confirm:
                flash('Passwords do not match.', 'danger')
            else:
                user.set_password(password)
                self.session.commit()
                flash(f'Password reset for {user.username}.', 'success')
                return redirect(url_for('.index_view'))
        return render_template('admin/reset_password.html')

    @expose('/')
    def index_view(self):
        from flask import render_template, request
        # Add a visible link/button to reset password in the user admin panel
        return super().index_view()

# --- File Validation Helpers ---
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4'}
MAX_IMAGE_SIZE = 20* 1024 * 1024  # 20MB
MAX_VIDEO_SIZE = 150 * 1024 * 1024  # 150MB

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

class PlaceAdmin(ModelView):
    form_extra_fields = {
        'image': ImageUploadField('Image', base_path=os.path.join(os.path.dirname(__file__), 'static', 'places'), allow_overwrite=True)
    }
    form_overrides = {'region': SelectField}  # Added to ensure region uses SelectField
    form_args = {
        'region': {
            'label': 'Region',
            'choices': [('Jammu', 'Jammu'), ('Kashmir', 'Kashmir'), ('Ladakh', 'Ladakh'), ('Gurez', 'Gurez')],
            'widget': Select2Widget()
        }
    }
    form_columns = ['name', 'description', 'region', 'image']
    column_searchable_list = ['name', 'description', 'region']
    column_filters = ['region']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True

class FAQAdmin(SecureModelView):
    form_overrides = {'answer': CKEditorField}
    form_columns = ['question', 'answer', 'is_active']
    column_searchable_list = ['question', 'answer']
    column_filters = ['is_active']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True

class BlogAdmin(SecureModelView):
    form_overrides = {'content': CKEditorField}
    form_columns = ['title', 'content', 'author', 'created_at', 'published']
    column_searchable_list = ['title', 'content', 'author']
    column_filters = ['published', 'created_at']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True

class EmailTemplateAdmin(SecureModelView):
    form_overrides = {'html_content': CKEditorField}
    form_columns = ['name', 'subject', 'html_content']
    column_searchable_list = ['name', 'subject']
    column_filters = ['name']
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    create_template = 'admin/model/create.html'
    edit_template = 'admin/model/edit.html'

class TestimonialAdmin(SecureModelView):
    form_overrides = dict(status=SelectField)
    form_args = dict(
        status=dict(
            choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
            widget=Select2Widget()
        )
    )
    form_columns = ['name', 'content', 'date', 'status']
    column_searchable_list = ['name', 'content', 'status']
    column_filters = ['status', 'date']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True
    can_edit_inline = True

    @action('approve', 'Approve', 'Are you sure you want to approve selected testimonials?')
    def action_approve(self, ids):
        try:
            query = self.session.query(self.model).filter(self.model.id.in_(ids))
            count = 0
            for t in query:
                t.status = 'Approved'
                count += 1
            self.session.commit()
            flash(f'{count} testimonials approved.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to approve testimonials. {str(ex)}', 'danger')

    @action('reject', 'Reject', 'Are you sure you want to reject selected testimonials?')
    def action_reject(self, ids):
        try:
            query = self.session.query(self.model).filter(self.model.id.in_(ids))
            count = 0
            for t in query:
                t.status = 'Rejected'
                count += 1
            self.session.commit()
            flash(f'{count} testimonials rejected.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to reject testimonials. {str(ex)}', 'danger')

class BookingAdmin(SecureModelView):
    form_overrides = dict(status=SelectField)
    form_args = dict(
        status=dict(
            choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('Cancelled', 'Cancelled')],
            widget=Select2Widget()
        )
    )
    form_columns = ['name', 'email', 'phone', 'package', 'message', 'date', 'status']
    column_searchable_list = ['name', 'email', 'phone', 'package', 'status']
    column_filters = ['status', 'date']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True
    can_edit_inline = True

    @action('confirm', 'Confirm', 'Are you sure you want to confirm selected bookings?')
    def action_confirm(self, ids):
        try:
            query = self.session.query(self.model).filter(self.model.id.in_(ids))
            count = 0
            for b in query:
                b.status = 'Confirmed'
                count += 1
            self.session.commit()
            flash(f'{count} bookings confirmed.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to confirm bookings. {str(ex)}', 'danger')

    @action('cancel', 'Cancel', 'Are you sure you want to cancel selected bookings?')
    def action_cancel(self, ids):
        try:
            query = self.session.query(self.model).filter(self.model.id.in_(ids))
            count = 0
            for b in query:
                b.status = 'Cancelled'
                count += 1
            self.session.commit()
            flash(f'{count} bookings cancelled.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to cancel bookings. {str(ex)}', 'danger')

class GalleryImageAdmin(ModelView):
    form_extra_fields = {
        'image': UniqueImageUploadField('Image', base_path=os.path.join(os.path.dirname(__file__), 'static', 'gallery'), allow_overwrite=True),
        'video': UniqueVideoUploadField('Video', base_path=os.path.join(os.path.dirname(__file__), 'static', 'gallery'), allowed_extensions=['mp4'], allow_overwrite=True)
    }
    form_columns = ['image', 'caption', 'video']
    column_searchable_list = ['caption']
    column_filters = ['caption']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True
    column_formatters = {
        'image': lambda v, c, m, p: f'<img src="/static/gallery/{m.image}" width="80">' if m.image else '',
        'video': lambda v, c, m, p: f'<video width="80" controls><source src="/static/gallery/{m.video}" type="video/mp4"></video>' if m.video else ''
    }
    column_formatters_detail = column_formatters
    column_display_pk = True
    column_display_all_relations = True
    column_formatters_export = {}

class TourPackageAdmin(ModelView):
    # Add thumbnail for image field in list view
    form_extra_fields = {
        'image': UniqueImageUploadField('Image', base_path=os.path.join(os.path.dirname(__file__), 'static', 'packages'), allow_overwrite=True)
    }
    form_columns = ['title', 'description', 'price', 'duration', 'image', 'places', 'custom_destinations']  # removed 'is_active'
    column_searchable_list = ['title', 'description']
    column_filters = ['duration']  # removed 'is_active'
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True
    column_formatters = {
        'image': lambda v, c, m, p: f'<img src="/static/packages/{m.image}" width="80">' if m.image else ''
    }
    column_formatters_detail = column_formatters
    column_display_pk = True
    column_display_all_relations = True
    column_formatters_export = {}

class SupportTicketAdmin(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['subject', 'status']  # removed 'user_email'
    column_filters = ['status', 'created_at']
    can_edit = True
    can_create = True
    can_delete = True

class EmailSettingsAdmin(SecureModelView):
    can_view_details = True
    can_edit = True
    can_create = True
    can_delete = True

class EmailLogAdmin(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['subject', 'status']  # removed 'recipient'
    column_filters = ['status', 'sent_at']
    can_edit = False
    can_create = False
    can_delete = True

class ActivityLogAdmin(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['username', 'action']  # removed 'ip_address'
    column_filters = ['action', 'timestamp']
    can_edit = False
    can_create = False
    can_delete = True

class SiteSettingsAdmin(SecureModelView):
    can_view_details = True
    can_edit = True
    can_create = True
    can_delete = True

# Register admin views with advanced classes
admin.add_view(PlaceAdmin(Place, db.session, name='Places', endpoint='admin_place'))
admin.add_view(GalleryImageAdmin(GalleryImage, db.session, name='Gallery Images', endpoint='admin_galleryimage'))
admin.add_view(TestimonialAdmin(Testimonial, db.session, name='Testimonials', endpoint='admin_testimonial'))
admin.add_view(BookingAdmin(Booking, db.session, name='Bookings', endpoint='admin_booking'))
admin.add_view(SupportTicketAdmin(SupportTicket, db.session, name='Support Tickets', endpoint='admin_supportticket'))
admin.add_view(FAQAdmin(FAQ, db.session, name='FAQs', endpoint='admin_faq'))
admin.add_view(BlogAdmin(Blog, db.session, name='Blog', endpoint='admin_blog'))
admin.add_view(EmailSettingsAdmin(EmailSettings, db.session, name='Email Settings', endpoint='admin_emailsettings'))
admin.add_view(EmailLogAdmin(EmailLog, db.session, name='Email Logs', endpoint='admin_emaillog'))
admin.add_view(ActivityLogAdmin(ActivityLog, db.session, name='Activity Log', endpoint='admin_activitylog'))
admin.add_view(EmailTemplateAdmin(EmailTemplate, db.session, name='Email Templates', endpoint='admin_emailtemplate'))
admin.add_view(TourPackageAdmin(TourPackage, db.session, name='Tour Packages', endpoint='admin_tourpackage'))
admin.add_view(SiteSettingsAdmin(SiteSettings, db.session, name='Site Settings', endpoint='admin_sitesettings'))

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
    return db.session.get(User, int(user_id))

login_manager.login_view = 'main.login'  # Redirect to login page if not authenticated

@app.errorhandler(404)
def not_found(e):
    from models import SiteSettings
    settings = SiteSettings.query.first()
    return render_template('404.html', site_settings=settings), 404

migrate = Migrate(app, db)

# --- Email Helper Functions ---
def log_email(to, subject, body, status, error=None):
    """Log email sending attempts to the EmailLog table."""
    log = EmailLog(to=to, subject=subject, body=body, status=status, error=error or '')
    db.session.add(log)
    db.session.commit()

def apply_email_settings():
    """Apply the latest email settings from the database to Flask-Mail config."""
    settings = EmailSettings.query.first()
    if settings:
        app.config['MAIL_SERVER'] = settings.smtp_server
        app.config['MAIL_PORT'] = settings.smtp_port
        app.config['MAIL_USE_TLS'] = settings.use_tls
        app.config['MAIL_USE_SSL'] = settings.use_ssl
        app.config['MAIL_USERNAME'] = settings.username
        app.config['MAIL_PASSWORD'] = settings.password
        app.config['MAIL_DEFAULT_SENDER'] = settings.default_sender
        mail.init_app(app)


def render_email_template(template_name, context):
    """Render an email template from the EmailTemplate model or fallback to file."""
    template = EmailTemplate.query.filter_by(name=template_name).first()
    if template and template.html_content:
        # Use subject and html_content from DB
        subject = template.subject.format(**context) if template.subject else context.get('subject', '')
        html = template.html_content
        try:
            html = html.format(**context)
        except Exception:
            pass  # If formatting fails, use raw html
        return subject, html
    else:
        # Fallback to file-based template
        subject = context.get('subject', '')
        try:
            html = render_template(f'emails/{template_name}.html', **context)
        except Exception:
            html = f"<p>{subject}</p>"
        return subject, html