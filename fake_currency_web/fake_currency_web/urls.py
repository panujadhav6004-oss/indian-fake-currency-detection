from django.contrib import admin

admin.site.site_header = "Fake Currency Detection Admin"
admin.site.site_title = "Fake Currency Admin"
admin.site.index_title = "Welcome Admin"
admin.site.site_header = "Fake Currency Detection Admin"
admin.site.site_title = "Fake Currency System"
admin.site.index_title = "Welcome to Fake Currency Detection Dashboard"

from django.contrib import admin
from django.urls import path
from detector import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from detector.views import admin_dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'), 
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path("", include("detector.urls")),
    path('register/', views.register_view, name='register'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('subscribe/<int:months>/', views.subscribe_view, name='subscribe'),
    path('payment/processing/<int:payment_id>/', views.payment_processing_view, name='payment_processing'),
    path('payment/success/<int:payment_id>/', views.payment_success_view, name='payment_success'),
    path('logout/', views.logout_view, name='logout'),
    path('detector/', views.detector_view, name='detector'),
    path("history/", views.history, name="history"),
    path("delete/<int:id>/", views.delete_record, name="delete_record"),
    path("delete-all/", views.delete_all_history, name="delete_all"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),
    path("export/excel/", views.export_excel, name="export_excel"),
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),


   
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
]
