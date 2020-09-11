from app import app, db
from models import Multisport, User
from flask import render_template, request, redirect, url_for, flash
from flask import session as session_flask
from wtforms import Form, StringField, DateTimeField, IntegerField, validators, PasswordField, SubmitField
from wtforms.validators import InputRequired
from passlib.hash import sha256_crypt
from datetime import datetime
from functools import wraps
from sqlalchemy.exc import DataError, IntegrityError, OperationalError
from statistic_functions import check_if_all, filter_activities, check_classes_popularity, count_ratings, \
     count_savings, count_duration
import random


class ActivityForm(Form):
    category = StringField('Category', validators=[InputRequired()])
    classes = StringField('Classes', validators=[InputRequired()])
    place = StringField('Place', validators=[InputRequired()])
    instructor = StringField('Instructor')
    duration = IntegerField('Duration')
    price = IntegerField('Price')
    date = DateTimeField('Date')
    classes_rate = IntegerField('Classes rate')
    training_rate = IntegerField('Training rate')
    submit = SubmitField("Submit")


class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=8, max=70)])
    email = StringField('Email', [validators.Length(min=8, max=100)])
    gender = StringField('Gender', [validators.Length(min=3, max=30)])
    password = PasswordField('Password', [
        validators.Length(min=8, max=50),
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm password')


class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=8, max=70)])
    password = PasswordField('Password', [
        validators.Length(min=8, max=50),
        validators.DataRequired()
    ])


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm(request.form)

    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        gender = form.gender.data
        password = sha256_crypt.encrypt(str(form.password.data))
        join_date = datetime.today()

        new_user = User(username=username, email=email, gender=gender, password=password, join_date=join_date)

        db.session.add(new_user)
        db.session.commit()

        flash('You are now registered and can log in.', 'success')
        redirect(url_for('index'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm(request.form)

    if request.method == 'POST' and form.validate():
        username = form.username.data
        password_candidate = form.password.data

        result = User.query.filter(User.username == username).first()

        if result:
            password = result.password

            # Compare passwords
            if sha256_crypt.verify(password_candidate, password):
                session_flask['logged_in'] = True
                session_flask['username'] = username
                session_flask.permanent = True

                flash('You are now logged in', 'success')
                return redirect(url_for('see_activities'))
            else:
                flash('Invalid password', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Username not found', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html', form=form)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session_flask:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please log in.', 'danger')
            return redirect(url_for('login'))

    return wrap


@app.route('/logout')
@is_logged_in
def logout():
    session_flask.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/activities')
@is_logged_in
def add():
    return render_template('activities.html')


@app.route('/submit', methods=['GET', 'POST'])
@is_logged_in
def submit():
    if request.method == 'POST':
        category = request.form.get('category')
        classes = request.form.get('classes')
        place = request.form.get('place')
        instructor = request.form.get('instructor')
        duration = request.form.get('duration')
        price = request.form.get('price')
        date = request.form.get('date')
        classes_rate = request.form.get('classes_rate')
        training_rate = request.form.get('training_rate')

        user = User.query.filter(User.username == session_flask['username']).first()
        gender = user.gender

        while True:
            try:
                activity_id = random.randint(100000, 999999)

                multi = Multisport(id=activity_id, gender=gender, category=category, classes=classes, place=place,
                                   instructor=instructor, duration=duration, price=price, date=date,
                                   classes_rate=classes_rate, training_rate=training_rate, user_id=user.id)
                db.session.add(multi)
                db.session.commit()
                break

            except IntegrityError:
                continue

            except DataError:
                if '' in [category, classes, instructor, duration, price, date, classes_rate, training_rate]:
                    flash('Fill in data!', 'danger')
                    return redirect(url_for('add'))
                else:
                    flash('Price and duration must be integers!', 'danger')
                    return redirect(url_for('add'))

            except OperationalError:
                flash('Special characters are not available!', 'danger')
                return redirect(url_for('add'))

        return render_template('success.html')


@app.route('/filter')
@is_logged_in
def show_filters():
    classes = set()
    instructors = set()
    places = set()

    user = User.query.filter(User.username == session_flask['username']).first()

    for activity in Multisport.query.filter(Multisport.user_id == user.id):
        classes.add(activity.classes)
        instructors.add(activity.instructor)
        places.add(activity.place)

    return render_template('filters.html', classes=classes, instructors=instructors, places=places)


@app.route('/stats', methods=['POST', 'GET'])
@is_logged_in
def see_stats():
    if request.method == 'POST':
        school = request.form.getlist('school')
        classes = request.form.getlist('classes')
        instructors = request.form.getlist('instructors')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        user = User.query.filter(User.username == session_flask['username']).first()

        school, classes, instructors = check_if_all(school, classes, instructors, user)

        try:
            activities = filter_activities(school, classes, instructors, start_date, end_date, user)

        except DataError:
            flash('Select dates!', 'danger')
            return redirect(url_for('show_filters'))

        if not activities:
            flash('No activities, change filters', 'danger')
            return redirect(url_for('show_filters'))

        number_of_classes = len(activities)
        duration = count_duration(activities)
        savings = count_savings(activities)
        most_popular, least_popular = check_classes_popularity(school, classes, instructors, start_date, end_date, user)
        average_classes_rate, average_training_rate = count_ratings(activities)

    return render_template('stats.html', duration=duration, start_date=start_date, end_date=end_date, savings=savings,
                           number_of_classes=number_of_classes, most_popular=most_popular,
                           least_popular=least_popular, average_classes_rate=average_classes_rate,
                           average_training_rate=average_training_rate)


@app.route('/all_activities')
@is_logged_in
def see_activities():
    user = User.query.filter(User.username == session_flask['username']).first()
    activities = Multisport.query.filter(Multisport.user_id == user.id).order_by(Multisport.date.desc()).all()

    if activities:
        return render_template('all_activities.html', activities=activities)

    else:
        return render_template('all_activities.html')


@app.route('/edit_activity/<activity_id>', methods=['GET', 'POST'])
@is_logged_in
def edit_activity(activity_id):
    activity = Multisport.query.filter(Multisport.id == activity_id).first()

    form = ActivityForm(request.form)
    form.category.data = activity.category
    form.classes.data = activity.classes
    form.instructor.data = activity.instructor
    form.place.data = activity.place
    form.duration.data = activity.duration
    form.price.data = activity.price
    form.date.data = activity.date
    form.classes_rate.data = activity.classes_rate
    form.training_rate.data = activity.training_rate

    if request.method == 'POST' and form.validate():
        category = request.form['category']
        classes = request.form['classes']
        instructor = request.form['instructor']
        place = request.form['place']
        duration = request.form['duration']
        price = request.form['price']
        date = request.form['date']
        classes_rate = request.form['classes_rate']
        training_rate = request.form['training_rate']

        activity.category = category
        activity.classes = classes
        activity.instructor = instructor
        activity.place = place
        activity.duration = duration
        activity.price = price
        activity.date = date
        activity.classes_rate = classes_rate
        activity.training_rate = training_rate

        db.session.commit()

        flash('Data updated', 'success')
        return redirect(url_for('see_activities'))

    return render_template('edit_activity.html', form=form)


@app.route('/delete_activity/<activity_id>', methods=['POST'])
@is_logged_in
def delete_activity(activity_id):
    activity = Multisport.query.filter(Multisport.id == activity_id).first()
    db.session.delete(activity)
    db.session.commit()
    flash('Activity deleted', 'success')
    return redirect(url_for('see_activities'))
