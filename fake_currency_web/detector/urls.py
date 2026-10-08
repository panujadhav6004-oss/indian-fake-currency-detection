from django.urls import path
from . import views
from detector import views

urlpatterns = [
    path("history/", views.history, name="history"),

    path("export/pdf/", views.export_pdf, name="export_pdf"),
    path("export/excel/", views.export_excel, name="export_excel"),

    path("delete/<int:id>/", views.delete_record, name="delete_record"),
    path("delete-all/", views.delete_all_history, name="delete_all"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path('', views.login_view, name='login'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('subscribe/<int:months>/', views.subscribe_view, name='subscribe'),
    path('payment/processing/<int:payment_id>/', views.payment_processing_view, name='payment_processing'),
    path('payment/success/<int:payment_id>/', views.payment_success_view, name='payment_success'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
