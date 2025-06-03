"""
URL configuration for warden project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt # Required for GraphQL
from graphene_django.views import GraphQLView
from warden_app.schema import schema as warden_app_schema # Import your app's schema

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('warden_app.urls')), # REST API endpoints
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True, schema=warden_app_schema))), # GraphQL endpoint
    path('', include('warden_app.urls')), # Frontend interface - Make sure this is specific enough or handled by warden_app.urls
]
