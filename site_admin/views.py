from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.views import generic
import json

from items.models import Item, Status, ItemFile, Location, Location_Category


class ReviewItems(LoginRequiredMixin, generic.ListView):
    template_name = "site_admin/review.html"
    context_object_name = "items"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_site_admin:
            return HttpResponseForbidden("You are not allowed to access this page.")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        items = Item.objects.filter(status__in=[Status.NEW, Status.FLAGGED, Status.IN_PROGRESS])

        # Order items by date
        items = items.order_by('-date')
        
        for item in items:
            item.files = list(ItemFile.objects.filter(item=item.id))

        return items


class Detail(LoginRequiredMixin, generic.DetailView):
    model = Item
    template_name = "site_admin/detail.html"
    context_object_name = "item"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_site_admin:
            return HttpResponseForbidden("You are not allowed to access this page.")

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        item = Item.objects.get(id=self.kwargs['id'])
        item.files = list(ItemFile.objects.filter(item=item.id))

        if item.status in [Status.NEW, Status.FLAGGED]:
            item.status = Status.IN_PROGRESS
            item.save(update_fields=['status'])

        return item

    def get_context_data(self, **kwargs):
        context = super(Detail, self).get_context_data(**kwargs)
        context['location_name'] = self.get_location_name(context['item'].location_id)
        return context

    def get_location_name(self, location_id):
        location = get_object_or_404(Location, pk=location_id)
        return location.name


class Resolve(LoginRequiredMixin, generic.DetailView):
    model = Item
    template_name = "site_admin/resolution_notes.html"
    context_object_name = "item"
    status = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.is_site_admin:
            return HttpResponseForbidden("You are not allowed to access this page.")

        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        item = Item.objects.get(id=self.kwargs['id'], status__in=[Status.NEW, Status.FLAGGED, Status.IN_PROGRESS])

        return item

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status'] = self.status
        context['status_resolved'] = self.status == Status.RESOLVED
        context['status_rejected'] = self.status == Status.REJECTED
        return context


def update(request, id):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(settings.LOGIN_URL)
    if not request.user.is_site_admin:
        return HttpResponseForbidden("You are not allowed to access this page.")

    item = get_object_or_404(Item, pk=id, status__in=[Status.NEW, Status.FLAGGED, Status.IN_PROGRESS])

    if request.method == "POST":
        status = request.POST.get('status')
        if not status:
            status = Status.RESOLVED
        item.status = status
        item.resolve_text = request.POST.get("resolve_text", "")
        item.save()
        messages.success(request, "Successfully resolved item.")

        return HttpResponseRedirect(reverse('site_admin:review'))

    else:
        return HttpResponse(reverse('site_admin:detail', args=(id,)))


def review_redirect(request):
    return HttpResponseRedirect(reverse('site_admin:review'))


def getLocations(request):
    data = json.loads(request.body)

    location_categoryID = data["id"]

    possibleLocations = Location.objects.filter(category__id=location_categoryID)

    print(location_categoryID)

    return JsonResponse(list(possibleLocations.values("id", "name")), safe=False)
