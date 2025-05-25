from app import app
from models import EmailTemplate
from extensions import db

with app.app_context():
    for t in EmailTemplate.query.all():
        if not isinstance(t.subject, str):
            t.subject = ''
        if not isinstance(t.html_content, str):
            t.html_content = ''
    db.session.commit()
    print("Fixed EmailTemplate data.")