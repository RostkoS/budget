from flask import Blueprint, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import Invite, User, Family
from utils import get_user
from models import db

auth = Blueprint('auth', __name__)

@auth.route('/')
def index():
    if not get_user():
        return redirect('/login')
    return redirect('/view')


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists", 'danger')
            return render_template('register.html')

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()

        family = Family(name=f"Family of {email}", owner_id=user.id)
        db.session.add(family)
        db.session.commit()

        user.family_id = family.id
        db.session.commit()

        session['user_id'] = user.id
        session['family_id'] = family.id

        return redirect('/')

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('/profile') 

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['family_id'] = user.family_id
            return redirect('/profile')
        
        flash('Invalid email or password. Please try again.', 'danger')
        
    return render_template('login.html')

@auth.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

@auth.route('/profile', methods=['GET'])
def profile():
    if not get_user():
        return redirect('/login')

    user_id = get_user()
    user = User.query.get(user_id)
    invitations = Invite.query.filter_by(email=user.email, used=False).all()
    for invite in invitations:
        family = Family.query.filter_by(id=invite.family_id).first() 
        invite.family_name = family.name if family else None 


    return render_template('profile.html', email=user.email, family_name=user.family.name if user.family else None, invitations=invitations)

