# from .settings import STATIC_URL

from ...models import Location, Location_Category

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        Location.objects.all().delete()
        Location_Category.objects.all().delete()

        with open('static/locations/locations.txt', 'r') as file:
            current_category_name = None  # Initialize current_category variable
            # Iterate over each line in the file
            for line in file:
                # Strip leading and trailing whitespace
                line = line.strip()
                # Check if the line starts with dashes
                if line.startswith("---"):
                    # Extract the category from the line
                    current_category_name = line.replace("-", "").strip()  # Remove dashes and strip whitespace
                    current_category = Location_Category.objects.create(name=current_category_name)
                else:
                    # Create a Location object with the extracted name and category
                    if line:
                        Location.objects.create(name=line, category=current_category)

        other_category = Location_Category.objects.create(name = "OTHER")
        Location.objects.create(name = "Other", category = other_category)