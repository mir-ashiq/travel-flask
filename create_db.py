from app import app, db
from models import *
from datetime import datetime

def create_all_and_seed():
    db.create_all()
    # --- Seed Users ---
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', is_admin=True, role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
    # --- Seed Places ---
    if not Place.query.first():
        db.session.add_all([
            Place(name='Srinagar', description='Beautiful city in Kashmir', region='Kashmir', image=''),
            Place(name='Gulmarg', description='Famous for skiing', region='Kashmir', image=''),
            Place(name='Leh', description='Capital of Ladakh', region='Ladakh', image=''),
            Place(name='Gurez', description='Hidden gem in Kashmir', region='Gurez', image=''),
        ])
    # --- Seed Tour Packages ---
    if not TourPackage.query.first():
        db.session.add(TourPackage(title='Kashmir Delight', description='7 days in Kashmir', price=25000, duration='7 Days', image='', itinerary='Day 1: Arrival', accommodations='Hotel', included='Meals', excluded='Flights', custom_destinations='Srinagar,Gulmarg'))
    # --- Seed Gallery Images ---
    if not GalleryImage.query.first():
        db.session.add(GalleryImage(image='', caption='Dal Lake', video=None))
    # --- Seed Testimonials ---
    if not Testimonial.query.first():
        db.session.add(Testimonial(name='John Doe', content='Amazing trip!', date=datetime.now(), status='Approved'))
    # --- Seed Site Settings ---
    if not SiteSettings.query.first():
        db.session.add(SiteSettings(site_name='JKLG Travel', logo='', phone='+91-12345-67890', email='info@jklgtravel.com', address='Jammu, Kashmir, Ladakh & Gurez'))
    # --- Seed Email Settings ---
    if not EmailSettings.query.first():
        db.session.add(EmailSettings(smtp_server='smtp.gmail.com', smtp_port=587, use_tls=True, use_ssl=False, username='test@jklgtravel.com', password='test', default_sender='noreply@jklgtravel.com'))
    # --- Seed Email Template ---
    if not EmailTemplate.query.first():
        db.session.add(EmailTemplate(name='booking_confirmation', subject='Booking Confirmed', html_content='<p>Your booking is confirmed!</p>'))
    # --- Seed FAQ ---
    if not FAQ.query.first():
        db.session.add(FAQ(question='How to book?', answer='Use our website to book your trip.', is_active=True))
    # --- Seed Support Ticket ---
    if not SupportTicket.query.first():
        db.session.add(SupportTicket(name='Jane', email='jane@example.com', subject='Help', message='Need help', status='Open'))
    # --- Seed Blog ---
    if not Blog.query.first():
        db.session.add(Blog(title='Welcome', content='Welcome to our travel blog!', author='Admin', published=True))
    db.session.commit()

if __name__ == "__main__":
    from app import app
    with app.app_context():
        create_all_and_seed()
    print('Database created and seeded!')
