from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_required, current_user
from mysql.connector.errors import DatabaseError
from app import db_connector
from datetime import datetime
import math

bp = Blueprint('records', __name__, url_prefix='/records')
PAGE_COUNT = 5

@bp.route('/<int:event_id>/recording', methods=['POST'])
@login_required
def recording(event_id):
    record = {}
    record['user_id'] = current_user.id
    record["event_id"] = event_id
    query = "INSERT INTO records (user_id, event_id) VALUES (%(user_id)s, %(event_id)s)"

    try:
        with db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(query, record)
            db_connector.connect().commit()
            flash("Вы записались на мероприятие", category="success")
            return redirect(url_for('index'))

    except DatabaseError:
        flash("Ошибка базы данных", category="danger")
        db_connector.connect().rollback()
        return redirect(url_for('index'))
    

@bp.route('/records')
@login_required
def records():
    page_number = request.args.get('page_number', 1, type = int)
    current_time = datetime.now()
    query = ("SELECT events.id, events.name, events.id as event_id, events.short_desc, events.date_start, "
             "events.time_start, events.duration, events.user_id FROM events "
             "INNER JOIN records ON events.id = records.event_id "
             f"WHERE records.user_id = {current_user.id} and events.date_start > NOW()")

    query_count = ("SELECT COUNT(*) as count FROM events INNER JOIN records ON events.id = records.event_id "
                   f"WHERE records.user_id = {current_user.id} and events.date_start > NOW()")
    
    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        records = cursor.fetchall()

        cursor.execute(query_count)
        total_count = cursor.fetchone().count

        all_page = math.ceil(total_count / PAGE_COUNT)
        start_page = max(page_number - 3, 1)
        end_page = min(page_number + 3, all_page)

    return render_template('user/my_records.html',
                           records=records,
                           start_page=start_page, 
                           end_page=end_page, 
                           page_number=page_number, 
                           total_pages=total_count/PAGE_COUNT,
                           current_time=current_time,
                           datetime=datetime)