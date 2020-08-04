from app import app, db, Multisport
from flask import render_template, request



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
def add():
    return render_template('activities.html')

@app.route('/filter')
def show_stats():
    classes = set()
    instructors = set()
    places = set()

    for activity in Multisport.query.all():
        classes.add(activity.classes)
        instructors.add(activity.instructor)
        places.add(activity.place)

    return render_template('filters.html', classes= classes, instructors= instructors, places= places)

@app.route('/submit', methods= ['GET', 'POST'])
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
def see_stats():
    if request.method == 'POST':
        school = request.form.getlist('school')
        classes = request.form.getlist('classes')
        instructors = request.form.getlist('instructors')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        print(school, classes, instructors, start_date, end_date)
        results= Multisport.query.filter(Multisport.classes.in_(classes), Multisport.place.in_(school),
                                         Multisport.instructor.in_(instructors), Multisport.date >= start_date,
                                         Multisport.date <= end_date).all()
        num = Multisport.query.filter(Multisport.classes.in_(classes), Multisport.place.in_(school),
                                         Multisport.instructor.in_(instructors), Multisport.date >= start_date,
                                         Multisport.date <= end_date).count()
        time = 0
        cost = 0

        for r in results:
            print(r.place, r.classes, r.instructor, r.date)
            time += r.duration
            cost += r.price
        savings = cost - 172.50
    return render_template('stats.html', time=time, savings=savings, num=num)
