from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='OSIAS CONTROLER').first():
        hashed_password = generate_password_hash('0220Osias')
        admin = User(username='OSIAS CONTROLER', password=hashed_password, role='admin')
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")
