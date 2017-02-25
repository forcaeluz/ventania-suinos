from django.shortcuts import render, HttpResponseRedirect
from .models import FeedType
from .forms import FeedTypeForm


def index(request):
    feed_types = FeedType.objects.all()
    parameters = {
        'feed_types': feed_types
    }
    return render(request, 'index.html', parameters)


def create_type(request):
    form = FeedTypeForm()
    return render(request, 'create_feed_type.html', {'form': form})


def save_type(request):
    form = FeedTypeForm(request.POST)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/feeding/')

    return render(request, 'create_feed_type.html', {'form': form})


def create_feed_entry(request):
    pass


def save_feed_entry(request):
    pass
