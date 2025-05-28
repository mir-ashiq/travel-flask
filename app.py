from flask import Flask, render_template, send_file, request, flash, current_app
from extensions import db, mail, babel, limiter
from flask_login import LoginManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView as FlaskAdminModelView
from wtforms.fields import PasswordField, SelectField
from flask_admin.form import ImageUploadField, FileUploadField, Select2Widget
# from wtforms_sqlalchemy.fields import QuerySelectMultipleField  # Not available in latest version
from flask_wtf import CSRFProtect, FlaskForm
from flask_mail import Mail, Message
from flask import render_template_string
from models import EmailTemplate
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
from wtforms import Form, StringField
import json
from werkzeug.utils import secure_filename

# Initialize extensions
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'travel_agency.db')}"
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
from flask_admin.babel import gettext
from flask_admin.model.template import macro
from markupsafe import Markup
from flask import jsonify, abort

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

def send_templated_email(to, template_name, context, subject=None):
    # Ensure site_name is always in context
    if 'site_name' not in context:
        site_settings = SiteSettings.query.first()
        context['site_name'] = site_settings.site_name if site_settings and site_settings.site_name else 'JKLG Travel'
    print(f"[send_templated_email] Called for to={to}, template_name={template_name}, context={context}, subject={subject}")
    try:
        template = EmailTemplate.query.filter_by(name=template_name).first()
        if template:
            try:
                html = render_template_string(template.html_content, **context)
            except Exception as e:
                print(f"[send_templated_email] Error rendering template string: {e}")
                html = f"Dear user, your request has been processed. (Template error: {e})"
            subject_final = subject or template.subject or "Notification from JKLG Travel"
        else:
            try:
                html = render_template(f'emails/{template_name}.html', **context)
            except Exception as e:
                print(f"[send_templated_email] Error rendering file template: {e}")
                html = f"Dear user, your request has been processed. (Template error: {e})"
            subject_final = subject or "Notification from JKLG Travel"
        print(f"[send_templated_email] About to send email to {to} with subject '{subject_final}'")
        msg = Message(subject_final, recipients=[to], html=html)
        try:
            mail.send(msg)
            print(f"[send_templated_email] Email sent to {to}")
            log_email(to, subject_final, html, status='Sent')
        except Exception as e:
            print(f"[send_templated_email] Error sending email: {e}")
            log_email(to, subject_final, html, status='Failed', error=str(e))
    except Exception as e:
        print(f"[send_templated_email] Fatal error: {e}")
        log_email(to, subject or template_name, '', status='Failed', error=str(e))

class PatchedModelView(FlaskAdminModelView):
    def render(self, template, **kwargs):
        from models import SiteSettings
        kwargs.setdefault('site_settings', SiteSettings.query.first())
        return super().render(template, **kwargs)

class SecureModelView(PatchedModelView):
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
    def render(self, template, **kwargs):
        from models import SiteSettings
        kwargs.setdefault('site_settings', SiteSettings.query.first())
        return super().render(template, **kwargs)

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
        # --- Advanced widgets ---
        # Bookings by region
        bookings_by_region = db.session.query(Place.region, db.func.count(Booking.id)).join(TourPackage.places).join(Booking, Booking.package == TourPackage.id).group_by(Place.region).all()
        # Ticket status pie
        ticket_statuses = db.session.query(SupportTicket.status, db.func.count(SupportTicket.id)).group_by(SupportTicket.status).all()
        # Revenue (sum of all bookings' package price)
        revenue = db.session.query(db.func.sum(TourPackage.price)).join(Booking, Booking.package == TourPackage.id).scalar() or 0
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
            total_tickets=total_tickets,
            bookings_by_region=bookings_by_region,
            ticket_statuses=ticket_statuses,
            revenue=revenue
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
                    raise ValueError('Image file too large (max 20MB).')
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
                    raise ValueError('Video file too large (max 150MB).')
                if not validate_video(self.data.stream):
                    raise ValueError('Invalid video file.')
        super().pre_validate(form)

class PlaceAdmin(SecureModelView):
    form_columns = [
        'name', 'description', 'region', 'image', 'featured_home', 'featured_order'
    ]
    column_list = [
        'name', 'region', 'featured_home', 'featured_order'
    ]
    column_editable_list = ['featured_home', 'featured_order']
    column_filters = ['region', 'featured_home']
    column_searchable_list = ['name', 'region']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True
    can_edit_inline = True  # Allow inline editing
    column_formatters = {
        'image': lambda v, c, m, p: f'<img src="/static/places/{m.image}" width="80">' if m.image else '',
        'description': lambda v, c, m, p: (m.description[:50] + '...') if m.description and len(m.description) > 50 else m.description
    }
    column_formatters_detail = column_formatters
    column_display_pk = True
    column_display_all_relations = True
    column_formatters_export = {}

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

# --- Admin Quick Actions and Advanced Features ---

class TestimonialAdmin(SecureModelView):
    form_overrides = dict(status=SelectField)
    form_args = dict(
        status=dict(
            choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
            widget=Select2Widget()
        )
    )
    form_columns = ['name', 'email', 'content', 'date', 'status']
    column_searchable_list = ['name', 'email', 'content', 'status']
    column_filters = ['status', 'date']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True
    can_edit_inline = True
    list_template = 'admin/model/list_with_actions.html'

    @action('approve', 'Approve', 'Are you sure you want to approve selected testimonials?')
    def action_approve(self, ids):
        try:
            query = self.session.query(self.model).filter(self.model.id.in_(ids))
            count = 0
            for t in query:
                t.status = 'Approved'
                # Send approval email if email exists
                if t.email:
                    context = {'testimonial': t}
                    send_templated_email(t.email, 'testimonial_approved', context, subject='Your Testimonial is Approved')
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
                # Send rejection email if email exists
                if t.email:
                    context = {'testimonial': t}
                    send_templated_email(t.email, 'testimonial_rejected', context, subject='Your Testimonial was Rejected')
                count += 1
            self.session.commit()
            flash(f'{count} testimonials rejected.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to reject testimonials. {str(ex)}', 'danger')

    def get_actions(self):
        actions = super().get_actions()
        actions['approve'] = (self.action_approve, 'approve', 'Approve')
        actions['reject'] = (self.action_reject, 'reject', 'Reject')
        return actions

    def on_model_change(self, form, model, is_created):
        from sqlalchemy import inspect
        old_status = None
        if not is_created:
            state = inspect(model)
            hist = state.attrs.status.history
            if hist.has_changes():
                old_status = hist.deleted[0] if hist.deleted else None
            else:
                old_status = getattr(model, 'status', None)
        super().on_model_change(form, model, is_created)
        print(f"[TestimonialAdmin] on_model_change: old.status={old_status}, new.status={model.status}, email={model.email}")
        if not is_created and old_status != model.status and model.email:
            context = {'name': model.name, 'email': model.email, 'content': model.content, 'date': model.date, 'status': model.status}
            print(f"[TestimonialAdmin] Sending email for status change to {model.status} for {model.email}")
            if model.status == 'Approved':
                send_templated_email(model.email, 'testimonial_approved', context, subject='Your Testimonial is Approved')
            elif model.status == 'Rejected':
                send_templated_email(model.email, 'testimonial_rejected', context, subject='Your Testimonial was Rejected')

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
    column_filters = ['status', 'date', 'package']  # Removed 'price' as Booking has no 'price' field
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True
    can_edit_inline = True
    list_template = 'admin/model/list_with_actions.html'  # For quick actions/details modal

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

    def on_model_change(self, form, model, is_created):
        from sqlalchemy import inspect
        old_status = None
        if not is_created:
            state = inspect(model)
            hist = state.attrs.status.history
            if hist.has_changes():
                old_status = hist.deleted[0] if hist.deleted else None
            else:
                old_status = getattr(model, 'status', None)
        super().on_model_change(form, model, is_created)
        print(f"[BookingAdmin] on_model_change: old.status={old_status}, new.status={model.status}, email={model.email}")
        if not is_created and old_status != model.status and model.email:
            context = {
                'name': model.name,
                'email': model.email,
                'package': model.package,
                'message': model.message,
                'date': model.date,
                'status': model.status
            }
            print(f"[BookingAdmin] Sending email for status change to {model.status} for {model.email}")
            if model.status == 'Confirmed':
                send_templated_email(model.email, 'booking_confirmation', context, subject='Your Booking is Confirmed')
            elif model.status == 'Cancelled':
                send_templated_email(model.email, 'booking_rejected', context, subject='Your Booking was Cancelled')

    def get_actions(self):
        actions = super().get_actions()
        actions['confirm'] = (self.action_confirm, 'confirm', 'Confirm')
        actions['cancel'] = (self.action_cancel, 'cancel', 'Cancel')
        return actions

class GalleryImageAdmin(PatchedModelView):
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

class ItineraryDayAdmin(PatchedModelView):
    form_overrides = {'description': CKEditorField}
    form_columns = ['day_number', 'title', 'description']
    column_searchable_list = ['title', 'description']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True

class TourPackageAdmin(PatchedModelView):
    # Add thumbnail for image field in list view
    form_extra_fields = {
        'image': UniqueImageUploadField('Image', base_path=os.path.join(os.path.dirname(__file__), 'static', 'packages'), allow_overwrite=True)
    }
    form_overrides = {
        'description': CKEditorField,
        'itinerary': CKEditorField,
        'accommodations': CKEditorField,
        'included': CKEditorField,
        'excluded': CKEditorField
    }
    form_args = {
        'title': {'description': 'Enter a descriptive and unique package title.'},
        'description': {'description': 'Full package description. Use formatting and images as needed.'},
        'price': {'description': 'Total price for the package (in INR).'},
        'duration': {'description': 'Number of days for the tour.'},
        'places': {
            'description': 'Select all included places.',
            'get_label': lambda place: place.name,
            'query_factory': lambda: Place.query.all(),
        },
        'custom_destinations': {'description': 'Comma-separated list of custom destinations (optional).'},
        'itinerary': {'description': 'Full itinerary in rich text.'},
        'accommodations': {'description': 'Accommodation details.'},
        'included': {'description': 'What is included in the package.'},
        'excluded': {'description': 'What is NOT included in the package.'},
        'itinerary_days': {'description': 'Add detailed day-wise itinerary.'},
        'published': {'description': 'Is this package visible to users?'}
    }
    form_columns = [
        'title', 'description', 'price', 'duration', 'image', 'places', 'custom_destinations',
        'itinerary', 'accommodations', 'included', 'excluded', 'itinerary_days', 'published'
    ]
    inline_models = [(ItineraryDay, dict(form_overrides={'description': CKEditorField}))]
    column_searchable_list = ['title', 'description', 'price', 'duration', 'custom_destinations']
    column_filters = ['duration', 'price', 'places', 'custom_destinations', 'published']
    can_view_details = True
    can_export = True
    can_edit = True
    can_create = True
    can_delete = True
    can_edit_inline = True
    list_template = 'admin/model/list_with_actions.html'  # For quick actions/details modal
    column_formatters = {
        'image': lambda v, c, m, p: f'<img src="/static/packages/{m.image}" width="80">' if m.image else '',
        'description': lambda v, c, m, p: (m.description[:50] + '...') if m.description and len(m.description) > 50 else m.description,
        'published': lambda v, c, m, p: '<span class="badge badge-success">Published</span>' if getattr(m, 'published', False) else '<span class="badge badge-secondary">Draft</span>',
        'places': lambda v, c, m, p: ', '.join([place.name for place in m.places]) if m.places else ''
    }
    column_formatters_detail = column_formatters
    column_display_pk = True
    column_display_all_relations = True
    column_formatters_export = {}
    edit_template = 'admin/tourpackage_edit.html'

    @action('publish', 'Publish', 'Are you sure you want to publish selected packages?')
    def action_publish(self, ids):
        try:
            query = self.session.query(self.model).filter(self.model.id.in_(ids))
            count = 0
            for pkg in query:
                pkg.published = True
                count += 1
            self.session.commit()
            flash(f'{count} packages published.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to publish packages. {str(ex)}', 'danger')

    @action('unpublish', 'Unpublish', 'Are you sure you want to unpublish selected packages?')
    def action_unpublish(self, ids):
        try:
            query = self.session.query(self.model).filter(self.model.id.in_(ids))
            count = 0
            for pkg in query:
                pkg.published = False
                count += 1
            self.session.commit()
            flash(f'{count} packages unpublished.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to unpublish packages. {str(ex)}', 'danger')

    @action('duplicate', 'Duplicate', 'Duplicate selected packages?')
    def action_duplicate(self, ids):
        try:
            from copy import deepcopy
            query = self.session.query(self.model).filter(self.model.id.in_(ids))
            count = 0
            for pkg in query:
                new_pkg = self.model(
                    title=pkg.title + ' (Copy)',
                    description=pkg.description,
                    price=pkg.price,
                    duration=pkg.duration,
                    image=pkg.image,
                    itinerary=pkg.itinerary,
                    accommodations=pkg.accommodations,
                    included=pkg.included,
                    excluded=pkg.excluded,
                    custom_destinations=pkg.custom_destinations,
                    published=False
                )
                new_pkg.places = list(pkg.places)
                self.session.add(new_pkg)
                count += 1
            self.session.commit()
            flash(f'{count} packages duplicated.', 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise
            flash(f'Failed to duplicate packages. {str(ex)}', 'danger')

    def get_actions(self):
        actions = super().get_actions()
        actions['publish'] = (self.action_publish, 'publish', 'Publish')
        actions['unpublish'] = (self.action_unpublish, 'unpublish', 'Unpublish')
        actions['duplicate'] = (self.action_duplicate, 'duplicate', 'Duplicate')
        return actions

    # Add a toggle for published status in list_with_actions.html (template)
    # Show published badge in list view (already in column_formatters)
    # Add a quick duplicate button in the actions column (template)
    # Add tooltips for all fields using WTForms descriptions
    # Add advanced filter widgets in template if needed

class SupportTicketAdmin(SecureModelView):
    can_view_details = True
    can_export = True
    column_searchable_list = ['subject', 'status']
    column_filters = ['status', 'created_at']
    can_edit = True
    can_create = True
    can_delete = True
    form_overrides = dict(status=SelectField)
    form_args = dict(
        status=dict(
            choices=[('Open', 'Open'), ('In Progress', 'In Progress'), ('Closed', 'Closed')]
        )
    )

    def on_model_change(self, form, model, is_created):
        from sqlalchemy import inspect
        old_status = None
        old_response = None
        if not is_created:
            state = inspect(model)
            hist_status = state.attrs.status.history
            hist_response = state.attrs.response.history
            if hist_status.has_changes():
                old_status = hist_status.deleted[0] if hist_status.deleted else None
            else:
                old_status = getattr(model, 'status', None)
            if hist_response.has_changes():
                old_response = hist_response.deleted[0] if hist_response.deleted else None
            else:
                old_response = getattr(model, 'response', None)
        super().on_model_change(form, model, is_created)
        # Send email if status or response changes
        if not is_created and (old_status != model.status or old_response != model.response):
            context = {
                'name': model.name,
                'email': model.email,
                'subject': model.subject,
                'message': model.message,
                'status': model.status,
                'response': model.response
            }
            send_templated_email(model.email, 'ticket_updated', context)

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

class HeroSlideForm(Form):
    title = StringField('Slide Title')
    subtitle = StringField('Slide Subtitle')
    image = StringField('Image Filename')
    animation_title = StringField('Title Animation Class')
    animation_subtitle = StringField('Subtitle Animation Class')

class SiteSettingsAdmin(SecureModelView):
    form_base_class = FlaskForm
    form_extra_fields = {
        'logo': ImageUploadField('Logo', base_path=os.path.join(os.path.dirname(__file__), 'static', 'uploads'), allow_overwrite=True),
        'hero_bg_image': ImageUploadField('Hero Background Image', base_path=os.path.join(os.path.dirname(__file__), 'static', 'uploads'), allow_overwrite=True),
    }
    form_overrides = {
        'hero_slides': TextAreaField  # We'll use a custom widget below
    }
    form_columns = [
        'site_name',
        'site_title',
        'logo',
        'phone',
        'email',
        'address',
        'facebook', 'show_facebook',
        'instagram', 'show_instagram',
        'twitter', 'show_twitter',
        'linkedin', 'show_linkedin',
        'youtube', 'show_youtube',
        'whatsapp', 'show_whatsapp',
        'telegram', 'show_telegram',
        'meta_description',
        'about',
        'google_analytics_id',
        'hero_title',
        'hero_subtitle',
        'hero_bg_image',
        'hero_slide_interval',  # <-- add here
        'hero_slides',
    ]
    form_widget_args = {
        'hero_slides': {
            'rows': 6,
            'placeholder': 'Use the Slide Editor below for a user-friendly interface.'
        }
    }
    create_template = 'admin/model/edit_hero_slides.html'
    edit_template = 'admin/model/edit_hero_slides.html'

    # Optional: Show image preview for logo in the form
    def _logo_preview(view, context, model, name):
        if model and model.logo:
            return Markup(f'<img src="/static/uploads/{model.logo}" style="max-height:60px;">')
        return ''
    column_formatters = {
        'logo': _logo_preview
    }

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    @staticmethod
    def allowed_file(filename, ALLOWED_EXTENSIONS):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def on_model_change(self, form, model, is_created):
        # Handle hero slides image uploads and CTA/alt fields
        import json
        slides_json = request.form.get('hero_slides')
        if slides_json:
            slides = json.loads(slides_json)
            for i, slide in enumerate(slides):
                file_field = f'slide_image_{i}'
                file = request.files.get(file_field)
                if file and self.allowed_file(file.filename, self.ALLOWED_EXTENSIONS):
                    filename = secure_filename(file.filename)
                    upload_path = os.path.join(current_app.root_path, 'static', 'uploads', filename)
                    file.save(upload_path)
                    slide['image'] = filename
                # Ensure all fields exist for each slide
                slide.setdefault('cta_text', '')
                slide.setdefault('cta_link', '')
                slide.setdefault('alt', '')
                slide.setdefault('title', '')
                slide.setdefault('subtitle', '')
                slide.setdefault('animation_title', 'animate__fadeInLeft')
                slide.setdefault('animation_subtitle', 'animate__fadeInRight')
            model.hero_slides = json.dumps(slides)
        return super().on_model_change(form, model, is_created)

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
admin.add_view(UserAdmin(User, db.session, name='Users', endpoint='admin_user'))

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
    writer.writerow(['ID', 'Name', 'Email', 'Content', 'Date'])
    for t in testimonials:
        writer.writerow([t.id, t.name, t.email, t.content, t.date])
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

@app.errorhandler(500)
def internal_error(e):
    from models import SiteSettings
    settings = SiteSettings.query.first()
    return render_template('500.html', site_settings=settings), 500

migrate = Migrate(app, db)

# --- Dark Mode Toggle (JS/CSS) ---
# Add to base admin template (see below for template instructions)

# --- Real-time Notifications (basic polling) ---
@app.route('/admin/notifications')
@login_required
def admin_notifications():
    from models import Booking, SupportTicket
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        abort(403)
    new_bookings = Booking.query.filter_by(status='Pending').count()
    new_tickets = SupportTicket.query.filter_by(status='Open').count()
    return jsonify({'new_bookings': new_bookings, 'new_tickets': new_tickets})

# --- User Impersonation (admin login as user) ---
@app.route('/admin/impersonate/<int:user_id>')
@login_required
def impersonate_user(user_id):
    from models import User
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        abort(403)
    user = User.query.get(user_id)
    if not user:
        abort(404)
    from flask_login import login_user
    login_user(user)
    flash(f'Now impersonating {user.username}', 'info')
    return redirect(url_for('main.index'))

# --- PDF Export for Bookings/Packages (basic) ---
@app.route('/admin/export_bookings_pdf')
@login_required
def export_bookings_pdf():
    from models import Booking
    from flask import render_template
    from xhtml2pdf import pisa
    bookings = Booking.query.order_by(Booking.date.desc()).all()
    html = render_template('admin/bookings_pdf.html', bookings=bookings)
    pdf = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name='bookings.pdf')

@app.route('/admin/export_packages_pdf')
@login_required
def export_packages_pdf():
    from models import TourPackage
    from flask import render_template
    from xhtml2pdf import pisa
    packages = TourPackage.query.order_by(TourPackage.id.desc()).all()
    html = render_template('admin/packages_pdf.html', packages=packages)
    pdf = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=pdf)
    pdf.seek(0)
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name='packages.pdf')

# --- Bulk Import for Users/Packages (CSV) ---
@app.route('/admin/import_users', methods=['GET', 'POST'])
@login_required
def import_users():
    from models import User
    import csv
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('No file uploaded.', 'danger')
            return redirect(request.url)
        reader = csv.DictReader(io.StringIO(file.read().decode()))
        count = 0
        for row in reader:
            if 'username' in row and row['username']:
                user = User(username=row['username'], is_admin=row.get('is_admin', False))
                user.set_password(row.get('password', 'changeme'))
                db.session.add(user)
                count += 1
        db.session.commit()
        flash(f'Imported {count} users.', 'success')
        return redirect(url_for('admin_user.index_view'))
    return render_template('admin/import_users.html')

@app.route('/admin/import_packages', methods=['GET', 'POST'])
@login_required
def import_packages():
    from models import TourPackage
    import csv
    if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('No file uploaded.', 'danger')
            return redirect(request.url)
        reader = csv.DictReader(io.StringIO(file.read().decode()))
        count = 0
        for row in reader:
            if 'title' in row and row['title']:
                pkg = TourPackage(title=row['title'], description=row.get('description', ''), price=row.get('price', 0), duration=row.get('duration', 0))
                db.session.add(pkg)
                count += 1
        db.session.commit()
        flash(f'Imported {count} packages.', 'success')
        return redirect(url_for('admin_tourpackage.index_view'))
    return render_template('admin/import_packages.html')

# --- Add links for new features ---
admin.add_link(MenuLink(name='Export Bookings (PDF)', category='', url='/admin/export_bookings_pdf'))
admin.add_link(MenuLink(name='Export Packages (PDF)', category='', url='/admin/export_packages_pdf'))
admin.add_link(MenuLink(name='Bulk Import Users', category='', url='/admin/import_users'))
admin.add_link(MenuLink(name='Bulk Import Packages', category='', url='/admin/import_packages'))

# --- Dashboard Analytics Widgets (add to dashboard.html template) ---
# - Bookings by region (bar chart)
# - Revenue (line chart)
# - Ticket status (pie chart)
# (See dashboard.html for implementation; data is already provided in CustomAdminIndexView)

# --- Quick Actions, Inline Editing, Tooltips ---
# For Bookings, Testimonials, Support Tickets: add a 'Quick Actions' column in the list view template (list_with_actions.html) with approve/reject/confirm/cancel buttons.
# For inline editing, set can_edit_inline = True and use Flask-Admin's inline editing for key fields.
# For tooltips/help, add WTForms field descriptions and update templates to show them as tooltips.

# --- Dark Mode Toggle ---
# Add a dark mode toggle button in the base admin template (base.html or admin/base.html). Use JS/CSS to switch themes.

# --- Details Modal ---
# In list_with_actions.html, add a 'Details' button to open a modal with record details (AJAX fetch or render hidden content).

# --- Help Comments ---
# For any complex field, add a description in the WTForms field definition (e.g., description='This field controls...').

# --- Template Changes Required ---
# - admin/list_with_actions.html: for quick actions, details modal, inline editing
# - admin/import_users.html, admin/import_packages.html: for bulk import forms
# - admin/bookings_pdf.html, admin/packages_pdf.html: for PDF export
# - base.html or admin/base.html: for dark mode toggle, notifications
#
# See README or comments for further UI/UX polish and advanced analytics.

@app.template_filter('from_json')
def from_json_filter(s):
    try:
        return json.loads(s)
    except Exception:
        return None