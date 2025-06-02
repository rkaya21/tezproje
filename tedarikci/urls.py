from django.urls import path
from . import views

app_name = 'tedarikci'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('verify-email/', views.verify_email, name='verify_email'), # E-posta doğrulama POST isteği için
    path('verify-email-page/', views.tedarikci_verify_email_page, name='verify_email_page'), # E-posta doğrulama sayfasını göstermek için (GET)
    path('anasayfa/', views.tedarikci_anasayfa, name='tedarikci_anasayfa'), # Tedarikçi ana sayfası
    path('gida-formu/', views.tedarikci_gida_formu, name='tedarikci_gida_formu'), # Gıda ekleme formu
    path('gida-listesi/', views.tedarikci_food_list, name='tedarikci_food_list'), # Gıda listesi sayfası
    path('gelen-basvurular/', views.tedarikci_incoming_applications, name='tedarikci_incoming_applications'), # Gelen başvurular sayfası
    path('update-application-status/', views.update_application_status, name='update_application_status'), # Başvuru durumu güncelleme URL'i
    path('profilim/', views.tedarikci_profile, name='tedarikci_profile'), # Tedarikçi Profil sayfası URL'i
    
]