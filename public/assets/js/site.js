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
  var header = document.querySelector(".site-header");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      if (header) { header.classList.toggle("is-open", open); }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        if (header) { header.classList.remove("is-open"); }
        toggle.focus();
      }
    });
  }

  /* ---- 1b. Header turns solid once the page scrolls past the top ---- */
  if (header && "IntersectionObserver" in window) {
    var sentinel = document.createElement("div");
    sentinel.setAttribute("aria-hidden", "true");
    sentinel.style.cssText = "position:absolute;top:0;left:0;width:1px;height:40px;pointer-events:none";
    document.body.insertBefore(sentinel, document.body.firstChild);
    new IntersectionObserver(function (entries) {
      header.classList.toggle("is-solid", !entries[0].isIntersecting);
    }).observe(sentinel);
  }

  /* ---- 1c. Sections ease in as they reach the viewport.
     Only when motion is allowed; without JS nothing is ever hidden. ---- */
  var still = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!still && "IntersectionObserver" in window) {
    var targets = document.querySelectorAll(
      "main .section .head, main .section .head-row, main .section .reveal-me, " +
      "main .section .grid > *, main .section .post-grid > *, main .section .process > li, " +
      "main .section .mosaic-tiles > *, main .section .steps > li, main .section .values > li, main .section .cta-band");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    Array.prototype.forEach.call(targets, function (el) {
      var parent = el.parentNode;
      var index = Array.prototype.indexOf.call(parent.children, el);
      el.style.setProperty("--i", Math.min(index, 6));
      el.classList.add("reveal");
      io.observe(el);
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
    var stepper = setupSteps(form, status);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      clearErrors(form);

      var firstBad = validate(form);
      if (firstBad) {
        // On a stepped form, go back to the step that holds the problem.
        if (stepper) { stepper.showStepOf(firstBad); }
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
          "Sorry, that didn't go through. Please try again, or email info@gvnestateinvest.com or call 01782 938 111.");
      }).then(function () {
        if (button) { button.disabled = false; button.textContent = buttonText; }
      });
    });
  }

  /* Stepped forms (the strategy call): one short step at a time, because
     a long form puts people off. Every field stays in the form, so what is
     sent is exactly what the one-page form sent. Without this script all
     steps simply show. */
  function setupSteps(form, status) {
    var steps = form.querySelectorAll(".form-step");
    if (steps.length < 2) { return null; }
    var progress = form.querySelector(".form-progress");
    var text = form.querySelector(".form-progress-text");
    var bar = form.querySelector(".form-progress-bar span");
    var back = form.querySelector(".form-back");
    var next = form.querySelector(".form-next");
    var submit = form.querySelector("button[type=submit]");
    var current = 0;

    form.classList.add("is-stepped");
    progress.hidden = false;

    function go(i, focus) {
      current = Math.max(0, Math.min(steps.length - 1, i));
      Array.prototype.forEach.call(steps, function (s, n) { s.classList.toggle("is-current", n === current); });
      var last = current === steps.length - 1;
      back.hidden = current === 0;
      next.hidden = last;
      submit.hidden = !last;
      text.textContent = "Step " + (current + 1) + " of " + steps.length + ": " + steps[current].getAttribute("data-step-title");
      bar.style.transform = "scaleX(" + ((current + 1) / steps.length).toFixed(4) + ")";
      if (focus) {
        var first = steps[current].querySelector("input:not([type=hidden]), select, textarea");
        if (first) { first.focus({ preventScroll: true }); }
        var top = form.getBoundingClientRect().top + window.pageYOffset - 110;
        if (window.pageYOffset > top) { window.scrollTo(0, top); }
      }
    }

    next.addEventListener("click", function () {
      clearErrors(form);
      var bad = validate(steps[current]);
      if (bad) {
        show(status, "err", "Please check the highlighted fields to continue.");
        bad.focus();
        return;
      }
      show(status, "", "");
      go(current + 1, true);
    });
    back.addEventListener("click", function () {
      clearErrors(form);
      show(status, "", "");
      go(current - 1, true);
    });
    form.addEventListener("reset", function () { setTimeout(function () { go(0, false); }, 0); });

    go(0, false);
    return {
      showStepOf: function (el) {
        Array.prototype.forEach.call(steps, function (s, n) { if (s.contains(el)) { go(n, false); } });
      }
    };
  }

  function finish(form, status) {
    show(status, "ok", form.getAttribute("data-success") || "Thank you. We'll be in touch soon.");
    var go = form.getAttribute("data-redirect");
    form.reset();
    if (go) { setTimeout(function () { location.assign(go); }, 1200); }
  }

  function show(el, kind, text) {
    if (!el) { return; }
    el.className = "form-status" + (kind ? " is-" + kind : "");
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
