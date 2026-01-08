function validateSSN(ssn) {
  // Accepts 9 digits or formatted as XXX-XX-XXXX
  return /^(\d{3}-\d{2}-\d{4}|\d{9})$/.test(ssn);
}
function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}
function validatePhone(phone) {
  // Accepts numbers, spaces, dashes
  return /^[\d\s\-]{6,}$/.test(phone);
}
// File preview (show file name together with selected ID type)
const idTypeSelect = document.getElementById("idType");
document.getElementById("idFront").addEventListener("change", function () {
  const preview = document.getElementById("idFrontPreview");
  const name = this.files && this.files[0] ? this.files[0].name : "";
  const typeLabel =
    idTypeSelect && idTypeSelect.options[idTypeSelect.selectedIndex]
      ? idTypeSelect.options[idTypeSelect.selectedIndex].text
      : "ID";
  preview.textContent = name ? `${typeLabel} â€” ${name}` : "";
});
document.getElementById("idBack").addEventListener("change", function () {
  const preview = document.getElementById("idBackPreview");
  const name = this.files && this.files[0] ? this.files[0].name : "";
  const typeLabel =
    idTypeSelect && idTypeSelect.options[idTypeSelect.selectedIndex]
      ? idTypeSelect.options[idTypeSelect.selectedIndex].text
      : "ID";
  preview.textContent = name ? `${typeLabel} â€” ${name}` : "";
});

// Password show/hide toggles
document.querySelectorAll(".pw-toggle").forEach((btn) => {
  btn.addEventListener("click", function () {
    const targetId = this.getAttribute("data-target");
    const input = document.getElementById(targetId);
    if (!input) return;
    if (input.type === "password") {
      input.type = "text";
      this.textContent = "Hide";
      this.setAttribute("aria-label", "Hide password");
    } else {
      input.type = "password";
      this.textContent = "Show";
      this.setAttribute("aria-label", "Show password");
    }
  });
});

// Show/hide SSN based on country code
const countryCodeInput = document.getElementById("countryCode");
const ssnSection = document.getElementById("ssnSection");
const ssnInput = document.getElementById("ssn");
function updateSSNVisibility() {
  if (countryCodeInput.value.trim() === "+1") {
    ssnSection.style.display = "block";
    ssnInput.required = true;
  } else {
    ssnSection.style.display = "none";
    ssnInput.required = false;
    ssnInput.value = "";
  }
}
countryCodeInput.addEventListener("input", updateSSNVisibility);
updateSSNVisibility();

const registerForm = document.getElementById("registerForm");
const registerError = document.getElementById("registerError");
const registerSuccess = document.getElementById("registerSuccess");
const summaryCard = document.getElementById("summaryCard");
const registerCard = document.getElementById("registerCard");

registerForm.addEventListener("submit", function (e) {
  registerError.textContent = "";
  registerSuccess.textContent = "";

  const firstName = document.getElementById("firstName").value.trim();
  const lastName = document.getElementById("lastName").value.trim();
  const email = document.getElementById("email").value.trim();
  const countryCode = countryCodeInput.value.trim();
  const phone = document.getElementById("phone").value.trim();
  const ssn = ssnInput.value.trim();
  const idFront = document.getElementById("idFront").files[0];
  const idBack = document.getElementById("idBack").files[0];
  const username = document.getElementById("regUsername").value.trim();

  // Basic client-side validation; let the server handle persistence and security-sensitive fields
  if (!firstName || !lastName) {
    e.preventDefault();
    registerError.textContent = "Please enter your first and last name.";
    return;
  }
  if (!username || username.length < 3) {
    e.preventDefault();
    registerError.textContent = "Please choose a username (min 3 characters).";
    return;
  }
  if (!email || !validateEmail(email)) {
    e.preventDefault();
    registerError.textContent = "Please enter a valid email address.";
    return;
  }
  if (!countryCode.match(/^\+\d{1,4}$/)) {
    e.preventDefault();
    registerError.textContent =
      "Please enter a valid country code (e.g. +1, +44, +234).";
    return;
  }
  if (!phone || !validatePhone(phone)) {
    e.preventDefault();
    registerError.textContent = "Please enter a valid phone number.";
    return;
  }
  if (countryCode === "+1") {
    if (!ssn || !validateSSN(ssn)) {
      e.preventDefault();
      registerError.textContent =
        "Please enter a valid SSN (9 digits or XXX-XX-XXXX) for USA.";
      return;
    }
  }
  if (!idFront || !idBack) {
    e.preventDefault();
    registerError.textContent =
      "Please upload both front and back of your valid ID.";
    return;
  }

  // Allow the form to submit to the server; server will create RegistrationRequest and handle next steps
});

// Format SSN as XXX-XX-XXXX while typing
document.getElementById("ssn").addEventListener("input", function (e) {
  let val = this.value.replace(/\D/g, "").slice(0, 9);
  if (val.length > 5) val = val.replace(/(\d{3})(\d{2})(\d{1,4})/, "$1-$2-$3");
  else if (val.length > 3) val = val.replace(/(\d{3})(\d{1,2})/, "$1-$2");
  this.value = val;
});
