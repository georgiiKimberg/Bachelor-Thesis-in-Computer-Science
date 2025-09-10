from django.urls import path
from . import views 
#from .views import sequence_summary


app_name = "algebradb"


urlpatterns = [
    # path("", views.home, name = "home"), 
    path("search/", views.main_search, name = "main_search"),
    path("summary/", views.sequence_summary, name='sequence_summary'),
    path("admin/", views.admin_panel, name="admin_panel"),
    path("admin/upload/", views.add_entries, name="add_entries"),
    path("admin/delete/", views.delete_entries, name="delete_entries"),
    ]
