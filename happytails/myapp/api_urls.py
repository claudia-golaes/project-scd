from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views
from myapp.views.adoption_views import AdoptionViewSet 
from myapp.views.visit_views import VisitViewSet


router = DefaultRouter()
router.register(r'animals', api_views.AnimalViewSet, basename='animal')
router.register(r'adoptions', AdoptionViewSet, basename='adoption') 
router.register(r'visits', VisitViewSet, basename='visit')  

urlpatterns = [
    path('', api_views.home, name='home'),
    path('api/', include(router.urls)),
    path('api/home/', api_views.home, name='api_home'),
    path('api/profile/', api_views.profile, name='api_profile'),
    path('api/logout/', api_views.custom_logout, name='api_logout'),
    path('api/register/', api_views.register_view, name='api_register'),
    path('api/admin-dashboard/', api_views.admin_dashboard, name='api_admin_dashboard'),
    path('api/volunteer-dashboard/', api_views.volunteer_dashboard, name='api_volunteer_dashboard'),
    path('api/debug/', api_views.debug_view, name='api_debug'),
]