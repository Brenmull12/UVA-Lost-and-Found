import shutil

from django.test import TestCase, override_settings
from django.contrib.auth import get_user
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile, UploadedFile, InMemoryUploadedFile

from authentication.models import User

from .models import Location, Status, Tag, Item, ItemFile, Location_Category

# Welcome to the LostandFound testing file.

# The purpose of testing this project is to try to attack and fix as many potential bugs as possible before rollout.

# WHAT YOU NEED TO TEST:

# * Please create at least one test for all functionalities that a user can do. 
# * ** This includes things like posting and being able to click on items to view them. 
# * Make tests ensuring that the expected outcome occurs whenever its requirements are met, and also for when they are not met
# * ** This includes things like having the appropriate error message come up when invalid/insufficient information is uploaded
# * It's only necessary to write one test for each scenario, but all scenarios must be accounted for.
# * ** For example, if a function needs 4 different fields to be filled out in order to be valid, 2 are strings, and 2 are ints, only 3 tests need to be made.
# * ** *** One test for a valid input, one test for an invalid/empty int input, and one test for an invalid/empty string input. 

# IMPORTANT: You must include the keyword 'test' at the beginning of each test you write. 
# For example, creating a test called 'createUser_test' will NOT run, but a test called 'test_createUser' would run.


TEST_MEDIA = "TEST MEDIA"


class FoundItemReportTests(TestCase):
    def setUp(self):
        user = User.objects.create(email='example@example.com', first_name='Test', last_name='User')
        user.set_password('password')
        user.save()

        self.other_category = Location_Category.objects.create(name="OTHER")
        self.location_other = Location.objects.create(name='Other', category=self.other_category)

        self.academic = Location_Category.objects.create(name="Academic Buildings")
        self.location_thornton = Location.objects.create(name='Thornton Stacks', category=self.academic)

    def tearDown(self):
        User.objects.all().delete()
        Item.objects.all().delete()
        ItemFile.objects.all().delete()

        Location_Category.objects.all().delete()
        Location.objects.all().delete()

        try:
            shutil.rmtree(TEST_MEDIA)
        except OSError:
            pass

    def login(self):
        self.client.login(email='example@example.com', password='password')
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        return user

    @override_settings(MEDIA_ROOT=TEST_MEDIA)
    def test_report_common_user_with_files(self):
        user = self.login()

        item_name = "test item"
        description = "test description"

        location_category = self.academic.pk
        location = self.location_thornton

        date = timezone.now().date()
        email = user.email
        phone_number = "0000000000"
        tag = Tag.UMBRELLA.value
        files = [SimpleUploadedFile("images/emo_mark_sherriff.png", b"file_content", content_type='image/png'),
                 SimpleUploadedFile("images/Kona Graduate.JPG", b"file_content", content_type="image/jpeg"),
                 # SimpleUploadedFile("images/IMG_1967.HEIC", b"file_content", content_type="image/heic"),
                 SimpleUploadedFile("images/Test Document.pdf", b"file_content", content_type="application/pdf"),
                 SimpleUploadedFile("images/TestTXT.txt", b"file_content", content_type="text/plain")]

        self.client.post(reverse("items:report_found"),
                         data={"item_name": item_name,
                               "description": description,
                               "location_category": location_category,
                               "location": location.pk,
                               "date": date,
                               "email": email,
                               "phone_number": phone_number,
                               "tag": tag,
                               "files": files
                               }
                         )

        self.assertEqual(Item.objects.count(), 1)
        self.assertEqual(ItemFile.objects.count(), len(files))
        found_item = Item.objects.first()

        self.assertEqual(found_item.user, user)

        self.assertEqual(found_item.item_name, item_name)
        self.assertEqual(found_item.description, description)
        self.assertEqual(found_item.location, location)
        self.assertEqual(found_item.tag, tag)
        self.assertEqual(found_item.date, date)

        self.assertEqual(found_item.email, email)
        self.assertEqual(found_item.phone_number, phone_number)

        self.assertEqual(found_item.status, Status.NEW)
        self.assertEqual(found_item.expiration_date, (timezone.now() + timezone.timedelta(days=30)).date())

        for file in ItemFile.objects.all():
            self.assertEqual(file.item, found_item)
            self.assertTrue(file.file)

    def test_report_anonymous_user_no_files(self):
        item_name = "test item"
        description = "test description"
        location_category = self.academic.pk
        location = self.location_thornton
        date = timezone.now().date()
        tag = Tag.UMBRELLA.value

        # Should be ignored
        email = "test@example.com"
        phone_number = "0000000000"

        self.client.post(reverse("items:report_found"),
                         data={"item_name": item_name,
                               "description": description,
                               "location_category": location_category,
                               "location": location.pk,
                               "date": date,
                               "email": email,
                               "phone_number": phone_number,
                               "tag": tag,
                               }
                         )

        self.assertEqual(Item.objects.count(), 1)
        found_item = Item.objects.first()

        self.assertEqual(found_item.item_name, item_name)
        self.assertEqual(found_item.description, description)
        self.assertEqual(found_item.location, location)
        self.assertEqual(found_item.date, date)
        self.assertEqual(found_item.tag, tag)

        self.assertIsNone(found_item.email)
        self.assertIsNone(found_item.phone_number)

        self.assertEqual(found_item.user, None)
        self.assertEqual(found_item.status, Status.NEW)
        self.assertEqual(found_item.expiration_date, (timezone.now() + timezone.timedelta(days=30)).date())

    def test_report_failure(self):
        # The item name is omitted, which should raise an error

        # Should not be an empty string
        description = ""

        location_category_other = self.other_category.pk

        # As normal. Should not cause an error.
        location = self.location_other

        # Date found is in the future, which is invalid
        date = (timezone.now() + timezone.timedelta(days=1)).date()

        # Invalid value. Location should be checked similarly
        tag = -1

        response = self.client.post(reverse("items:report_found"),
                                    data={
                                        "description": description,
                                        "location_category": location_category_other,
                                        "location": location.pk,
                                        "date": date,
                                        "tag": tag,
                                    }
                                    )

        self.assertEqual(Item.objects.count(), 0)

        self.assertNotEqual(response.context, None)
        self.assertIn('item_name', response.context['form'].errors)
        self.assertIn('description', response.context['form'].errors)
        self.assertNotIn('location', response.context['form'].errors)
        self.assertIn('date', response.context['form'].errors)
        self.assertIn('tag', response.context['form'].errors)

    def test_report_anonymous_invalid_file(self):
        item_name = "test item"
        description = "test description"
        location_category = self.academic.pk
        location = self.location_thornton
        date = timezone.now().date()

        tag = Tag.UMBRELLA.value
        files = [SimpleUploadedFile("images/Spam Word Doc.docx", b"file_content",
                                    content_type="application/vnd.openxmlformats-officedocument")]

        response = self.client.post(reverse("items:report_found"),
                                    data={"item_name": item_name,
                                          "description": description,
                                          "location_category": location_category,
                                          "location": location.pk,
                                          "date": date,
                                          "tag": tag,
                                          "files": files
                                          }
                                    )

        self.assertEqual(Item.objects.count(), 0)
        self.assertEqual(ItemFile.objects.count(), 0)

        self.assertIn('files', response.context['form'].errors)
