from django.urls import path
from . import views # Aynı klasördeki views dosyasını import et

app_name = 'stk' # Bu satır 'stk' namespace'ini tanımlar

urlpatterns = [
    # Kayıt formunun gönderileceği URL
    # HTML formundaki {% url 'stk:your_view_name'%} buraya işaret ediyor
    path('register/', views.register_user, name='register'),
    path('login/',views.login_user, name='login'),
    path('verify_email/', views.verify_email, name='verify_email'),
    path('main/',views.main_user, name='main'),
    path('gida-vitrini/', views.stk_food_showcase, name='stk_food_showcase'), # Gıda vitrini sayfası
    path('basvur/', views.apply_for_food, name='apply_for_food'), # Gıda başvurusu yapma URL'i (AJAX için)
    path('basvurularim/', views.stk_my_applications, name='stk_my_applications'), # Gıda Başvurularım sayfası
    path('test-durumu/', views.stk_test_status, name='stk_test_status'), # Test Durumu sayfası için yeni URL
    path('test-sonucu-kaydet/', views.set_test_result, name='set_test_result'), # Test sonucunu kaydetme URL'i
    path('nihai-hedef-belirle/', views.set_final_destination, name='set_final_destination'), 
    # Toplu Soğuk depoya gönderme URL'i
    path('soguk-depoya-gonder-toplu/', views.send_to_cold_storage, name='send_to_cold_storage'), 
    # Tekil soğuk depoya gönderme URL'iSoğuk depoya gönderme URL'i
    path('soguk-depoya-gonder-tekil/', views.send_to_cold_storage_single, name='send_to_cold_storage_single'), 
    path('depo-durumu/', views.stk_warehouse_status, name='stk_warehouse_status'), # Depo Durumu sayfası için yeni URL
    path('mark-as-distributed/', views.mark_as_distributed, name='mark_as_distributed'), # Gıda dağıtıldı olarak işaretleme URL'i
    path('delivery-status/', views.delivery_status, name='delivery_status'),
    path('profilim/', views.stk_profile, name='stk_profile'), # STK Profil sayfası URL'i

    
    
    # İsterseniz kayıt sayfasını gösteren URL'yi de buraya ekleyebilirsiniz
    # path('kayit/', views.register_page_view, name='kayit_sayfasi'),
]