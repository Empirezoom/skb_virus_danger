// Hamburger menu logic
const hamburger = document.getElementById("hamburger");
const mobileNav = document.getElementById("mobileNav");
hamburger.addEventListener("click", () => {
  hamburger.classList.toggle("open");
  mobileNav.classList.toggle("show");
});
hamburger.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    hamburger.click();
  }
});
Array.from(mobileNav.querySelectorAll("a")).forEach((link) => {
  link.addEventListener("click", () => {
    hamburger.classList.remove("open");
    mobileNav.classList.remove("show");
  });
});

// Quick Actions
function transferFunds() {
  alert("Transfer Funds feature coming soon!");
}
function payBill() {
  alert("Pay a Bill feature coming soon!");
}
function downloadStatement() {
  alert("Download Statement feature coming soon!");
}
window.transferFunds = transferFunds;
window.payBill = payBill;
window.downloadStatement = downloadStatement;
