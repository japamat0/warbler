"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from models import db, User, Message, Like, FollowersFollowee

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

# db.create_all()


class UserModelTestCase(TestCase):
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

        self.client = app.test_client()

    def tearDown(self):

        db.session.close()
        db.drop_all(bind=None)

    def test_user_creation(self):
        """Does basic model Userwork?"""

        # print(User.query.all())
        # print(Like.query.all())
        # print(Message.query.all())
        # print(FollowersFollowee.query.all())

        # check to see if total is correct
        self.assertEqual(User.query.count(), 6)

        #check to see if 1 row is correct
        self.assertEqual(User.query.first().email, "test0@test.com")
        self.assertEqual(User.query.first().username, "testuser0")
        
        #check to see if User.create fails to create user when validators fail
        user_x = User(username="testuser0", email="test_email0@gmail.com", password="admin1234")
        db.session.add(user_x)
        self.assertRaises(IntegrityError, db.session.commit)
        
        user_y = User(username="", email="test_email0@gmail.com", password="admin1234")
        db.session.add(user_y)
        self.assertRaises(InvalidRequestError, db.session.commit)

        # check to see that errors raised when null values passed

    def test_user_authentication(self):
        """ does user authentication work """

        user_1 = User.query.filter_by(id=1).first()
        user_2 = User.query.filter_by(id=2).first()

        self.assertEqual(User.authenticate("testuser1", "HASHED_PASSWORD"), user_2)
        self.assertEqual(User.authenticate("testuser0", "BAD_PASS"), False)

    def test_like_model(self):
        """Does basic model Like work?"""

        # check to see if total is correct
        self.assertEqual(Like.query.count(),5)


        #check to see if 1 row is correct
        self.assertEqual(Like.query.first().user_id, 1)
        self.assertEqual(Like.query.first().message_id, 2)

    def test_message_model(self):
        """Does basic model Message work?"""

        # check to see if total is correct
        self.assertEqual(Message.query.count(),6)

        #check to see if 1 row is correct
        self.assertEqual(Message.query.first().text, 'I love numer 0')
        self.assertEqual(Message.query.first().user_id, 1)

    def test_ff_model(self):
        """Does basic model FF work?"""

        # check to see if total is correct
        self.assertEqual(FollowersFollowee.query.count(),5)

        #check to see if 1 row is correct
        self.assertEqual(FollowersFollowee.query.first().followee_id, 1)
        self.assertEqual(FollowersFollowee.query.first().follower_id, 2)

        # check to see user method is_following & is_followed_by works
        user_1 = User.query.filter_by(id=1).first()
        user_2 = User.query.filter_by(id=2).first()
        user_4 = User.query.filter_by(id=4).first()

        self.assertEqual(user_2.is_followed_by(user_1), True)
        self.assertEqual(user_1.is_following(user_2), True)
        self.assertEqual(user_2.is_followed_by(user_4), False)
        self.assertEqual(user_1.is_following(user_4), False)

