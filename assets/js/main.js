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

// Contact form stub (wire to Formspree or your backend)
const form = document.querySelector("#contact-form");
if (form) {
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const btn = form.querySelector("button[type=submit]");
    if (btn) { btn.disabled = true; btn.textContent = "Sending..."; }
    setTimeout(() => {
      form.innerHTML = `<div style="padding:32px;text-align:center;">
        <div style="font-size:2.5rem;margin-bottom:12px;">✓</div>
        <h3 style="color:var(--cyan);font-family:var(--font-head);margin-bottom:8px;">Message received.</h3>
        <p>We'll reply within one business day.</p>
      </div>`;
    }, 800);
  });
}
