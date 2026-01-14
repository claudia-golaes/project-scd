from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views
from myapp.views.adoption_views import AdoptionViewSet 
from myapp.views.visit_views import VisitViewSet
from myapp.views.activity_views import ActivityViewSet


router = DefaultRouter()
router.register(r'animals', api_views.AnimalViewSet, basename='animal')
router.register(r'adoptions', AdoptionViewSet, basename='adoption') 
router.register(r'visits', VisitViewSet, basename='visit')  
router.register(r'activities', ActivityViewSet, basename='activity') 


urlpatterns = [
    path('', api_views.home, name='home'),
    path('api/', include(router.urls)),
    path('api/home/', api_views.home, name='api_home'),
    path('api/profile/', api_views.profile, name='api_profile'),
    path('api/logout/', api_views.custom_logout, name='api_logout'),
    path('api/register/', api_views.register_view, name='api_register'),
    path('api/debug/', api_views.debug_view, name='api_debug'),
]