from app import app, db
from models import User
from getpass import getpass

# Create a new admin user with hashed password and email
def create_admin():
    username = input('Enter new admin username: ')
    email = input('Enter admin email: ')
    password = getpass('Enter password: ')
    confirm = getpass('Confirm password: ')
    if password != confirm:
        print('Passwords do not match.')
        return
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print('Username already exists.')
            return
        user = User(username=username, is_admin=True, role='admin')
        user.set_password(password)
        user.email = email
        db.session.add(user)
        db.session.commit()
        print(f'Admin user {username} created.')

# Reset password for a user by email
def reset_password():
    email = input('Enter user email to reset password: ')
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print('No user found with that email.')
            return
        password = getpass('Enter new password: ')
        confirm = getpass('Confirm new password: ')
        if password != confirm:
            print('Passwords do not match.')
            return
        user.set_password(password)
        db.session.commit()
        print(f'Password reset for {user.username} ({email}).')

if __name__ == '__main__':
    print('1. Create admin user')
    print('2. Reset user password by email')
    print('3. List all users')
    choice = input('Choose an option (1/2/3): ')
    if choice == '1':
        create_admin()
    elif choice == '2':
        reset_password()
    elif choice == '3':
        with app.app_context():
            users = User.query.all()
            print(f"{'Username':<20} {'Email':<30} {'Is Admin':<10} {'Role':<10}")
            print('-'*70)
            for u in users:
                print(f"{u.username:<20} {getattr(u, 'email', ''):<30} {str(u.is_admin):<10} {getattr(u, 'role', ''):<10}")
    else:
        print('Invalid choice.')
