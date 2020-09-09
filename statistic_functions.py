from models import Multisport
from app import session
from operator import itemgetter
from sqlalchemy import func


def check_if_all(school, classes, instructors, user):

    if 'all' in school:
        for activity in Multisport.query.filter(Multisport.user_id == user.id):
            school.append(activity.place)
        school = set(school)

    if 'all' in classes:
        for activity in Multisport.query.filter(Multisport.user_id == user.id):
            classes.append(activity.classes)
        classes = set(classes)

    if 'all' in instructors:
        for activity in Multisport.query.filter(Multisport.user_id == user.id):
            instructors.append(activity.instructor)
        instructors = set(instructors)

    return school, classes, instructors


def filter_activities(school, classes, instructors, start_date, end_date, user):

    return Multisport.query.filter(Multisport.classes.in_(classes), Multisport.place.in_(school),
                                   Multisport.instructor.in_(instructors), Multisport.date >= start_date,
                                   Multisport.date <= end_date, Multisport.user_id == user.id).all()


def check_classes_popularity(school, classes, instructors, start_date, end_date, user):
    class_categories = session.query(func.count(Multisport.classes), Multisport.classes).group_by(
        Multisport.classes).filter(Multisport.classes.in_(classes), Multisport.place.in_(school),
                                   Multisport.instructor.in_(instructors), Multisport.date >= start_date,
                                   Multisport.date <= end_date, Multisport.user_id == user.id).all()

    class_categories = sorted(class_categories, key=itemgetter(0))

    most_popular = class_categories[-1][1]
    if len(class_categories) > 1:
        least_popular = class_categories[0][1]
    else:
        least_popular = '---'

    return most_popular, least_popular


def count_ratings(activities):
    classes_rate_sum = 0
    training_rate_sum = 0
    classes_num = 0
    trainings_num = 0
    for activity in activities:
        if activity.classes_rate:
            classes_rate_sum += activity.classes_rate
            classes_num += 1
        if activity.training_rate:
            training_rate_sum += activity.training_rate
            trainings_num += 1

    average_classes_rate = round(classes_rate_sum / classes_num, 2)
    average_training_rate = round(training_rate_sum / trainings_num, 2)
    return average_classes_rate, average_training_rate


def count_duration(activities):
    duration = 0
    for activity in activities:
        duration += activity.duration
    return duration


def count_savings(activities):
    cost = 0
    for activity in activities:
        cost += activity.price
    savings = cost - 172.50
    return savings

