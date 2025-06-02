from django.db import models
from django.contrib.auth import get_user_model
from tedarikci.models import FoodItem

# Create your models here.

class UserRegistrationData(models.Model):
    """
    Kullanıcı kayıt formundan gelen verileri tutar.
    """
    stk_ad = models.CharField(max_length=150, unique=True)
    stk_temsilci_ad = models.CharField(max_length=40)
    stk_temsilci_soyad = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    # Şifreleri şifrelenmiş olarak saklamak daha güvenlidir.
    # Gerçek bir uygulamada şifreler mutlaka hashlenmelidir.
    password = models.CharField(max_length=128) # Basitçe tutuyoruz, hashlemek gerek
    adres = models.TextField(unique=True)
    cep_telefon = models.CharField(max_length=11, unique=True)
    stk_turu = models.CharField(max_length=10) # 'dernek' veya 'vakif'
    kutuk_no = models.CharField(max_length=10, unique=True, blank=True, null=True) # Opsiyonel alanlar için blank=True, null=True
    etebligat = models.CharField(max_length=19, unique=True, blank=True, null=True) # Opsiyonel alanlar için blank=True, null=True
    faaliyet_belgesi = models.FileField(upload_to='faaliyet_belgeleri/') # Dosyalar için upload_to belirttik
    registered_at = models.DateTimeField(auto_now_add=True)
    # E-posta doğrulama alanları
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    # Admin onay alanı
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.stk_ad + " (" + self.stk_temsilci_ad + " " + self.stk_temsilci_soyad + ")"

User = get_user_model() # Django'nun aktif User modelini alırız

class Profile(models.Model):
    """
    Onaylanmış kullanıcıların ek STK bilgilerini tutar.
    auth.User modeline OneToOneField ile bağlıdır.
    """
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile') # auth.User modeline bağlı, related_name ekledik

    stk_ad = models.CharField(max_length=150) # unique=True burada olmayacak, UserRegistrationData'daydı geçici olarak
    stk_temsilci_ad = models.CharField(max_length=40)
    stk_temsilci_soyad = models.CharField(max_length=50)
    adres = models.TextField()
    cep_telefon = models.CharField(max_length=11)
    stk_turu = models.CharField(max_length=10)
    kutuk_no = models.CharField(max_length=10, blank=True, null=True)
    etebligat = models.CharField(max_length=19, blank=True, null=True)
    
    # Faaliyet belgesi buraya EKLENMEYECEK

    def __str__(self):
        return f"Profile of {self.user.email}"


class FoodApplication(models.Model):
    stk_profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='food_applications')
    food_item = models.ForeignKey(FoodItem, on_delete=models.CASCADE, related_name='applications')
    

    APPLICATION_STATUS_CHOICES = [
    ('pending', 'Beklemede'),
    ('approved', 'Onaylandı'),
    ('rejected', 'Reddedildi'),
    ('awaiting_distribution', 'Dağıtım Bekliyor'), 
    ('completed', 'Tamamlandı'), # Teslimat sonrası için
    ]

    # Yeni alanlar eklendi
    TEST_RESULT_CHOICES = [
        ('awaiting_test', 'Test Bekleniyor'),
        ('edible', 'Yenilebilir'),
        ('inedible', 'Yenilemez'),
    ]
    
    FINAL_DESTINATION_CHOICES = [
        ('awaiting_test_result', 'Test Sonucu Bekleniyor'),
        ('cold_storage', 'Soğuk Hava Deposu'),
        ('compost_center', 'Gübre Atık Merkezi'),
        ('disposal', 'İmha Edilecek'),
        ('distributed', 'Dağıtıldı'),
    ]

    status = models.CharField(max_length=50, choices=APPLICATION_STATUS_CHOICES, default='pending')
    test_result = models.CharField(max_length=50, choices=TEST_RESULT_CHOICES, default='awaiting_test')
    final_destination = models.CharField(max_length=50, choices=FINAL_DESTINATION_CHOICES, default='awaiting_test_result')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('stk_profile', 'food_item') # Bir STK'nın aynı gıdaya birden fazla başvurmasını engelle
    
    def __str__(self):
        return f"STK: {self.stk_profile.stk_ad} -> Gıda: {self.food_item.name} (Başvuru: {self.status}, Test: {self.get_test_result_display()})"
    
    