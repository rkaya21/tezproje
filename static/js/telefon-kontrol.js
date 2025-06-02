document.addEventListener("DOMContentLoaded", function () {
  const telefonInput = document.getElementById("cepTelefon");
  const form = document.getElementById("myForm");

  if (telefonInput) {
    // Sayfa yüklendiğinde "05" ile başlamıyorsa düzelt
    if (!telefonInput.value.startsWith("05")) {
      telefonInput.value = "05";
    }

    // Kullanıcı giriş yaptığında sadece rakam alsın ve 05'le başlasın
    telefonInput.addEventListener("input", function () {
      let onlyDigits = this.value.replace(/\D/g, "");

      if (!onlyDigits.startsWith("05")) {
        onlyDigits = "05" + onlyDigits.slice(2);
      }

      this.value = onlyDigits.slice(0, 11);

      // Geçerlilik kontrolü: 11 haneli mi?
      if (this.value.length === 11) {
        this.classList.remove("is-invalid");
        this.classList.add("is-valid");
      } else {
        this.classList.remove("is-valid");
        this.classList.add("is-invalid");
      }
    });

    // 05 kısmının silinmesini engelle (ama tüm input seçilirse izin ver)
    telefonInput.addEventListener("keydown", function (e) {
      const isFullSelection =
        this.selectionStart === 0 && this.selectionEnd === this.value.length;
      const isTryingToDeletePrefix =
        (this.selectionStart <= 2 || this.selectionEnd <= 2) &&
        (e.key === "Backspace" || e.key === "Delete");

      if (isTryingToDeletePrefix && !isFullSelection) {
        e.preventDefault();
      }
    });

    // Yapıştırmayı engelle
    telefonInput.addEventListener("paste", function (e) {
      e.preventDefault();
    });

    // Rakam dışında karakter girişini ve 05'ten önce yazmayı engelle
    telefonInput.addEventListener("keypress", function (e) {
      const charCode = e.which ? e.which : e.keyCode;
      if (charCode < 48 || charCode > 57 || this.selectionStart < 2) {
        e.preventDefault();
      }
    });

    // Form submit kontrolü
    // form.addEventListener("submit", function (e) {
    //   if (telefonInput.value.length !== 11) {
    //     telefonInput.classList.remove("is-valid");
    //     telefonInput.classList.add("is-invalid");
    //     e.preventDefault(); // Form gönderimini engelle
    //   }
    // });
  }
});

// const phoneValidator = {
//   finalValidation: function () {
//     const isPhoneValid = validatePhone();

//     return isPhoneValid;
//   },
// };

function validatePhone() {
  const phoneInput = document.getElementById("cepTelefon");
  const phone = phoneInput.value.trim();
  const validDiv = document.getElementById("phoneValid");
  const invalidDiv = document.getElementById("phoneInvalid");

  // Telefon numarası sadece rakamlardan oluşuyor mu?
  const phonePattern = /^[0-9]{11}$/;

  if (phonePattern.test(phone)) {
    phoneInput.classList.remove("is-invalid");
    phoneInput.classList.add("is-valid");
    validDiv.style.display = "block";
    invalidDiv.style.display = "none";
    return true;
  } else {
    phoneInput.classList.remove("is-valid");
    phoneInput.classList.add("is-invalid");
    validDiv.style.display = "none";
    invalidDiv.style.display = "block";
    return false;
  }
}

// function finalValidation() {
//   return validatePhone();
// }

// Sayfa yüklendiğinde valid-feedback ve invalid-feedback kutularını gizle
window.onload = function () {
  document.getElementById("phoneValid").style.display = "none";
  document.getElementById("phoneInvalid").style.display = "none";
};
