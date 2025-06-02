// function validateEmail(input) {
//   const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
//   const warning = document.getElementById("emailWarning");

//   // E-posta doğru formatta mı?
//   if (!emailPattern.test(input.value) && input.value.length > 0) {
//     warning.classList.remove("d-none"); // Hata mesajını göster
//   } else {
//     warning.classList.add("d-none"); // Hata mesajını gizle
//   }
// }

function validateEmail(input) {
  const warning = document.getElementById("emailWarning");
  const success = document.getElementById("emailSuccess");

  const email = input.value.trim();
  let isValid = false;

  // E-posta @ ile ayrılmış mı?
  const parts = email.split("@");

  if (parts.length === 2 && parts[0].length >= 2) {
    const localPart = parts[0];
    const domainPart = parts[1];

    // Harfle başlamalı
    const startsWithLetter = /^[a-zA-Z]/.test(localPart);

    // @ öncesi geçerli karakterler içermeli
    const localValid = /^[a-zA-Z0-9._-]+$/.test(localPart);

    // @ sonrası domain: harf içermeli, ve geçerli bir domain olmalı
    const hasLetterInDomain = /[a-zA-Z]/.test(domainPart.split(".")[0]);
    const domainValid = /^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(domainPart);

    if (startsWithLetter && localValid && hasLetterInDomain && domainValid) {
      isValid = true;
    }
  }

  // Uyarı ve başarı durumlarını güncelle
  if (email.length === 0) {
    warning.classList.add("d-none");
    success?.classList.add("d-none");
  } else if (isValid) {
    warning.classList.add("d-none");
    success?.classList.remove("d-none");
  } else {
    warning.classList.remove("d-none");
    success?.classList.add("d-none");
  }
}
