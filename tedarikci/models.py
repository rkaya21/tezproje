from django.db import models
from django.conf import settings

# Geçici kayıt verilerini tutmak için model
class TedarikciRegistrationData(models.Model):
    tedarikci_ad = models.CharField(max_length=150)
    temsilci_ad = models.CharField(max_length=40)
    temsilci_soyad = models.CharField(max_length=50)
    email = models.EmailField(max_length=150, unique=True)
    password = models.CharField(max_length=128) # Hashlenmiş şifre için daha uzun alan
    adres = models.TextField(unique=True)
    cep_telefon = models.CharField(max_length=11, unique=True)
    vergi_no = models.CharField(max_length=10, unique=True)
    vergi_levhasi = models.FileField(upload_to='vergi_levhalari/')
    verification_code = models.CharField(max_length=6)
    is_email_verified = models.BooleanField(default=False)
    # Admin onay alanı
    is_approved = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.tedarikci_ad

# Onaylanmış kullanıcılar için profil modeli (auth.User ile ilişkili)
class TedarikciProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tedarikci_profile')
    tedarikci_ad = models.CharField(max_length=150)
    temsilci_ad = models.CharField(max_length=40)
    temsilci_soyad = models.CharField(max_length=50)
    adres = models.TextField()
    cep_telefon = models.CharField(max_length=11)
    vergi_no = models.CharField(max_length=10, unique=True)
    

    def __str__(self):
        return self.tedarikci_ad

class FoodItem(models.Model): 
    tedarikci = models.ForeignKey(TedarikciProfile, on_delete=models.CASCADE, related_name='food_items') 
    name = models.CharField(max_length=200) 
    quantity = models.FloatField() # Kilo, litre veya adet için ondalıklı sayıya izin ver
    UNIT_CHOICES = [
        ('adet', 'Adet'),
        ('kilo', 'Kilo'),
        ('litre', 'Litre'),
    ]
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='adet') #  ölçü birimi (kg, litre, adet vb.)
    expiry_date = models.DateField() 
    FOOD_STATUS_CHOICES = [ ('iyi', 'İyi'), ('yaklasmis', 'Son kullanım tarihi yaklaşmış'), ('kotu', 'Kötü'), ] 
    status = models.CharField(max_length=20, choices=FOOD_STATUS_CHOICES) 
    image = models.ImageField(upload_to='food_images/') # Gıda resmi alanı (zorunlu yapıldı)

    # Yeni tahsis durumu alanı
    ALLOCATION_STATUS_CHOICES = [
        ('available', 'Başvurulabilir'),
        ('allocated', 'Tahsis Edildi'),
    ]
    allocation_status = models.CharField(max_length=20, choices=ALLOCATION_STATUS_CHOICES, default='available')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit}) - {self.tedarikci.tedarikci_ad} "
    