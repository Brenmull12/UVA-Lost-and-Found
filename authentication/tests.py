from django.test import TestCase
from django.contrib.auth import get_user_model
from authentication.models import UserManager, User

# Welcome to the authentication testing file.

# The purpose of testing this project is to try to attack and fix as many potential bugs as possible before rollout.

# WHAT YOU NEED TO TEST:

# * Please create at least one test for all functionalities this module covers. 
# * ** This essentially just includes creating users (for now)
# * Make tests ensuring that the expected outcome occurs whenever its requirements are met, and also for when they are not met
# * ** This includes things like having the appropriate error message come up when invalid/insufficient information is uploaded
# * It's only necessary to write one test for each scenario, but all scenarios must be accounted for.
# * ** For example, if a function needs 4 different fields to be filled out in order to be valid, 2 are strings, and 2 are ints, only 3 tests need to be made.
# * ** *** One test for a valid input, one test for an invalid/empty int input, and one test for an invalid/empty string input. 

# IMPORTANT: You must include the keyword 'test' at the beginning of each test you write. 
# For example, creating a test called 'createUser_test' will NOT run, but a test called 'test_createUser' would run.


class AuthenticationTest(TestCase):

    def test_createUser_Success(self):
        User = get_user_model()
        email = "test@example.com"
        password = "testpassword"
        first_name = "John"
        last_name = "Doe"

        user = User.objects.create_user(email, password)

        user.first_name = first_name
        user.last_name = last_name
        user.save()
        
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.first_name, first_name)
        self.assertEqual(user.last_name, last_name)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_site_admin)

    # The way you test for exceptions is a little weird, I'd suggest looking at this page for more information and examples:
    #https://docs.djangoproject.com/en/5.0/topics/testing/tools/

    def test_createUserBlank_Failure(self):
        
        with self.assertRaisesMessage(ValueError, "Users must have an email address."):
            user = User.objects.create_user('', '')
