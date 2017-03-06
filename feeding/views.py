from django.shortcuts import render, HttpResponseRedirect
from .models import FeedType, FeedEntry
from .forms import FeedTypeForm, FeedEntryForm
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    feed_types = FeedType.objects.all()
    feed_entries = FeedEntry.objects.all().order_by('-date')

    parameters = {
        'feed_types': feed_types,
        'feed_entries': feed_entries
    }
    return render(request, 'feeding/index.html', parameters)


@login_required
def create_type(request):
    form = FeedTypeForm()
    return render(request, 'feeding/create_feed_type.html', {'form': form})


@login_required
def save_type(request):
    form = FeedTypeForm(request.POST)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/feeding/')

    return render(request, 'feeding/create_feed_type.html', {'form': form})


@login_required
def create_feed_entry(request):
    form = FeedEntryForm()
    return render(request, 'feeding/create_feed_entry.html', {'form': form})


@login_required
def save_feed_entry(request):
    form = FeedEntryForm(request.POST)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/feeding/')

    return render(request, 'feeding/create_feed_entry.html', {'form': form})