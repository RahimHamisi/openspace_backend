import graphene
from .models import *
from django.contrib.auth.models import User
from openspaceBuilders.openspaceBuilders import *
from openspace_dto.openspace import *
from .views import *
import graphql_jwt
from myapprest.views import *

class Mutation(graphene.ObjectType):
    register_user = RegistrationMutation.Field()
    login_user =   LoginUser.Field()
    register_report = ReportMutation.Field()
    create_report = CreateReport.Field()
    add_space = CreateOpenspaceMutation.Field()
    delete_open_space = DeleteOpenspace.Field()
    confirm_report = ConfirmReport.Field()
    delete_report = DeleteReport.Field()
    toggle_openspace_status = ToggleOpenspaceMutation.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    

class Query(OpenspaceQuery, TotalOpenSpaceQuery, ReportQuery, HistoryReportQuery, HistoryCountQuery, ReportCountQuery,ReportAnonymousQuery,AuthenticatedUserReport, UserProfileQuery, ReportUssdQuery, QueryUsers, BookedOpenSpaceQuery, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)