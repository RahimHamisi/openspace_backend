import os
from django.shortcuts import render
import graphene
from graphene_django import DjangoObjectType

from myapprest.tasks import send_reset_email_task
from rest_framework.views import APIView # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework import status # type: ignore
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from django.contrib.auth.tokens import default_token_generator

from rest_framework.decorators import api_view # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework import status # type: ignore
from .models import *
from myapp.models import *
from .serializers import ProblemReportSerializer
from cryptography.fernet import Fernet # type: ignore

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_decode
from rest_framework.decorators import api_view, permission_classes
from .booking_sms import send_sms


# views.py
from rest_framework.parsers import MultiPartParser, FormParser # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from rest_framework import status # type: ignore
from django.core.files.storage import default_storage

class FileUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            # No file provided, which is okay
            return Response({'file_path': None}, status=status.HTTP_200_OK)
        
        file_path = default_storage.save(f'reports/{file_obj.name}', file_obj)
        return Response({'file_path': file_path}, status=status.HTTP_201_CREATED)
    
    
FERNET_KEY = os.getenv('FERNET_KEY')
fernet = Fernet(FERNET_KEY)

@api_view(['POST'])
def submit_problem_report(request):
    try:
        # Get data from the incoming request
        phone_number = request.data['phone_number']
        open_space = request.data['open_space']
        description = request.data['description']
        reference_number = request.data['reference_number']

        # Encrypt the phone number before saving
        encrypted_phone = fernet.encrypt(phone_number.encode()).decode()

        report = UssdReport.objects.create(
            phone_number=encrypted_phone,
            open_space=open_space,
            description=description,
            reference_number=reference_number,
            status="Pending"
        )

        serializer = ProblemReportSerializer(report)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except KeyError as e:
        return Response({'error': f'Missing key: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmReportAPIView(APIView):
    def post(self, request, pk):
        try:
            report = UssdReport.objects.get(pk=pk)
            if report.status != 'processed':
                report.status = 'processed'
                report.save()

                # Send SMS to user
                message = f"Hello {report.username}, your report #{report.reference} has been confirmed."
                send_sms(report.phone_number, message)

                return Response({'message': 'Report confirmed and SMS sent.'}, status=status.HTTP_200_OK)
            return Response({'message': 'Report already processed.'}, status=status.HTTP_200_OK)
        except UssdReport.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)






# @api_view(['POST'])
# def confirm_report(request, pk):
#     try:
#         # Get report by primary key (id)
#         report = UssdReport.objects.get(pk=pk)

#         # Update status
#         report.status = 'Processed'
#         report.save()

#         # Send SMS using encrypted phone number
#         success = send_confirmation_sms(report.phone_number, report.reference_number)
#         if not success:
#             return Response({"warning": "Report confirmed, but SMS failed to send"}, status=status.HTTP_200_OK)

#         return Response({"message": "Report confirmed and SMS sent successfully."}, status=status.HTTP_200_OK)

#     except UssdReport.DoesNotExist:
#         return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['GET'])
def get_report_status(request, reference_number):
    try:
        # Find the report by reference number
        report = UssdReport.objects.get(reference_number=reference_number)
        serializer = ProblemReportSerializer(report)
        return Response({
            "reference_number": report.reference_number,
            "status": report.status
        }, status=status.HTTP_200_OK)
    except UssdReport.DoesNotExist:
        return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)


class UssdReportType(DjangoObjectType):
    class Meta:
        model = UssdReport

class ReportUssdQuery(graphene.ObjectType):
    all_reports_ussds = graphene.List(UssdReportType)
    def resolve_all_reports_ussds(self, info):
        # Fetch all reports
        return UssdReport.objects.all()
    


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ProfileImageUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ProfileImageUploadSerializer(instance=request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            image_url = request.build_absolute_uri(serializer.data['profile_image'])
            return Response({'imageUrl': image_url}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)



CustomUser = get_user_model()

class SendResetPasswordEmailView(APIView):
    def post(self, request):
        print("PasswordResetRequestView POST called")

        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

        # Use Celery to send the email asynchronously
        send_reset_email_task.delay(email, reset_link)

        return Response({'message': 'Password reset link sent to email.'}, status=200)


class PasswordResetConfirmView(APIView):
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("password")

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)

            if PasswordResetTokenGenerator().check_token(user, token):
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password reset successful"})
            else:
                return Response({"error": "Invalid token"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)




class OpenSpaceBookingView(APIView):
    def post(self, request):
        serializer = OpenSpaceBookingSerializer(
            data=request.data,
            context={'request': request}  # Pass the request to the serializer context
        )

        if serializer.is_valid():
            # Save booking and associate with the logged-in user
            booking = serializer.save(user=request.user)

            # Mark the space as unavailable
            booking.space.status = 'unavailable'
            booking.space.save()

            return Response(OpenSpaceBookingSerializer(booking).data, status=status.HTTP_201_CREATED)

        print("Booking validation errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from django.db.models import Q

class DistrictBookingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != "ward_executive":
            return Response({"error": "Unauthorized"}, status=403)

        forwarded_booking_ids = ForwardedBooking.objects.values_list('booking_id', flat=True)
        bookings = OpenSpaceBooking.objects.filter(
            district=user.ward
        ).exclude(id__in=forwarded_booking_ids)

        serializer = OpenSpaceBookingSerializer(bookings, many=True)
        return Response(serializer.data)

    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_and_forward_booking(request, booking_id):
    user = request.user
    if user.role != "ward_executive":
        return Response({"error": "Unauthorized"}, status=403)

    try:
        booking = OpenSpaceBooking.objects.get(id=booking_id, district=user.ward)
    except OpenSpaceBooking.DoesNotExist:
        return Response({"error": "Booking not found or unauthorized"}, status=404)

    ward_executive_description = request.data.get('description', '').strip()
    if not ward_executive_description:
        return Response({"error": "Description is required"}, status=400)

    forwarded_booking = ForwardedBooking.objects.create(
        booking=booking,
        ward_executive_description=ward_executive_description,
        forwarded_by=user
    )
    return Response({"message": "Booking accepted and forwarded to admin"}, status=200)


class ForwadedBookingAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        forwarded_bookings = ForwardedBooking.objects.filter(forwarded_by=user)
        serializer = ForwardedBookingSerializer(forwarded_bookings, many=True)
        return Response(serializer.data)


class AllBookingsAdminAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user

        if user.role != "staff":
            return Response({"error": "Unauthorized"}, status=403)
        bookings = OpenSpaceBooking.objects.all().order_by('-created_at')
        serializer = OpenSpaceBookingSerializer(bookings, many=True)
        return Response(serializer.data)
    


@api_view(['POST'])
def reject_booking(request, booking_id):
    try:
        booking = OpenSpaceBooking.objects.get(id=booking_id)

        # Update booking status
        booking.status = 'rejected'
        booking.save()

        # Update OpenSpace status to available
        booking.space.status = 'available'
        booking.space.save()

        # Send rejection email if email exists
        user_email = None
        if booking.user and booking.user.email:
            user_email = booking.user.email
        elif hasattr(booking, 'email') and booking.email:
            user_email = booking.email

        if user_email:
            subject = 'Your Booking Has Been Rejected'
            message = f"""
Hello {booking.username},

Your booking for {booking.space.name} from {booking.startdate} to {booking.enddate} has been rejected.
The space is now available for others.

Thank you for understanding.
"""
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user_email],
                fail_silently=True
            )

        # Send SMS notification if contact exists
        if booking.contact:
            sms_message = f"Hello {booking.username}, your booking for {booking.space.name} from {booking.startdate} to {booking.enddate} has been REJECTED."
            try:
                send_sms(phone=booking.contact, message=sms_message)
            except Exception as e:
                print("Failed to send rejection SMS:", e)

        return Response({'message': 'Booking rejected successfully.'}, status=status.HTTP_200_OK)

    except OpenSpaceBooking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)





@api_view(['POST'])
def accept_booking(request, booking_id):
    try:
        booking = OpenSpaceBooking.objects.get(id=booking_id)

        # 1. Update booking status to 'accepted'
        booking.status = 'accepted'
        booking.save()

        # 2. Mark open space as 'unavailable'
        booking.space.status = 'unavailable'
        booking.space.save()

        # 3. Send SMS notification to user
        if booking.contact:
            sms_message = (
                f"Hello {booking.username}, your booking for {booking.space.name} "
                f"from {booking.startdate} to {booking.enddate} has been ACCEPTED. "
                f"Please prepare accordingly."
            )
            try:
                send_sms(phone=booking.contact, message=sms_message)
            except Exception as e:
                print("Failed to send acceptance SMS:", e)

        return Response({'message': 'Booking accepted and user notified.'}, status=status.HTTP_200_OK)

    except OpenSpaceBooking.DoesNotExist:
        return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)




class UserBooking(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        bookings = OpenSpaceBooking.objects.filter(user=user).order_by('-created_at')
        serializer = OpenSpaceBookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

from rest_framework import generics, permissions

class MyBookingsView(generics.ListAPIView):
    serializer_class = OpenSpaceBookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Get bookings for the logged-in user
        return OpenSpaceBooking.objects.filter(user=self.request.user).order_by('-created_at')



from rest_framework.decorators import api_view
from rest_framework.response import Response
from .sms import send_sms
from .utils import decrypt_phone_number

@api_view(['POST'])
def confirm_report(request, report_id):
    try:
        report = UssdReport.objects.get(id=report_id)
        decrypted_phone = decrypt_phone_number(report.phone_number)

        message = (
            f"Hello! Your report with reference number {report.reference_number} "
            f"regarding '{report.open_space}' has been successfully confirmed. "
            f"Thank you for helping us improve our community."
        )

        response = send_sms(decrypted_phone, message)
        report.status = 'processed'
        report.save()

        return Response({"status": "success", "data": response})

    except UssdReport.DoesNotExist:
        return Response({"status": "error", "message": "Report not found"}, status=404)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)



@api_view(['POST'])
def reply_to_report(request, report_id):
    try:
        report = UssdReport.objects.get(id=report_id)
        decrypted_phone = decrypt_phone_number(report.phone_number)

        custom_message = request.data.get("message", "")
        if not custom_message:
            return Response({"status": "error", "message": "Message content is required"}, status=400)

        response = send_sms(decrypted_phone, custom_message)

        return Response({"status": "success", "message": "Reply sent successfully", "data": response})

    except UssdReport.DoesNotExist:
        return Response({"status": "error", "message": "Report not found"}, status=404)


@api_view(['DELETE'])
def delete_report(request, report_id):
    try:
        report = UssdReport.objects.get(id=report_id)
        report.delete()
        return Response({"status": "success", "message": "Report deleted successfully"})
    
    except UssdReport.DoesNotExist:
        return Response({"status": "error", "message": "Report not found"}, status=404)
    
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=500)



class DeleteBookingAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, booking_id):
        try:
            booking = OpenSpaceBooking.objects.get(id=booking_id)

            # Optional: only allow deletion by staff or the booking owner
            if request.user != booking.user and not request.user.is_staff:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

            booking.delete()
            return Response({'message': 'Booking deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

        except OpenSpaceBooking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_booking_stats(request):
    user = request.user
    bookings = OpenSpaceBooking.objects.filter(user=user)

    total = bookings.count()
    accepted = bookings.filter(status='accepted').count()
    pending = bookings.filter(status='pending').count()

    return Response({
        'total': total,
        'accepted': accepted,
        'pending': pending
    })


class NotifyAllWardExecutivesView(APIView):
    def post(self, request):
        message = request.data.get('message')
        if not message:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)

        ward_executives = CustomUser.objects.filter(role='ward_executive').exclude(email='')

        for executive in ward_executives:
            send_mail(
                subject='Notification from Kinondoni Municipal',
                message=message,
                from_email='admin@example.com',  # Replace with your configured email
                recipient_list=[executive.email],
                fail_silently=True
            )

        return Response({'success': 'Notifications sent to all ward executives.'}, status=status.HTTP_200_OK)


class NotifySingleWardExecutiveView(APIView):
    def post(self, request):
        email = request.data.get('email')
        message = request.data.get('message')

        if not email or not message:
            return Response({'error': 'Email and message are required'}, status=status.HTTP_400_BAD_REQUEST)

        send_mail(
            subject='Notification from Kinondoni Municipal',
            message=message,
            from_email='admin@example.com',  # Replace with your configured email
            recipient_list=[email],
            fail_silently=True
        )

        return Response({'success': f'Notification sent to {email}'}, status=status.HTTP_200_OK)



class UserReportHistoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = Report.objects.filter(user=request.user).order_by('-created_at')
        serializer = ReportSerializer(reports, many=True)
        return Response(serializer.data)