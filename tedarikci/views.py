from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponse # Sadece test veya basit yanıtlar için
from .models import TedarikciRegistrationData, TedarikciProfile, FoodItem # Tedarikci modellerini import et
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError
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
from stk.models import FoodApplication
from django.db.models import OuterRef, Subquery # Import necessary functions
from stk.models import FoodApplication # Import FoodApplication model

User = get_user_model() # Django'nun aktif User modelini alırız

# Tedarikçi kayıt view
def register(request):
    if request.method == 'POST':
        # Formdan gelen verileri alıyoruz
        tedarikci_ad = request.POST.get('tedarikciAd')
        temsilci_ad = request.POST.get('tedarikciTemsilciAd')
        temsilci_soyad = request.POST.get('tedarikciTemsilciSoyad')
        email = request.POST.get('email')
        password = request.POST.get('inputPassword4') # HTML'deki name="inputPassword4"
        confirm_password = request.POST.get('confirmPassword') # HTML'deki name="confirmPassword"
        adres = request.POST.get('adres')
        cep_telefon = request.POST.get('cepTelefon')
        vergi_no = request.POST.get('vergiNo')
        vergi_levhasi = request.FILES.get('faaliyetBelgesi') # HTML'deki name="faaliyetBelgesi"
        terms_accepted = request.POST.get('termsCheckbox') # Onay kutusu

        # --- Benzersizlik Kontrolleri ---

        # 1. E-posta adresinin auth.User veya TedarikciRegistrationData modelinde zaten kayıtlı olup olmadığını kontrol et
        if User.objects.filter(email=email).exists() or TedarikciRegistrationData.objects.filter(email=email).exists():
            messages.error(request, "Bu e-posta adresi zaten sistemde kayıtlı.")
            context = {
               'tedarikci_ad': tedarikci_ad,
               'temsilci_ad': temsilci_ad,
               'temsilci_soyad': temsilci_soyad,
               'email': email,
               'adres': adres,
               'cep_telefon': cep_telefon,
               'vergi_no': vergi_no,
               'terms_accepted': 'on' if terms_accepted else '',
            }
            return render(request, 'tedarikci/tedarikci-register-page.html', context)

        # 2. Diğer benzersiz alanların (Vergi No, Adres, Cep Telefonu) TedarikciRegistrationData VEYA TedarikciProfile tablosunda zaten var olup olmadığını kontrol et
        unique_checks = Q()
        if vergi_no: unique_checks |= Q(vergi_no=vergi_no)
        if adres: unique_checks |= Q(adres=adres)
        if cep_telefon: unique_checks |= Q(cep_telefon=cep_telefon)

        if unique_checks:
             if TedarikciRegistrationData.objects.filter(unique_checks).exclude(email=email).exists() or TedarikciProfile.objects.filter(unique_checks).exclude(user__email=email).exists():
                 messages.error(request, 'Bu bilgilerle (Vergi No, Adres veya Telefon) zaten sistemde kayıtlı bir tedarikçi bulunmaktadır.')
                 context = {
                     'tedarikci_ad': tedarikci_ad, 'temsilci_ad': temsilci_ad, 'temsilci_soyad': temsilci_soyad,
                     'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'vergi_no': vergi_no,
                     'terms_accepted': 'on' if terms_accepted else '', 
                 }
                 return render(request, 'tedarikci/tedarikci-register-page.html', context)

        # --- Temel Doğrulama Adımları ---
        # 1. Zorunlu alanların kontrolü
        if not all([tedarikci_ad, temsilci_ad, temsilci_soyad, email, password, confirm_password, adres, cep_telefon, vergi_no, vergi_levhasi, terms_accepted]):
             messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
             context = {
                'tedarikci_ad': tedarikci_ad, 'temsilci_ad': temsilci_ad, 'temsilci_soyad': temsilci_soyad,\
                'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'vergi_no': vergi_no,
                'terms_accepted': 'on' if terms_accepted else '',
             }
             return render(request, 'tedarikci/tedarikci-register-page.html', context)

        # 2. Şifrelerin eşleşip eşleşmediği kontrolü
        if password != confirm_password:
            messages.error(request, "Girdiğiniz şifreler eşleşmiyor.")
            context = {
                'tedarikci_ad': tedarikci_ad, 'temsilci_ad': temsilci_ad, 'temsilci_soyad': temsilci_soyad,\
                'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'vergi_no': vergi_no,
                'terms_accepted': 'on' if terms_accepted else '',
             }
            return render(request, 'tedarikci/tedarikci-register-page.html', context)

        # 3. Gizlilik politikası onay kutusu kontrolü
        if terms_accepted != 'on':
             messages.error(request, "Kayıt olmak için Gizlilik Politikası ve Kullanım Şartlarını kabul etmelisiniz.")
             context = {
                'tedarikci_ad': tedarikci_ad, 'temsilci_ad': temsilci_ad, 'temsilci_soyad': temsilci_soyad,\
                'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'vergi_no': vergi_no,
                'terms_accepted': 'on' if terms_accepted else '',
             }
             return render(request, 'tedarikci/tedarikci-register-page.html', context)


        # --- Veritabanına Kaydetme Yerine Oturumda Saklama ve Dosya İşleme ---

        # Şifreyi hashle
        hashed_password = make_password(password)

        # Doğrulama kodu oluştur
        verification_code = ''.join(random.choices('0123456789', k=6))
        print(f"Tedarikçi Doğrulama kodu: {verification_code}")

        # Vergi levhasını geçici olarak kaydet
        temp_file_path = None
        if vergi_levhasi:
             try:
                 fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'temp_tedarikci')) # temp_tedarikci klasörüne kaydet
                 filename = fs.save(vergi_levhasi.name, vergi_levhasi)
                 temp_file_path = fs.path(filename) # Geçici dosyanın tam yolu
                 print(f"Geçici vergi levhası kaydedildi: {temp_file_path}")
             except Exception as e:
                 print(f"Vergi levhası geçici kaydedilirken hata: {e}")
                 messages.error(request, "Vergi levhası yüklenirken bir hata oluştu. Lütfen tekrar deneyin.")
                 context = {
                     'tedarikci_ad': tedarikci_ad, 'temsilci_ad': temsilci_ad, 'temsilci_soyad': temsilci_soyad,\
                     'email': email, 'adres': adres, 'cep_telefon': cep_telefon, 'vergi_no': vergi_no,
                     'terms_accepted': 'on' if terms_accepted else '',
                 }
                 return render(request, 'tedarikci/tedarikci-register-page.html', context)


        # Kullanıcı verilerini ve doğrulama kodunu oturumda sakla
        request.session['tedarikci_registration_data'] = {
            'tedarikci_ad': tedarikci_ad,
            'temsilci_ad': temsilci_ad,
            'temsilci_soyad': temsilci_soyad,
            'email': email,
            'password': hashed_password, # Hashlenmiş şifreyi sakla
            'adres': adres,
            'cep_telefon': cep_telefon,
            'vergi_no': vergi_no,
            'temp_vergi_levhasi_path': temp_file_path, # Geçici dosya yolunu kaydet
            'verification_code': verification_code,
            'terms_accepted': terms_accepted, # Checkbox durumu
        }

        # E-postayı gönder
        subject = 'Tedarikçi E-posta Doğrulama Kodunuz'
        message = f"""Merhaba {temsilci_ad},

    Kayıt işleminizi tamamlamak için lütfen aşağıdaki doğrulama kodunu kullanın:

    {verification_code}

    Teşekkürler!"""
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email,]
        send_mail( subject, message, email_from, recipient_list )

        print(f"Tedarikçi kayıt bilgileri oturumda saklandı. Doğrulama kodu gönderildi: {email}")
        messages.success(request, "Kayıt bilgileriniz alındı! E-posta adresinize doğrulama kodu gönderildi.")

        # E-posta doğrulama sayfasına yönlendir
        return redirect(reverse('tedarikci:verify_email') + f'?email={email}')

    else:
        # GET isteği: Kayıt sayfasını göster
        # Eğer oturumda tamamlanmamış bir kayıt varsa kullanıcıyı doğrulama sayfasına yönlendirebilirsiniz
        # if 'tedarikci_registration_data' in request.session:
        #     return redirect(reverse('tedarikci:verify_email') + f"?email={request.session['tedarikci_registration_data'].get('email', '')}")
        return render(request, 'tedarikci/tedarikci-register-page.html')


# Tedarikçi e-posta doğrulama view
def verify_email(request):
    # Oturumdaki kayıt verilerini her durumda (GET ve POST) al
    registration_data = request.session.get('tedarikci_registration_data')

    # Oturumda kayıt verisi yoksa
    if not registration_data:
        messages.error(request, "Kayıt bilgileri bulunamadı veya oturum süresi dolmuş. Lütfen tekrar kayıt olunuz.")
        return redirect(reverse('tedarikci:register')) # Kayıt sayfasına geri yönlendir

    # Oturumdaki e-posta, doğrulama kodu ve geçici dosya yolunu al
    stored_email = registration_data.get('email')
    stored_code = registration_data.get('verification_code')
    temp_file_path = registration_data.get('temp_vergi_levhasi_path') # Geçici dosya yolu oturumda


    if request.method == 'POST':
        submitted_code = request.POST.get('verification_code')

        # Girilen kod, oturumdaki kod ile eşleşiyor mu kontrol et
        if submitted_code == stored_code:
            try:
                # --- Doğrulama Başarılı: Veriyi Veritabanına Kaydet ---

                # TedarikciRegistrationData objesini oluştur
                tedarikci_data = TedarikciRegistrationData.objects.create(
                    tedarikci_ad=registration_data.get('tedarikci_ad'),
                    temsilci_ad=registration_data.get('temsilci_ad'),
                    temsilci_soyad=registration_data.get('temsilci_soyad'),
                    email=stored_email, # Oturumdaki email'i kullan
                    password=registration_data.get('password'), # Hashlenmiş şifreyi kullan
                    adres=registration_data.get('adres'),
                    cep_telefon=registration_data.get('cep_telefon'),
                    vergi_no=registration_data.get('vergi_no'),
                    verification_code=stored_code, # Doğrulanmış kodu saklayabiliriz (veya boş bırakabiliriz)
                    is_email_verified=True, # E-posta doğrulandı
                    is_approved=False, # Admin onayı bekleniyor (RegistrationData modelinde)
                    # Vergi levhası daha sonra FileField'a atanacak
                )

                # Vergi levhasını (geçici dosyadan) TedarikciRegistrationData objesine ata ve objeyi kaydet
                # Geçici dosya yolu oturumda saklanmıştı
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        # Geçici dosyayı aç
                        with open(temp_file_path, 'rb') as f:
                            # Django File objesi oluştur ve FileField'a ata
                            tedarikci_data.vergi_levhasi.save(os.path.basename(temp_file_path), File(f), save=True) # save=True ile objeyi tekrar kaydet

                        # Dosya TedarikciRegistrationData'ya başarıyla eklendi, geçici dosyayı sil
                        os.remove(temp_file_path)
                        print(f"Geçici vergi levhası silindi: {temp_file_path}")

                    except Exception as file_process_error:
                         print(f"Vergi levhası işlenirken/silinirken hata oluştu: {file_process_error}")
                         messages.warning(request, "Vergi levhası yüklenirken bir sorun oluştu. Lütfen admin ile iletişime geçin.")


                # --- Veritabanı Kaydı Başarılı: Oturumu Temizle ve Mesaj Göster ---\
                # Oturumdaki verileri temizle
                if 'tedarikci_registration_data' in request.session:
                   del request.session['tedarikci_registration_data']
                print(f"Tedarikçi kaydı başarıyla veritabanına eklendi ve oturum temizlendi: {stored_email}")


                messages.success(request, "E-postanızı doğruladınız. Girdiğiniz veriler kontrol ediliyor. Kayıt sonucunuz 1-5 iş günü içerisinde e-postanıza bildirilecektir.") 

                # Başarılı doğrulama ve kayıttan sonra kullanıcıyı giriş sayfasına yönlendir
                return redirect(reverse('tedarikci:login')) # Login sayfasına yönlendir (fonksiyon adı user_login)

            except IntegrityError as e:
                 print(f"TedarikciRegistrationData kaydı sırasında IntegrityError: {e}")
                 messages.error(request, "Kayıt bilgilerinizle ilgili bir çakışma oluştu. Lütfen tekrar kayıt olunuz veya admin ile iletişime geçiniz.")
                 # Hata durumunda oturumdaki verileri temizleyebiliriz
                 if 'tedarikci_registration_data' in request.session:
                     del request.session['tedarikci_registration_data']
                 # Geçici dosyayı silmeyi unutma (eğer varsa)
                 if temp_file_path and os.path.exists(temp_file_path):
                     try:
                         os.remove(temp_file_path)
                     except: pass
                 return redirect(reverse('tedarikci:register'))


            except Exception as e:
                print(f"TedarikciRegistrationData kaydı sırasında beklenmeyen hata: {e}")
                messages.error(request, f"Kayıt sırasında bir hata oluştu: {e}. Lütfen tekrar deneyiniz veya admin ile iletişime geçiniz.")
                if 'tedarikci_registration_data' in request.session:
                    del request.session['tedarikci_registration_data']
                # Geçici dosyayı silmeyi unutma (eğer varsa)
                if temp_file_path and os.path.exists(temp_file_path):
                     try:
                         os.remove(temp_file_path)
                     except: pass
                return redirect(reverse('tedarikci:register'))


        else:
            # Kod e��leşmedi
            messages.error(request, "Geçersiz doğrulama kodu. Lütfen tekrar deneyin.")
            # Hata durumunda doğrulama sayfasını tekrar göster, email'i oturumdan alıp context'e gönder
            email_to_show = stored_email 
            return render(request, 'tedarikci/tedarikci-verify-email.html', {'email': email_to_show}) # Template adını düzelt

    else:
        # GET isteği: Doğrulama sayfasını göster
        if not registration_data:
             messages.warning(request, "Lütfen önce kayıt formunu doldurunuz.")
             return redirect(reverse('tedarikci:register'))

        email_to_show = stored_email
        return render(request, 'tedarikci/tedarikci-verify-email.html', {'email': email_to_show}) # Template adını düzelt


# Tedarikçi giriş view
def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Kullanıcıyı kimlik bilgileriyle doğrula (email ve şifre)
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # Kullanıcı auth.User modelinde bulundu, şimdi TedarikciProfile objesi var mı kontrol et
            # (Profile objesinin varlığı admin onayı anlamına gelir)
            try:
                # auth.User objesi ile ilişkili TedarikciProfile objesine erişmeye çalış
                # models.py dosyasında User modeline OneToOneField eklerken related_name='tedarikci_profile' vermiştik.
                tedarikci_profile = user.tedarikci_profile

                # Kullanıcının aktif olup olmadığını kontrol et (Django'nun default is_active alanı)
                if user.is_active:
                    # Kullanıcı aktif ve TedarikciProfile objesi var (yani onaylanmış)
                    login(request, user) # Kullanıcı oturumunu başlat
                    messages.success(request, f"Hoş geldiniz, {tedarikci_profile.tedarikci_ad}!") # Başarı mesajı
                    print(f"Tedarikçi giriş yaptı: {user.email}")

                    # Başarılı giriş sonrası yönlendirilecek sayfa
                    # Burayı uygulamanızın ana sayfası veya kullanıcı paneli URL'si ile değiştirin
                    return redirect(reverse('tedarikci:tedarikci_anasayfa')) # Tedarikçi ana sayfasına yönlendir


                else:
                    # Kullanıcı aktif değil (genellikle admin tarafından deaktif edilir)
                    messages.error(request, "Hesabınız aktif değil. Lütfen yönetici ile iletişime geçin.")
                    print(f"Tedarikçi giriş denemesi başarısız: Hesap aktif değil - {user.email}")

            except TedarikciProfile.DoesNotExist:
                 # TedarikciProfile objesi yoksa, kullanıcı auth.User tablosunda var ama TedarikciProfile tablosunda yok demektir.
                 # Bu da bizim akışımızda admin tarafından henüz tam onaylanmadığı anlamına gelir (çünkü Profile onay sonrası oluşuyor).
                 messages.error(request, "Hesabınız henüz yönetici tarafından onaylanmadı.")
                 print(f"Tedarikçi giriş denemesi başarısız: TedarikciProfile objesi yok - {user.email}")
            except Exception as e:
                 # Beklenmeyen bir hata oluştu
                 print(f"Tedarikçi giriş sırasında beklenmeyen bir hata oluştu: {e}")
                 messages.error(request, "Giriş sırasında bir hata oluştu. Lütfen tekrar deneyin.")


        else:
            # Kimlik doğrulama başarısız oldu (email veya şifre yanlış veya auth.User modelinde yok)
            messages.error(request, "Geçersiz e-posta veya şifre.")
            print(f"Tedarikçi giriş denemesi başarısız: Geçersiz kimlik bilgileri - {email}")

        # Başarısız giriş veya onaylanmamış kullanıcı durumunda login sayfasını tekrar göster
        context = {
            'email': email # Girilen email'i tekrar forma doldurmak için
        }
        return render(request, 'tedarikci/tedarikci-login-page.html', context)

    else:
        # GET isteği: Login sayfasını göster
        return render(request, 'tedarikci/tedarikci-login-page.html')

# Tedarikçi ana sayfa view (örnek)
def tedarikci_anasayfa(request):
    # Kullanıcının giriş yapmış olduğundan emin olun
    if not request.user.is_authenticated:
        return redirect(reverse('tedarikci:user_login')) # Giriş yapmamışsa login sayfasına yönlendir

    # Giriş yapmışsa ana sayfayı göster
    return render(request, 'tedarikci/tedarikci-anasayfa.html')

def tedarikci_gida_formu(request):
    # Kullanıcının giriş yapmış olduğundan emin olun
    if not request.user.is_authenticated:
        messages.error(request, "Gıda eklemek için giriş yapmalısınız.")
        return redirect(reverse('tedarikci:login')) # Giriş yapmamışsa login sayfasına yönlendir
    
    if request.method == 'POST':
        # Formdan gelen verileri al
        food_name = request.POST.get('food_name')
        food_quantity = request.POST.get('food_quantity')
        food_unit = request.POST.get('food_unit')
        expiry_date = request.POST.get('expiry_date')
        food_status = request.POST.get('food_status')
        food_image = request.FILES.get('food_image') # Resim dosyasını al

        # Dosya boyutu kontrolü (5MB = 5 * 1024 * 1024 byte)
        max_size = 5 * 1024 * 1024  
        if food_image and food_image.size > max_size:
            messages.error(request, "Yüklenen resim dosyası 5MB'tan büyük olamaz.")
            # Formu tekrar gösterirken girilen verileri korumak isterseniz context içine ekleyebilirsiniz.
            context = {
                'food_name': food_name,
                'food_quantity': food_quantity,
                'food_unit': food_unit,
                'expiry_date': expiry_date,
                'food_status': food_status,
                # Resim dosyası POST isteği sonrası kaybolur, tekrar gösterilemez.
            }
            return render(request, 'tedarikci/tedarikci-gida-formu.html', context)

        # Basit doğrulama (Resim artık zorunlu, bu kontrolü güncelleyelim)
        # if not all([food_name, food_quantity, food_unit, expiry_date, food_status]):
        if not all([food_name, food_quantity, food_unit, expiry_date, food_status, food_image]):
            messages.error(request, "Lütfen tüm zorunlu alanları doldurun.")
            # Formu tekrar gösterirken girilen verileri korumak isterseniz context içine ekleyebilirsiniz.
            context = {
                'food_name': food_name,
                'food_quantity': food_quantity,
                'food_unit': food_unit,
                'expiry_date': expiry_date,
                'food_status': food_status,
                # Resim dosyası POST isteği sonrası kaybolur, tekrar gösterilemez.
            }
            return render(request, 'tedarikci/tedarikci-gida-formu.html', context)

        try:
            # Miktarı float'a çevir
            food_quantity = float(food_quantity)
        except (ValueError, TypeError):
            messages.error(request, "Miktar geçerli bir sayı olmalıdır.")
            # Formu tekrar gösterirken girilen verileri korumak isterseniz context içine ekleyebilirsiniz.
            context = {
                'food_name': food_name,
                'food_quantity': food_quantity,
                'food_unit': food_unit,
                'expiry_date': expiry_date,
                'food_status': food_status,
            }
            return render(request, 'tedarikci/tedarikci-gida-formu.html', context)

        # Giriş yapmış tedarikçi profilini al
        try:
            tedarikci_profile = request.user.tedarikci_profile
        except TedarikciProfile.DoesNotExist:
            messages.error(request, "Tedarikçi profiliniz bulunamadı. Lütfen tekrar giriş yapın.")
            return redirect(reverse('tedarikci:login')) # Profil yoksa login sayfasına yönlendir

        # Yeni FoodItem objesi oluştur ve kaydet
        food_item = FoodItem.objects.create(
            tedarikci=tedarikci_profile,
            name=food_name,
            quantity=food_quantity,
            unit=food_unit,
            expiry_date=expiry_date,
            status=food_status,
            image=food_image # Resmi kaydet
        )

        messages.success(request, "Gıda başarıyla yayınlandı!")

        # Başarılı kayıttan sonra tedarikçi gıda listesi sayfasına yönlendir
        return redirect(reverse('tedarikci:tedarikci_food_list')) # Yeni sayfaya yönlendir

    else:
        # GET isteği: Gıda formu sayfasını göster
        return render(request, 'tedarikci/tedarikci-gida-formu.html')

# Tedarikçi gıda ürünleri listesi view
def tedarikci_food_list(request):
    # Kullanıcının giriş yapmış olduğundan emin olun
    if not request.user.is_authenticated:
        messages.error(request, "Gıda listenizi görmek için giriş yapmalısınız.")
        return redirect(reverse('tedarikci:login'))

    # Giriş yapmış tedarikçi profilini al
    try:
        tedarikci_profile = request.user.tedarikci_profile
    except TedarikciProfile.DoesNotExist:
        messages.error(request, "Tedarikçi profiliniz bulunamadı.")
        return redirect(reverse('tedarikci:tedarikci_anasayfa')) # Veya uygun bir hata sayfası/yönlendirme


    completed_application_destination = FoodApplication.objects.filter(
        food_item=OuterRef('pk'),
        status='completed'
    ).order_by('-applied_at').values('final_destination')[:1] # Get the latest completed application's destination

    # Tedarikçiye ait gıda ürünlerini çek
    # food_items = FoodItem.objects.filter(tedarikci=tedarikci_profile).order_by('-created_at') # En son eklenenler üstte olsun 
    food_items = FoodItem.objects.filter(tedarikci=tedarikci_profile).annotate(
        final_destination=Subquery(completed_application_destination)
    ).order_by('-created_at')

    context = {
        'food_items': food_items
    }

    # Gıda listesi sayfasını render et
    return render(request, 'tedarikci/tedarikci-food-list.html', context)



# E-posta doğrulama sayfasını render eden view (GET isteği için kullanılacak)
# verify_email POST isteklerini işler, bu sadece sayfayı göstermek için
def tedarikci_verify_email_page(request):
    # Oturumdaki veriyi kontrol et, yoksa kayıt sayfasına yönlendir
    if 'tedarikci_registration_data' not in request.session:
        messages.warning(request, "Lütfen önce kayıt formunu doldurunuz.")
        return redirect(reverse('tedarikci:register'))
    
    # Oturumdaki email'i template'e gönder
    email_to_show = request.session['tedarikci_registration_data'].get('email', '')

    return render(request, 'tedarikci/tedarikci-verify-email.html', {'email': email_to_show})


def tedarikci_incoming_applications(request): # Kullanıcının giriş yapmış olduğundan emin olun
    if not request.user.is_authenticated:
        messages.error(request, "Gelen başvuruları görmek için giriş yapmalısınız.")
        return redirect(reverse('tedarikci:login')) # Giriş yapmamışsa login sayfasına yönlendir
    
    # Giriş yapmış tedarikçi profilini al
    try:
        tedarikci_profile = request.user.tedarikci_profile
    except TedarikciProfile.DoesNotExist:
        messages.error(request, "Tedarikçi profiliniz bulunamadı.")
        return redirect(reverse('tedarikci:tedarikci_anasayfa')) # Veya uygun bir hata sayfası/yönlendirme
    
    # Tedarikçiye ait gıda ürünlerine yapılan başvuruları çek
    # FoodApplication modelinin food_item alanının TedarikciProfile modeline bağlı olduğunu varsayıyoruz.
    # FoodApplication -> FoodItem -> TedarikciProfile
    # Bu ilişki FoodApplication modelinizde tanımlı olmalı.
    applications = FoodApplication.objects.filter(food_item__tedarikci=tedarikci_profile).order_by('-applied_at') # En son yapılan başvurular üstte olsun

    context = {
        'applications': applications
    }

    # Gelen başvurular sayfasını render et
    return render(request, 'tedarikci/tedarikci-incoming-applications.html', context)

def update_application_status(request):
    if request.method == 'POST' and request.user.is_authenticated and hasattr(request.user, 'tedarikci_profile'):
        try: 
            data = json.loads(request.body)
            application_id = data.get('application_id')
            status = data.get('status') 
            # 'approved' veya 'rejected' bekleniyor
            if not application_id or status not in ['approved', 'rejected']:
                return JsonResponse({'success': False, 'message': 'Geçersiz istek verisi.'}, status=400)
            
            # Başvuruyu veritabanından çek
            application = FoodApplication.objects.get(id=application_id, food_item__tedarikci=request.user.tedarikci_profile) # Sadece kendi ilanına gelen başvuruları güncelleyebilir

            # Başvurunun durumunu güncelle
            application.status = status
            application.save()

            
            # Eğer başvuru onaylandıysa, aynı gıdaya ait diğer beklemedeki başvuruları reddet
            if status == 'approved':
                FoodApplication.objects.filter(
                    food_item=application.food_item, 
                    status='pending'
                ).exclude(id=application.id).update(status='rejected')

                # İlgili gıda ürününün allocation_status'unu 'allocated' olarak güncelle
                food_item = application.food_item
                food_item.allocation_status = 'allocated'
                food_item.save()

            return JsonResponse({'success': True, 'message': f'Başvuru durumu {application.get_status_display()} olarak güncellendi.'})
        
        except FoodApplication.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Başvuru bulunamadı veya yetkiniz yok.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Geçersiz JSON verisi.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Bir hata oluştu: {e}'}, status=500)

    # POST dışında bir metotla veya kimlik doğrulaması olmadan gelirse
    return JsonResponse({'success': False, 'message': 'Geçersiz istek.'}, status=405)

def tedarikci_profile(request):
    """ Giriş yapmış tedarikçi kullanıcısının profil bilgilerini görüntüler. """
    if not request.user.is_authenticated:
        messages.error(request, "Profilinizi görüntülemek için giriş yapmalısınız.")
        return redirect(reverse('tedarikci:login'))

    try:
        # Giriş yapmış kullanıcının TedarikciProfile objesini al
        tedarikci_profile = request.user.tedarikci_profile
        context = {
        'tedarikci_profile': tedarikci_profile
        }
        # Tedarikçi profil şablonunu render et
        return render(request, 'tedarikci/tedarikci-profile.html', context) # Yeni şablon adı olacak

    except TedarikciProfile.DoesNotExist:
        messages.error(request, "Tedarikçi profiliniz bulunamadı.")
        return redirect(reverse('tedarikci:tedarikci_anasayfa')) # Veya uygun bir hata sayfası/yönlendirme 





