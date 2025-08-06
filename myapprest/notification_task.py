from celery import shared_task
from django.utils.timezone import now
from .models import OpenSpaceBooking
from .sms_utils import send_sms

@shared_task
def check_expired_bookings_task():
    today = now().date()
    expired_bookings = OpenSpaceBooking.objects.filter(
        enddate__lte=today,
        status='accepted'
    )

    for booking in expired_bookings:
        # Update space availability
        booking.space.status = 'available'
        booking.space.save()

        # Notify user
        message = f"Hello {booking.username}, your booking for {booking.space.name} has ended today. Thank you!"
        send_sms(booking.contact, message)
