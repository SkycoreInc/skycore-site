// Sticky nav border on scroll
const nav = document.querySelector(".nav");
if (nav) {
  const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 8);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
}

// Mobile burger toggle
const burger = document.querySelector(".nav-burger");
if (burger && nav) {
  burger.addEventListener("click", () => nav.classList.toggle("menu-open"));
}

// Active nav link
document.querySelectorAll(".nav-links a").forEach((link) => {
  const href = link.getAttribute("href");
  if (!href || href.startsWith("#")) return;
  const path = window.location.pathname.replace(/\/$/, "");
  const linkPath = href.replace(/\/$/, "").replace(/^\./, "");
  if (
    path.endsWith(linkPath) ||
    (linkPath === "/index.html" && (path === "" || path.endsWith("/"))) ||
    (linkPath.includes("blog") && path.includes("blog"))
  ) {
    link.classList.add("active");
  }
});

// Reveal on scroll
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.1 }
);
document.querySelectorAll(".reveal").forEach((el) => revealObserver.observe(el));

// TidyCal popup modal
(function () {
  const TIDYCAL_URL = "https://tidycal.com/";

  // Inject modal markup
  const modal = document.createElement("div");
  modal.id = "tc-modal";
  modal.setAttribute("role", "dialog");
  modal.setAttribute("aria-modal", "true");
  modal.setAttribute("aria-label", "Book a free consultation");
  modal.innerHTML =
    '<div id="tc-overlay"></div>' +
    '<div id="tc-dialog">' +
      '<button id="tc-close" aria-label="Close">&times;</button>' +
      '<iframe id="tc-frame" src="" allow="camera; microphone; fullscreen" title="Book a consultation"></iframe>' +
    "</div>";
  document.body.appendChild(modal);

  function openModal(path) {
    document.getElementById("tc-frame").src = TIDYCAL_URL + path;
    modal.classList.add("tc-open");
    document.body.style.overflow = "hidden";
    document.getElementById("tc-close").focus();
  }

  function closeModal() {
    modal.classList.remove("tc-open");
    // Small delay so the animation plays before src is cleared
    setTimeout(function () {
      document.getElementById("tc-frame").src = "";
    }, 250);
    document.body.style.overflow = "";
  }

  document.getElementById("tc-overlay").addEventListener("click", closeModal);
  document.getElementById("tc-close").addEventListener("click", closeModal);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal.classList.contains("tc-open")) closeModal();
  });

  // Delegate all [data-tidycal-popup] clicks
  document.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-tidycal-popup]");
    if (!btn) return;
    e.preventDefault();
    openModal(btn.getAttribute("data-tidycal-popup"));
  });
})();
