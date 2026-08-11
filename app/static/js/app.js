function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("open");
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("open");
}

function confirmDelete(message) {
  return window.confirm(message || "Are you sure you want to delete this? This cannot be undone.");
}

// Live "min N characters" feedback on password fields. Pairs with a
// <p id="{input.dataset.hint}"> helper-text element next to the input.
function validatePasswordLength(input) {
  const minLen = parseInt(input.getAttribute("minlength"), 10) || 6;
  const hint = document.getElementById(input.dataset.hint);
  const len = input.value.length;
  const tooShort = len > 0 && len < minLen;

  if (tooShort) {
    input.setCustomValidity(`Password must be at least ${minLen} characters.`);
  } else {
    input.setCustomValidity("");
  }

  if (!hint) return;
  hint.textContent = tooShort
    ? `Too short — ${len}/${minLen} characters minimum.`
    : `Minimum ${minLen} characters.`;
  hint.classList.toggle("helper-text-error", tooShort);
}

// Show/hide the "Inspection Type" (Tempering / Rede) sub-select depending
// on whether "Inspection" is chosen in the Service Type dropdown.
function toggleInspectionSub(uid) {
  const top = document.getElementById("service_type_top_" + uid);
  const wrap = document.getElementById("inspection_sub_wrap_" + uid);
  if (!top || !wrap) return;
  wrap.style.display = top.value === "Inspection" ? "" : "none";
}

// Close modal when clicking on the backdrop itself
document.addEventListener("click", function (e) {
  if (e.target.classList && e.target.classList.contains("modal-backdrop")) {
    e.target.classList.remove("open");
  }
});

// Close modal on Escape key
document.addEventListener("keydown", function (e) {
  if (e.key === "Escape") {
    document.querySelectorAll(".modal-backdrop.open").forEach(function (el) {
      el.classList.remove("open");
    });
  }
});

// Auto-dismiss flash messages after a few seconds
document.addEventListener("DOMContentLoaded", function () {
  const flashes = document.querySelectorAll(".flash");
  flashes.forEach(function (el) {
    setTimeout(function () {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(function () { el.remove(); }, 400);
    }, 5000);
  });
});
