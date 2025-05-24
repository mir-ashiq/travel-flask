from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_babel import Babel
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
mail = Mail()
babel = Babel()
limiter = Limiter(key_func=get_remote_address)
