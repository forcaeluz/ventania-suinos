from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from .models import Medicine
from .models import Treatment


@login_required()
def index(request):
    available_medicine = Medicine.objects.all()
    ongoing_treatment = [obj for obj in Treatment.objects.all() if obj.is_active is True]
    params = {
        'medicines': available_medicine,
        'treatments': ongoing_treatment
    }
    return render(request, 'medications/index.html', params)