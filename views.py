from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from models import Place, TourPackage, GalleryImage, Testimonial, User, Booking, SiteSettings, EmailLog, Blog, ItineraryDay
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, mail, limiter, babel
from flask_mail import Message
from flask_babel import _
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
from itsdangerous import URLSafeSerializer, BadSignature

main = Blueprint('main', __name__)

@main.route('/')
def index():
    featured_places = Place.query.filter_by(featured_home=True).order_by(Place.featured_order.asc()).limit(6).all()
    featured_packages = TourPackage.query.all()
    testimonials = Testimonial.query.order_by(Testimonial.id.desc()).all()
    gallery = GalleryImage.query.all()
    return render_template('index.html', featured_places=featured_places, featured_packages=featured_packages, testimonials=testimonials, gallery=gallery)

@main.route('/places')
def places():
    page = request.args.get('page', 1, type=int)
    per_page = 6
    pagination = Place.query.paginate(page=page, per_page=per_page, error_out=False)
    places = pagination.items
    return render_template('places.html', places=places, pagination=pagination)

@main.route('/packages')
def packages():
    page = request.args.get('page', 1, type=int)
    per_page = 6
    q = request.args.get('q', '').strip()
    region = request.args.get('region', '').strip()
    sort = request.args.get('sort', '')
    query = TourPackage.query
    if q:
        query = query.filter((TourPackage.title.ilike(f'%{q}%')) | (TourPackage.description.ilike(f'%{q}%')))
    if region:
        query = query.join(TourPackage.places).filter_by(region=region)
    if sort == 'price_asc':
        query = query.order_by(TourPackage.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(TourPackage.price.desc())
    elif sort == 'duration_asc':
        query = query.order_by(TourPackage.duration.asc())
    elif sort == 'duration_desc':
        query = query.order_by(TourPackage.duration.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    packages = pagination.items
    return render_template('packages.html', packages=packages, pagination=pagination)

@main.route('/gallery')
def gallery():
    page = request.args.get('page', 1, type=int)
    per_page = 6
    pagination = GalleryImage.query.paginate(page=page, per_page=per_page, error_out=False)
    gallery = pagination.items
    return render_template('gallery.html', gallery=gallery, pagination=pagination)

@main.route('/testimonials', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def testimonials():
    from models import Testimonial, SiteSettings, EmailLog  # Ensure Testimonial is always imported
    from app import mail
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        email = request.form.get('email')
        t = Testimonial(name=name, email=email, content=content, status='Pending')
        db.session.add(t)
        db.session.commit()
        # Advanced: Notify admin of new testimonial and send confirmation to user
        try:
            settings = SiteSettings.query.first()
            admin_email = settings.email if settings and settings.email else 'info@jklgtravel.com'
            msg = Message('New Testimonial Submitted', recipients=[admin_email])
            msg.body = f"""
New testimonial submitted:\n\nName: {name}\nEmail: {email or '-'}\nContent: {content}\n"""
            mail.send(msg)
            db.session.add(EmailLog(to=admin_email, subject=msg.subject, body=msg.body, status='sent', error=''))
            # Confirmation to user (if email provided)
            if email:
                user_msg = Message('Thank you for your testimonial!', recipients=[email])
                user_msg.html = render_template('emails/testimonial_confirmation.html', name=name)
                mail.send(user_msg)
                db.session.add(EmailLog(to=email, subject=user_msg.subject, body=user_msg.html, status='sent', error=''))
            db.session.commit()
        except Exception as e:
            db.session.add(EmailLog(to=admin_email, subject='Testimonial Notification', body='', status='failed', error=str(e)))
            db.session.commit()
            print('Testimonial email failed:', e)
        flash('Thank you for your testimonial! It will appear after admin approval.')
        return redirect(url_for('main.testimonials'))
    page = request.args.get('page', 1, type=int)
    per_page = 6
    pagination = Testimonial.query.filter_by(status='Approved').order_by(Testimonial.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    testimonials = pagination.items
    return render_template('testimonials.html', testimonials=testimonials, pagination=pagination)

# Blog/news section
@main.route('/blog')
def blog():
    posts = Blog.query.filter_by(published=True).order_by(Blog.created_at.desc()).all()
    return render_template('blog.html', posts=posts)

@main.route('/book', methods=['GET', 'POST'])
@limiter.limit('5 per minute')
def book():
    from app import mail  # Import here to avoid circular import
    from models import SiteSettings
    package_name = request.args.get('package')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        package = request.form['package']
        message = request.form['message']
        booking = Booking(name=name, email=email, phone=phone, package=package, message=message)
        db.session.add(booking)
        db.session.commit()
        # Generate a real verification token
        s = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='booking-confirm')
        verification_token = s.dumps({'booking_id': booking.id, 'email': email})
        try:
            settings = SiteSettings.query.first()
            admin_email = settings.email if settings and settings.email else 'info@jklgtravel.com'
            user_msg = Message(_('Booking Confirmation - JKLG Travel'), recipients=[email])
            user_msg.html = render_template('emails/booking_confirmation.html', name=name, package=package, message=message, verification_token=verification_token)
            mail.send(user_msg)
            db.session.add(EmailLog(to=email, subject=user_msg.subject, body=user_msg.html, status='sent', error=''))
            admin_msg = Message(_('New Booking Received'), recipients=[admin_email])
            admin_msg.html = render_template('emails/booking_admin.html', name=name, email=email, phone=phone, package=package, message=message)
            mail.send(admin_msg)
            db.session.add(EmailLog(to=admin_email, subject=admin_msg.subject, body=admin_msg.html, status='sent', error=''))
            db.session.commit()
        except Exception as e:
            db.session.add(EmailLog(to=email, subject='Booking Confirmation', body='', status='failed', error=str(e)))
            db.session.commit()
            print('Email send failed:', e)
        flash(_('Thank you for your booking request! Our team will contact you soon.'))
        return redirect(url_for('main.book'))
    return render_template('book.html', package_name=package_name)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('main.index'))

@main.route('/bookings', methods=['GET', 'POST'])
@login_required
def bookings():
    if not current_user.is_admin:
        flash('Admins only!')
        return redirect(url_for('main.index'))
    bookings = Booking.query.order_by(Booking.date.desc()).all()
    # Edit booking
    if request.method == 'POST':
        booking_id = request.form.get('booking_id')
        booking = Booking.query.get(booking_id)
        if booking:
            booking.name = request.form.get('name', booking.name)
            booking.email = request.form.get('email', booking.email)
            booking.phone = request.form.get('phone', booking.phone)
            booking.package = request.form.get('package', booking.package)
            booking.message = request.form.get('message', booking.message)
            db.session.commit()
            flash('Booking updated!')
        return redirect(url_for('main.bookings'))
    return render_template('bookings.html', bookings=bookings)

@main.route('/packages/<int:package_id>')
def package_detail(package_id):
    package = TourPackage.query.get_or_404(package_id)
    # Eager load itinerary days, ordered
    itinerary_days = ItineraryDay.query.filter_by(package_id=package.id).order_by(ItineraryDay.day_number).all()
    return render_template('package_detail.html', package=package, itinerary_days=itinerary_days)

@main.route('/dashboard')
@login_required
def dashboard():
    from models import Booking, TourPackage, Place, Testimonial
    total_bookings = Booking.query.count()
    total_packages = TourPackage.query.count()
    total_places = Place.query.count()
    total_testimonials = Testimonial.query.count()
    recent_bookings = Booking.query.order_by(Booking.date.desc()).limit(5).all()
    popular_packages = db.session.query(Booking.package, db.func.count(Booking.package).label('count')).group_by(Booking.package).order_by(db.func.count(Booking.package).desc()).limit(5).all()
    return render_template('dashboard.html',
        total_bookings=total_bookings,
        total_packages=total_packages,
        total_places=total_places,
        total_testimonials=total_testimonials,
        recent_bookings=recent_bookings,
        popular_packages=popular_packages)

@main.route('/admin/analytics')
@login_required
def analytics():
    if not current_user.is_admin:
        return redirect(url_for('main.login'))
    from models import Booking, TourPackage
    from extensions import db
    now = datetime.now()
    months = [(now.replace(day=1) - timedelta(days=30*i)).strftime('%b %Y') for i in range(11, -1, -1)]
    bookings_per_month = []
    for i in range(11, -1, -1):
        start = (now.replace(day=1) - timedelta(days=30*i))
        end = (now.replace(day=1) - timedelta(days=30*(i-1))) if i > 0 else now
        count = Booking.query.filter(Booking.date >= start, Booking.date < end).count()
        bookings_per_month.append(count)
    popular_packages = [
        (row[0], row[1])
        for row in db.session.query(Booking.package, db.func.count(Booking.package).label('count'))
            .group_by(Booking.package)
            .order_by(db.func.count(Booking.package).desc())
            .limit(5)
            .all()
    ]
    return render_template('analytics.html', months=months, bookings_per_month=bookings_per_month, popular_packages=popular_packages)

@main.route('/faq')
def faq():
    from models import FAQ
    faqs = FAQ.query.filter_by(is_active=True).all()
    return render_template('faq.html', faqs=faqs)

@main.route('/contact', methods=['GET', 'POST'])
def contact():
    from models import SupportTicket
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        ticket = SupportTicket(name=name, email=email, subject=subject, message=message)
        db.session.add(ticket)
        db.session.commit()
        flash('Your message has been received. Our team will contact you soon.')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')

@main.route('/help')
def help_center():
    return render_template('help.html')

@main.route('/booking/confirm')
def booking_confirm():
    from models import Booking, SiteSettings
    token = request.args.get('verify')
    booking = None
    confirmed = False
    error = None
    if token:
        s = URLSafeSerializer(current_app.config['SECRET_KEY'], salt='booking-confirm')
        try:
            data = s.loads(token)
            booking_id = data.get('booking_id')
            email = data.get('email')
            booking = Booking.query.filter_by(id=booking_id, email=email).first()
            if booking:
                if booking.status != 'Confirmed':
                    booking.status = 'Confirmed'
                    db.session.commit()
                confirmed = True
            else:
                error = 'Booking not found.'
        except BadSignature:
            error = 'Invalid or expired confirmation link.'
        except Exception as e:
            error = str(e)
    else:
        error = 'Missing confirmation token.'
    site_settings = SiteSettings.query.first()
    return render_template('booking_confirmed.html', booking=booking, confirmed=confirmed, error=error, site_settings=site_settings)

@main.context_processor
def inject_site_settings():
    settings = SiteSettings.query.first()
    return dict(site_settings=settings)

# Multi-language support
@main.route('/lang/<lang_code>')
def set_language(lang_code):
    from flask import session
    session['lang'] = lang_code
    return redirect(request.referrer or url_for('main.index'))

# Flask-Babel v4.0.0 may not provide the decorator, so set the selector function directly.
def get_locale():
    from flask import session
    return session.get('lang', 'en')

babel.locale_selector_func = get_locale
