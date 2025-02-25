from flask import Blueprint, session, url_for, flash, request, redirect
from models import Invite, User
from utils import get_user, get_family_id, get_user_email
import uuid
from models import db

family = Blueprint('family', __name__)

@family.route('/invite', methods=['POST'])
def invite():
    if 'user_id' not in session:
        flash("You need to be logged in to send invitations.", "danger")
        return redirect(url_for('login'))
    
    family_id = get_family_id()
    if not family_id:
        flash("You must be part of a family to send invitations.", "danger")
        return redirect(url_for('auth.profile'))
    
    invitee_email = request.form.get('invitee_email')
    
    if invitee_email == get_user_email():  
        flash("You cannot invite yourself.", "danger")
        return redirect(url_for('auth.profile'))
    
    existing_invite = Invite.query.filter_by(family_id=family_id, email=invitee_email).first()
    if existing_invite:
        flash("This email has already been invited to your family.", "danger")
        return redirect(url_for('auth.profile'))
    
    token = str(uuid.uuid4())
    
    invite = Invite(family_id=family_id, email=invitee_email, token=token)
    db.session.add(invite)
    db.session.commit()
    
    flash(f"Invitation sent to {invitee_email}.", "success")
    return redirect(url_for('auth.profile'))


@family.route('/accept_invite/<token>', methods=['POST'])
def accept_invite(token):
    user = User.query.get(get_user())  
    if not user: 
        return redirect('/login')

    invite = Invite.query.filter_by(token=token, used=False).first()
    if not invite:
        return "Invalid or already used invite."

    user.family_id = invite.family_id  

    invite.used = True  

    db.session.commit()

    return redirect('/profile')
