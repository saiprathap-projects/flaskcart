from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
from models import Base, User, Product, get_engine
from config import Config

engine = get_engine(Config.SQLALCHEMY_DATABASE_URI)

print("Creating tables...")
Base.metadata.create_all(engine)

with Session(engine) as db:
    # Create admin user if not exists
    admin_email = "admin@example.com"
    admin = db.query(User).filter(User.email == admin_email).first()
    if not admin:
        admin = User(
            email=admin_email,
            name="Admin",
            password_hash=generate_password_hash("admin123"),
            is_admin=True,
        )
        db.add(admin)

    # Seed products if table empty
    if db.query(Product).count() == 0:
        sample = [
            dict(name="Wireless Headphones", description="Noise-cancelling over-ear headphones.", price=4999.00, stock=20,
                 image_url="https://images.unsplash.com/photo-1518449073035-61e8b7f1cd4a"),
            dict(name="Mechanical Keyboard", description="RGB backlit, hot-swappable switches.", price=6999.00, stock=15,
                 image_url="https://images.unsplash.com/photo-1517336714731-489689fd1ca8"),
            dict(name="Smart Watch", description="Heart-rate, GPS, 7-day battery.", price=7999.00, stock=30,
                 image_url="https://images.unsplash.com/photo-1511607276578-0a1ff814c0ce"),
            dict(name="USB-C Hub", description="8-in-1 HDMI/PD/USB/SD.", price=2499.00, stock=50,
                 image_url="https://images.unsplash.com/photo-1517336714731-489689fd1ca8"),
        ]
        for p in sample:
            db.add(Product(**p))
    db.commit()

print("Done. Admin: admin@example.com / admin123")
