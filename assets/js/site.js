/* GVN Estate Invest — the only script on the site.
   1. Mobile menu toggle.
   2. Every <form data-form="..."> posts JSON to FORM_ENDPOINT.

   Change the endpoint here and nowhere else. */
var FORM_ENDPOINT = "https://bkgjoztepcdranhbaurx.supabase.co/functions/v1/site-form";

(function () {
  "use strict";

  /* ---- 1. Menu ---- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
  }

  /* ---- 2. Forms ---- */
  var forms = document.querySelectorAll("form[data-form]");
  Array.prototype.forEach.call(forms, setupForm);

  function setupForm(form) {
    var status = form.querySelector(".form-status");
    var button = form.querySelector("button[type=submit]");
    var buttonText = button ? button.textContent : "";

    form.setAttribute("novalidate", "novalidate");

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      clearErrors(form);

      var firstBad = validate(form);
      if (firstBad) {
        show(status, "err", "Please check the highlighted fields and try again.");
        firstBad.focus();
        return;
      }

      // Honeypot: a person never sees this field, so anything in it is a bot.
      // Pretend it worked and send nothing.
      var trap = form.querySelector("input[name=website]");
      if (trap && trap.value) {
        finish(form, status);
        return;
      }

      var payload = {
        form: form.getAttribute("data-form"),
        fields: collect(form),
        page: location.pathname
      };

      if (button) { button.disabled = true; button.textContent = "Sending…"; }
      show(status, "busy", "Sending…");

      fetch(FORM_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }).then(function (res) {
        if (!res.ok) { throw new Error("HTTP " + res.status); }
        finish(form, status);
      }).catch(function () {
        show(status, "err", form.getAttribute("data-error") ||
          "Sorry, that didn't go through. Please try again, or email v.grey@gvnestateinvest.com or call 01782 938 111.");
      }).then(function () {
        if (button) { button.disabled = false; button.textContent = buttonText; }
      });
    });
  }

  function finish(form, status) {
    show(status, "ok", form.getAttribute("data-success") || "Thank you. We'll be in touch soon.");
    var go = form.getAttribute("data-redirect");
    form.reset();
    if (go) { setTimeout(function () { location.assign(go); }, 1200); }
  }

  function show(el, kind, text) {
    if (!el) { return; }
    el.className = "form-status is-" + kind;
    el.textContent = text;
  }

  /* Each control carries data-label: the exact question wording from the
     old Wix form. That wording is the key the CRM reads, so it must not be
     "tidied". Checkbox groups with the same data-label are joined. */
  function collect(form) {
    var out = {};
    var controls = form.querySelectorAll("[data-label]");
    Array.prototype.forEach.call(controls, function (el) {
      var label = el.getAttribute("data-label");
      var value;
      if (el.type === "checkbox") {
        if (el.hasAttribute("data-group")) {
          if (!el.checked) { return; }
          out[label] = out[label] ? out[label] + ", " + el.value : el.value;
          return;
        }
        value = el.checked ? "Yes" : "No";
      } else if (el.type === "file") {
        var names = [];
        for (var i = 0; i < el.files.length; i++) { names.push(el.files[i].name); }
        value = names.join(", ");
      } else {
        value = (el.value || "").trim();
      }
      if (value === "" && out[label] !== undefined) { return; }
      out[label] = value;
    });
    return out;
  }

  function validate(form) {
    var first = null;
    var controls = form.querySelectorAll("input, select, textarea");
    Array.prototype.forEach.call(controls, function (el) {
      if (el.name === "website" || el.type === "hidden") { return; }
      var msg = "";
      if (el.type === "checkbox") {
        if (el.required && !el.checked) { msg = "Please tick this box to continue."; }
      } else if (el.required && !(el.value || "").trim()) {
        msg = "This field is required.";
      } else if (el.type === "email" && el.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value.trim())) {
        msg = "Please enter a valid email address.";
      } else if (el.type === "tel" && el.value && el.value.replace(/[^0-9]/g, "").length < 7) {
        msg = "Please enter a valid phone number.";
      } else if (el.type === "file" && el.files && el.getAttribute("data-max")) {
        if (el.files.length > parseInt(el.getAttribute("data-max"), 10)) {
          msg = "Please choose up to " + el.getAttribute("data-max") + " photos.";
        }
      }
      if (msg) {
        markError(el, msg);
        if (!first) { first = el; }
      }
    });
    return first;
  }

  function markError(el, msg) {
    el.setAttribute("aria-invalid", "true");
    var box = el.closest(".field") || el.parentNode;
    var p = document.createElement("p");
    p.className = "error-text";
    p.id = (el.id || el.name) + "-error";
    p.textContent = msg;
    box.appendChild(p);
    var described = el.getAttribute("aria-describedby");
    el.setAttribute("aria-describedby", described ? described + " " + p.id : p.id);
  }

  function clearErrors(form) {
    Array.prototype.forEach.call(form.querySelectorAll(".error-text"), function (p) {
      var el = form.querySelector("[aria-describedby~='" + p.id + "']");
      if (el) {
        var rest = el.getAttribute("aria-describedby").split(" ").filter(function (x) { return x !== p.id; }).join(" ");
        if (rest) { el.setAttribute("aria-describedby", rest); } else { el.removeAttribute("aria-describedby"); }
        el.removeAttribute("aria-invalid");
      }
      p.parentNode.removeChild(p);
    });
  }
})();
