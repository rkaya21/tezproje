// document
//   .getElementById("faaliyetBelgesi")
//   .addEventListener("change", function () {
//     const file = this.files[0];
//     const previewDiv = document.getElementById("pdfPreview");
//     const pdfFrame = document.getElementById("pdfFrame");

//     if (file && file.type === "application/pdf") {
//       const fileURL = URL.createObjectURL(file);
//       pdfFrame.src = fileURL;
//       previewDiv.classList.remove("d-none");
//     } else {
//       previewDiv.classList.add("d-none");
//       pdfFrame.src = "";
//       alert("Lütfen sadece PDF formatında bir dosya yükleyin.");
//     }
//   });

function validatePDF(input) {
  const file = input.files[0];
  const warning = document.getElementById("fileWarning");

  if (file && file.size > 2 * 1024 * 1024) {
    // 2MB sınırı
    warning.classList.remove("d-none");
    input.value = ""; // dosya seçimini iptal et
  } else {
    warning.classList.add("d-none");
  }
}
