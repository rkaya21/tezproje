function validateLoginPassword(input) {
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

  //   if (value.length === 0) {
  //     warning.classList.add("d-none");
  //     success.classList.add("d-none");
  //   } else if (!isValid) {
  //     warning.classList.remove("d-none");
  //     success.classList.add("d-none");
  //   } else {
  //     warning.classList.add("d-none");
  //     success.classList.remove("d-none");
  //   }
}

function toggleLoginPasswordVisibility(inputId, button) {
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
