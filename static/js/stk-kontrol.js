document.getElementById("stkTuru").addEventListener("change", function () {
  const secilen = this.value;
  const kutukDiv = document.getElementById("kutukNoDiv");
  const etebligatDiv = document.getElementById("etebligatDiv");
  const kutukInput = document.getElementById("kutukNo");

  if (secilen === "dernek") {
    kutukDiv.classList.remove("d-none");
    etebligatDiv.classList.add("d-none");
    kutukInput.setAttribute("required", "required");
  } else if (secilen === "vakif") {
    etebligatDiv.classList.remove("d-none");
    kutukDiv.classList.add("d-none");
    kutukInput.removeAttribute("required");
  } else {
    kutukDiv.classList.add("d-none");
    etebligatDiv.classList.add("d-none");
    kutukInput.removeAttribute("required");
  }
});
