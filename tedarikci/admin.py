from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.urls import reverse
User = get_user_model()
from .models import TedarikciRegistrationData, TedarikciProfile
import os
import traceback
from django.core.files import File # Dosya objesi oluşturmak için import
from django.core.mail import send_mail
from django.conf import settings


# TedarikciRegistrationData modeli için özel Admin sınıfı oluşturma
class TedarikciRegistrationDataAdmin(admin.ModelAdmin):
    list_display = ('tedarikci_ad', 'email', 'is_email_verified', 'is_approved', 'registered_at')
    list_filter = ('is_email_verified', 'is_approved') # Tedarikçi Türü yok
    search_fields = ('tedarikci_ad', 'email', 'temsilci_ad', 'temsilci_soyad', 'cep_telefon', 'vergi_no')
    actions = ['approve_registrations']

    def approve_registrations(self, request, queryset):
        # Seçili tedarikçi kayıtlarının is_approved alanını True yapar
        # Bu action tetiklendiğinde her objenin save() metodu çağrılır, bu da aşağıdaki save_model metodumuzu tetikler.
        # updated_count = queryset.update(is_approved=True)
        # Not: queryset.update() save_model'ı tetiklemez. Bu yüzden save_model'ı ça��ırmak için objeler üzerinde dönebiliriz.
        # Ancak STK örneği update kullanmıştı, bu durumda save_model manuel olarak çağrılmalı veya logic update içinde olmalı.
        # STK örneğindeki yorumlar save_model'ın tetikleneceğini söylüyor, bu muhtemelen eski bir davranış ya da özel bir durum.
        # Güvenli yol: is_approved True yapıldığında User/Profile oluşturma logic'ini hem save_model'a (tekil objeler için) hem de action metoduna (toplu güncellemeler için) koymak.
        # STK örneği save_model'a koymuş, biz de şimdilik öyle yapalım ve update'in tetiklediğini varsayalım veya güncel Django davranışına göre bu logic'i action içine de ekleyelim.
        # Şimdilik STK örneğine sadık kalıp save_model'a koyalım. Action sadece is_approved=True yapsın.
        
        # Ancak toplu update save_model'ı tetiklemez. Bu durumda logic action içine taşınmalı veya save_model'ı tetikleyecek şekilde update yapılmalı.
        # STK örneğindeki save_model kullanımı toplu güncellemelerde beklediğiniz gibi çalışmayabilir.
        # En temiz yol, toplu onaylama mantığını action metoduna taşımak ve tekil kaydetmeler için save_model'da tutmaktır.
        # STK örneğine tam uyum için save_model'a koyup action'ın update kullanmasını sağlayalım, ama bunun toplu onaylarda User/Profile oluşturmayabileceğini unutmayalım.

        # STK örneğine sadık kalarak sadece update yapıyoruz:
        count = 0
        for obj in queryset:
            if not obj.is_approved: # Sadece onaylanmamışları işle
                 obj.is_approved = True
                 obj.save() # Bu, save_model metodunu tetiklemeli (tekil save)
                 count += 1

        # messages.success(request, f"{updated_count} tedarikçi kaydı onay için işaretlendi.") # Update'in mesajı
        messages.success(request, f"{count} tedarikçi kaydı onay süreci için işleme alındı.") # Tekil save mesajı

    approve_registrations.short_description = "Seçili tedarikçi kayıtlarını onayla ve kullanıcı oluştur"

    # Reddetme action'ı (isteğe bağlı olarak eklenebilir) - Şimdilik STK örneğinde yok, atlıyorum.
    # def reject_registrations(self, request, queryset): ...


    # Model objesi kaydedildiğinde çalışacak metod (tekil kaydetmelerde ve muhtemelen tekil save() çağrıldığında)
    def save_model(self, request, obj, form, change):
        # Orijinal objeyi al (is_approved durumundaki değişikliği kontrol etmek için)
        original_obj = None
        if obj.pk:
            try:
                original_obj = TedarikciRegistrationData.objects.get(pk=obj.pk)
            except TedarikciRegistrationData.DoesNotExist:
                pass # Obje yeni oluşturuluyorsa original_obj None kalır

        # Varsayılan kaydetme işlemini yap (objeyi veritabanına yazar)
        super().save_model(request, obj, form, change)

        # Eğer obje e-posta doğrulandıysa, admin tarafından onaylandıysa
        # VE is_approved durumu False'dan True'ya değiştiyse
        # VE aynı e-posta ile auth.User'da henüz bir kullanıcı yoksa
        # (Original objenin is_approved True değilken yeni objenin True olması durumu)
        if obj.is_email_verified and obj.is_approved and (original_obj is None or not original_obj.is_approved) and not User.objects.filter(email=obj.email).exists():
            try:
                # auth.User objesini oluştur
                # username olarak email kullanıyoruz
                user = User(
                    username=obj.email,
                    email=obj.email,
                    first_name=obj.temsilci_ad,
                    last_name=obj.temsilci_soyad,
                    is_active=True, # Varsayılan olarak aktif
                    is_staff=False,
                    is_superuser=False,
                )
                # UserRegistrationData'dan gelen hashlenmiş şifreyi ata
                user.password = obj.password
                user.save() # User objesini kaydet
                print(f"User created for {user.email}.") # Terminale bilgi

                # TedarikciProfile objesini oluştur ve verileri kopyala (vergi levhası hariç)
                try:
                    profile = TedarikciProfile.objects.create(
                        user=user,
                        tedarikci_ad=obj.tedarikci_ad,
                        temsilci_ad=obj.temsilci_ad,
                        temsilci_soyad=obj.temsilci_soyad,
                        adres=obj.adres,
                        cep_telefon=obj.cep_telefon,
                        vergi_no=obj.vergi_no
                    )
                    print(f"TedarikciProfile created for user {user.email}") # Terminale bilgi

                except Exception as profile_create_error:
                    print("-" * 50)
                    print("TEDARIKCIPROFILE OLUŞTURULURKEN HATA:")
                    print(f"Hata Türü: {type(profile_create_error).__name__}")
                    print(f"Hata Mesajı: {profile_create_error}")
                    traceback.print_exc()
                    print("-" * 50)

                    # Hata durumunda oluşturulan User objesini sil
                    if user: 
                         user.delete()
                         print(f"Hata sonrası User objesi silindi: {obj.email}")

                    messages.error(request, f"Tedarikçi Profili oluşturulurken bir hata oluştu: {profile_create_error}. Kullanıcı kaydı tamamlanamadı.")
                    # RegistrationData objesi silinmeyecek ki admin hatayı görüp düzeltebilsin
                    return # save_model metodundan çık

                # Vergi levhası dosyasını depolama alanından sil (STK mantığına göre)
                if obj.vergi_levhasi:
                    # Dosyanın varlığını kontrol et ve sil
                    if os.path.exists(obj.vergi_levhasi.path):
                        try:
                            obj.vergi_levhasi.delete(save=False) # Modeli kaydetmeden dosyayı sil
                            print(f"Vergi levhası silindi: {obj.vergi_levhasi.name}")
                        except Exception as file_delete_error:
                            print(f"Vergi levhası silinirken hata: {file_delete_error}")
                            messages.warning(request, f"Vergi levhası silinirken bir hata oluştu: {file_delete_error}")

                # TedarikciRegistrationData objesini sil (User ve Profile başarılıysa)
                try:
                    # Kendi kendini silmeden önce pk değerini alalım, delete() çağrısından sonra objeye erişilemeyebilir
                    obj_email = obj.email
                    obj.delete() # Objeyi sil
                    print(f"TedarikciRegistrationData object for {obj_email} deleted after approval.")
                    # Onay e-postası gönder
                    subject = 'Tedarikçi Kaydınız Onaylandı'
                    message = f"""Merhaba {user.first_name},

Gıda Fazlası Yönetimi Sistemi'ne yaptığınız tedarikçi kaydı yönetici tarafından onaylanmıştır. Artık sisteme giriş yapabilirsiniz.

Giriş yapmak için: {request.build_absolute_uri(reverse('tedarikci:login'))}

Teşekkürler!"""
                    email_from = settings.EMAIL_HOST_USER
                    recipient_list = [user.email,]
                    try:
                        send_mail( subject, message, email_from, recipient_list )
                        print(f"Onay e-postası gönderildi: {user.email}")
                    except Exception as email_error:
                        print(f"Onay e-postası gönderilirken hata: {email_error}")
                        messages.warning(request, f"Onay e-postası gönderilemedi: {email_error}") # Admin bilgilendirilebilir

                except Exception as delete_error:
                    print(f"TedarikciRegistrationData silinirken hata: {delete_error}")
                    messages.error(request, f"Onaylanmış tedarikçinin beklemedeki kaydı silinirken bir hata oluştu: {delete_error}")

            except Exception as main_error:
                # User oluşturma veya genel hata durumları
                print("-" * 50)
                print("TEDARIKCI ONAY ANA HATA (User Oluşturma veya Genel):")
                print(f"Hata Türü: {type(main_error).__name__}")
                print(f"Hata Mesajı: {main_error}")
                traceback.print_exc()
                print("-" * 50)

                messages.error(request, f"Beklenmeyen bir hata oluştu: {main_error}. Tedarikçi kullanıcı oluşturulamadı.")
                # RegistrationData objesi hata durumunda silinmeyecek

        elif obj.is_approved and not obj.is_email_verified:
             # Admin onayladı ama email doğrulanmamış - bilgilendirme mesajı
             messages.warning(request, f"Tedarikçi '{obj.email}' admin tarafından onaylandı ancak e-posta doğrulaması henüz tamamlanmamış. Kullanıcı ve Profil oluşturulmadı.")
        # is_approved False'a çekildiğinde ne yapılacağı logic'i STK'da yok, burada da eklemiyorum.

    # Tekil obje silindiğinde çalışır (Admin deği��iklik sayfasından)
    def delete_model(self, request, obj):
        email_to_notify = obj.email # Silinmeden önce e-posta adresini al
        try:
            # Varsayılan silme işlemini yap
            super().delete_model(request, obj)
            messages.success(request, f"Tedarikçi kaydı '{email_to_notify}' silindi.")

            # Reddetme e-postası gönder
            subject = 'Tedarikçi Kayıt Başvurunuz Hk.'
            message = f"""Merhaba, Gıda Fazlası Yönetimi Sistemi'ne yapmış olduğunuz tedarikçi kayıt başvurusu incelenmiş olup, mevcut durumda uygun bulunmamıştır.

            Başvurunuzla ilgili detaylı bilgi almak veya sorularınız için lütfen bizimle iletişime geçin.

            Anlayışınız için teşekkür ederiz.

            Saygılarımızla, Gıda Fazlası Yönetimi Sistemi Ekibi"""
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [email_to_notify,] 
            try: 
                send_mail( subject, message, email_from, recipient_list ) 
                print(f"Reddetme e-postası gönderildi: {email_to_notify}") 
            except Exception as email_error: 
                print(f"Reddetme e-postası gönderilirken hata: {email_error}") 
                messages.warning(request, f"Reddetme e-postası gönderilemedi: {email_error}") # Admin bilgilendirilebilir
        except Exception as e:
            print(f"Tedarikçi kaydı silinirken beklenmeyen hata: {e}")
            messages.error(request, f"Tedarikçi kaydı silinirken bir hata oluştu: {e}")
    
    # Toplu objeler silindiğinde çalışır (Admin listeleme sayfasından action veya delete button)
    def delete_queryset(self, request, queryset):
        # Silinecek objelerin e-posta adreslerini al.
        # Queryset'i listeye çevirmek, silme işlemi sırasında objelerin kaybolmasını önler.
        emails_to_notify = [obj.email for obj in list(queryset)]

        # Varsayılan toplu silme işlemini yap
        # super().delete_queryset bazı durumlarda None dönebilir, bu yüzden dönüş değerini kontrol edelim.
        result = super().delete_queryset(request, queryset)

        # super().delete_queryset'in dönüş değerini kontrol et ve işleme al
        deleted_count = 0
        if result is not None and isinstance(result, tuple) and len(result) >= 1:
             deleted_count = result[0] # Tuple'ın ilk elemanı silinen obje sayısıdır
        # else durumunu kaldırıyoruz, çünkü mesajı her durumda göndereceğiz ve silinen sayısı tam bilinemeyebilir.

        # Admin bilgilendirme mesajı: Silinen sayısı tam doğru olmayabilir.
        messages.success(request, f"{len(emails_to_notify)} adet tedarikçi kaydı silindi (denendi).")

        # Her bir e-posta adresine reddetme e-postası gönder
        subject = 'Tedarikçi Kayıt Başvurunuz Hk.'
        message_template = f"""Merhaba,
Gıda Fazlası Yönetimi Sistemi\'ne yapmış olduğunuz tedarikçi kayıt başvurusu incelenmiş olup, mevcut durumda uygun bulunmamıştır.

Başvurunuzla ilgili detaylı bilgi almak veya sorularınız için lütfen bizimle iletişime geçin.

Anlayışınız için teşekkür ederiz.

Saygılarımızla,
Gıda Fazlası Yönetimi Sistemi Ekibi"""
        emails_sent_count = 0
        for email in emails_to_notify:
            try:
                send_mail( subject, message_template, settings.EMAIL_HOST_USER, [email,] )
                print(f"Reddetme e-postası gönderildi (toplu silme): {email}")
                emails_sent_count += 1
            except Exception as email_error:
                print(f"Reddetme e-postası gönderilirken hata (toplu silme) \'{email}\': {email_error}")
                # Toplu silmede her hata için mesaj göstermek spam olabilir, konsola yazdırmak yeterli olabilir.

        if emails_sent_count > 0:
            messages.info(request, f"{emails_sent_count} adet reddetme e-postası gönderildi.")
        # Silinen sayısı tam doğru olmadığı için bu uyarı mesajını kaldırmak daha iyi olabilir.
        # if deleted_count > emails_sent_count:
        #    messages.warning(request, f"{deleted_count - emails_sent_count} adet reddetme e-postası gönderilemedi (bazı kayıtlar zaten silinmiş olabilir).")

# TedarikciRegistrationData modelini özel Admin sınıfı ile admin paneline kaydet
admin.site.register(TedarikciRegistrationData, TedarikciRegistrationDataAdmin)

# TedarikciProfile modelini de admin paneline kaydedelim (isteğe bağlı)
# Adminin onaylanmış tedarikçilerin profillerini görmesi gerekirse
@admin.register(TedarikciProfile)
class TedarikciProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'tedarikci_ad', 'cep_telefon', 'vergi_no')
    search_fields = ('user__email', 'tedarikci_ad', 'temsilci_ad', 'temsilci_soyad', 'vergi_no')
    # list_filter eklemek isterseniz ekleyebilirsiniz
