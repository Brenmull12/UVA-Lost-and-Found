from django.test import TestCase
from django.contrib.auth import get_user
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from authentication.models import User
from items.models import Location, Location_Category, Item, ItemFile, Status, Tag


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


class DeletionStatusTests(TestCase):
    def setUp(self):
        self.common_user = User.objects.create(email='common@example.com', first_name='Common', last_name='User')
        self.common_user.set_password('password')
        self.common_user.save()

        other_user = User.objects.create(email='other@example.com', first_name='Common', last_name='User')
        other_user.set_password('password')
        other_user.save()

        site_admin = User.objects.create(email='admin@example.com', first_name='Site', last_name='Admin')
        site_admin.set_password('password')
        site_admin.is_site_admin = True
        site_admin.save()

        self.location_category = Location_Category.objects.create(name="Other")
        self.location_category.save()
        self.location = Location.objects.create(name="Other", category=self.location_category)
        self.location.save()

    def tearDown(self):
        Location_Category.objects.all().delete()
        Location.objects.all().delete()
        Item.objects.all().delete()
        ItemFile.objects.all().delete()
        User.objects.all().delete()

    def common_user_login(self):
        self.client.login(email='common@example.com', password='password')
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        return user

    def other_user_login(self):
        self.client.login(email='other@example.com', password='password')
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        return user

    def site_admin_login(self):
        self.client.login(email='admin@example.com', password='password')
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        return user

    def create_item(self, status: Status, user: User = None):
        item = Item.objects.create(
            user=user,
            item_name='test item',
            description='test description',
            location_category=self.location_category,
            location=self.location,
            status=status,
            tag=Tag.OTHER.value
        )
        item.save()

        file = ItemFile.objects.create(
            item=item,
            file=SimpleUploadedFile("images/emo_mark_sherriff.png", b"file_content", content_type='image/png'),
            type="png"
        )
        file.save()

        return item, file

    def test_common_user_delete(self):
        user = self.common_user_login()
        item, file = self.create_item(Status.NEW, self.common_user)

        self.client.post(reverse('items:delete', args=(item.id,)))

        self.assertNotIn(item, Item.objects.all())
        self.assertNotIn(file, ItemFile.objects.all())

    def test_wrong_user_delete(self):
        user = self.other_user_login()
        item, file = self.create_item(Status.NEW, self.common_user)

        response = self.client.post(reverse('items:delete', args=(item.id,)))

        self.assertIn(item, Item.objects.all())
        self.assertIn(file, ItemFile.objects.all())

    def test_anonymous_user_delete(self):
        item, file = self.create_item(Status.NEW, self.common_user)

        self.client.post(reverse('items:delete', args=(item.id,)))

        self.assertIn(item, Item.objects.all())
        self.assertIn(file, ItemFile.objects.all())

    def test_admin_delete(self):
        user = self.site_admin_login()
        item, file = self.create_item(Status.NEW, self.common_user)

        self.client.post(reverse('items:delete', args=(item.id,)))

        self.assertIn(item, Item.objects.all())
        self.assertIn(file, ItemFile.objects.all())

    def test_common_user_flag(self):
        user = self.common_user_login()
        item, file = self.create_item(Status.RESOLVED, self.common_user)

        self.client.post(reverse('items:flag', args=(item.id,)))
        item = Item.objects.get(pk=item.id)

        self.assertEqual(item.status, Status.FLAGGED)

    def test_common_user_not_flaggable(self):
        user = self.common_user_login()
        item, file = self.create_item(Status.NEW, self.common_user)

        # NEW
        self.client.post(reverse('items:flag', args=(item.id,)))

        item = Item.objects.get(pk=item.id)
        self.assertEqual(item.status, Status.NEW)

        # IN PROGRESS
        item.status = Status.IN_PROGRESS
        item.save()

        self.client.post(reverse('items:flag', args=(item.id,)))

        item = Item.objects.get(pk=item.id)
        self.assertEqual(item.status, Status.IN_PROGRESS)

    def test_other_user_flag(self):
        user = self.other_user_login()
        item, file = self.create_item(Status.RESOLVED, self.common_user)

        self.client.post(reverse('items:flag', args=(item.id,)))
        item = Item.objects.get(pk=item.id)

        self.assertEqual(item.status, Status.FLAGGED)

    def test_admin_view_in_progress(self):
        user = self.site_admin_login()
        item, file = self.create_item(Status.NEW, self.common_user)

        self.client.get(reverse("site_admin:detail", args=(item.id, )))
        item = Item.objects.get(pk=item.id)

        self.assertEqual(item.status, Status.IN_PROGRESS)

    def test_admin_view_flagged(self):
        user = self.site_admin_login()
        item, file = self.create_item(Status.FLAGGED, self.common_user)

        self.client.get(reverse("site_admin:detail", args=(item.id,)))
        item = Item.objects.get(pk=item.id)

        self.assertEqual(item.status, Status.IN_PROGRESS)

    def test_admin_view_already_resolved(self):
        user = self.site_admin_login()
        item, file = self.create_item(Status.RESOLVED, self.common_user)

        try:
            self.client.get(reverse("site_admin:detail", args=(item.id,)))
            item = Item.objects.get(pk=item.id)
        except Item.DoesNotExist:
            pass

        self.assertEqual(item.status, Status.RESOLVED)

    def test_common_user_admin_review_page(self):
        user = self.common_user_login()
        item, file = self.create_item(Status.NEW, self.common_user)

        self.client.get(reverse("site_admin:detail", args=(item.id, )))
        item = Item.objects.get(pk=item.id)

        self.assertEqual(item.status, Status.NEW)

    def test_admin_resolve(self):
        user = self.site_admin_login()
        item, file = self.create_item(Status.IN_PROGRESS, self.common_user)

        self.client.post(reverse("site_admin:update", args=(item.id,)), data={
            "resolve_text": "TEST TEXT"
        })
        item = Item.objects.get(pk=item.id)

        self.assertEqual(item.status, Status.RESOLVED)
        self.assertEqual(item.resolve_text, "TEST TEXT")

    def test_admin_reject(self):
        user = self.site_admin_login()
        item, file = self.create_item(Status.IN_PROGRESS, self.common_user)

        self.client.post(reverse("site_admin:update", args=(item.id,)), data={
            "resolve_text": "TEST TEXT",
            "status": Status.REJECTED
        })
        item = Item.objects.get(pk=item.id)

        self.assertEqual(item.status, Status.REJECTED)
        self.assertEqual(item.resolve_text, "TEST TEXT")

