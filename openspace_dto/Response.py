import graphene
from  .openspace import *

class RegistrationResponse(graphene.ObjectType):
    message = graphene.String()
    success = graphene.Boolean()
    user = graphene.Field(RegisterObject)
    
class OpenspaceResponse(graphene.ObjectType):
    message = graphene.String()
    success = graphene.Boolean()
    openspace = graphene.Field(OpenspaceObject)
    
class ReportResponse(graphene.ObjectType):
    message = graphene.String()
    success = graphene.Boolean()
    report = graphene.Field(ReportObject)