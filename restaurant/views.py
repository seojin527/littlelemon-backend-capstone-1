import json
from datetime import datetime

from django.core import serializers
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from .forms import BookingForm
from .models import Booking, Menu


def home(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def reservations(request):
    bookings = Booking.objects.all()
    booking_json = serializers.serialize('json', bookings)
    return render(request, 'bookings.html', {'bookings': booking_json})


def book(request):
    form = BookingForm()
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
    return render(request, 'book.html', {'form': form})


def menu(request):
    menu_data = Menu.objects.all().order_by('name')
    return render(request, 'menu.html', {'menu': menu_data})


def display_menu_item(request, pk=None):
    menu_item = get_object_or_404(Menu, pk=pk) if pk else ''
    return render(request, 'menu_item.html', {'menu_item': menu_item})


@csrf_exempt
def bookings(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            Booking.objects.create(
                first_name=data['first_name'],
                reservation_date=data['reservation_date'],
                reservation_slot=data['reservation_slot'],
            )
            return HttpResponse(status=201)
        except IntegrityError:
            return JsonResponse({'error': 1, 'message': 'This slot is already booked.'}, status=409)

    date = request.GET.get('date', datetime.today().date())
    bookings_data = Booking.objects.filter(reservation_date=date)
    booking_json = serializers.serialize('json', bookings_data)
    return HttpResponse(booking_json, content_type='application/json')