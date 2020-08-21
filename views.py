from app import app, db, Multisport, User
from flask import render_template, request, redirect, url_for, flash
from flask import session as session_flask
from wtforms import Form, StringField, DateTimeField, IntegerField, validators, PasswordField
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker
from passlib.hash import sha256_crypt
from operator import itemgetter
from datetime import datetime
from functools import wraps

engine = create_engine('mysql://root:23101996Kamila@localhost/multisport', echo=False)
Session = sessionmaker(bind=engine)
session = Session()


class ActivityForm(Form):
    category = StringField('Category', [validators.Length(min=1, max=200)])
    classes = StringField('Classes', [validators.Length(min=1, max=200)])
    place = StringField('Place', [validators.Length(min=1, max=200)])
    instructor = StringField('Instructor')
    duration = IntegerField('Duration')
    price = IntegerField('Price')
    date = DateTimeField('Date')
    classes_rate = IntegerField('Classes rate')
    training_rate = IntegerField('Training rate')


class RegisterForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=70)])
    email = StringField('Email', [validators.Length(min=1, max=200)])
    gender = StringField('Gender', [validators.Length(min=1, max=70)])
    password = PasswordField('Password', [
        validators.Length(min=8, max=50),
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm password')


class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=70)])
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
        redirect(url_for('/index'))

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

                flash('You are now logged in', 'success')
                # app.logger.info('PASSWORD MATCHED')  <- shows up only in console!
                return redirect(url_for('see_activities'))
            else:
                error = 'Invalid login'
                return render_template('/login.html', error=error)

    return render_template('login.html', form=form)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session_flask:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login.', 'danger')
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


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/activities')
@is_logged_in
def add():
    return render_template('activities.html')


@app.route('/filter')
@is_logged_in
def show_stats():
    classes = set()
    instructors = set()
    places = set()

    for activity in Multisport.query.all():
        classes.add(activity.classes)
        instructors.add(activity.instructor)
        places.add(activity.place)

    return render_template('filters.html', classes=classes, instructors=instructors, places=places)


@app.route('/submit', methods=['GET', 'POST'])
@is_logged_in
def submit():
    if request.method == 'POST':
        gender = request.form.get('gender')
        category = request.form.get('category')
        classes = request.form.get('classes')
        place = request.form.get('place')
        instructor = request.form.get('instructor')
        duration = request.form.get('duration')
        price = request.form.get('price')
        date = request.form.get('date')
        classes_rate = request.form.get('classes_rate')
        training_rate = request.form.get('training_rate')

        multi = Multisport(gender=gender, category=category, classes=classes, place=place, instructor=instructor,
                           duration=duration, price=price, date=date, classes_rate=classes_rate,
                           training_rate=training_rate)
        db.session.add(multi)
        db.session.commit()
        return render_template('success.html')


@app.route('/stats', methods=['POST', 'GET'])
@is_logged_in
def see_stats():
    if request.method == 'POST':
        school = request.form.getlist('school')
        classes = request.form.getlist('classes')
        instructors = request.form.getlist('instructors')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        results = Multisport.query.filter(Multisport.classes.in_(classes), Multisport.place.in_(school),
                                          Multisport.instructor.in_(instructors), Multisport.date >= start_date,
                                          Multisport.date <= end_date).all()
        num = len(results)
        time = 0
        cost = 0

        class_categories = session.query(func.count(Multisport.classes), Multisport.classes).group_by(
            Multisport.classes).filter(Multisport.classes.in_(classes), Multisport.place.in_(school),
                                       Multisport.instructor.in_(instructors), Multisport.date >= start_date,
                                       Multisport.date <= end_date).all()

        class_categories = sorted(class_categories, key=itemgetter(0))

        if len(class_categories) > 1:
            least_popular = class_categories[0][1]
        else:
            least_popular = '---'

        most_popular = class_categories[-1][1]

        for category in sorted(class_categories, key=itemgetter(0)):
            print('style: {}, {} classes'.format(category[1], category[0]))

        for r in results:
            time += r.duration
            cost += r.price
        savings = cost - 172.50

        class_rate_sum = 0
        training_rate_sum = 0
        for r in results:
            class_rate_sum += r.classes_rate
            training_rate_sum += r.training_rate
        average_class_rate = round(class_rate_sum / num, 2)
        average_training_rate = round(training_rate_sum / num, 2)

    return render_template('stats.html', time=time, start_date=start_date, end_date=end_date, savings=savings, num=num,
                           most_popular=most_popular,
                           least_popular=least_popular, average_class_rate=average_class_rate,
                           average_training_rate=average_training_rate)


@app.route('/all_activities')
@is_logged_in
def see_activities():
    activities = Multisport.query.all()

    if activities:
        return render_template('all_activities.html', activities=activities)

    else:
        print('no activities in database')


@app.route('/edit_activity/<id>', methods=['POST', 'GET'])
@is_logged_in
def edit_activity(id):
    activity = Multisport.query.filter(Multisport.id == id).first()

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

@app.route('/delete_activity/<id>', methods=['POST'])
@is_logged_in
def delete_activity(id):
    activity = Multisport.query.filter(Multisport.id == id).first()
    db.session.delete(activity)
    db.session.commit()
    flash('Activity deleted', 'success')
    return redirect(url_for('see_activities'))


