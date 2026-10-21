/* GVN Estate Invest — the only script on the site.
   1. Mobile menu toggle.
   2. Every <form data-form="..."> posts JSON to FORM_ENDPOINT.
   3. /letter: the code from a GVN letter goes to LETTER_ENDPOINT.

   Change the endpoint here and nowhere else. */
var FORM_ENDPOINT = "https://bkgjoztepcdranhbaurx.supabase.co/functions/v1/site-form";
var LETTER_ENDPOINT = "https://bkgjoztepcdranhbaurx.supabase.co/functions/v1/lead-engine-response";

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

  /* ---- 1d. Strategy-call booking (Cal.com, connected to Valentine's Google
     Calendar). The form the visitor has just sent left their name, email and
     phone in sessionStorage, so the calendar opens already filled in and they
     only pick a time. Kept in this tab only, and cleared once read. ---- */
  var calBox = document.getElementById("cal-booking");
  if (calBox) {
    var who = {};
    try {
      who = JSON.parse(sessionStorage.getItem("gvn-booking") || "{}") || {};
      sessionStorage.removeItem("gvn-booking");
    } catch (e) { who = {}; }
    var config = { layout: "month_view", theme: "light" };
    if (who.name) { config.name = who.name; }
    if (who.email) { config.email = who.email; }
    if (who.phone) { config.attendeePhoneNumber = who.phone; }
    (function (C, A, L) {
      var p = function (a, ar) { a.q.push(ar); };
      var d = C.document;
      C.Cal = C.Cal || function () {
        var cal = C.Cal, ar = arguments;
        if (!cal.loaded) {
          cal.ns = {}; cal.q = cal.q || [];
          d.head.appendChild(d.createElement("script")).src = A;
          cal.loaded = true;
        }
        if (ar[0] === L) {
          var api = function () { p(api, arguments); };
          var namespace = ar[1];
          api.q = api.q || [];
          if (typeof namespace === "string") {
            cal.ns[namespace] = cal.ns[namespace] || api;
            p(cal.ns[namespace], ar);
            p(cal, ["initNamespace", namespace]);
          } else { p(cal, ar); }
          return;
        }
        p(cal, ar);
      };
    })(window, "https://app.cal.com/embed/embed.js", "init");
    window.Cal("init", "strategy", { origin: "https://cal.com" });
    window.Cal.ns.strategy("inline", {
      elementOrSelector: "#cal-booking",
      calLink: calBox.getAttribute("data-cal-link"),
      config: config
    });
    // Light, in the site's navy, so the calendar sits on the cream page as part of it.
    window.Cal.ns.strategy("ui", { theme: "light", hideEventTypeDetails: false, layout: "month_view",
      cssVarsPerTheme: { light: { "cal-brand": "#0B1220" } } });
  }

  function rememberForBooking(form) {
    if (!form.querySelector("[data-label='Email']") || !/optinform\/gv2/.test(form.getAttribute("data-redirect") || "")) { return; }
    var val = function (label) {
      var el = form.querySelector("[data-label='" + label + "']");
      return el ? (el.value || "").trim() : "";
    };
    var name = [val("First name"), val("Last name")].filter(Boolean).join(" ") || val("Full name");
    try {
      sessionStorage.setItem("gvn-booking", JSON.stringify({ name: name, email: val("Email"), phone: val("Phone") }));
    } catch (e) { /* private mode: the calendar simply opens empty */ }
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

      uploadPhotos(form, payload.form, status).then(function (photos) {
        if (photos.length) { payload.fields["Attachments Files"] = JSON.stringify(photos); }
        return fetch(FORM_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
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

  /* Photos (sell form): each file goes straight to the private photo store
     through a one-time signed URL from the form endpoint, then the form says
     which files it sent. A photo that fails is skipped, never the enquiry:
     the file names still travel in "File upload" as before. */
  var PHOTO_TYPES = /^image\/(jpeg|png|webp|gif|heic|heif|avif)$/;
  var PHOTO_MAX = 15 * 1024 * 1024;

  function uploadPhotos(form, key, status) {
    var input = form.querySelector("input[type=file]");
    if (!input || !input.files || !input.files.length || !window.fetch) { return Promise.resolve([]); }
    var files = Array.prototype.filter.call(input.files, function (f) {
      return PHOTO_TYPES.test(f.type);
    }).slice(0, parseInt(input.getAttribute("data-max") || "10", 10));
    if (!files.length) { return Promise.resolve([]); }

    return Promise.all(files.map(shrink)).then(function (blobs) {
      blobs = blobs.filter(function (b) { return b.size <= PHOTO_MAX; });
      if (!blobs.length) { return []; }
      return fetch(FORM_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ form: key, upload: blobs.map(function (b) { return { type: b.type, size: b.size }; }) })
      }).then(function (res) {
        if (!res.ok) { throw new Error("HTTP " + res.status); }
        return res.json();
      }).then(function (data) {
        var done = [];
        var n = 0;
        // One at a time: a phone on a weak signal does better with one
        // upload than with ten fighting each other.
        return blobs.reduce(function (chain, b, i) {
          return chain.then(function () {
            show(status, "busy", "Uploading photo " + (i + 1) + " of " + blobs.length + "…");
            var slot = data.uploads[i];
            return fetch(slot.url, { method: "PUT", headers: { "Content-Type": b.type }, body: b })
              .then(function (res) {
                if (res.ok) { n++; done.push({ path: slot.path, name: b.photoName, type: b.type }); }
              }, function () {});
          });
        }, Promise.resolve()).then(function () {
          show(status, "busy", n ? "Sending…" : "Photos could not be uploaded. Sending your details…");
          return done;
        });
      });
    }).catch(function () { return []; });
  }

  /* A phone photo is often 4-8MB. Resized to 2400px on the long side it is a
     fraction of that and still more than enough to judge a property. Any
     file the browser cannot draw (HEIC outside Safari, say) goes as it is. */
  function shrink(file) {
    var keep = function () { file.photoName = file.name; return file; };
    if (file.size < 1500000 || !/^image\/(jpeg|png|webp)$/.test(file.type) || !window.createImageBitmap) {
      return Promise.resolve(keep());
    }
    return createImageBitmap(file).then(function (img) {
      var scale = Math.min(1, 2400 / Math.max(img.width, img.height));
      var c = document.createElement("canvas");
      c.width = Math.round(img.width * scale);
      c.height = Math.round(img.height * scale);
      c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
      return new Promise(function (ok) {
        c.toBlob(function (b) {
          if (!b || b.size >= file.size) { ok(keep()); return; }
          b.photoName = file.name;
          ok(b);
        }, "image/jpeg", 0.85);
      });
    }).catch(keep);
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
    rememberForBooking(form);
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

  /* ---- Your agreement (/agreement/?t=...) ----
     The client's own page for the agreement we emailed: read it, accept it, or
     cancel it. Everything goes through the client-agreement function with the
     link's token; nothing is decided here. Text is set with textContent, never
     innerHTML, because the names come from the database. */
  var agrBox = document.getElementById("agreement");
  if (agrBox) setupAgreement(agrBox);

  function setupAgreement(box) {
    var AGR = "https://bkgjoztepcdranhbaurx.supabase.co/functions/v1/client-agreement";
    var params = new URLSearchParams(location.search);
    var token = params.get("t") || "";
    function h(tag, cls, text) {
      var n = document.createElement(tag);
      if (cls) n.className = cls;
      if (text != null) n.textContent = text;
      return n;
    }
    function clear() { while (box.firstChild) box.removeChild(box.firstChild); }
    function money(n) { return "\u00a3" + Number(n || 0).toLocaleString("en-GB"); }
    function call(action, extra) {
      var body = { action: action, token: token };
      for (var k in extra) body[k] = extra[k];
      return fetch(AGR, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
        .then(function (r) { return r.json().then(function (j) { if (!r.ok && !j.error) j.error = "Something went wrong."; return j; }); })
        .catch(function () { return { error: "We could not reach our server. Please check your connection and try again." }; });
    }
    function fail(msg) {
      clear();
      var c = h("div", "agr-card");
      c.appendChild(h("h2", null, "We could not open this agreement"));
      c.appendChild(h("p", null, msg || "This link is not valid. Please use the link in our most recent email, or contact us."));
      box.appendChild(c);
    }
    function bank(v) {
      var b = h("div", "agr-bank");
      b.appendChild(h("p", "agr-bank-t", "Pay the Reservation Fee of " + money(v.reservation) + " by bank transfer"));
      [["Account name", v.bank.name], ["Sort code", v.bank.sort], ["Account number", v.bank.account], ["Reference", v.bank.reference]]
        .forEach(function (r) {
          var row = h("div", "agr-bank-r");
          row.appendChild(h("span", null, r[0]));
          row.appendChild(h("b", null, r[1]));
          b.appendChild(row);
        });
      b.appendChild(h("p", "agr-note", "Use your first name, or your company name if you are buying through one, as the reference."));
      return b;
    }
    function render(v) {
      clear();
      var c = h("div", "agr-card");
      c.appendChild(h("p", "eyebrow", "Agreement " + v.reference));
      c.appendChild(h("h2", null, v.packageName));
      var facts = h("dl", "agr-facts");
      [["Total fee", money(v.total)], ["Reservation Fee", money(v.reservation)],
       ["Balance", money(v.balance) + ", due " + v.balanceWhen], ["Sent", v.sentOn]].forEach(function (r) {
        facts.appendChild(h("dt", null, r[0])); facts.appendChild(h("dd", null, r[1]));
      });
      c.appendChild(facts);
      if (v.pdf) {
        var a = h("a", "btn btn--ghost", "Download your agreement (PDF)");
        a.href = v.pdf; a.target = "_blank"; a.rel = "noopener";
        c.appendChild(a);
      }
      box.appendChild(c);

      if (v.status === "cancelled") {
        var x = h("div", "agr-card agr-done");
        x.appendChild(h("h2", null, "This agreement was cancelled"));
        x.appendChild(h("p", null, "Cancelled " + v.cancelledAt + ". We have emailed you to confirm it."));
        box.appendChild(x);
        return;
      }

      var act = h("div", "agr-card");
      if (v.acceptedAt) {
        act.appendChild(h("h2", null, "You accepted this agreement"));
        act.appendChild(h("p", null, "Accepted " + v.acceptedAt + ". We have emailed you to confirm it."));
        if (!v.paid) act.appendChild(bank(v));
      } else if (v.canAccept) {
        act.appendChild(h("h2", null, "Accept your agreement"));
        act.appendChild(h("p", null, "Please read the agreement first. No signature is needed: pressing I accept records your acceptance, with the date and time."));
        var lab = h("label", "agr-check");
        var cb = document.createElement("input"); cb.type = "checkbox";
        lab.appendChild(cb);
        lab.appendChild(document.createTextNode(" I have read the agreement and I accept its terms."));
        act.appendChild(lab);
        var go = h("button", "btn btn--gold", "I accept");
        go.type = "button"; go.disabled = true;
        cb.addEventListener("change", function () { go.disabled = !cb.checked; });
        var msg = h("p", "agr-note");
        go.addEventListener("click", function () {
          go.disabled = true; go.textContent = "Recording…";
          call("accept").then(function (r) {
            if (r.ok) { load(); } else { go.disabled = false; go.textContent = "I accept"; msg.textContent = r.error; }
          });
        });
        act.appendChild(go);
        act.appendChild(msg);
        if (!v.paid) {
          act.appendChild(h("p", "agr-note", "Once you have accepted, pay the Reservation Fee by bank transfer. The details will appear here and in our email."));
        }
      } else if (v.paid) {
        act.appendChild(h("h2", null, "Your agreement is in place"));
        act.appendChild(h("p", null, "We have received your Reservation Fee. Your agreement is in force."));
      }
      if (act.childNodes.length) box.appendChild(act);

      if (v.canCancel) {
        var cc = h("div", "agr-cancel");
        var open = h("button", "agr-link", "Cancel this agreement");
        open.type = "button";
        var panel = h("div", "agr-cancel-p");
        panel.hidden = true;
        panel.appendChild(h("p", null, v.cancelUntil
          ? "If you are buying as an individual, you can cancel within 14 days, until " + v.cancelUntil + ". After that, clause 7 of the agreement applies."
          : "If you are buying as an individual, you can cancel within 14 days of our confirmation email."));
        var why = document.createElement("textarea");
        why.rows = 3; why.placeholder = "Your reason (optional)"; why.maxLength = 1000;
        why.setAttribute("aria-label", "Your reason (optional)");
        panel.appendChild(why);
        var yes = h("button", "btn btn--dark", "Confirm cancellation");
        yes.type = "button";
        var cmsg = h("p", "agr-note");
        yes.addEventListener("click", function () {
          yes.disabled = true; yes.textContent = "Cancelling…";
          call("cancel", { reason: why.value.trim() }).then(function (r) {
            if (r.ok) { load(); } else { yes.disabled = false; yes.textContent = "Confirm cancellation"; cmsg.textContent = r.error; }
          });
        });
        panel.appendChild(yes);
        panel.appendChild(cmsg);
        open.addEventListener("click", function () { panel.hidden = !panel.hidden; });
        cc.appendChild(open);
        cc.appendChild(panel);
        box.appendChild(cc);
      }
    }
    function load() {
      call("view").then(function (v) { if (v && v.ok) render(v); else fail(v && v.error); });
    }
    if (!/^[0-9a-f-]{36}$/i.test(token)) { fail(); return; }
    load();
  }

  /* ------------------------------------------------ 3. a reply to a letter
     The QR code opens /letter?c=CODE&s=q; the printed link is /letter, where
     the code is typed. The code is sent once, then taken out of the address
     bar so it isn't bookmarked or shared. "Stop the letters" sends opt_out,
     which puts the address on GVN's do-not-contact list. */
  var letter = document.querySelector("[data-letter]");
  if (letter) {
    var lform = letter.querySelector("[data-letter-form]");
    var lknown = letter.querySelector("[data-letter-known]");
    var lstatus = lform.querySelector(".form-status");
    var kstatus = letter.querySelector("[data-letter-status]");
    var stop = letter.querySelector("[data-letter-stop]");
    var code = "";
    var send = function (c, via) {
      return fetch(LETTER_ENDPOINT, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: c, via: via })
      }).then(function (r) { return r.json(); }).catch(function () { return { ok: false }; });
    };
    var say = function (el, cls, text) { el.className = "form-status " + cls; el.textContent = text; };
    var tryCode = function (c, via) {
      c = String(c || "").toUpperCase().replace(/[^A-Z0-9]/g, "");
      if (c.length !== 6) { lform.hidden = false; say(lstatus, "is-err", "The code is six letters and numbers. Please check it and try again."); return; }
      say(lstatus, "is-busy", "Checking…");
      send(c, via).then(function (r) {
        if (r && r.ok && r.known) {
          code = c; lform.hidden = true; lknown.hidden = false;
          var hd = lknown.querySelector("h2"); if (hd) { hd.setAttribute("tabindex", "-1"); hd.focus(); }
        } else if (r && r.ok) {
          lform.hidden = false;
          say(lstatus, "is-err", "We couldn't find that code. Please check it, or call or email us and we'll help.");
        } else {
          lform.hidden = false;
          say(lstatus, "is-err", "Sorry, something went wrong. Please try again, or call or email us.");
        }
      });
    };
    lform.addEventListener("submit", function (e) { e.preventDefault(); tryCode(lform.code.value, "link"); });
    stop.addEventListener("click", function () {
      stop.disabled = true; say(kstatus, "is-busy", "Saving…");
      send(code, "opt_out").then(function (r) {
        if (r && r.ok && r.known) {
          say(kstatus, "is-ok", "Done. This address is on our do-not-contact list, and you won't receive any more letters from us.");
          stop.textContent = "Letters stopped";
        } else {
          stop.disabled = false;
          say(kstatus, "is-err", "Sorry, that didn't save. Please try again, or call or email us and we'll stop the letters.");
        }
      });
    });
    var q = new URLSearchParams(location.search);
    var given = q.get("c");
    if (given) {
      try { history.replaceState(null, "", location.pathname); } catch (err) { /* keep the address as it is */ }
      tryCode(given, q.get("s") === "q" ? "qr" : "link");
    } else {
      lform.hidden = false;
    }
  }
})();
