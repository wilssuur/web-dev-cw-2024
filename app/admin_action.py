from flask import render_template, request, redirect, url_for, flash, Blueprint
from flask_login import login_required
from mysql.connector.errors import DatabaseError
from authorization import can_user
from app import db_connector
from datetime import datetime
import math

bp = Blueprint('admin', __name__, url_prefix='/admin')
PAGE_COUNT = 5

@bp.route('/awaiting')
@login_required
@can_user('managing')
def awaiting():
    page_number = request.args.get('page_number', 1, type = int)
    current_time = datetime.now()
    query = ("SELECT events.id, events.name, events.date_start, events.time_start, "
            "users.first_name as first_name, users.last_name as last_name "
            "FROM events JOIN users ON events.user_id = users.id "
            "WHERE events.status_id = 3 "
            f"LIMIT {PAGE_COUNT} OFFSET {PAGE_COUNT * (page_number - 1)}")

    query_count = ("SELECT COUNT(*) as count FROM events WHERE events.status_id = 3")

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        data = cursor.fetchall()

        cursor.execute(query_count)
        total_count = cursor.fetchone().count

        all_page = math.ceil(total_count / PAGE_COUNT)
        start_page = max(page_number - 3, 1)
        end_page = min(page_number + 3, all_page)

    return render_template('admin/awaiting.html',
                           events=data, 
                           start_page=start_page, 
                           end_page=end_page, 
                           page_number=page_number, 
                           total_pages=total_count/PAGE_COUNT,
                           current_time=current_time,
                           datetime=datetime)

@bp.route('/accept_event/<int:event_id>', methods=['POST'])
@login_required
@can_user('managing')
def accept_event(event_id):
    query = ("UPDATE events SET status_id = 1 WHERE id = %s")
    try:
        with db_connector.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (event_id,))
                conn.commit()
        flash('Мероприятие принято', 'success')
    except DatabaseError:
        flash(f'Ошибка база данных', 'danger')

    return redirect(url_for('admin.awaiting'))

@bp.route('/reject_event/<int:event_id>', methods=['POST'])
@login_required
@can_user('managing')
def reject_event(event_id):
    query = ("UPDATE events SET status_id = 2 WHERE id = %s")
    try:
        with db_connector.connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (event_id,))
                conn.commit()
        flash('Мероприятие отклонено', 'success')

    except DatabaseError as e:
        flash(f'Ошибка база данных', 'danger')

    return redirect(url_for('admin.awaiting'))

@bp.route('/ready')
@login_required
@can_user('managing')
def ready():
    page_number = request.args.get('page_number', 1, type = int)
    current_time = datetime.now()
    query = ("SELECT events.name, events.date_start, events.time_start, status.name as status, "
             "users.first_name as first_name, users.last_name as last_name "
             "FROM events JOIN status ON events.status_id = status.id JOIN users ON events.user_id = users.id "
             "WHERE events.status_id = 1 or events.status_id = 2 "
             f"LIMIT {PAGE_COUNT} OFFSET {PAGE_COUNT * (page_number - 1)}")
    
    query_count = ("SELECT COUNT(*) as count FROM events WHERE events.status_id = 1 or events.status_id = 2")
    try:
        with db_connector.connect().cursor(named_tuple=True) as cursor:
            cursor.execute(query)
            data = cursor.fetchall()

            cursor.execute(query_count)
            total_count = cursor.fetchone().count

            all_page = math.ceil(total_count / PAGE_COUNT)
            start_page = max(page_number - 3, 1)
            end_page = min(page_number + 3, all_page)

        return render_template('admin/ready.html', 
                               events=data, 
                               start_page=start_page, 
                               end_page=end_page, 
                               page_number=page_number, 
                               total_pages=total_count/PAGE_COUNT,
                               current_time=current_time,
                               datetime=datetime)
    except DatabaseError:
        flash("Произошла ошибка БД", category="danger")
        return render_template('admin/ready.html', events=data, start_page=1, end_page=1, page_number=1)


@bp.route('/archive')
@login_required
@can_user('managing')
def archive():
    query = ("SELECT events.id, events.name, events.short_desc, events.date_start, events.time_start, "
             "events.duration, events.image_filename FROM events WHERE events.date_start < NOW()")

    with db_connector.connect().cursor(named_tuple=True) as cursor:
        cursor.execute(query)
        data = cursor.fetchall()

    return render_template('admin/archive.html', events=data)