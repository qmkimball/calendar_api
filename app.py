# from typing_extensions import Self
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')

db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)

# MONTH MODEL
class Month(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    start_day = db.Column(db.Integer, nullable=False)
    days_in_month = db.Column(db.Integer, nullable=False)
    days_in_previous_month = db.Column(db.Integer, nullable=False)
    reminders = db.relationship('Reminder', backref='month', cascade="all, delete, delete-orphan")

    def __init__(self, name, year, start_day, days_in_month, days_in_previous_month):
        self.name = name
        self.year = year
        self.start_day = start_day
        self.days_in_month = days_in_month
        self.days_in_previous_month = days_in_previous_month



# REMINDER MODEL
class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    date = db.Column(db.Integer, nullable=False)
    month_id = db.Column(db.Integer, db.ForeignKey('month.id'), nullable=False)

    def __init__(self, content, date, month_id):
        self.content = content
        self.date = date
        self.month_id = month_id


class ReminderSchema(ma.Schema):
    class Meta:
        fields = ("id", "content", "date", "month_id")
    
reminder_schema = ReminderSchema()
multiple_reminder_schema = ReminderSchema(many=True)


# MOVIE SCHEMA
class MonthSchema(ma.Schema):
    class Meta: 
        fields = ("id", "name", "year", "start_day", "days_in_month", "days_in_previous_month", "reminders")

    reminders = ma.Nested(multiple_reminder_schema )
    
month_schema = MonthSchema()
multiple_month_schema = MonthSchema(many=True)

# POST REQUEST
@app.route("/month/add", methods=["POST"])
def add_month():
    if request.content_type != "application/json":
        return jsonify("Error: content must be in JSON")

    post_data = request.get_json()
    name = post_data.get("name")
    year = post_data.get("year")
    start_day = post_data.get("start_day")
    days_in_month = post_data.get("days_in_month")
    days_in_previous_month = post_data.get("days_in_previous_month")

    existing_month_check = db.session.query(Month).filter(Month.name == name).filter(Month.year == year).first()
    if existing_month_check is not None: 
        return jsonify("Error: Month already exists.")

    new_record = Month(name, year, start_day, days_in_month, days_in_previous_month)
    db.session.add(new_record)
    db.session.commit()

    return jsonify(month_schema.dump(new_record))



# GET REQUEST
@app.route("/month/get", methods=["GET"])
def get_all_months():
    months = db.session.query(Month).all()
    return jsonify(multiple_month_schema.dump(months))

@app.route("/month/get/<id>", methods=["GET"])
def get_month_by_id(id):
    month = db.session.query(Month).filter(Month.id == id).first()
    return jsonify(month_schema.dump(month))


@app.route("/month/get/<year>/<name>", methods=["GET"])
def get_month_by_year_and_name(year, name):
    month = db.session.query(Month).filter(Month.year == year).filter(Month.name == name).first()
    return jsonify(month_schema.dump(month))

# REMINDER POST REQUEST
@app.route("/reminder/add", methods=["POST"])
def add_reminder():
    if request.content_type != "application/json":
        return jsonify("Error: content must be in JSON")

    post_data = request.get_json()
    content = post_data.get("content")
    date = post_data.get("date")
    month_id = post_data.get("month_id")

    exisiting_reminder_check = db.session.query(Reminder).filter(Reminder.date == date).filter(Reminder.month_id == month_id).first()
    if exisiting_reminder_check is not None: 
        return jsonify("Error: Reminder already exists")

    new_record = Reminder(content, date, month_id)
    db.session.add(new_record)
    db.session.commit()
    
    return jsonify(reminder_schema.dump(new_record))

@app.route("/month/add/multiple", methods=["POST"])
def add_multiple_months():
    if request.content_type != "application/json":
        return jsonify("Error: content must be in JSON")
    
    post_data = request.get_json()
    data = post_data.get("data")

    new_records = []
    for month in data:
        name = month.get("name")
        year = month.get("year")
        start_day = month.get("start_day")
        days_in_month = month.get("days_in_month")
        days_in_previous_month = month.get("days_in_previous_month")

        existing_month_check = db.session.query(Month).filter(Month.name == name).filter(Month.year == year).first()
        if existing_month_check is not None:
            return jsonify("Error: month already exists")
        else:
            new_record = Month(name, year, start_day, days_in_month, days_in_previous_month)
            db.session.add(new_record)
            db.session.commit()
            new_records.append(new_record)

    return jsonify(multiple_month_schema.dump(new_records))


@app.route("/month/delete/<id>", methods=["DELETE"])
def delete_month_by_id(id):
    month_to_delete = db.session.query(Month).filter(Month.id == id).first()
    db.session.delete(month_to_delete)
    db.session.commit()
    return jsonify(month_schema.dump(month_to_delete))

@app.route("/reminder/update/<month_id>/<date>", methods=["PUT"])
def update_reminder(month_id, date):
    if request.content_type != "application/json":
        return jsonify("Error: Please send as JSON")

    put_data = request.get_json()
    content = put_data.get("content")

    reminder = db.session.query(Reminder).filter(Reminder.month_id == month_id).filter(Reminder.date == date).first()

    reminder.content = content
    db.session.commit()

    return jsonify(reminder_schema.dump(reminder))







if __name__ == "__main__":
    app.run(debug=True)