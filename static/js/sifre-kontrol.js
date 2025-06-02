function togglePasswordInfo() {
  const infoBox = document.getElementById("passwordInfoBox");
  infoBox.style.display = infoBox.style.display === "none" ? "block" : "none";
}

function validatePassword(input) {
  const value = input.value;
  const warning = document.getElementById("passwordWarning");
  const success = document.getElementById("passwordSuccess");

  const isValid =
    value.length >= 8 &&
    value.length <= 15 &&
    /[a-z]/.test(value) &&
    /[A-Z]/.test(value) &&
    /[0-9]/.test(value) &&
    /[^A-Za-z0-9]/.test(value);

  if (value.length === 0) {
    warning.classList.add("d-none");
    success.classList.add("d-none");
  } else if (!isValid) {
    warning.classList.remove("d-none");
    success.classList.add("d-none");
  } else {
    warning.classList.add("d-none");
    success.classList.remove("d-none");
  }
}

function validatePasswordMatch() {
  const password = document.getElementById("inputPassword4").value;
  const confirmPassword = document.getElementById("confirmPassword").value;

  const warning = document.getElementById("passwordMatchWarning");
  const success = document.getElementById("passwordMatchSuccess");

  if (confirmPassword.length === 0) {
    warning.classList.add("d-none");
    success.classList.add("d-none");
  } else if (password !== confirmPassword) {
    warning.classList.remove("d-none");
    success.classList.add("d-none");
  } else {
    warning.classList.add("d-none");
    success.classList.remove("d-none");
  }
}

function togglePasswordVisibility(inputId, button) {
  const input = document.getElementById(inputId);
  const icon = button.querySelector("i");

  if (input.type === "password") {
    input.type = "text";
    icon.classList.remove("fa-eye");
    icon.classList.add("fa-eye-slash");
  } else {
    input.type = "password";
    icon.classList.remove("fa-eye-slash");
    icon.classList.add("fa-eye");
  }
}

function finalValidation() {
  // kutuk kontrol
  const kutukNoInput = document.getElementById("kutukNo");
  if (kutukNoInput && !kutukNoInput.classList.contains("d-none")) {
    kutukNoInput.reportValidity(); // Uyarıyı göster
  }

  const passwordInput = document.getElementById("inputPassword4");
  const confirmPasswordInput = document.getElementById("confirmPassword");
  const phoneValid = validatePhone(); // Daha önce tanımlandıysa

  const passwordValue = passwordInput.value;
  const confirmPasswordValue = confirmPasswordInput.value;

  const isPasswordValid =
    passwordValue.length >= 8 &&
    passwordValue.length <= 15 &&
    /[a-z]/.test(passwordValue) &&
    /[A-Z]/.test(passwordValue) &&
    /[0-9]/.test(passwordValue) &&
    /[^A-Za-z0-9]/.test(passwordValue);

  const isPasswordMatch = passwordValue === confirmPasswordValue;

  // Tüm doğrulamaların başarılı olması gerekiyor
  if (phoneValid && isPasswordValid && isPasswordMatch) {
    return true; // Form gönderilebilir
  } else {
    // Hatalıysa görsel uyarıları yeniden çalıştır
    validatePassword(passwordInput);
    validatePasswordMatch();
    return false; // Form gönderilmesin
  }
}
