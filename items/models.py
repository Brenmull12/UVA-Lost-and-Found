from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as translate
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage


class Location_Category(models.Model):
    name = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Location_Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Tag(models.IntegerChoices):
    OTHER = 1

    # TECHNOLOGY
    AIR_PODS = 100
    PHONE = 101
    COMPUTER = 102
    IPAD = 103
    HEADPHONES = 104
    CAMERA = 105
    TABLET = 106
    SMART_WATCH = 107
    CHARGER = 108

    # CLOTHING & WEATHER
    RAIN_JACKET = 300
    UMBRELLA = 301
    SUNGLASSES = 302
    COAT = 303
    HAT = 304
    GLOVES = 306
    SCARF = 307
    SHOES = 308

    # ACCESSORIES
    CREDIT_CARD = 400
    KEYS = 401
    WATCH = 402
    BACKPACK = 403
    PURSE = 404
    JEWELRY = 405
    WALLET = 406
    PASSPORT = 407
    ID = 408
    GLASSES = 409
    WATER_BOTTLE = 410
    BOOK = 411
    NOTEBOOK = 412
    PENCIL_CASE = 413
    SPORTS_EQUIPMENT = 414

    # TRANSPORTATION
    BICYCLE = 500
    SCOOTER = 501
    HELMET = 502


class Status(models.IntegerChoices):
    NEW = 100, "Submitted"  # automatically assigned whenever a report is created

    FLAGGED = 200, "Flagged"  # manually selected by a common user

    IN_PROGRESS = 300, "Under Review"  # automatically assigned whenever a site admin clicks on an item's detail report

    RESOLVED = 400, "Approved"  # manually selected by a site admin

    REJECTED = 500, "Rejected" # Manually selected by a site admin


def return_expiration_date():
    return (timezone.now() + timezone.timedelta(days=30)).date()


def date_validator(value):
    if timezone.now().date() < value:
        raise ValidationError(translate("The date an item was lost/found must not be in the future."))


class PhoneNumberValidator(RegexValidator):
    regex = r"(\+\d+ ?)?((\(\d{3}\))|(\d{3}))(-| )?(\d{3})(-| )?(\d{4})"
    message = "Phone number must include ten numeric digits, separated using spaces, dashes, or parentheses. Area code is optional."


class Item(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, default=None,
                             on_delete=models.SET_DEFAULT)

    item_name = models.CharField(max_length=50)
    description = models.TextField(max_length=500)

    location_category = models.ForeignKey(Location_Category, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    status = models.PositiveIntegerField(choices=Status, default=100)
    tag = models.PositiveIntegerField(choices=Tag)

    date = models.DateField(validators=[date_validator], default=timezone.now)

    expiration_date = models.DateField(default=return_expiration_date)

    email = models.EmailField(blank=True, default=None, null=True)
    phone_number = models.CharField(max_length=50, blank=True, null=True, default=None,
                                    validators=[PhoneNumberValidator()])

    resolve_text = models.CharField(max_length=1024, blank=True, default=None, null=True)
    is_found = models.BooleanField(default=False)

    def __str__(self):
        return self.item_name


class ItemFile(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    file = models.FileField(upload_to='imageUpload/')
    type = models.CharField(max_length=30)


@receiver(post_delete, sender=ItemFile)
def delete_file_from_s3(sender, instance, **kwargs):
    if instance.file:
        file_path = instance.file.name
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
