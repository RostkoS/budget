from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from models import Family, Record, Category, Tag, User,record_tags
from utils import get_user, get_family_id, export_csv
from models import db
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

records = Blueprint('records', __name__)
@records.route('/add', methods=['GET', 'POST'])
def add_record():
    if not session.get('user_id'):
        return redirect('/login')

    user_id = session['user_id']
    user = User.query.get(user_id)
    categories = Category.query.filter_by(family_id=user.family_id).all()

    existing_tags = Tag.query.all()  

    if request.method == 'POST':
        amount = request.form['amount']
        category = request.form.get('category')
        new_category = request.form.get('new_category') 
        print(new_category)
        record_type = request.form['type']
        record_date = request.form['date']
        tag_names = request.form.get('tags', '').split(',')  

        if new_category: 
            existing_category = Category.query.filter_by(name=new_category).first()
            if not existing_category:
                new_cat = Category(name=new_category, family_id=user.family_id) 
                db.session.add(new_cat)
                db.session.commit() 
                category = new_category  
        new_record = Record(
            amount=amount, category=category, type=record_type,
            date=record_date, user_id=user.id, family_id=user.family_id
        )
        db.session.add(new_record)

        tag_objects = []
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            tag_objects.append(tag)

        db.session.commit()

        new_record.tags.extend(tag_objects)
        db.session.commit() 

        return redirect('/view')

    return render_template('add_record.html', categories=categories, existing_tags=existing_tags)


@records.route('/edit_record/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    if not get_user():
        return redirect('/login')

    family_id = get_family_id()
    if not family_id:
        return redirect('/')

    record = Record.query.filter_by(id=record_id, family_id=family_id).first()
    if not record:
        return "Record not found or you do not have permission to edit this record."

    categories = Category.query.filter_by(family_id=family_id).all()
    existing_tags = Tag.query.all()

    if request.method == 'POST':
        record.amount = request.form['amount']
        record_type = request.form['type']
        record_date = request.form['date']
        category = request.form.get('category')  
        new_category = request.form.get('new_category') 

        if new_category:
            existing_category = Category.query.filter_by(name=new_category, family_id=family_id).first()
            if not existing_category:
                new_cat = Category(name=new_category, family_id=family_id)
                db.session.add(new_cat)
                db.session.commit()
                category = new_cat.name  

        record.category = category  
        record.type = record_type
        record.date = record_date

        tag_names = request.form.get('tags', '').split(',')
        record.tags.clear() 

        tag_objects = []
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            tag_objects.append(tag)

        db.session.commit()

        record.tags.extend(tag_objects)
        db.session.commit()

        return redirect('/view')

    return render_template('edit_record.html', record=record, categories=categories, existing_tags=existing_tags)

@records.route('/delete_record/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    if not session.get('user_id'):
        flash("You need to be logged in to delete records.", "warning")
        return redirect('/login')

    user_id = session['user_id']
    record = Record.query.filter_by(id=record_id, user_id=user_id).first()

    if not record:
        flash("Record not found or you don't have permission to delete it.", "danger")
        return redirect('/view')

    db.session.delete(record)
    db.session.commit()
    flash("Record deleted successfully!", "success")

    return redirect('/view')


@records.route('/view', methods=['GET'])
def view_records():
    period = request.args.get('period', 'місяць')
    category = request.args.get('category', '')
    record_type = request.args.get('record_type', '')
    tag_filter = request.args.get('tag', '') 
    sort_by_family = request.args.get('sort_by_family', 'email')
    sort_order_family = request.args.get('sort_order_family', 'asc')

    sort_by = request.args.get('sort_by', 'date')  
    sort_order = request.args.get('sort_order', 'desc')

    family_id = get_family_id()

    categories = db.session.query(Category).filter(Category.family_id == family_id).all()

    family_members_query = db.session.query(User).filter(User.family_id == family_id)

    records_query = db.session.query(Record).filter(Record.family_id == family_id)

    if category:
        records_query = records_query.filter(Record.category == category)

    if record_type:
        records_query = records_query.filter(Record.type == record_type)

    if tag_filter:
        records_query = records_query.join(record_tags).join(Tag).filter(Tag.name == tag_filter)

    records = records_query.all()

    if category:
        family_members_query = family_members_query.join(Record).filter(Record.category == category)

    family_members = family_members_query.all()

    user_financials = {}
    for member in family_members:
        member_records = db.session.query(Record).filter(
            Record.family_id == family_id,
            Record.user_id == member.id
        )
        
        if category:
            member_records = member_records.filter(Record.category == category)

        if record_type:
            member_records = member_records.filter(Record.type == record_type)

        member_records = member_records.all()

        income = sum(r.amount for r in member_records if r.type == 'дохід')
        expenses = sum(r.amount for r in member_records if r.type == 'витрата')
        balance = income - expenses

        user_financials[member.id] = {
            'total_income': income,
            'total_expenses': expenses,
            'net_balance': balance
        }

    family_sort_columns = {
        'email': lambda x: x.email,
        'total_income': lambda x: user_financials[x.id]['total_income'],
        'total_expenses': lambda x: user_financials[x.id]['total_expenses'],
        'net_balance': lambda x: user_financials[x.id]['net_balance'],
    }

    if sort_by_family in family_sort_columns:
        family_members = sorted(
            family_members, 
            key=family_sort_columns[sort_by_family], 
            reverse=(sort_order_family == 'desc')
        )

    valid_sort_columns = {
        'date': Record.date,
        'amount': Record.amount,
        'category': Record.category,
        'type': Record.type,
    }

    if sort_by in valid_sort_columns:
        column = valid_sort_columns[sort_by]
        records = records_query.order_by(column.desc() if sort_order == 'desc' else column.asc()).all()
    else:
        records = records_query.order_by(Record.date.asc()).all()

    tags = Tag.query.all()

    total_income = sum(record.amount for record in records if record.type == 'дохід')
    total_expenses = sum(record.amount for record in records if record.type == 'витрата')
    net_balance = total_income - total_expenses

    return render_template(
        'view.html', 
        records=records, 
        family_members=family_members,
        user_financials=user_financials, 
        period=period, 
        category=category, 
        record_type=record_type,
        sort_by_family=sort_by_family,
        sort_order_family=sort_order_family,
        sort_by=sort_by,  
        sort_order=sort_order, 
        categories=categories,
        tags=tags,
        total_income=total_income, 
        total_expenses=total_expenses, 
        net_balance=net_balance
    )



@records.route('/clear_filters')
def clear_filters():
    return redirect(url_for('records.view_records')) 

@records.route('/export', methods=['GET'])
def export():
    if not session.get('user_id'):
        return redirect('/login')

    family_id = get_family_id()
    if not family_id:
        return "You are not part of a family.", 400

    period = request.args.get('period', 'місяць')
    category = request.args.get('category', '').strip()
    record_type = request.args.get('record_type', 'Всі').strip()
    tag_filter = request.args.get('tag', '')

    now = datetime.now()

    if period == 'місяць':
        start_date = now.replace(day=1)
    elif period == 'півроку':
        start_date = now - timedelta(days=183)
    elif period == 'рік':
        start_date = now - timedelta(days=364)
    else:
        start_date = now 

    records_query = (
    db.session.query(Record)
    .join(User, Record.user_id == User.id)
    .filter(Record.family_id == family_id)
    .filter(Record.date >= start_date, Record.date <= now)
    .options(joinedload(Record.tags)) 
)


    if category:
        records_query = records_query.filter(Record.category == category)

    if record_type and record_type != 'Всі':
        records_query = records_query.filter(Record.type == record_type)

    if tag_filter:
        records_query = records_query.join(record_tags).join(Tag).filter(Tag.name == tag_filter)

    records = records_query.all()

    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = now.strftime("%Y-%m-%d")
    filename = f"report-{start_date_str}-to-{end_date_str}.csv"

    return export_csv(records, filename)