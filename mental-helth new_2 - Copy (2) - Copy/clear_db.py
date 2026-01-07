from app import app, db
from models import UserSession

with app.app_context():
    try:
        num_deleted = db.session.query(UserSession).delete()
        db.session.commit()
        print(f"Successfully deleted {num_deleted} old user session records.")
    except Exception as e:
        db.session.rollback()
        print(f"Error clearing records: {e}")
