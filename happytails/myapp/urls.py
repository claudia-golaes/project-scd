from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("animals/", views.animals, name="animals"),
    path("animals/add/", views.add_animal, name='add_animal'),
    path('animals/edit/<int:animal_id>/', views.edit_animal, name='edit_animal'),
    path('animals/<int:animal_id>/', views.animal_info, name='animal_info'),
    path('animals/delete/<int:animal_id>/', views.delete_animal, name='delete_animal'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('favorites/toggle/<int:animal_id>/', views.toggle_favorite, name='toggle_favorite'),
    path("login/", views.login_view, name="login"),
    path('logout/', views.custom_logout, name='logout'),
    path("profile/", views.profile, name="profile"),
    path("register/", views.register_view, name="register"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("volunteer-dashboard/", views.volunteer_dashboard, name="volunteer_dashboard"),
    path("debug/", views.debug_view, name="debug"),
]