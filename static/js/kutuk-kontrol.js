function formatKutukNo(input) {
  const raw = input.value;

  // 20- kısmı sabit olmalı, onu kontrol et
  if (!raw.startsWith("20-")) {
    input.value = "20-";
    return;
  }

  // Sadece 20- sonrası işlenmeli
  let digits = raw.replace(/[^0-9]/g, "").substring(2); // 20'yi at, kalan sadece rakamlar

  // En fazla 6 rakam girilebilir (3 + 3)
  digits = digits.substring(0, 6);

  // Biçimlendir: 20-XXX-XXX
  let formatted = "20-";
  if (digits.length > 3) {
    formatted += digits.substring(0, 3) + "-" + digits.substring(3);
  } else {
    formatted += digits;
  }

  input.value = formatted;

  // Geçerlilik kontrolü
  const warning = document.getElementById("kutukWarning");
  const success = document.getElementById("kutukSuccess");

  const isValid = /^20-\d{3}-\d{3}$/.test(formatted);

  if (!isValid && digits.length > 0) {
    warning.classList.remove("d-none");
    success?.classList.add("d-none"); // <-- Yeni satır
    input.setCustomValidity("Kütük numarası formatı geçersiz."); // Burada
  } else if (isValid) {
    warning.classList.add("d-none");
    success?.classList.remove("d-none"); // <-- Yeni satır
    input.setCustomValidity(""); // Geçerli durumunda temizle
  } else {
    warning.classList.add("d-none");
    success?.classList.add("d-none"); // <-- Yeni satır
    input.setCustomValidity("Lütfen geçerli bir kütük numarası girin."); // burada
  }
}
