from django.forms import ModelForm, SelectDateWidget, FileField, ClearableFileInput, Textarea, ModelChoiceField
from django.utils.translation import gettext as translate
from django.utils import timezone
from django.core.exceptions import ValidationError
from django import forms
from .models import Item, Location, ItemFile, Location_Category, Tag


class MultipleFileInput(ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, file, initial=None):
        if isinstance(file, (list, tuple)):
            result = [super().clean(file, initial) for file in file]
        else:
            result = [super().clean(file, initial)]

        return result


def validate_file(file):
    max_size = 100000000  # ~ 100 MB
    valid_types = {
        'text/plain': ['txt'],
        'image/png': ['png'],
        'image/jpeg': ['jpeg', 'jpg'],
        'application/pdf': ['pdf'],
        # 'application/octet-stream': ['heic'],
    }

    filetype = file.content_type
    extension = file.__str__().split(".")[-1].strip().lower()

    if filetype in valid_types and extension in valid_types[filetype]:
        file.type = filetype.split('/')[-1].strip()
    else:
        raise ValidationError(translate("Please submit a valid file type."))

    if max_size and file.size > max_size:
        raise ValidationError(translate("File is too large."))


class ItemForm(ModelForm):
    files = MultipleFileField(required=False, widget=MultipleFileInput(attrs={'class': 'input-basic file'}))
    location_category = ModelChoiceField(queryset=Location_Category.objects.all())
    location = ModelChoiceField(queryset=Location.objects.all())

    class Meta:
        model = Item
        fields = ['item_name', 'description', 'location_category', 'location', 'date', 'email', 'phone_number', 'tag']
        widgets = {
            'date': SelectDateWidget(years=range(timezone.now().year - 5, timezone.now().year + 1),
                                     attrs={'class': 'input-basic narrow'}),
            'description': Textarea(attrs={'class': 'input-basic tall'}),
        }
        error_messages = {
            'item_name': {'required': 'Please enter the item name.'},
            'email': {'invalid': 'Please enter a valid email address.'},
        }
        exclude = ['user', 'is_found']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.is_found = kwargs.pop('is_found')
        super(ItemForm, self).__init__(*args, **kwargs)
        self.fields['location'].queryset = Location.objects.none()

        if 'location_category' in self.data:

            try:
                location_id = int(self.data.get('location_category'))
                self.fields['location'].queryset = Location.objects.filter(category__id = location_id).order_by("name")

            except (ValueError, TypeError):
                print(ValueError)

        elif self.instance.pk:
            self.fields['location'].queryset = self.instance.location_category.location_set.order_by('name')



        # Disable contact fields if the user is anonymous
        if not self.user.is_authenticated:
            self.user = None
            self.fields['email'].disabled = True
            self.fields['phone_number'].disabled = True

        # Update the location and tag blank choices
        self.fields['location_category'].empty_label = "Select..."
        self.fields['location'].empty_label = "Must select a location category."
        self.fields['tag'].choices = [("", "Select...")] + list(self.fields["tag"].choices)[1:]

        if not self.is_found:
            pass

        # Update input CSS classes
        for field in self.fields.values():
            if field.disabled is True:
                field.widget.attrs.update({'class': 'input-basic disabled'})
            elif field.widget.attrs.get('class', None) is None:
                field.widget.attrs.update({'class': 'input-basic'})

    def clean(self):
        cleaned_data = super().clean()

        if self.user is None:
            if cleaned_data['email'] is not None:
                self.add_error('email', translate("Sign in to share your email."))
            if cleaned_data['phone_number'] is not None:
                self.add_error('phone_number', translate("Sign in to share your phone number."))

        try:
            for file in cleaned_data['files']:
                validate_file(file)
        except ValidationError as error:
            self.add_error('files', error.message)

        if self.is_found:
            pass
            # location = cleaned_data['location']
            # if location.name == 'Other' and len(cleaned_data['files']) == 0:
            #     self.add_error('files', translate('File upload is required when location is OTHER.'))

        else:
            if self.user is None:
                self.add_error('__all__', translate('You must be signed in to submit this form.'))

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.user = self.user
        instance.is_found = self.is_found
        if commit:
            instance.save()

        for file in self.cleaned_data['files']:
            file_instance = ItemFile(item=instance, file=file, type=file.type)
            file_instance.save()

        return instance
    

class FilterForm(forms.Form):
        tag = forms.ChoiceField(choices=[], required=False)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['tag'].choices = [("", "Select...")] + [
                (tag.value, tag.label) for tag in Tag
            ]