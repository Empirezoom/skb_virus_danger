const loginForm = document.getElementById("loginForm");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("togglePassword");
const notification = document.getElementById("notification");

// Show/Hide Password Logic
togglePassword.addEventListener("click", function () {
  const type =
    passwordInput.getAttribute("type") === "password" ? "text" : "password";
  passwordInput.setAttribute("type", type);
  this.textContent = type === "password" ? "SHOW" : "HIDE";
});

// Fancy Notification Function
function showNotification(message, type) {
  notification.textContent = message;
  notification.className =
    "show " + (type === "success" ? "notif-success" : "notif-error");

  setTimeout(() => {
    notification.classList.remove("show");
  }, 3000);
}

loginForm.addEventListener("submit", function (e) {
  const username = document.getElementById("username").value.trim();
  const password = passwordInput.value;
  // Minimal client-side validation: require both fields, otherwise block submit
  if (!username || !password) {
    e.preventDefault();
    showNotification("Please enter username and password", "error");
  }
  // Otherwise allow the form to submit to the server for real authentication
});
