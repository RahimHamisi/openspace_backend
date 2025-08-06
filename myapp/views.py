import uuid
from django.conf import settings
from myapprest.models import *
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError # type: ignore
# from .tasks import send_verification_email # type: ignore
from .models import *
from openspaceBuilders.openspaceBuilders import UserBuilder, open_space, register_user, report_issue
from openspace_dto.openspace import *
from openspace_dto.Response import OpenspaceResponse, RegistrationResponse, ReportResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from better_profanity import profanity # type: ignore
import os
from .utils import is_explicit_image, is_inappropriate_text
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions
from .serializer import *


class RegistrationMutation(graphene.Mutation):
    user = graphene.Field(RegistrationObject)
    output = graphene.Field(RegistrationResponse)

    class Arguments:
        input = RegistrationInputObject(required=True)

    def mutate(self, info, input):
        response = register_user(input)
        return RegistrationMutation(user=response.user, output=response)


class UserType(DjangoObjectType):
    class Meta:
        model = CustomUser
        fields = ("id", "username", "is_staff", "is_superuser", "ward_executive")


class LoginUser(graphene.Mutation):
    class Arguments:
        input=UserLoginInputObject(required=True)

    output=graphene.Field(UserResponseObject)
    
    def mutate(self, info,input):
        username = input.username
        password = input.password
        try:
            user = authenticate(username=username, password=password)
            print(user)

            # if user is None:
            #     return LoginUser(success=False, message="Invalid credentials")
            
            if not isinstance(user, CustomUser):
                raise ValidationError("User is not a valid CustomUser instance.")

            # Create JWT token
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            success=    True
            message=f"{user.role} login successful"

            user_data = UserLoginObject(
                id=user.id,
                username=user.username,
                access_token=access_token,
                refresh_token=refresh,
                isStaff=user.is_staff,
                isWardExecutive=(user.role == "ward_executive")
            )
            output=UserResponseObject (
                user=user_data,
                success=success,
                message=message
            )

            return LoginUser(
                output=output
            )
            


        except Exception as e:
            success=False
            message=f"An error occurred"
            output=UserResponseObject (
                success=success,
                message=message
            )
            return LoginUser(output=output)




class RegisterUserMutation(graphene.Mutation):
    class Arguments:
        input = UserRegistrationInput(required=True)

    Output = UserRegistrationObject

    def mutate(root, info, input):
        return UserBuilder.register_user(
            username=input.username,
            password=input.password,
            passwordConfirm=input.passwordConfirm
        )

class CreateOpenspaceMutation(graphene.Mutation):
    openspace = graphene.Field(OpenspaceObject)
    output = graphene.Field(OpenspaceResponse)
    
    class Arguments:
        input = OpenspaceInputObject(required=True)
        
    def mutate(self, info, input):
        response = open_space(input)
        
        return CreateOpenspaceMutation(openspace=response.openspace, output=response)
    

class DeleteOpenspace(graphene.Mutation):
    message = graphene.String()
    success = graphene.Boolean()
    
    class Arguments:
        id = graphene.ID(required=True)
        
    def mutate(self, info, id):
        try:
            open_space = OpenSpace.objects.get(pk=id)
            open_space.delete()
            return DeleteOpenspace(success=True, message="Openspace delete successfully")
        except OpenSpace.DoesNotExist:
            return DeleteOpenspace(success=False, message="Fail to delete openspace")
        

class ToggleOpenspaceMutation(graphene.Mutation):
    class Arguments:
        input = ToggleOpenspaceInput(required=True)

    openspace = graphene.Field(OpenspaceObject)

    def mutate(self, info, input):
        try:
            openspace = OpenSpace.objects.get(pk=input.id)
            openspace.is_active = input.is_active
            openspace.save()
            return ToggleOpenspaceMutation(openspace=openspace)
        except OpenSpace.DoesNotExist:
            raise Exception("OpenSpace not found")


class OpenspaceQuery(graphene.ObjectType):
    all_open_spaces_admin = graphene.List(OpenspaceObject)
    
    all_open_spaces_user = graphene.List(OpenspaceObject)
    
    def resolve_all_open_spaces_admin(self, info):
        return OpenSpace.objects.all()
    
    def resolve_all_open_spaces_user(self, info):
        return OpenSpace.objects.filter(is_active=True)

        
class TotalOpenSpaceQuery(graphene.ObjectType):
    total_openspaces = graphene.Int()
    
    def resolve_total_openspaces(self, info):
        return OpenSpace.objects.count()

class ReportMutation(graphene.Mutation):
    report = graphene.Field(ReportObject)
    output = graphene.Field(ReportResponse)
    
    class Arguments:
        input = ReportInputObject(required=True)
        
    def mutate(self, info, input):
        response = report_issue(input)
        return ReportMutation(report=response.report, output=response)
    
    
class ReportType(DjangoObjectType):
    class Meta:
        model = Report
        fields = "__all__"
        
    def resolve_file_url(self, info):
        if self.file:
            return f"{settings.MEDIA_URL}{self.file}"
        return None

profanity.load_censor_words()

ALLOWED_FILE_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png']
    
class CreateReport(graphene.Mutation):
    class Arguments:
        description = graphene.String(required=True)
        email = graphene.String(required=False)
        file_path = graphene.String(required=False)
        space_name = graphene.String(required=False)
        latitude = graphene.Float(required=False) 
        longitude = graphene.Float(required=False)
        user_id = graphene.ID(required=False)

    report = graphene.Field(ReportType)

    def mutate(self, info, description, email=None, file_path=None, space_name=None,
               latitude=None, longitude=None, user_id=None):


        if profanity.contains_profanity(description):
            raise GraphQLError("Description contains inappropriate language.")

        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ALLOWED_FILE_EXTENSIONS:
                raise GraphQLError("Invalid file type. Only PDF, JPG, and PNG are allowed.")

            if is_explicit_image(file_path):
                raise GraphQLError("Inappropriate image content detected.")

        user = None
        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
            except CustomUser.DoesNotExist:
                raise GraphQLError("Invalid user ID.")

        report = Report(
            description=description,
            email=email,
            file=file_path,
            space_name=space_name,
            latitude=latitude,
            longitude=longitude,
            user=user,
        )
        report.save()

        return CreateReport(report=report)

    
class ReportQuery(graphene.ObjectType):
    all_reports = graphene.List(ReportType)
    
    def resolve_all_reports(self, info):
        return Report.objects.all()
    

class ConfirmReport(graphene.Mutation):
    message = graphene.String()
    success = graphene.Boolean()
    
    class Arguments:
        report_id = graphene.String(required=True)
        
    def mutate(self, info, report_id):
        try:
            report = Report.objects.get(report_id=report_id)
            
            ReportHistory.objects.create(
                report_id = report.report_id,
                description=report.description,
                email=report.email,
                file=report.file if report.file else None,
                user=report.user  # Link the report to the original user
            )
            
            # Delete the original report
            report.delete()
            
            # Send email if user provided one
            if report.email:
                send_mail(
                    subject="Report Confirmation",
                    message="Your report has been reviewed and confirmed.",
                    from_email="limbureubenn@gmail.com",
                    recipient_list=[report.email],
                    fail_silently=True
                )
                
            return ConfirmReport(success=True, message="Report confirmed and moved to history.")
        except Report.DoesNotExist:
            return ConfirmReport(success=False, message="Report not found.")

        
class DeleteReport(graphene.Mutation):
    message = graphene.String()
    success = graphene.String()
    
    class Arguments:
        report_id = graphene.ID(required=True)
    def mutate(self, info, report_id):
        try:
            report = Report.objects.get(pk=report_id)
            report.delete()
            return DeleteReport(success=True, message="Report deleted successfully")
        except report.DoesNotExist:
            return DeleteReport(success=False, message="Report not found")
        
class HistoryReportQuery(graphene.ObjectType):
    all_historys = graphene.List(HistoryObject)
    
    def resolve_all_historys(self, info):
        return ReportHistory.objects.all()
    
class HistoryCountQuery(graphene.ObjectType):
    total_historys = graphene.Int()
    
    def resolve_total_historys(self, info):
        return ReportHistory.objects.count()
    
class ReportCountQuery(graphene.ObjectType):
    total_report = graphene.Int()
    
    def resolve_total_report(self, info):
        return Report.objects.count()
    
class ReportAnonymousQuery(graphene.ObjectType):
    anonymous = graphene.List(HistoryObject, session_id=graphene.String(required=True))
    
    def resolve_anonymous(self, info, session_id):
        return ReportHistory.objects.filter(session_id=session_id)
    


class AuthenticatedUserReport(graphene.ObjectType):
    my_reports = graphene.List(HistoryObject)
    
    def resolve_my_reports(self, info, **kwargs):
        user = info.context.user
        print("Authenticated user:", user)  # Debugging

        if user.is_authenticated:
            reports = UserBuilder.get_report_history(user=user)
            print(reports)  # Debugging
            return reports

        print("User is anonymous or not authenticated.")
        return ReportHistory.objects.none()


from graphql_jwt.decorators import login_required

User = get_user_model()

from rest_framework_simplejwt.tokens import AccessToken


class UserProfileQuery(graphene.ObjectType):
    profile=graphene.Field(ProfileObject)
    
    def resolve_profile(self,info):
        user=info.context.user
        if user.is_authenticated:
            return UserBuilder.get_user_profile_data(user=user)
            

class QueryUsers(graphene.ObjectType):
    ward_exectives = graphene.List(UserAllObject)

    def resolve_ward_exectives(root, info):
        users = CustomUser.objects.filter(role='ward_executive')
        return [
            UserAllObject(
                pk=user.pk,
                username=user.username,
                email=user.email,
                ward = user.ward,
                is_staff = user.is_staff,
                role = user.role,
            )
        for user in users
        ]
    


class BookedOpenSpaceQuery(graphene.ObjectType):
    booked_openspace = graphene.List(BookedOpenspaceObject)
    def resolve_booked_openspace(self, info):
        return OpenSpaceBooking.objects.all()



CustomerUser = get_user_model()
class ReplyToReportAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        report_id = request.data.get('report_id')
        message = request.data.get('message')

        if not report_id or not message:
            return Response({'error': 'Missing report_id or message'}, status=400)

        try:
            report = Report.objects.get(report_id=report_id)
        except Report.DoesNotExist:
            return Response({'error': 'Report not found'}, status=404)

        try:
            reply = ReportReply.objects.create(
                report=report,
                sender=request.user if request.user.is_authenticated else None,
                message=message
            )
            reply.save()

            # Send email if email exists
            if report.email:
                send_mail(
                    subject="Reply to Your Report",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[report.email],
                    fail_silently=False,
                )
            return Response({'success': 'Reply sent successfully'}, status=200)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
