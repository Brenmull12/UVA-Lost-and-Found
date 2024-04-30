from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.views import generic
from django.conf import settings as django_settings

from LostAndFound import settings
from items.models import Item, ItemFile, Tag
from items.forms import FilterForm


class History(LoginRequiredMixin, generic.ListView):
    template_name = "common_user/history.html"
    context_object_name = "items"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(django_settings.LOGIN_URL)
        if request.user.is_site_admin:
            return HttpResponseForbidden('As an admin, you have no history to view.')

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        items = Item.objects.filter(user=self.request.user)
        tag=self.request.GET.get('tag')

        if tag:
            items = items.filter(tag=int(tag))

        # Order items by date
        items = items.order_by('-date')
        
        for item in items:
            item.files = list(ItemFile.objects.filter(item=item.id))

        return items

    def get_context_data(self, **kwargs):
        context = super(History, self).get_context_data(**kwargs)
        context['s3_url'] = settings.AWS_S3_CUSTOM_DOMAIN
        context['tags'] = Tag.choices
        context['form'] = FilterForm(self.request.GET) 
        return context
