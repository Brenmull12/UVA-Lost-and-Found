from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.conf import settings
from django.utils import timezone
import json

from .forms import FilterForm, ItemForm
from .models import Item, Status, ItemFile, Location, Location_Category, Tag


class ReportItemView(generic.CreateView):
    form_class = ItemForm
    template_name = "items/report.html"
    success_url = reverse_lazy('items:report_success')
    is_found = None

    # Used to get the current user in ItemForm.__init__()
    def get_form_kwargs(self):
        kwargs = super(ReportItemView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user, 'is_found': self.is_found})
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and not self.is_found:
            return HttpResponseRedirect(settings.LOGIN_URL)
        if request.user.is_authenticated and request.user.is_site_admin:
            return HttpResponseForbidden('As an admin, you are not allowed to make a report.')

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()

        if self.request.user.is_authenticated:
            initial['email'] = self.request.user.email

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_found'] = self.is_found
        return context


class Index(LoginRequiredMixin, generic.ListView):
    template_name = "items/index.html"
    context_object_name = "items"
    is_found = None

    def get_queryset(self):
        today = timezone.now().date()
        tag = self.request.GET.get('tag')

        # Filter the queryset based on is_found
        items = Item.objects.filter(
            is_found=self.is_found,
            status__in=[Status.RESOLVED],
            expiration_date__gte=today  # This will only include items whose expiration date is today or later
        )
        # if a tag is specified, filter based on tag from already filtered list
        if tag:
            items = items.filter(tag=int(tag))
            
        # Order items by date
        items = items.order_by('-date')

        for item in items:
            item.files = list(ItemFile.objects.filter(item=item.id))

        return items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_found'] = self.is_found
        context['tags'] = Tag.choices
        context['form'] = FilterForm(self.request.GET)
        return context


class Detail(LoginRequiredMixin, generic.DetailView):
    model = Item
    template_name = "items/details.html"
    context_object_name = "item"

    def dispatch(self, request, *args, **kwargs):
        item = self.get_object()
        if item.status != Status.RESOLVED and request.user != item.user and not request.user.is_site_admin:
            return HttpResponseForbidden("You are not allowed to view this item.")

        request.session['previous_url'] = request.META.get('HTTP_REFERER', None)
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        item = Item.objects.get(id=self.kwargs['id'])
        item.files = list(ItemFile.objects.filter(item=item.id))

        return item

    def get_context_data(self, **kwargs):
        context = super(Detail, self).get_context_data(**kwargs)
        context["can_flag"] = context['item'].status is not Status.FLAGGED or Status.IN_PROGRESS
        context['is_rejected'] = context['item'].status == Status.REJECTED
        context['location_name'] = self.get_location_name(context['item'].location_id)

        return context

    def get_location_name(self, location_id):
        location = get_object_or_404(Location, pk=location_id)
        return location.name


@login_required
def delete(request, id):
    item = get_object_or_404(Item, pk=id)

    # Check if the logged-in user is the owner of the item
    if not request.user.is_authenticated or item.user != request.user:
        return HttpResponseForbidden('You are not allowed to delete this post.')

    if request.method == 'POST':
        item.delete()
        messages.success(request, "Item deleted successfully.")

        previous_url = request.session.pop('previous_url', None)
        if previous_url:
            return HttpResponseRedirect(previous_url)
        return HttpResponseRedirect(reverse("index"))

    return HttpResponse(reverse("items:details", args=(id,)))


@login_required
def flag(request, id):
    item = get_object_or_404(Item, pk=id)

    if not request.user.is_authenticated:
        return HttpResponseForbidden('You are not allowed to flag this post.')

    if request.method == 'POST':
        if item.status == Status.RESOLVED or (item.status == Status.REJECTED and item.user == request.user):
            item.status = Status.FLAGGED
            item.save(update_fields=['status'])
            messages.success(request, "Item flagged successfully.")
        else:
            messages.warning(request, "This item cannot be flagged.")
            return HttpResponseRedirect(reverse('items:details', args=(id,)))

        previous_url = request.session.pop('previous_url', None)
        if previous_url:
            return HttpResponseRedirect(previous_url)
        return HttpResponseRedirect(reverse("index"))

    return HttpResponse(reverse('items:details', args=(id,)))


def getLocations(request):
    data = json.loads(request.body)

    location_categoryID = data["id"]

    possibleLocations = Location.objects.filter(category__id=location_categoryID)

    return JsonResponse(list(possibleLocations.values("id", "name")), safe=False)
