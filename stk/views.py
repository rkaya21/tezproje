from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse # Sadece test veya basit yanıtlar için
from .models import UserRegistrationData, Profile, FoodApplication # Profile modelini de import et
from tedarikci.models import FoodItem
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError # IntegrityError sadece UserRegistrationData.create() sırasında hala gerekebilir, ama ön kontrollerle yakalanır
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import random
from django.contrib.auth import get_user_model # auth.User modelini almak için
from django.db.models import Q # Q objesi ile karmaşık sorgular için
from django.core.files.storage import FileSystemStorage # Dosya yönetimi için
from django.core.files import File # Dosya objesi oluşturmak için import
import os # Dosya yolları için
from django.contrib.auth import authenticate, login # Kimlik doğrulama ve oturum başlatma için
import json



User = get_user_model() # Django'nun aktif User modelini alırız

# ... diğer importlar ve kodlar ...

# Formdan gelen POST verisini işleyecek view
def register_user(request):
    if request.method == 'POST':
        # Formdan gelen verileri alıyoruz
        stk_ad = request.POST.get('stkAd')
        stk_temsilci_ad = request.POST.get('stkTemsilciAd')
        stk_temsilci_soyad = request.POST.get('stkTemsilciSoyad')
        email = request.POST.get('email')
        password = request.POST.get('inputPassword4') # HTML'deki name="inputPassword4"
        confirm_password = request.POST.get('confirmPassword') # HTML'deki name="confirmPassword"
        adres = request.POST.get('adres')
        cep_telefon = request.POST.get('cepTelefon')
        stk_turu = request.POST.get('stkTuru')
        kutuk_no = request.POST.get('kutukNo')
        etebligat = request.POST.get('etebligat')
        faaliyet_belgesi = request.FILES.get('faaliyetBelgesi') # Dosyalar request.FILES içinde bulunur
        terms_accepted = request.POST.get('termsCheckbox') # Onay kutusu

        # E-tebligat boşsa None yap
        if stk_turu == 'vakif' and etebligat == '':
            etebligat = None

        # --- Yeni Benzersizlik Kontrolleri (Veritabanına Kaydetmeden Önce) ---

        # 1. E-posta adresinin zaten auth.User modelinde kayıtlı olup olmadığını kontrol et
        if User.objects.filter(email=email).exists():
            messages.error(request, "Bu e-posta adresi zaten sistemde kayıtlı.")
            # Hata durumunda verileri tekrar göndermek için context oluşturun (güvenlik nedeniyle şifre hariç)
            context = {
               'stk_ad': stk_ad,
               'stk_temsilci_ad': stk_temsilci_ad,
               'stk_temsilci_soyad': stk_temsilci_soyad,
               'email': email, # Email'i tekrar göstermek isteyebilirsiniz, hata mesajı zaten nedenini açıklar
               'adres': adres,
               'cep_telefon': cep_telefon,
               'stk_turu': stk_turu,
               'kutuk_no': kutuk_no,
               'etebligat': etebligat,
               'terms_accepted': 'on' if terms_accepted else '',
            }
            # Faaliyet belgesi geri gönderilemez
            return render(request, 'stk/stk-register-page.html', context)

        # 2. Diğer benzersiz alanların UserRegistrationData VEYA Profile tablosunda zaten var olup olmadığını kontrol et
        # Email hariç, çünkü email kontrolünü auth.User üzerinde zaten yaptık.

        # UserRegistrationData tablosundaki çakışmaları aramak için Q objesi
        urd_q_objects = Q()
        if stk_ad:
             urd_q_objects |= Q(stk_ad=stk_ad)
        if adres:
             urd_q_objects |= Q(adres=adres)
        if cep_telefon:
             urd_q_objects |= Q(cep_telefon=cep_telefon)
        if stk_turu == 'dernek' and kutuk_no:
             urd_q_objects |= Q(kutuk_no=kutuk_no)
        if stk_turu == 'vakif' and etebligat:
             urd_q_objects |= Q(etebligat=etebligat)

        # Profile tablosundaki çakışmaları aramak için Q objesi
        profile_q_objects = Q()
        if stk_ad:
             profile_q_objects |= Q(stk_ad=stk_ad)
        if adres:
             profile_q_objects |= Q(adres=adres)
        if cep_telefon:
             profile_q_objects |= Q(cep_telefon=cep_telefon)
        if stk_turu == 'dernek' and kutuk_no:
             profile_q_objects |= Q(kutuk_no=kutuk_no)
        if stk_turu == 'vakif' and etebligat:
             profile_q_objects |= Q(etebligat=etebligat)


        # Her iki tabloda da (UserRegistrationData veya Profile) çakışma var mı kontrol et
        urd_exists = False
        if urd_q_objects:
            urd_exists = UserRegistrationData.objects.filter(urd_q_objects).exists()

        profile_exists = False
        if profile_q_objects:
            profile_exists = Profile.objects.filter(profile_q_objects).exists()


        if urd_exists or profile_exists:
            messages.error(request, 'Bu bilgilerle (STK Adı, Adres, Telefon, Kütük No veya E-tebligat Adresi) zaten sistemde kayıtlı bir kurum bulunmaktadır.')

            # Hata durumunda verileri tekrar göndermek için context oluşturun
            context = {
                'stk_ad': stk_ad, 'stk_temsilci_ad': stk_temsilci_ad, 'stk_temsilci_soyad': stk_temsilci_soyad,
                'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'stk_turu': stk_turu,
                'kutuk_no': kutuk_no, 'etebligat': etebligat, # Dosya ve şifreyi geri göndermeyin
                'terms_accepted': 'on' if terms_accepted else '', # Checkbox durumu
            }
            return render(request, 'stk/stk-register-page.html', context)

        # --- Temel Doğrulama Adımları (Mevcut Kodunuzdan) ---
        # 1. Zorunlu alanların kontrolü (yukarıdaki unique kontrollerden sonra olmalı)
        if not all([stk_ad, stk_temsilci_ad, stk_temsilci_soyad, email, password, confirm_password, adres, cep_telefon, stk_turu, faaliyet_belgesi, terms_accepted]):
             print("Zorunlu alanlar eksik!")
             messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
             context = { # Context buraya taşındı
                'stk_ad': stk_ad, 'stk_temsilci_ad': stk_temsilci_ad, 'stk_temsilci_soyad': stk_temsilci_soyad,\
                'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'stk_turu': stk_turu,\
                'kutuk_no': kutuk_no, 'etebligat': etebligat, # Dosya ve şifreyi geri göndermeyin
                'terms_accepted': 'on' if terms_accepted else '', # Checkbox durumu
             }
             return render(request, 'stk/stk-register-page.html', context)

        # 2. Şifrelerin eşleşip eşleşmediği kontrolü
        if password != confirm_password:
            print("Şifreler eşleşmiyor!")
            messages.error(request, "Girdiğiniz şifreler eşleşmiyor.")
            context = { # Context buraya taşındı
                'stk_ad': stk_ad, 'stk_temsilci_ad': stk_temsilci_ad, 'stk_temsilci_soyad': stk_temsilci_soyad,\
                'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'stk_turu': stk_turu,
                'kutuk_no': kutuk_no, 'etebligat': etebligat, # Dosya ve şifreyi geri göndermeyin
                'terms_accepted': 'on' if terms_accepted else '', # Checkbox durumu
             }
            return render(request, 'stk/stk-register-page.html', context)

        # 3. STK Türüne göre zorunlu alan kontrolü (Kütük No veya E-Tebligat)
        if stk_turu == 'dernek' and not kutuk_no:
             print("Dernek için Kütük Numarası zorunludur.")
             messages.error(request, "Dernek kaydı için Kütük Numarası zorunludur.")
             context = { # Context buraya taşındı
                'stk_ad': stk_ad, 'stk_temsilci_ad': stk_temsilci_ad, 'stk_temsilci_soyad': stk_temsilci_soyad,
                'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'stk_turu': stk_turu,
                'kutuk_no': kutuk_no, 'etebligat': etebligat, # Dosya ve şifreyi geri göndermeyin
                'terms_accepted': 'on' if terms_accepted else '', # Checkbox durumu
             }
             return render(request, 'stk/stk-register-page.html', context)
        elif stk_turu == 'vakif' and not etebligat and False: # Vakıf için etebligat opsiyoneldi, bu kontrolü isterseniz True yapın
             pass # HTML'e göre vakıf için e-tebligat opsiyonel


        # 4. Gizlilik politikası onay kutusu kontrolü
        if terms_accepted != 'on': # HTML formunda checkbox işaretlendiğinde değeri 'on' olur
             print("Gizlilik politikası ve kullanım şartları kabul edilmelidir.")
             messages.error(request, "Kayıt olmak için Gizlilik Politikası ve Kullanım Şartlarını kabul etmelisiniz.")
             context = { # Context buraya taşındı
                'stk_ad': stk_ad, 'stk_temsilci_ad': stk_temsilci_ad, 'stk_temsilci_soyad': stk_temsilci_soyad,
                'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'stk_turu': stk_turu,
                'kutuk_no': kutuk_no, 'etebligat': etebligat, # Dosya ve şifreyi geri göndermeyin
                'terms_accepted': 'on' if terms_accepted else '', # Checkbox durumu
             }
             return render(request, 'stk/stk-register-page.html', context)


        # --- Veritabanına Kaydetme Yerine Oturumda Saklama ---

        # Şifreyi hashle
        hashed_password = make_password(password)

        # Doğrulama kodu oluştur
        verification_code = ''.join(random.choices('0123456789', k=6))
        print(f"Doğrulama kodu: {verification_code}")

        # Faaliyet belgesini geçici olarak kaydet
        temp_file_path = None
        if faaliyet_belgesi:
             try:
                 fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp')) # MEDIA_ROOT altında temp klasörüne kaydet
                 filename = fs.save(faaliyet_belgesi.name, faaliyet_belgesi)
                 temp_file_path = fs.path(filename) # Geçici dosyanın tam yolu
                 print(f"Geçici faaliyet belgesi kaydedildi: {temp_file_path}")
             except Exception as e:
                 print(f"Faaliyet belgesi geçici kaydedilirken hata: {e}")
                 messages.error(request, "Faaliyet belgesi yüklenirken bir hata oluştu. Lütfen tekrar deneyin.")
                 # Hata durumunda kayıt işlemine devam etme
                 context = {
                     'stk_ad': stk_ad, 'stk_temsilci_ad': stk_temsilci_ad, 'stk_temsilci_soyad': stk_temsilci_soyad,\
                     'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'stk_turu': stk_turu,
                     'kutuk_no': kutuk_no, 'etebligat': etebligat,
                     'terms_accepted': 'on' if terms_accepted else '',
                 }
                 return render(request, 'stk/ststk-register-page.html', context)


        # Kullanıcı verilerini ve doğrulama kodunu oturumda sakla
        request.session['registration_data'] = {
            'stk_ad': stk_ad,
            'stk_temsilci_ad': stk_temsilci_ad,
            'stk_temsilci_soyad': stk_temsilci_soyad,
            'email': email,
            'password': hashed_password, # Hashlenmiş şifreyi sakla
            'adres': adres,
            'cep_telefon': cep_telefon,
            'stk_turu': stk_turu,
            'kutuk_no': kutuk_no if stk_turu == 'dernek' else None,
            'etebligat': etebligat if stk_turu == 'vakif' else None,
            'temp_faaliyet_belgesi_path': temp_file_path, # Geçici dosya yolunu kaydet
            'verification_code': verification_code,
            'terms_accepted': terms_accepted, # Checkbox durumu
        }

        # E-postayı gönder
        subject = 'E-posta Doğrulama Kodunuz'
        message = f"""Merhaba {stk_temsilci_ad},

Kayıt işleminizi tamamlamak için lütfen aşağıdaki doğrulama kodunu kullanın:

{verification_code}

Teşekkürler!"""
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email,]
        send_mail( subject, message, email_from, recipient_list )

        print(f"Kayıt bilgileri oturumda saklandı. Doğrulama kodu gönderildi: {email}")
        messages.success(request, "Kayıt bilgileri alındı! E-posta adresinize doğrulama kodu gönderildi.")

        # E-posta doğrulama sayfasına yönlendir
        return redirect(reverse('stk:verify_email') + f'?email={email}')

    else:
        # GET isteği: Kayıt sayfasını göster
        # Eğer oturumda tamamlanmamış bir kayıt varsa kullanıcıyı doğrulama sayfasına yönlendirebilirsiniz
        # if 'registration_data' in request.session:
        #     return redirect(reverse('stk:verify_email') + f"?email={request.session['registration_data'].get('email', '')}")
        return render(request, 'stk/stk-register-page.html')

# ... diğer view fonksiyonlarınız ...


# E-posta doğrulama view
def verify_email(request):
    # Oturumdaki kayıt verilerini her durumda (GET ve POST) al
    registration_data = request.session.get('registration_data')

    # Oturumda kayıt verisi yoksa (yani kayıt işlemi başlatılmamış veya oturum bitmişse)
    if not registration_data:
        messages.error(request, "Kayıt bilgileri bulunamadı veya oturum süresi dolmuş. Lütfen tekrar kayıt olunuz.")
        return redirect(reverse('stk:register')) # Kayıt sayfasına geri yönlendir

    # Oturumdaki e-posta ve doğrulama kodunu al
    stored_email = registration_data.get('email')
    stored_code = registration_data.get('verification_code')
    temp_file_path = registration_data.get('temp_faaliyet_belgesi_path') # Dosya yolu da oturumda


    if request.method == 'POST':
        submitted_code = request.POST.get('verification_code')
        # submitted_email artık burada directly kullanılmayacak, oturumdaki stored_email kullanılacak

        # Girilen kod, oturumdaki kod ile eşleşiyor mu kontrol et
        # E-posta kontrolüne burada gerek yok, oturumdaki veri zaten ilgili e-postaya ait
        if submitted_code == stored_code:
            try:
                # --- Doğrulama Başarılı: Veriyi Veritabanına Kaydet ---

                # UserRegistrationData objesini oluştur
                user_data = UserRegistrationData.objects.create(
                    stk_ad=registration_data.get('stk_ad'),
                    stk_temsilci_ad=registration_data.get('stk_temsilci_ad'),
                    stk_temsilci_soyad=registration_data.get('stk_temsilci_soyad'),
                    email=stored_email, # Oturumdaki email'i kullan
                    password=registration_data.get('password'), # Hashlenmiş şifreyi kullan
                    adres=registration_data.get('adres'),
                    cep_telefon=registration_data.get('cep_telefon'),
                    stk_turu=registration_data.get('stk_turu'),
                    kutuk_no=registration_data.get('kutuk_no'),
                    etebligat=registration_data.get('etebligat'),
                    is_email_verified=True, # E-posta doğrulandı
                    is_approved=False, # Admin onayı bekleniyor
                    # Faaliyet belgesi daha sonra FileField'a atanacak
                )

                # Faaliyet belgesini (geçici dosyadan) UserRegistrationData objesine ata ve objeyi kaydet
                # Geçici dosya yolu oturumda saklanmıştı
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        # Geçici dosyayı aç
                        with open(temp_file_path, 'rb') as f:
                            # Django File objesi oluştur ve FileField'a ata
                            user_data.faaliyet_belgesi.save(os.path.basename(temp_file_path), File(f), save=True) # save=True ile objeyi tekrar kaydet

                        # Dosya UserRegistrationData'ya başarıyla eklendi, geçici dosyayı sil
                        os.remove(temp_file_path)
                        print(f"Geçici faaliyet belgesi silindi: {temp_file_path}")

                    except Exception as file_process_error:
                         print(f"Faaliyet belgesi işlenirken/silinirken hata oluştu: {file_process_error}")
                         messages.warning(request, "Faaliyet belgesi yüklenirken bir sorun oluştu. Lütfen admin ile iletişime geçin.")
                         # Hata durumunda UserRegistrationData objesini silmemeyi seçebiliriz (veri tutarlılığı için düşünülebilir)
                         # user_data.delete()


                # --- Veritabanı Kaydı Başarılı: Oturumu Temizle ve Mesaj Göster ---\
                # Oturumdaki verileri temizle (sadece 'registration_data' anahtarını sil)
                if 'registration_data' in request.session:
                   del request.session['registration_data']
                print(f"Kayıt başarıyla veritabanına eklendi ve oturum temizlendi: {stored_email}")


                messages.success(request, "E-postanızı doğruladınız. Girdiğiniz veriler kontrol ediliyor. Kayıt sonucunuz 1-5 iş günü içerisinde e-postanıza e-postanıza bildirilecektir.") # Başarı mesajı güncellendi

                # Başarılı doğrulama ve kayıttan sonra kullanıcıyı giriş sayfasına yönlendir
                return redirect(reverse('stk:login')) # Login sayfasına yönlendir

            except IntegrityError as e:
                 # Nadir durumlarda (eş zamanlı kayıtlar gibi) IntegrityError hala oluşabilir
                 print(f"UserRegistrationData kaydı sırasında IntegrityError: {e}")
                 messages.error(request, "Kayıt bilgilerinizle ilgili bir çakışma oluştu. Lütfen tekrar kayıt olunuz veya admin ile iletişime geçiniz.")
                 # Hata durumunda oturumdaki verileri temizleyebiliriz
                 if 'registration_data' in request.session:
                     del request.session['registration_data']
                 # Geçici dosyayı silmeyi unutma
                 if temp_file_path and os.path.exists(temp_file_path):
                     try:
                         os.remove(temp_file_path)
                     except: pass # Silme hatasını göz ardı et
                 # IntegrityError durumunda doğrulama sayfasında kalmak yerine kayıt sayfasına yönlendirmek daha iyi olabilir
                 return redirect(reverse('stk:register'))


            except Exception as e:
                # Veritabanı kaydı sırasında diğer olası hatalar
                print(f"UserRegistrationData kaydı sırasında beklenmeyen hata: {e}")
                messages.error(request, f"Kayıt sırasında bir hata oluştu: {e}. Lütfen tekrar deneyiniz veya admin ile iletişime geçiniz.")
                # Hata durumunda oturumdaki verileri temizleyebiliriz
                if 'registration_data' in request.session:
                    del request.session['registration_data']
                 # Geçici dosyayı silmeyi unutma
                if temp_file_path and os.path.exists(temp_file_path):
                     try:
                         os.remove(temp_file_path)
                     except: pass # Silme hatasını göz ardı et
                # Beklenmeyen hata durumunda da kayıt sayfasına yönlendirmek daha iyi olabilir
                return redirect(reverse('stk:register'))


        else:
            # Kod eşleşmedi
            messages.error(request, "Geçersiz doğrulama kodu. Lütfen tekrar deneyin.")
            # Hata durumunda doğrulama sayfasını tekrar göster, email'i oturumdan alıp context'e gönder
            # registration_data objesi hala oturumda (doğrulama başarısız olduğu için silinmedi)
            email_to_show = stored_email # Oturumdaki email'i kullan
            return render(request, 'stk/stk-verify-email.html', {'email': email_to_show}) # Formdaki email'i tekrar göster

    else:
        # GET isteği: Doğrulama sayfasını göster
        # Kullanıcı direkt verify_email sayfasına gelirse veya sayfayı yenilerse
        # Oturumda kayıt verisi var mı kontrol et
        if not registration_data:
             messages.warning(request, "Lütfen önce kayıt formunu doldurunuz.")
             return redirect(reverse('stk:register'))

        # Oturumda veri varsa, email'i oturumdan alıp template'e gönder
        email_to_show = stored_email
        return render(request, 'stk/stk-verify-email.html', {'email': email_to_show}) # Email'i template'e gönder


def login_user(request):
    if request.method == 'POST':
        # Formdan gelen email (veya kullanıcı adı) ve şifreyi al
        email = request.POST.get('email') # Login formunda email inputunun adı 'email' olmalı
        password = request.POST.get('password') # Login formunda password inputunun adı 'password' olmalı

        # Kullanıcıyı kimlik bilgileriyle doğrula (username olarak email kullanıyoruz)
        # authenticate fonksiyonu arka planda hashlenmiş şifreyi kontrol eder
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Kullanıcı kimlik doğrulamadan geçti (email ve şifre doğru)

            # Şimdi kullanıcının aktif ve onaylanmış olup olmadığını kontrol et
            # Onay kontrolünü Profile objesinin varlığına göre yapıyoruz
            try:
                # auth.User objesi ile ilişkili Profile objesine erişmeye çalış
                # models.py dosyasında User modeline OneToOneField eklerken related_name='profile' verdiyseniz
                # user.profile şeklinde erişebilirsiniz.
                # Eğer related_name vermediyseniz, Profile modelindeki OneToOneField alan adını (örn: user_profile) kullanmalısınız
                # Şimdiki kodda related_name='profile' varsayılıyor.
                profile = user.profile

                # Kullanıcının aktif olup olmadığını kontrol et (Django'nun default is_active alanı)
                if user.is_active:
                    # Kullanıcı aktif ve Profile objesi var (yani onaylanmış)
                    login(request, user) # Kullanıcı oturumunu başlat
                    messages.success(request, f"Hoş geldiniz, {user.first_name}!") # Başarı mesajı (istersek STK adını da kullanabiliriz)
                    print(f"Kullanıcı giriş yaptı: {user.email}")

                    # Başarılı giriş sonrası yönlendirilecek sayfa
                    # Burayı uygulamanızın ana sayfası veya kullanıcı paneli URL'si ile değiştirin
                    # Örnek: return redirect(reverse('anasayfa_adi'))
                    return redirect(reverse('stk:main')) # Geçici olarak kayıt sayfasına yönlendirildi


                else:
                    # Kullanıcı aktif değil (genellikle admin tarafından deaktif edilir)
                    messages.error(request, "Hesabınız aktif değil. Lütfen yönetici ile iletişime geçin.")
                    print(f"Giriş denemesi başarısız: Hesap aktif değil - {user.email}")

            except Profile.DoesNotExist:
                 # Profile objesi yoksa, kullanıcı auth.User tablosunda var ama Profile tablosunda yok demektir.
                 # Bu da bizim akışımızda admin tarafından henüz tam onaylanmadığı anlamına gelir.
                 messages.error(request, "Hesabınız henüz onaylanmadı. Lütfen e-posta adresinizi doğrulayın ve admin onayını bekleyin.")
                 print(f"Giriş denemesi başarısız: Profile objesi yok - {user.email}")
            except Exception as e:
                 # Beklenmeyen bir hata oluştu
                 print(f"Giriş sırasında beklenmeyen bir hata oluştu: {e}")
                 messages.error(request, "Giriş sırasında bir hata oluştu. Lütfen tekrar deneyin.")


        else:
            # Kimlik doğrulama başarısız oldu (email veya şifre yanlış)
            messages.error(request, "Geçersiz e-posta veya şifre.")
            print(f"Giriş denemesi başarısız: Geçersiz kimlik bilgileri - {email}")

        # Başarısız giriş veya onaylanmamış/aktif olmayan kullanıcı durumunda login sayfasını tekrar göster
        # Kullanıcının girdiği email'i formda tutmak için context'e ekleyebilirsiniz
        context = {
            'email': email # Girilen email'i tekrar forma doldurmak için
        }
        return render(request, 'stk/stk-login-page.html', context)

    else:
        # GET isteği: Login sayfasını göster
        # Eğer kullanıcı zaten giriş yapmışsa, başka bir sayfaya yönlendirebilirsiniz
        # if request.user.is_authenticated:
        #     return redirect(reverse('anasayfa_adi')) # Örneğin anasayfaya yönlendir

        return render(request, 'stk/stk-login-page.html')

def main_user(request):
    return render(request, 'stk/stk-main-page.html')



def stk_food_showcase(request): # STK kullanıcısının giriş yapmış olduğundan emin olun
    if not request.user.is_authenticated:
        messages.error(request, "Gıda vitrinini görüntülemek için giriş yapmalısınız.")
        return redirect(reverse('stk:login')) # Login sayfasına yönlendir

    # Get the STK profile for the logged-in user
    stk_profile = None
    try:
        stk_profile = request.user.profile
    except Profile.DoesNotExist:
        # This should ideally not happen if the user is authenticated and is an STK user
        messages.error(request, "Kullanıcı profiliniz bulunamadı.")
        return redirect(reverse('stk:main')) # Redirect to a suitable page

    # Get all applications for the current STK user, prefetch related food_item
    user_applications = FoodApplication.objects.filter(stk_profile=stk_profile).select_related('food_item')

    # Create a dictionary mapping food_item_id to application status for quick lookup
    application_status_dict = {app.food_item.id: app.status for app in user_applications}

    # Fetch all food items that are 'available' for application
    food_items = FoodItem.objects.filter(allocation_status='available').order_by('-created_at') # Only show available items

    # Although we are filtering for 'available', we still need to add user_application_status for any existing applications (e.g., if a user applied before it was allocated)
    for item in food_items:
        item.user_application_status = application_status_dict.get(item.id, None) # Get status from dict, default to None if no application
    
    context = {
        'food_items': food_items, # food_items now contains user_application_status for each item
        # We no longer need to pass the full application_statuses dictionary if we add status to each item
    }

    # Render the food showcase page
    return render(request, 'stk/stk-food-showcase.html', context)

def apply_for_food(request): # Bu view sadece POST isteklerini kabul etmeli ve STK kullanıcıları için olmalı
    if request.method == 'POST' and request.user.is_authenticated and hasattr(request.user, 'profile'):
        food_item_id = None
        # Check if the request content type is JSON
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                food_item_id = data.get('food_item_id')
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
        else:
            # Fallback for form data
            food_item_id = request.POST.get('food_item_id')

        if not food_item_id:
            return JsonResponse({'success': False, 'message': 'food_item_id is required.'}, status=400)

        try:
            food_item = FoodItem.objects.get(id=food_item_id)
            stk_profile = request.user.profile # Giriş yapmış kullanıcının STK profilini al

            # Daha önce bu gıdaya başvurulmuş mu kontrol et (models.py'deki unique_together bunu veritabanı seviyesinde de sağlar, ama burada kullanıcıya bilgi vermek için kontrol ediyoruz)
            if FoodApplication.objects.filter(stk_profile=stk_profile, food_item=food_item).exists():
                return JsonResponse({'success': False, 'message': 'Bu gıdaya zaten başvurdunuz.'})

            # Yeni başvuruyu oluştur
            FoodApplication.objects.create(
                stk_profile=stk_profile,
                food_item=food_item,
                status='pending' # Varsayılan olarak beklemede
            )
            return JsonResponse({'success': True, 'message': 'Başvurunuz alındı. Beklemede.'})

        except FoodItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Başvurulan gıda bulunamadı.'})
        except Profile.DoesNotExist: # Bu hata teorik olarak oluşmamalı çünkü hasattr(request.user, 'profile') kontrolü yaptık
            return JsonResponse({'success': False, 'message': 'Kullanıcı profiliniz bulunamadı.'})
        except Exception as e:
            # Diğer olası hatalar
            return JsonResponse({'success': False, 'message': f'Başvuru sırasında bir hata oluştu: {e}'})

    # GET isteği veya kimlik doğrulaması başarısız olursa
    return JsonResponse({'success': False, 'message': 'Geçersiz istek.'}, status=400) 


def stk_my_applications(request): # Kullanıcının giriş yapmış olduğundan emin olun
    if not request.user.is_authenticated:
        messages.error(request, "Başvurularınızı görüntülemek için giriş yapmalısınız.")
        return redirect(reverse('stk:login')) # Giriş yapmamışsa login sayfasına yönlendir
    
    # Giriş yapmış STK profilini al
    try:
        stk_profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "STK profiliniz bulunamadı.")
        return redirect(reverse('stk:main')) # Veya uygun bir hata sayfası/yönlendirme
    
    # STK'ya ait gıda başvurularını çek
    applications = FoodApplication.objects.filter(stk_profile=stk_profile).order_by('-applied_at') # En son yapılan başvurular üstte olsun

    

    context = {
        'applications': applications
        
    }

    # Başvurularım sayfasını render et
    return render(request, 'stk/stk-my-applications.html', context)


def stk_test_status(request):
    if not request.user.is_authenticated:
        messages.error(request, "Test durumunu görüntülemek için giriş yapmalısınız.")
        return redirect(reverse('stk:login'))

    # Giriş yapmış STK profilini al
    try:
        stk_profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "STK profiliniz bulunamadı.")
        return redirect(reverse('stk:main')) # Veya uygun bir hata sayfası/yönlendirme 

    # STK'ya ait ONAYLANMIŞ gıda başvurularını çek
    approved_applications = FoodApplication.objects.filter(
        stk_profile=stk_profile,
        status='approved' # Sadece onaylanmış başvurular
    ).select_related('food_item').order_by('-applied_at') # En son yapılan başvurular üstte olsun

    context = {
    'approved_applications': approved_applications,
    }

    # Test durumu sayfasını render et (Yeni şablon adı olacak)
    return render(request, 'stk/stk-test-status.html', context)


# def process_test_result(request):
    # if request.method == 'POST' and request.user.is_authenticated and hasattr(request.user, 'profile'):
    #     application_id = request.POST.get('application_id')
    #     test_result = request.POST.get('test_result')

    #     if not application_id or not test_result:
    #         messages.error(request, "Eksik bilgi: Başvuru veya test sonucu seçilmedi.")
    #         return redirect(reverse('stk:stk_test_status')) # Hata durumunda test durumu sayfasına geri dön

    #     # Geçerli test sonucu seçeneklerini al
    #     valid_test_results = [choice[0] for choice in FoodApplication.TEST_RESULT_CHOICES]
    #     if test_result not in valid_test_results:
    #          messages.error(request, "Geçersiz test sonucu değeri.")
    #          return redirect(reverse('stk:stk_test_status'))

    #     try:
    #         # Başvuruyu STK'nın profili ve onaylanmış durumuyla bul
    #         # Ayrıca test sonucunun henüz 'awaiting_test' olup olmadığını kontrol edebiliriz
    #         application = FoodApplication.objects.get(
    #             id=application_id,
    #             stk_profile=request.user.profile,
    #             status='approved',
    #             test_result='awaiting_test' # Sadece test edilmemiş başvuruları işle
    #         )

    #         # Test sonucunu kaydet
    #         application.test_result = test_result

    #         # Test sonucuna göre nihai hedefi belirle
    #         if test_result == 'edible':
    #             application.final_destination = 'cold_storage'
    #             application.status = 'completed' # Yenilebilir ise tamamlandı olarak işaretlenebilir
    #             messages.success(request, f"Gıda '{application.food_item.name}' yenilebilir olarak test edildi ve soğuk hava deposuna yönlendirildi.")
    #         elif test_result == 'inedible':
    #              # Yenilemez ise, FoodItem modelindeki is_compostable alanına bak
    #              if application.food_item.is_compostable: # FoodItem modelinize is_compostable alanı eklediğinizi varsayıyorum
    #                   application.final_destination = 'compost_center'
    #                   messages.warning(request, f"Gıda '{application.food_item.name}' yenilemez olarak test edildi ve gübre atık merkezine yönlendirildi.")
    #              else:
    #                   application.final_destination = 'disposal'
    #                   messages.warning(request, f"Gıda '{application.food_item.name}' yenilemez olarak test edildi ve imha edilmesi gerekiyor.")
    #              application.status = 'completed' # Yenilemez ise de tamamlandı olarak işaretlenebilir


    #         application.save()

    #         # Başarılı işlem sonrası test durumu sayfasına yönlendir
    #         return redirect(reverse('stk:stk_test_status'))

    #     except FoodApplication.DoesNotExist:
    #         messages.error(request, "Başvuru bulunamadı veya test için uygun değil.")
    #         return redirect(reverse('stk:stk_test_status')) # Hata durumunda test durumu sayfasına geri dön
    #     except Exception as e:
    #         messages.error(request, f"Test sonucu kaydedilirken bir hata oluştu: {e}")
    #         print(f"Test sonucu kaydetme hatası: {e}") # Loglama için
    #         return redirect(reverse('stk:stk_test_status')) # Hata durumunda test durumu sayfasına geri dön

    # else:
    #     # Ana koşul sağlanmazsa (POST değil, giriş yapmamış vb.) buraya gelinir
    #     messages.error(request, "Geçersiz istek.")
    #     return redirect(reverse('stk:login')) # Geçersiz istekte login sayfasına yönlendir


def set_test_result(request):
    """
    Onaylanmış bir gıda başvurusunun test sonucunu kaydeder.
    """
    if request.method == 'POST' and request.user.is_authenticated and hasattr(request.user, 'profile'):
        application_id = request.POST.get('application_id')
        test_result = request.POST.get('test_result') # 'edible' veya 'inedible' bekleniyor

        if not application_id or not test_result:
            messages.error(request, "Eksik bilgi: Başvuru veya test sonucu seçilmedi.")
            return redirect(reverse('stk:stk_test_status'))

        # Geçerli test sonucu seçeneklerini kontrol et
        valid_test_results = ['edible', 'inedible']
        if test_result not in valid_test_results:
             messages.error(request, "Geçersiz test sonucu değeri.")
             return redirect(reverse('stk:stk_test_status'))

        try:
            # Başvuruyu STK'nın profili, onaylanmış durumu ve henüz test edilmemiş (awaiting_test) olmasıyla bul
            application = FoodApplication.objects.get(
                id=application_id,
                stk_profile=request.user.profile,
                status='approved',
                test_result='awaiting_test' # Sadece test edilmemiş başvuruları işle
            )

            # Test sonucunu kaydet
            application.test_result = test_result
            # Nihai hedefi test sonucuna göre başlangıç değeriyle güncelle
            if test_result == 'edible':
                 application.final_destination = 'awaiting_cold_storage' # Yeni bir durum gerekebilir veya awaiting_test_result kalabilir
                 application.status = 'awaiting_distribution' # Durumu 'Dağıtım Bekliyor' olarak güncelle
                 messages.success(request, f"Gıda '{application.food_item.name}' yenilebilir olarak işaretlendi.")
            elif test_result == 'inedible':
                 application.final_destination = 'awaiting_disposal_or_compost' # Yeni bir durum gerekebilir
                 messages.warning(request, f"Gıda '{application.food_item.name}' yenilemez olarak işaretlendi.")


            application.save()

            # Başarılı işlem sonrası test durumu sayfasına yönlendir
            # Kullanıcıyı doğru sekmeye yönlendirmek için bir parametre eklenebilir
            return redirect(reverse('stk:stk_test_status')) # Şimdilik sadece sayfaya yönlendir

        except FoodApplication.DoesNotExist:
            # Başvuru bulunamadıysa veya durumu 'approved' veya test_result 'awaiting_test' değilse bu hataya düşer
            messages.error(request, "Başvuru bulunamadı veya test için uygun değil.")
            return redirect(reverse('stk:stk_test_status')) # Hata durumunda test durumu sayfasına geri dön
        except Exception as e:
            messages.error(request, f"Test sonucu kaydedilirken beklenmeyen bir hata oluştu: {e}")
            print(f"Test sonucu kaydetme hatası: {e}") # Loglama için
            return redirect(reverse('stk:stk_test_status')) # Hata durumunda test durumu sayfasına geri dön

    else:
        # Ana koşul sağlanmazsa (POST değil, giriş yapmamış vb.) buraya gelinir
        messages.error(request, "Bu işlem için geçerli bir istek yapılmadı.")
        return redirect(reverse('stk:login')) # Geçersiz istekte login sayfasına yönlendir


def set_final_destination(request):
    """
    Yenilemez olarak test edilmiş bir gıdanın nihai hedefini belirler.
    """
    if request.method == 'POST' and request.user.is_authenticated and hasattr(request.user, 'profile'):
        application_id = request.POST.get('application_id')
        final_destination = request.POST.get('final_destination') # 'compost_center' veya 'disposal' bekleniyor

        if not application_id or not final_destination:
            messages.error(request, "Eksik bilgi: Başvuru veya nihai hedef seçilmedi.")
            return redirect(reverse('stk:stk_test_status') + '?tab=kalanlar') # Hata durumunda Kalanlar sekmesine yönlendir

        # Geçerli nihai hedef seçeneklerini kontrol et (sadece bu fonksiyon için geçerli olanlar)
        valid_final_destinations = ['compost_center', 'disposal']
        if final_destination not in valid_final_destinations:
             messages.error(request, "Geçersiz nihai hedef değeri.")
             return redirect(reverse('stk:stk_test_status') + '?tab=kalanlar')

        try:
            # Başvuruyu STK'nın profili, onaylanmış durumu ve test sonucunun 'inedible' olmasıyla bul
            # Ayrıca nihai hedefin henüz belirlenmemiş olması (awaiting_disposal_or_compost gibi) kontrol edilebilir
            application = FoodApplication.objects.get(
                id=application_id,
                stk_profile=request.user.profile,
                status='approved', # Sadece onaylanmış başvurular üzerinde işlem yap
                test_result='inedible', # Sadece yenilemez olarak işaretlenmiş başvuruları işle
                # final_destination='awaiting_disposal_or_compost' # Opsiyonel: Sadece hedefi belirlenmemişleri işle
            )

            # Nihai hedefi kaydet
            application.final_destination = final_destination
            # Başvurunun durumunu tamamlandı olarak işaretle
            application.status = 'completed'

            application.save()

            if final_destination == 'compost_center':
                 messages.success(request, f"Gıda '{application.food_item.name}' gübre atık merkezine yönlendirildi.")
            elif final_destination == 'disposal':
                 messages.success(request, f"Gıda '{application.food_item.name}' imha edilecek olarak işaretlendi.")


            # Başarılı işlem sonrası test durumu sayfasına (Kalanlar sekmesine) yönlendir
            return redirect(reverse('stk:stk_test_status') + '?tab=kalanlar')

        except FoodApplication.DoesNotExist:
            # Başvuru bulunamadıysa veya durumu/test sonucu uygun değilse
            messages.error(request, "Başvuru bulunamadı veya nihai hedef belirlemek için uygun değil.")
            return redirect(reverse('stk:stk_test_status') + '?tab=kalanlar')
        except Exception as e:
            messages.error(request, f"Nihai hedef kaydedilirken beklenmeyen bir hata oluştu: {e}")
            print(f"Nihai hedef kaydetme hatası: {e}") # Loglama için
            return redirect(reverse('stk:stk_test_status') + '?tab=kalanlar')

    else:
        # Ana koşul sağlanmazsa (POST değil, giriş yapmamış vb.) buraya gelinir
        messages.error(request, "Bu işlem için geçerli bir istek yapılmadı.")
        return redirect(reverse('stk:login')) # Geçersiz istekte login sayfasına yönlendir


def send_to_cold_storage(request):
    """
    Seçili yenilebilir gıda başvurularını soğuk hava deposuna gönderildi olarak işaretler.
    """
    if request.method == 'POST' and request.user.is_authenticated and hasattr(request.user, 'profile'):

        try:
            # Gelen JSON verisini oku ve parse et
            data = json.loads(request.body)
            selected_application_ids = data.get('selected_applications', []) # Liste bekleniyor

            if not selected_application_ids:
                # messages.warning(request, "Soğuk depoya gönderilecek gıda seçmediniz.") # AJAX ile yanıt verdiğimiz için messages kullanmayız
                return JsonResponse({'success': False, 'message': 'Soğuk depoya gönderilecek gıda seçmediniz.'}, status=400)
            
            # Seçili başvuruları STK'nın profili, onaylanmış durumu ve test sonucunun 'edible' olmasıyla bul
            applications_to_update = FoodApplication.objects.filter(
                id__in=selected_application_ids, # Seçili ID'ler içinde olanlar
                stk_profile=request.user.profile,
                status='approved', # Sadece onaylanmış başvurular üzerinde işlem yap
                test_result='edible' # Sadece yenilebilir olarak işaretlenmiş başvuruları işle
                # final_destination='awaiting_cold_storage' # Opsiyonel: Sadece hedefi belirlenmemişleri işle
            )

            # Başvuruları güncelle: nihai hedefi 'cold_storage' ve durumu 'completed' yap
            updated_count = applications_to_update.update(
                final_destination='awaiting_cold_storage', # Nihai hedefi soğuk depo olarak ayarla
                status='completed' # İşlem tamamlandı olarak işaretle
            )

            if updated_count > 0:
                # messages.success(request, f"{updated_count} adet gıda başarıyla soğuk hava deposuna gönderildi olarak işaretlendi.") # AJAX ile yanıt verdiğimiz için messages kullanmayız
                return JsonResponse({'success': True, 'message': f"{updated_count} adet gıda başarıyla soğuk hava deposuna gönderildi olarak işaretlendi."}) # Başarı yanıtı
            else:
                # messages.warning(request, "Seçili gıdalardan hiçbiri soğuk depoya göndermek için uygun değildi.") # AJAX ile yanıt verdiğimiz için messages kullanmayız
                return JsonResponse({'success': False, 'message': "Seçili gıdalardan hiçbiri soğuk depoya göndermek için uygun değildi."})
            
        except json.JSONDecodeError:
            # messages.error(request, "Geçersiz JSON verisi.") # AJAX ile yanıt verdiğimiz için messages kullanmayız
            return JsonResponse({'success': False, 'message': 'Geçersiz JSON verisi.'}, status=400)
        
        except Exception as e:
            # messages.error(request, f"Soğuk depoya gönderme sırasında beklenmeyen bir hata oluştu: {e}") # AJAX ile yanıt verdiğimiz için messages kullanmayız
            print(f"Soğuk depoya gönderme hatası: {e}") # Sunucu tarafında logla
            return JsonResponse({'success': False, 'message': f'Bir hata oluştu: {e}'}, status=500) # Hata yanıtı
        
    else:
        # Ana koşul sağlanmazsa (POST değil, giriş yapmamış vb.) buraya gelinir
        # messages.error(request, "Bu işlem için geçerli bir istek yapılmadı.") # AJAX ile yanıt verdiğimiz için messages kullanmayız
        return JsonResponse({'success': False, 'message': 'Geçersiz istek.'}, status=405) # Geçersiz istek metodu yanıtı



    #     selected_application_ids = request.POST.getlist('selected_applications') # Checkboxlardan gelen id listesi

    #     if not selected_application_ids:
    #         messages.warning(request, "Soğuk depoya gönderilecek gıda seçmediniz.")
    #         return redirect(reverse('stk:stk_test_status') + '?tab=gecenler') # Seçim yapılmazsa Geçenler sekmesine dön

    #     try:
    #         # Seçili başvuruları STK'nın profili, onaylanmış durumu ve test sonucunun 'edible' olmasıyla bul
    #         # Ayrıca nihai hedefin henüz belirlenmemiş olması (awaiting_cold_storage gibi) kontrol edilebilir
    #         applications_to_update = FoodApplication.objects.filter(
    #             id__in=selected_application_ids, # Seçili ID'ler içinde olanlar
    #             stk_profile=request.user.profile,
    #             status='approved', # Sadece onaylanmış başvurular üzerinde işlem yap
    #             test_result='edible', # Sadece yenilebilir olarak işaretlenmiş başvuruları işle
    #             # final_destination='awaiting_cold_storage' # Opsiyonel: Sadece hedefi belirlenmemişleri işle
    #         )

    #         # Başvuruları güncelle: nihai hedefi 'cold_storage' ve durumu 'completed' yap
    #         updated_count = applications_to_update.update(
    #             final_destination='cold_storage',
    #             status='completed'
    #         )

    #         if updated_count > 0:
    #              messages.success(request, f"{updated_count} adet gıda başarıyla soğuk hava deposuna gönderildi olarak işaretlendi.")
    #         else:
    #              messages.warning(request, "Seçili gıdalardan hiçbiri soğuk depoya göndermek için uygun değildi.")


    #         # Başarılı işlem sonrası test durumu sayfasına (Geçenler sekmesine) yönlendir
    #         return redirect(reverse('stk:stk_test_status') + '?tab=gecenler')

    #     except Exception as e:
    #         messages.error(request, f"Soğuk depoya gönderme sırasında beklenmeyen bir hata oluştu: {e}")
    #         print(f"Soğuk depoya gönderme hatası: {e}") # Loglama için
    #         return redirect(reverse('stk:stk_test_status') + '?tab=gecenler')

    # else:
    #     # Ana koşul sağlanmazsa (POST değil, giriş yapmamış vb.) buraya gelinir
    #     messages.error(request, "Bu işlem için geçerli bir istek yapılmadı.")
    #     return redirect(reverse('stk:login')) # Geçersiz istekte login sayfasına yönlendir


def send_to_cold_storage_single(request):
    """
    Tek bir yenilebilir gıda başvurusunu soğuk hava deposuna gönderildi olarak işaretler.
    """
    if request.method == 'POST' and request.user.is_authenticated and hasattr(request.user, 'profile'):
        application_id = request.POST.get('application_id')

        if not application_id:
            messages.error(request, "Eksik bilgi: Başvuru seçilmedi.")
            return redirect(reverse('stk:stk_test_status') + '?tab=gecenler') # Hata durumunda Geçenler sekmesine dön

        try:
            # Başvuruyu STK'nın profili, onaylanmış durumu ve test sonucunun 'edible' olmasıyla bul
            # Ayrıca nihai hedefin henüz belirlenmemiş olması kontrol edilebilir
            application = FoodApplication.objects.get(
                id=application_id,
                stk_profile=request.user.profile,
                status='approved', # Sadece onaylanmış başvurular üzerinde işlem yap
                test_result='edible', # Sadece yenilebilir olarak işaretlenmiş başvuruları işle
                # final_destination='awaiting_cold_storage' # Opsiyonel: Sadece hedefi belirlenmemişleri işle
            )

            # Nihai hedefi 'awaiting_cold_storage' ve durumu 'completed' yap
            application.final_destination = 'awaiting_cold_storage' # Veya uygun durum
            application.status = 'completed' # İşlem tamamlandı olarak işaretle

            application.save()

            messages.success(request, f"Gıda '{application.food_item.name}' başarıyla soğuk hava deposuna gönderildi olarak işaretlendi.")

            # Başarılı işlem sonrası test durumu sayfasına (Geçenler sekmesine) yönlendir
            return redirect(reverse('stk:stk_test_status') + '?tab=gecenler')

        except FoodApplication.DoesNotExist:
            # Başvuru bulunamadıysa veya durumu/test sonucu uygun değilse
            messages.error(request, "Başvuru bulunamadı veya soğuk depoya göndermek için uygun değil.")
            return redirect(reverse('stk:stk_test_status') + '?tab=gecenler')
        except Exception as e:
            messages.error(request, f"Soğuk depoya gönderme sırasında beklenmeyen bir hata oluştu: {e}")
            print(f"Soğuk depoya gönderme hatası: {e}") # Loglama için
            return redirect(reverse('stk:stk_test_status') + '?tab=gecenler')

    else:
        # Ana koşul sağlanmazsa (POST değil, giriş yapmamış vb.) buraya gelinir
        messages.error(request, "Bu işlem için geçerli bir istek yapılmadı.")
        return redirect(reverse('stk:login')) # Geçersiz istekte login sayfasına yönlendir



def delivery_status(request):
    """ STK'nın dağıtılmış gıda başvurularını listeler. """
    if not request.user.is_authenticated:
        messages.error(request, "Bu sayfayı görüntülemek için giriş yapmalısınız.")
        return redirect(reverse('stk:login'))

    # Giriş yapmış STK profilini al
    try:
        stk_profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "STK profiliniz bulunamadı.")
        return redirect(reverse('stk:main')) # Veya uygun bir hata sayfası/yönlendirme

    # Durumu 'completed' ve nihai hedefi 'distributed' olan başvuruları çek
    distributed_applications = FoodApplication.objects.filter(
        stk_profile=stk_profile,
        status='completed', # Tamamlanmış başvurular
        final_destination='distributed' # Dağıtılmış olanlar
    ).select_related('food_item').order_by('-applied_at') # En son yapılanlar üstte olsun

    context = {
        'distributed_applications': distributed_applications,
    }

    return render(request, 'stk/delivery-status.html', context)


def stk_warehouse_status(request):
    """ STK'nın soğuk hava deposuna gönderilen veya bekleyen gıda başvurularını listeler. """
    if not request.user.is_authenticated:
        messages.error(request, "Depo durumunu görüntülemek için giriş yapmalısınız.")
        return redirect(reverse('stk:login'))
    
    # Giriş yapmış STK profilini al
    try:
        stk_profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, "STK profiliniz bulunamadı.")
        return redirect(reverse('stk:main')) # Veya uygun bir hata sayfası/yönlendirme

    # Soğuk hava deposuna gönderilen veya bekleyen başvuruları çek
    warehouse_applications = FoodApplication.objects.filter(
        stk_profile=stk_profile,
        final_destination__in=['awaiting_cold_storage', 'cold_storage'] # Nihai hedefi soğuk depo ile ilgili olanlar
    ).select_related('food_item').order_by('-applied_at') # En son yapılan başvurular üstte olsun

    context = {
        'warehouse_applications': warehouse_applications,
    }

    # Depo durumu sayfasını render et
    return render(request, 'stk/stk-warehouse-status.html', context) # Yeni şablon adı


def mark_as_distributed(request):
    """ Soğuk hava deposundaki dağıtım bekleyen bir gıda başvurusunu dağıtıldı olarak işaretler. """ 
    if request.method == 'POST' and request.user.is_authenticated and hasattr(request.user, 'profile'):
        application_id = request.POST.get('application_id')

        if not application_id:
            messages.error(request, "Eksik bilgi: Başvuru seçilmedi.")
            return redirect(reverse('stk:stk_warehouse_status')) # Hata durumunda Depo Durumu sayfasına dön
        
        try:
            # Başvuruyu STK'nın profili, nihai hedefinin soğuk depo ile ilgili olması ve dağıtım bekliyor durumuyla bul
            application = FoodApplication.objects.get(
                id=application_id,
                stk_profile=request.user.profile,
                final_destination__in=['awaiting_cold_storage', 'cold_storage'], # Nihai hedefi soğuk depo ile ilgili olanlar
                status='awaiting_distribution' # Sadece dağıtım bekleyenleri işle
            )

            # Nihai hedefi 'distributed' ve durumu 'completed' yap
            application.final_destination = 'distributed'
            application.status = 'completed' # İşlem tamamlandı olarak işaretle

            application.save()

            messages.success(request, f"Gıda '{application.food_item.name}' başarıyla dağıtıldı olarak işaretlendi.")

            # Başarılı işlem sonrası Depo Durumu sayfasına yönlendir
            # return redirect(reverse('stk:stk_warehouse_status'))
            return redirect(reverse('stk:delivery_status'))

        
        except FoodApplication.DoesNotExist:
            # Başvuru bulunamadıysa veya durumu/nihai hedefi uygun değilse
            messages.error(request, "Başvuru bulunamadı veya dağıtıldı olarak işaretlemek için uygun değil.")
            return redirect(reverse('stk:stk_warehouse_status'))
        
        except Exception as e:
            messages.error(request, f"Dağıtıldı olarak işaretlerken beklenmeyen bir hata oluştu: {e}")
            print(f"Dağıtıldı olarak işaretleme hatası: {e}") # Loglama için
            return redirect(reverse('stk:stk_warehouse_status'))

    else:
        # Ana koşul sağlanmazsa (POST değil, giriş yapmamış vb.) buraya gelinir
        messages.error(request, "Bu işlem için geçerli bir istek yapılmadı.")
        return redirect(reverse('stk:login')) # Geçersiz istekte login sayfasına yönlendir


def stk_profile(request):
    """ Giriş yapmış STK kullanıcısının profil bilgilerini görüntüler. """ 
    if not request.user.is_authenticated:
        messages.error(request, "Profilinizi görüntülemek için giriş yapmalısınız.")
        return redirect(reverse('stk:login'))

    try:
    # Giriş yapmış kullanıcının STK profilini al
        stk_profile = request.user.profile
        context = {
            'stk_profile': stk_profile
        }   
        return render(request, 'stk/stk-profile.html', context)

    except Profile.DoesNotExist:
        messages.error(request, "STK profiliniz bulunamadı.")
        return redirect(reverse('stk:main')) # Veya uygun bir hata sayfası/yönlendirme 
