function formatEtebligat(input) {
  const warning = document.getElementById("etebligatWarning");
  const success = document.getElementById("etebligatSuccess");

  // Sayı dışında her şeyi kaldır
  let digits = input.value.replace(/\D/g, "").substring(0, 15);

  // Formatla: xxxxx-xxxxx-xxxxx
  let formatted = "";
  if (digits.length > 0) {
    formatted += digits.substring(0, 5);
  }
  if (digits.length > 5) {
    formatted += "-" + digits.substring(5, 10);
  }
  if (digits.length > 10) {
    formatted += "-" + digits.substring(10, 15);
  }

  input.value = formatted;

  // Geçerlilik kontrolü
  const isValid = /^\d{5}-\d{5}-\d{5}$/.test(formatted);

  if (input.value.length === 0) {
    warning.classList.add("d-none");
    success?.classList.add("d-none");
    input.setCustomValidity(""); // Hata yok
  } else if (isValid) {
    warning.classList.add("d-none");
    success?.classList.remove("d-none");
    input.setCustomValidity(""); // Hata yok
  } else {
    warning.classList.remove("d-none");
    success?.classList.add("d-none");
    input.setCustomValidity("E-Tebligat adresi hatalı formatta."); // Hata varsa buradan yakalanacak
  }
}
