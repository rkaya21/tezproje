function validateImage(input) {
    const file = input.files[0];
    const warning = document.getElementById("imageWarning"); // Uyarı mesajı için yeni ID
  
    const maxSizeBytes = 5 * 1024 * 1024; // 5MB sınırı
  
    if (file && file.size > maxSizeBytes) {
      warning.textContent = "Yüklenen resim dosyası 5MB'tan büyük olamaz."; // Uyarı metni
      warning.classList.remove("d-none");
      input.value = ""; // dosya seçimini iptal et
    } else {
      warning.classList.add("d-none");
      warning.textContent = ""; // Uyarı metnini temizle
    }
  
    // İsteğe bağlı: Dosya türü kontrolü de eklenebilir, ama 'accept' attribute'u zaten yardımcı oluyor
    // const allowedTypes = ['image/jpeg', 'image/jpg', 'image/heic', 'image/heif'];
    // if (file && !allowedTypes.includes(file.type)) {
    //   warning.textContent = "Sadece .jpg, .jpeg ve .heic formatında resim yükleyebilirsiniz.";
    //   warning.classList.remove("d-none");
    //   input.value = "";
    // } else if (file && file.size <= maxSizeBytes) { // Sadece boyut kontrolü geçtiyse türü kontrol et
    //   warning.classList.add("d-none");
    //   warning.textContent = "";
    // }
  }