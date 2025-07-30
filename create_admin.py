# create_admin.py

from werkzeug.security import generate_password_hash
from app import app, db  
from model import Admin  

# Wrap inside app context
with app.app_context():
    hashed_password = generate_password_hash("subburakesh@2255")
    admin = Admin(
        admin_name="Super Admin",
        admin_email="subburakesh2255@gmail.com",
        admin_password=hashed_password
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin created successfully.")
