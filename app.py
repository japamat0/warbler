import os

from flask import Flask, render_template, request, flash, redirect, session, g, abort, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from itertools import chain

from forms import UserAddForm, LoginForm, MessageForm, EditUserForm, CommentForm
from models import db, connect_db, User, Message, Like, Comment

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

# Get DB_URI from environ variable (useful for production/testing) or,
# if not set there, use development local db.
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgres:///warbler'))

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
toolbar = DebugToolbarExtension(app)

connect_db(app)


##############################################################################
# User signup/login/logout


@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If the there already is a user with that username: flash message
    and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    flash("you have been successfully logged out!")
    return redirect('/')


##############################################################################
# Like routes

@app.route('/like', methods=["POST"])
def add_like():

    msg_id = request.json.get('msg-id')
    is_existing = Like.query.filter_by(message_id=msg_id, user_id=g.user.id).first()
    msg = Message.query.filter_by(id=msg_id).first_or_404()

    if is_existing is None:
        like = Like(user_id=g.user.id, message_id=msg_id)
        db.session.add(like)
        db.session.commit()
    else:
        db.session.delete(is_existing)
        db.session.commit()

    resp = {
        "likes": len(msg.likes),
        "is-liked": msg.is_liked_by(g.user.id),
        "msgId": msg.id,
        "userImg": g.user.image_url
    }
    return jsonify(resp)


@app.route('/likes')
def render_likes_page():

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")    

    liked_msg_id = [l.message_id for l in g.user.likes]

    messages = Message.query.filter(Message.id.in_(liked_msg_id)).order_by(Message.timestamp.desc()).all()

    return render_template('/users/likes.html', messages=messages, user=g.user)



##############################################################################
# General user routes:

@app.route('/users')
def list_users():
    """Page with listing of users.

    Can take a 'q' param in querystring to search by that username.
    """

    search = request.args.get('q')

    if not search:
        users = User.query.all()
    else:
        users = User.query.filter(User.username.like(f"%{search}%")).all()

    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    user = User.query.get_or_404(user_id)

    # snagging messages in order from the database;
    # user.messages won't be in order by default
    messages = (Message
                .query
                .filter(Message.user_id == user_id)
                .order_by(Message.timestamp.desc())
                .limit(100)
                .all())

    return render_template('users/show.html', user=user, messages=messages)


@app.route('/users/<int:user_id>/following')
def show_following(user_id):
    """Show list of people this user is following."""


    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    return render_template('users/following.html', user=user, form=form)


@app.route('/users/<int:user_id>/followers')
def users_followers(user_id):
    """Show list of followers of this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/followers.html', user=user)


@app.route('/users/follow/<int:follow_id>', methods=['POST'])
def add_follow(follow_id):
    """Add a follow for the currently-logged-in user."""

    followee = User.query.get(follow_id)
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    if g.user.is_following(followee):
        g.user.following.remove(followee)
    else:
        g.user.following.append(followee)
    db.session.commit()

    load = {
        "followeeId": followee.id,
        "isFollowing": g.user.is_following(followee)
    }

    return jsonify(load)


@app.route('/users/stop-following/<int:follow_id>', methods=['POST'])
def stop_following(follow_id):
    """Have currently-logged-in-user stop following this user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.commit()

    return redirect(f"/users/{g.user.id}/following")


@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    ## if user not logged in, redirect
    if not g.user:
        return redirect('/')

    form = EditUserForm(obj=g.user)

    if form.validate_on_submit():
        pw = form.password.data
        user = User.authenticate(g.user.username, pw)  # returns user or false

        if user:

            for k, v in form.data.items():

                if k != 'csrf_token' and k != 'password':
                    setattr(user, k, v)
            db.session.commit()
            return redirect(f'/users/{g.user.id}')
        else:
            form.password.errors = ["invalid password"]

    return render_template('/users/edit.html', form=form)   


@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")


##############################################################################
# Comment routes:


@app.route('/messages/comments', methods=["POST"])
def add_comment():
    """ add comment to message """

    msg_id = request.json.get('msgId')
    text = request.json.get('text')

    comment = Comment(text=text, message_id=msg_id, user_id=g.user.id)
    db.session.add(comment)
    db.session.commit()

    return jsonify(comment.serialize())


##############################################################################
# Messages routes:

@app.route('/messages/new', methods=["GET", "POST"])
def messages_add():
    """Add a message:

    Show form if GET. If valid, update message and redirect to user page.
    """

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(text=form.text.data)
        g.user.messages.append(msg)
        db.session.commit()

        return redirect(f"/users/{g.user.id}")

    return render_template('messages/new.html', form=form)


@app.route('/messages/<int:message_id>', methods=["GET", "POST"])
def messages_show(message_id):
    """Show a message."""

    if request.method == "POST":
        msg = Message.query.get(message_id)
        serialized_msg = msg.serialize()
        return jsonify(serialized_msg)

    msg = Message.query.get_or_404(message_id)
    return render_template('messages/show.html', message=msg)


@app.route('/messages/<int:message_id>/delete', methods=["POST"])
def messages_destroy(message_id):
    """Delete a message."""

    msg = Message.query.get(message_id)

    if msg.user_id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect('/401'), 401
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    db.session.delete(msg)
    db.session.commit()


    return jsonify(message_id)



##############################################################################
# Homepage and error pages


@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent messages of followees
    """

    if g.user:
        following_users_id = [u.id for u in g.user.following]
        following_users_id.append(g.user.id)

        messages = Message.query.filter(Message.user_id.in_(following_users_id)).order_by(Message.timestamp.desc()).all()

        # import pdb; pdb.set_trace()
        # import pdb; pdb.set_trace()
        return render_template('home.html', messages=messages)

    else:
        return render_template('home-anon.html')


@app.errorhandler(401)
def show_401(error):
    return 'oof', 401
    
    #  Response('<Why access is denied string goes here...>', 401, {'WWW-Authenticate':'Basic realm="Login Required"'})


##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
