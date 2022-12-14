from flask import Flask, request, url_for, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask import flash
from flask_login import login_required, LoginManager, login_user, logout_user, UserMixin, current_user
from util import hash_pass, verify_pass
import sqlite3

login_manager = LoginManager()
db = SQLAlchemy()

app = Flask(__name__)
app.secret_key = 'SECRET_key_1'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///project.db"
db.init_app(app)
login_manager.init_app(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_protected = db.Column(db.BINARY)
    password = db.Column(db.String)
    fines = db.relationship('Fine', backref='user', lazy=True)
    is_active = db.Column(db.Boolean, default=True)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            if property == 'password_protected':
                value = hash_pass(value)

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)


class Fine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    type_id = db.Column(db.Integer)
    sum = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String)
    is_payed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return str(self.id)


with app.app_context():
    db.create_all()


@app.route('/')
def main():
    if current_user.is_authenticated:
        return redirect(url_for("user_detail", id=current_user.id))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
@app.route("/register/", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form["password"] == request.form["repass"]:
            # Check usename exists
            user = User.query.filter_by(username=request.form['username']).first()
            if user:
                error = 'User already exist!'
                flash(error)
                return render_template('register.html')
            # Check email exists
            user = User.query.filter_by(email=request.form['email']).first()
            if user:
                error = 'User already exist!'
                flash(error)
                return render_template('register.html')
            user = User(
                username=request.form['username'],
                email=request.form["email"],
                password=request.form["password"],
                password_protected=request.form["password"],
                is_active=True
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("user_detail", id=user.id))
        else:
            error = 'Password does not match!'
            flash(error)
            return render_template('register.html')
    return render_template("register.html")


@app.route('/login', methods=['POST', 'GET'])
@app.route('/login/', methods=['POST', 'GET'])
def login():
    error = None
    if request.method == 'POST':
        #  admin' OR 1=1;--
        #  ' OR 'str'='str';--
        username = request.values.get('username')
        password = request.values.get('password')

        print(username, password)

        try:
            query = "SELECT id FROM User WHERE username = '%s' AND password = '%s'" % (username, password)
            record_id = db.session.execute(query).scalar()

            if record_id:
                user = load_user(record_id)
                login_user(user)
                return redirect(url_for("user_detail", id=record_id))
            else:
                error = 'Invalid username/password!'
                flash(error)
        except Exception as E:
            print(E)
            error = 'Something went wrong!'
            flash(error)
    if not current_user.is_authenticated:
        return render_template('login.html', error=error)
    return redirect(url_for("user_detail", id=current_user.id))


@app.route('/login_protected', methods=['POST', 'GET'])
@app.route('/login_protected/', methods=['POST', 'GET'])
def login_protected():
    error = None
    if request.method == 'POST':
        username = request.values.get('username')
        password = request.values.get('password')
        print(username, password)
        try:
            user = User.query.filter_by(username=request.values.get('username')).first()
            # Check the password
            if user and verify_pass(password, user.password_protected):
                login_user(user)
                return redirect(url_for("user_detail", id=user.id))
            else:
                error = 'Invalid username/password!'
                flash(error)
        except Exception as E:
            print(E)
            error = 'Something went wrong!'
            flash(error)
    if not current_user.is_authenticated:
        return render_template('login.html', error=error)
    return redirect(url_for("user_detail", id=current_user.id))


@app.route("/users/<int:id>", methods=['GET'])
@login_required
def user_detail(id):
    user = db.get_or_404(User, id)
    return render_template('users.html', users=[user])


@app.route("/users/", methods=['GET', 'POST'])
@login_required
def users_detail():
    users = db.session.query(User).all()
    return render_template('users.html', users=users)


@app.route("/fines", methods=['GET', 'POST'])
@app.route("/fines/", methods=['GET', 'POST'])
@login_required
def fines():
    fines = []
    try:
        fines = db.session.query(Fine).all()
        if request.method == "POST":
            mydb = sqlite3.connect('instance/project.db', check_same_thread=False)
            description = request.form['description']
            fine_id = request.form['fineId']
            # change description
            # ';delete from Fine;Select id from 'Fine
            # ';delete from Fine WHERE id=1;Select id from 'User

            query = "UPDATE Fine SET description = '%s' WHERE id = '%s';" % (description, fine_id)
            mycursor = mydb.cursor()
            mycursor.executescript(query)
            return redirect(url_for("fines", fines=fines))
    except Exception as E:
        print(E)

    return render_template('fines.html', fines=fines)


@app.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    users = []
    if request.method == "POST":
        try:
            user = request.form['user']
            # search by username
            query = "SELECT * FROM User WHERE username LIKE '%s'" % (f'%{user}%')
            users = db.session.execute(query).all()
        except Exception as E:
            print(E)

    return render_template('users.html', users=users)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=user_id).first()


if __name__ == '__main__':
    app.run()
