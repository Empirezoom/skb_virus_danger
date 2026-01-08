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
// Hide mobile nav on link click
Array.from(mobileNav.querySelectorAll("a")).forEach((link) => {
  link.addEventListener("click", () => {
    hamburger.classList.remove("open");
    mobileNav.classList.remove("show");
  });
});

// Demo data
const transactions = [
  { date: "2025-12-29", desc: "Starbucks", amount: -4.5 },
  { date: "2025-12-28", desc: "Direct Deposit", amount: 1500.0 },
  { date: "2025-12-27", desc: "Amazon", amount: -89.99 },
  { date: "2025-12-26", desc: "ATM Withdrawal", amount: -100.0 },
];
// Populate transactions
function populateTransactions() {
  const transactionList = document.getElementById("transactionList");
  transactionList.innerHTML = "";
  transactions.forEach((tx) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${tx.date} <small>${tx.desc}</small></span>
          <span style="font-weight:bold; color:${
            tx.amount < 0 ? "#d32f2f" : "#388e3c"
          };">
            ${tx.amount < 0 ? "-" : "+"}$${Math.abs(tx.amount).toFixed(2)}
          </span>`;
    transactionList.appendChild(li);
  });
}
// Initial population
populateTransactions();
