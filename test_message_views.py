"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, User, Message, Like, FollowersFollowee

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        # Create all tables
        db.create_all()

        # Add 6 test Users
        for i in range(6):

            u = User.signup(
                email=f"test{i}@test.com",
                username=f"testuser{i}",
                password="HASHED_PASSWORD",
                image_url="/static/images/default-pic.png"
            )
            db.session.add(u)
        db.session.commit()

        # Add 6 message
        for i in range(6):

            m = Message(
                text=f"I love numer {i}",
                user_id=i+1
            )
            db.session.add(m)
        db.session.commit()

        # Add 5 likes
        for i in range(5):

            like = Like(
                user_id=i+1,
                message_id=i+2
            )
            db.session.add(like)

        # Add 5 follower/followee relationship

        for i in range(5):

            ff = FollowersFollowee(
                followee_id=i+1,
                follower_id=i+2
            )
            db.session.add(ff)

        db.session.commit()
        self.testuser = User.query.get(1)

        self.client = app.test_client()

    def tearDown(self):

        db.session.close()
        db.drop_all(bind=None)

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            # make sure that it can post a message
            msg = Message.query.filter_by(id=7).first()
            self.assertEqual(msg.text, "Hello")

    def test_delete_message(self):
        """ can delete own and not others' messages """
        # print(f"\n{msgs}\n")

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        # test that we can delete our message
        resp = c.post("/messages/1/delete")
        self.assertEqual(resp.status_code, 302)

        # test that we can no longer access aforementioned message
        resp2 = c.get("/messages/1")
        self.assertEqual(resp2.status_code, 404)


        # test that we cannot delete other user's messgae
        resp3 = c.post("/messages/2/delete")
        self.assertEqual(resp3.status_code, 401)

        # test that we can no longer access aforementioned message
        resp2 = c.get("/messages/2")
        self.assertEqual(resp2.status_code, 200)



            
