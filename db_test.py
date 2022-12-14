from app import app, db, User, Fine
import random
from util import hash_pass

def add_fine(user_id, type_id, sum, description=''):
    with app.app_context():
        fine = Fine()
        fine.user_id = user_id
        fine.type_id = type_id
        fine.sum = sum
        fine.description = description
        db.session.add(fine)
        db.session.commit()

def add_user(email, username, password):
    with app.app_context():
        print(username)
        user = User()
        user.email = email
        user.username = username
        user.password = password
        user.password_protected = hash_pass(password)
        db.session.add(user)
        db.session.commit()

if __name__ == '__main__':
    for i in range(10):
        username = f"user{random.randint(10000, 99999)}"
        add_user(f"{username}@gmail.com", username, username)
    for i in range(10):
        add_fine(i + 1, random.randint(1,3), random.randint(100, 1000))