from django.contrib import admin
from django.contrib import messages # messages framework için
from django.contrib.auth import get_user_model # auth.User modelini almak için
User = get_user_model() # Django'nun aktif User modelini alırız
from .models import UserRegistrationData, Profile # Profile modelini import et
import os # Dosya silme için gerekli olabilir
import traceback # Hata detayını almak için import et
from django.core.mail import send_mail # E-posta gönderme için import
from django.conf import settings # Settings'e erişim için import
from django.urls import reverse # URL ters çözümleme için import

# UserRegistrationData modeli için özel Admin sınıfı oluşturma
class UserRegistrationDataAdmin(admin.ModelAdmin):
    # Admin listeleme sayfasında görünecek alanlar
    list_display = ('stk_ad', 'email', 'is_email_verified', 'is_approved', 'registered_at')

    # Admin listeleme sayfasında filtreleme seçenekleri
    list_filter = ('is_email_verified', 'is_approved', 'stk_turu')

    # Admin listeleme sayfasında arama yapılabilecek alanlar
    search_fields = ('stk_ad', 'email', 'stk_temsilci_ad', 'stk_temsilci_soyad', 'cep_telefon', 'kutuk_no', 'etebligat')

    # Kayıt detay sayfasında alanların sıralaması (isteğe bağlı)
    # fields = (...) veya fieldsets = (...) ile daha detaylı kontrol sağlanabilir.

    # Admin panelinden is_approved durumunu toplu güncellemek için action ekleyelim
    actions = ['approve_users']

    def approve_users(self, request, queryset):
        # Seçili kullanıcıların is_approved alanını True yapar
        # Bu action tetiklendiğinde her objenin save() metodu çağrılır,
        # bu da aşağıdaki save_model metodumuzu tetikler.

        # updated_count = queryset.update(is_approved=True)
        # self.message_user(request, f"{updated_count} kullanıcı onay için işaretlendi. Kaydedildiklerinde User ve Profile oluşturulacaktır.", messages.SUCCESS)

        # STK örneğindeki save_model'ın toplu update ile tetiklenme durumu belirsiz olduğundan,
        # tek tek save çağırarak save_model'ın çalıştığını garanti edelim.
        count = 0
        for obj in queryset:
            if not obj.is_approved: # Sadece onaylanmamışları işle
                 obj.is_approved = True
                 obj.save() # Bu, save_model metodunu tetiklemeli (tekil save)
                 count += 1

        if count > 0:
            messages.success(request, f"{count} STK kaydı onay süreci için işleme alındı.")

    approve_users.short_description = "Seçili kullanıcıları onayla"

    def save_model(self, request, obj, form, change):
        # Orijinal objeyi al (eğer değişiklik yapılıyorsa)
        # Bu, is_approved alanının gerçekten değişip değişmediğini kontrol etmek için

        # if change:
        #     try:
        #         original_obj = UserRegistrationData.objects.get(pk=obj.pk)
        #     except UserRegistrationData.DoesNotExist:
        #         original_obj = None
        # else:
        #     original_obj = None

        original_obj = None
        if obj.pk:
            try:
                original_obj = UserRegistrationData.objects.get(pk=obj.pk)
            except UserRegistrationData.DoesNotExist:
                pass # Obje yeni oluşturuluyorsa original_obj None kalır
        else:
            original_obj = None

        # Varsayılan kaydetme işlemini yap
        super().save_model(request, obj, form, change)

        # Eğer obje hem e-posta doğrulandıysa hem de admin tarafından onaylandıysa
        # VE is_approved durumu False'dan True'ya değiştiyse
        # VE aynı e-posta ile auth.User'da henüz bir kullanıcı yoksa
        if obj.is_email_verified and obj.is_approved and (original_obj is None or not original_obj.is_approved) and not User.objects.filter(email=obj.email).exists():
            try:
                # auth.User objesini oluştur
                # create_user yerine doğrudan User objesi oluşturup password atayacağız
                user = User(
                    username=obj.email, # E-postayı kullanıcı adı olarak kullan
                    email=obj.email,
                    # Diğer standart User alanları (isteğe bağlı)
                    first_name=obj.stk_temsilci_ad,
                    last_name=obj.stk_temsilci_soyad,
                    is_active=True, # Yeni oluşturulan kullanıcılar varsayılan olarak aktif olsun
                    is_staff=False, # Admin panel erişimi olmasın
                    is_superuser=False, # Superuser olmasın
                )
                # UserRegistrationData'dan gelen birinci kez hashlenmiş şifreyi doğrudan ata
                user.password = obj.password
                user.save() # User objesini kaydet
                # User objesini kaydetmeye gerek yok, create_user otomatik yapar
                print(f"User created for {user.email}.") # Terminale bilgi yazdır

                # Profile objesini oluştur ve verileri kopyala (faaliyet belgesi hariç)
                try:
                    profile = Profile.objects.create(
                        user=user,
                        stk_ad=obj.stk_ad,
                        stk_temsilci_ad=obj.stk_temsilci_ad,
                        stk_temsilci_soyad=obj.stk_temsilci_soyad,
                        adres=obj.adres,
                        cep_telefon=obj.cep_telefon,
                        stk_turu=obj.stk_turu,
                        kutuk_no=obj.kutuk_no,
                        etebligat=obj.etebligat
                    )
                    # Profile objesini kaydetmeye gerek yok, create metodu otomatik yapar
                    print(f"Profile created for user {user.email}") # Terminale bilgi yazdır

                except Exception as profile_create_error:
                    print("-" * 50) # Ayırıcı çizgiler
                    print("PROFILE OLUŞTURULURKEN HATA:")
                    print(f"Hata Türü: {type(profile_create_error).__name__}")
                    print(f"Hata Mesajı: {profile_create_error}")
                    traceback.print_exc() # Hata detayını terminale yazdır
                    print("-" * 50)

                    # Hata durumunda oluşturulan User objesini sil
                    if user: # User objesi oluşturulduysa sil
                         user.delete()
                         print(f"Hata sonrası User objesi silindi: {obj.email}")

                    messages.error(request, f"Profil oluşturulurken bir hata oluştu: {profile_create_error}. Kullanıcı kaydı tamamlanamadı.")
                    return # save_model metodundan çık, UserRegistrationData silinmeyecek

                # Faaliyet belgesi dosyasını depolama alanından sil
                if obj.faaliyet_belgesi:
                    # Dosyanın varlığını kontrol et
                    if os.path.exists(obj.faaliyet_belgesi.path):
                        try:
                            obj.faaliyet_belgesi.delete(save=False) # Modeli kaydetmeden dosyayı sil
                            print(f"Faaliyet belgesi silindi: {obj.faaliyet_belgesi.name}")
                        except Exception as file_delete_error:
                            print(f"Faaliyet belgesi silinirken hata: {file_delete_error}")
                            messages.warning(request, f"Faaliyet belgesi silinirken bir hata oluştu: {file_delete_error}")

                # UserRegistrationData objesini sil
                # Eğer buraya kadar geldiysek User ve Profile başarılı
                try:
                    obj_email = obj.email 
                    obj.delete()
                    print(f"UserRegistrationData object for {obj_email} deleted.")
                    messages.success(request, f"Kullanıcı '{user.email}' başarıyla oluşturuldu, profili oluşturuldu ve beklemedeki kayıt silindi.")

                    # Onay e-postası gönder
                    subject = 'STK Kaydınız Onaylandı'
                    message = f"""Merhaba {user.first_name},

Gıda Fazlası Yönetimi Sistemi\'ne yaptığınız STK kaydı yönetici tarafından onaylanmıştır. Artık sisteme giriş yapabilirsiniz.

Giriş yapmak için: {request.build_absolute_uri(reverse('stk:login'))}

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
                    print(f"UserRegistrationData silinirken hata: {delete_error}")
                    messages.error(request, f"Beklemedeki kayıt silinirken bir hata oluştu: {delete_error}")

            except Exception as main_error:
                # Ana try bloğunda User oluşturma veya başka bir genel hata
                print("-" * 50) # Ayırıcı çizgiler
                print("ANA HATA (User Oluşturma veya Genel):")
                print(f"Hata Türü: {type(main_error).__name__}")
                print(f"Hata Mesajı: {main_error}")
                traceback.print_exc() # Hata detayını terminale yazdır
                print("-" * 50)

                # Hata durumunda objeyi silmeyiz
                messages.error(request, f"Beklenmeyen bir hata oluştu: {main_error}. Kullanıcı oluşturulamadı.")
        elif obj.is_email_verified and obj.is_approved and original_obj is not None and original_obj.is_approved:
             # Eğer zaten onaylanmış bir kayıtta bir değişiklik yapılıyorsa (User ve Profile zaten oluşmuş olmalı)
             messages.info(request, f"Kullanıcı '{obj.email}' zaten onaylanmış. Bilgiler güncellendi (User/Profile yeniden oluşturulmadı).")
        elif obj.is_approved and not obj.is_email_verified:
             # Admin onayladı ama email doğrulanmamış
             messages.warning(request, f"Kullanıcı '{obj.email}' admin tarafından onaylandı ancak e-posta doğrulaması henüz tamamlanmamış. User/Profile oluşturulmadı.")
        elif not obj.is_approved and obj.is_email_verified and original_obj is not None and original_obj.is_approved:
             # Admin onayı kaldırıldı
             # Bu durumda User ve Profile silinmeli mi? Şimdilik silmiyoruz, mantığı eklemek gerekebilir.
             messages.warning(request, f"Kullanıcı '{obj.email}' admin onayı kaldırıldı. User/Profile silinmedi.")
    
    # Tekil obje silindiğinde çalışır (Admin değişiklik sayfasından)
    def delete_model(self, request, obj):
        email_to_notify = obj.email # Silinmeden önce e-posta adresini al
        try:
            # Varsayılan silme işlemini yap
            super().delete_model(request, obj)
            messages.success(request, f"STK kaydı \'{email_to_notify}\' silindi.")

            # Reddetme e-postası gönder
            subject = 'STK Kayıt Başvurunuz Hk.'
            message = f"""Merhaba,
            Gıda Fazlası Yönetimi Sistemi\'ne yapmış olduğunuz STK kayıt başvurusu incelenmiş olup, mevcut durumda uygun bulunmamıştır.

            Başvurunuzla ilgili detaylı bilgi almak veya sorularınız için lütfen bizimle iletişime geçin.

            Anlayışınız için teşekkür ederiz.

            Saygılarımızla,
            Gıda Fazlası Yönetimi Sistemi Ekibi"""
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [email_to_notify,]
            try:
                send_mail( subject, message, email_from, recipient_list )
                print(f"Reddetme e-postası gönderildi: {email_to_notify}")
            except Exception as email_error:
                print(f"Reddetme e-postası gönderilirken hata: {email_error}")
                messages.warning(request, f"Reddetme e-postası gönderilemedi: {email_error}") # Admin bilgilendirilebilir

        except Exception as e:
            print(f"STK kaydı silinirken beklenmeyen hata: {e}")
            messages.error(request, f"STK kaydı silinirken bir hata oluştu: {e}")


    # Toplu objeler silindiğinde çalışır (Admin listeleme sayfasından action veya delete button)
    def delete_queryset(self, request, queryset):
        # Silinecek objelerin e-posta adreslerini al.
        # Queryset'i listeye çevirmek, silme işlemi sırasında objelerin kaybolmasını önler.
        emails_to_notify = [obj.email for obj in list(queryset)] 

        try:
            # Varsayılan toplu silme işlemini yap
            # super().delete_queryset bazı durumlarda None dönebilir, bu yüzden dönüş değerini kontrol edelim.
            result = super().delete_queryset(request, queryset)

            if result is not None and isinstance(result, tuple):
                deleted_count, _ = result
            else:
                # Eğer dönüş değeri None ise veya tuple değilse, silinen sayısını queryset'in orijinal boyutundan tahmin edebiliriz,
                # ancak tam doğru olmayabilir eğer bazı objeler zaten silinmişse.
                # Güvenli bir sayı almak zor, mesajı ona göre ayarlayalım veya 0 kabul edelim.
                # Admin mesajını daha genel tutmak en iyisi.
                deleted_count = len(emails_to_notify) # Tahmini sayı, tam doğru olmayabilir.
                messages.warning(request, "Silme işlemi tamamlandı, ancak silinen obje sayısı tam olarak belirlenemedi.")


            messages.success(request, f"{deleted_count} adet STK kaydı silindi (tahmini).")

            # Her bir e-posta adresine reddetme e-postası gönder
            subject = 'STK Kayıt Başvurunuz Hk.'
            message_template = f"""Merhaba,
Gıda Fazlası Yönetimi Sistemi\'ne yapmış olduğunuz STK kayıt başvurusu incelenmiş olup, mevcut durumda uygun bulunmamıştır.

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
            if deleted_count > emails_sent_count:
                messages.warning(request, f"{deleted_count - emails_sent_count} adet reddetme e-postası gönderilemedi (bazı kayıtlar zaten silinmiş olabilir).")

        except Exception as e:
            print(f"STK kayıtları toplu silinirken beklenmeyen hata: {e}")
            messages.error(request, f"STK kayıtları toplu silinirken bir hata oluştu: {e}")

        # deleted_count, _ = super().delete_queryset(request, queryset) # Varsayılan toplu silme işlemini yap
        # messages.success(request, f"{deleted_count} STK kaydı silindi.")

        # # Her bir e-posta adresine reddetme e-postası gönder
        # subject = 'STK Kayıt Başvurunuz Hk.'
        # message_template = f"""Merhaba,
        # Gıda Fazlası Yönetimi Sistemi\'ne yapmış olduğunuz STK kayıt başvurusu incelenmiş olup, mevcut durumda uygun bulunmamıştır.

        # Başvurunuzla ilgili detaylı bilgi almak veya sorularınız için lütfen bizimle iletişime geçin.

        # Anlayışınız için teşekkür ederiz.

        # Saygılarımızla,
        # Gıda Fazlası Yönetimi Sistemi Ekibi"""

        # emails_sent_count = 0
        # for email in emails_to_notify:
        #     try:
        #         send_mail( subject, message_template, settings.EMAIL_HOST_USER, [email,] )
        #         print(f"Reddetme e-postası gönderildi (toplu silme): {email}")
        #         emails_sent_count += 1
        #     except Exception as email_error:
        #         print(f"Reddetme e-postası gönderilirken hata (toplu silme) \'{email}\': {email_error}")
        #         # Toplu silmede her hata için mesaj göstermek spam olabilir, konsola yazdırmak yeterli olabilir.

        # if emails_sent_count > 0:
        #     messages.info(request, f"{emails_sent_count} adet reddetme e-postası gönderildi.")
        # if deleted_count > emails_sent_count:
        #     messages.warning(request, f"{deleted_count - emails_sent_count} adet reddetme e-postası gönderilemedi.")

# UserRegistrationData modelini özel Admin sınıfı ile admin paneline kaydet
admin.site.register(UserRegistrationData, UserRegistrationDataAdmin)


# Profile modelini de admin paneline kaydedelim (isteğe bağlı)
# Adminin onaylanmış kullanıcıların profillerini görmesi gerekirse bu satırı etkinleştirin
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'stk_ad', 'stk_turu', 'cep_telefon')
    search_fields = ('user__email', 'stk_ad', 'stk_temsilci_ad', 'stk_temsilci_soyad')
    list_filter = ('stk_turu',)
