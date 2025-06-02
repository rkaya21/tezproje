// function formatNameInput(input) {
//   // Sadece harf ve boşluklara izin ver
//   let cleaned = input.value.replace(/[^a-zA-ZğüşöçıİĞÜŞÖÇ\s]/g, "");

//   // Başta/sonda boşlukları kaldır, birden fazla boşluğu teke indir
//   cleaned = cleaned.replace(/\s+/g, " ").trim();

//   // Her kelimenin ilk harfini büyük yap, diğer harfleri küçük
//   cleaned = cleaned
//     .split(" ")
//     .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
//     .join(" ");

//   input.value = cleaned;
// }

function formatNameInput(input) {
  // Sadece harf ve boşluklara izin ver
  let cleaned = input.value.replace(/[^a-zA-ZğüşöçıİĞÜŞÖÇ\s]/g, "");

  // Başta/sonda boşlukları kaldır, birden fazla boşluğu teke indir
  cleaned = cleaned.replace(/\s+/g, " ").trim();

  // Her kelimenin ilk harfini büyük yap, diğer harfleri küçük
  let words = cleaned.split(" ");
  let isValid = true;

  let formattedWords = words.map((word) => {
    if (word.length < 2) {
      isValid = false;
    }
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  });

  input.value = formattedWords.join(" ");

  // Eğer bir kelime 2 harften kısa ise geçersiz say
  if (!isValid) {
    input.setCustomValidity("Her kelime en az 2 harfli olmalıdır.");
    input.reportValidity(); // Tarayıcıya hatayı göster
  } else {
    input.setCustomValidity(""); // Hata yoksa temizle
  }
}
