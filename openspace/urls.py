from django.conf import settings
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from django.urls import path, include
from django.conf.urls.static import static

# from myapp.views import verify_email

urlpatterns = [
    path('admin/', admin.site.urls),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    path('Api/', include('myapp.urls')),
    path('api/v1/', include('myapprest.urls')),
    # path('verify-email/<uuid:token>/', verify_email, name='verify_email'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
