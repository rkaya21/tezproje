const form = document.getElementById("myForm");
const vergiNoInput = document.getElementById("vergiNo");
const vergiNoInvalid = document.getElementById("vergiNoInvalid");
const vergiNoValid = document.getElementById("vergiNoValid");

// Sadece sayı girilmesini sağla
vergiNoInput.addEventListener("input", () => {
  vergiNoInput.value = vergiNoInput.value.replace(/\D/g, ""); // Harf varsa sil
  if (vergiNoInput.value.length === 10) {
    vergiNoValid.style.display = "block";
    vergiNoInvalid.style.display = "none";
  } else {
    vergiNoValid.style.display = "none";
    vergiNoInvalid.style.display = "block";
  }
});

// Form gönderimini kontrol et
form.addEventListener("submit", (e) => {
  const value = vergiNoInput.value.trim();
  if (!/^\d{10}$/.test(value)) {
    e.preventDefault(); // Formu gönderme
    vergiNoInvalid.style.display = "block";
    vergiNoValid.style.display = "none";
    vergiNoInput.focus();
  }
});

// Sayfa yüklendiğinde feedback'leri gizle
window.addEventListener("DOMContentLoaded", () => {
  vergiNoInvalid.style.display = "none";
  vergiNoValid.style.display = "none";
});
