(function () {
  "use strict";
  var ROOT = window.CRM_ROOT || "";
  var EMBED = document.body.classList.contains("embed");

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c];
    });
  }
  function num(v) {
    var n = parseFloat(String(v || "").replace(/\s/g, "").replace(",", "."));
    return isNaN(n) ? 0 : n;
  }
  function money(n) {
    var r = Math.round(n * 100) / 100;
    var s = (r % 1 === 0 ? r.toFixed(0) : r.toFixed(2));
    return s.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  }
  function withEmbed(url) {
    return url + (url.indexOf("?") >= 0 ? "&" : "?") + "embed=1";
  }

  // ---------------------------------------------------------- спливні повідомлення
  var toasts = document.getElementById("toasts");
  if (toasts) {
    toasts.querySelectorAll(".flash").forEach(function (t) {
      var ms = t.dataset.kind === "error" ? 9000 : 3500;
      setTimeout(function () { t.style.transition = "opacity .3s"; t.style.opacity = "0"; setTimeout(function () { t.remove(); }, 300); }, ms);
      t.addEventListener("click", function () { t.remove(); });
    });
  }

  // ---------------------------------------------------------- картка замовлення поверх списку
  var modal = null;
  function openModal(url) {
    closeModal(false);
    modal = document.createElement("div");
    modal.className = "modal";
    modal.innerHTML = '<div class="modal-box"><button class="modal-close" title="Закрити (Esc)"><svg class="i"><use href="#x"/></svg></button>' +
      '<iframe src="' + esc(withEmbed(url)) + '"></iframe></div>';
    document.body.appendChild(modal);
    document.body.style.overflow = "hidden";
    var frame = modal.querySelector("iframe"), loads = 0;
    frame.addEventListener("load", function () {
      loads++;
      modal.dataset.changed = loads > 1 ? "1" : "";
      try { frame.contentWindow.addEventListener("keydown", onKey); } catch (e) { /* інший домен */ }
    });
    modal.addEventListener("click", function (e) {
      if (e.target === modal || e.target.closest(".modal-close")) closeModal(true);
    });
  }
  function closeModal(reload) {
    if (!modal) return;
    var changed = modal.dataset.changed === "1";
    try {
      var w = modal.querySelector("iframe").contentWindow;
      if (w.OrderForm && w.OrderForm.dirty && !confirm("Є незбережені зміни. Закрити без збереження?")) return;
    } catch (e) { /* ignore */ }
    modal.remove();
    modal = null;
    document.body.style.overflow = "";
    if (reload && changed) window.location.reload();
  }
  function onKey(e) { if (e.key === "Escape" && modal) closeModal(true); }
  document.addEventListener("keydown", onKey);
  window.CRM = {openModal: openModal, closeModal: closeModal};

  document.addEventListener("click", function (e) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button === 1) return;
    var a = e.target.closest("a[data-modal]");
    if (a && !EMBED) { e.preventDefault(); openModal(a.getAttribute("href")); return; }
    var tr = e.target.closest("tr[data-href]");
    if (!tr || e.target.closest("a, input, button, select, label, textarea")) return;
    if (tr.hasAttribute("data-modal") && !EMBED) openModal(tr.dataset.href);
    else window.location = tr.dataset.href;
  });
  // посилання на замовлення в списку теж відкривають картку поверх
  document.addEventListener("click", function (e) {
    var a = e.target.closest("tr[data-modal] a[href]");
    if (!a || EMBED || e.metaKey || e.ctrlKey) return;
    e.preventDefault();
    openModal(a.getAttribute("href"));
  }, true);

  // Підтвердження небезпечних дій
  document.addEventListener("submit", function (e) {
    var f = e.target;
    if (f.dataset.confirm && !window.confirm(f.dataset.confirm)) e.preventDefault();
  });

  // ---------------------------------------------------------- масовий вибір у таблицях
  function updateBulk() {
    var form = document.getElementById("bulkform");
    if (!form) return;
    var boxes = form.querySelectorAll("input[name=ids]");
    var n = 0;
    boxes.forEach(function (c) { c.closest("tr").classList.toggle("sel-on", c.checked); if (c.checked) n++; });
    document.getElementById("bulkcount").textContent = n;
    document.getElementById("bulkbar").classList.toggle("on", n > 0);
  }
  document.addEventListener("change", function (e) {
    if (e.target.matches("[data-check-all]")) {
      e.target.closest("table").querySelectorAll("input[name=ids]").forEach(function (c) { c.checked = e.target.checked; });
    }
    if (e.target.matches("input[name=ids], [data-check-all]")) updateBulk();
  });

  // ---------------------------------------------------------- автодоповнення (міста й відділення НП)
  function initAutocomplete(root) {
    var input = root.querySelector("[data-ac-input]");
    var ref = root.querySelector("[data-ac-ref]");
    var list = root.querySelector(".ac-list");
    var url = root.dataset.ac;
    var min = parseInt(root.dataset.acMin || "2", 10);
    var timer = null, items = [], hl = -1, seq = 0;

    function close() { list.classList.remove("on"); hl = -1; }
    function show(html) { list.innerHTML = html; list.classList.add("on"); }

    function search() {
      var q = input.value.trim();
      var params = new URLSearchParams({q: q});
      if (root.dataset.acDepends) {
        var dep = document.getElementById(root.dataset.acDepends);
        if (!dep || !dep.value) { show('<div class="note">Спочатку оберіть місто зі списку</div>'); return; }
        params.set("city_ref", dep.value);
      }
      if (q.length < min) { close(); return; }
      var my = ++seq;
      show('<div class="note">Пошук…</div>');
      fetch(url + "?" + params.toString(), {credentials: "same-origin"})
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (my !== seq) return;
          if (!data.ok) { show('<div class="note">' + esc(data.error || "Помилка") + "</div>"); return; }
          items = data.items || [];
          if (!items.length) { show('<div class="note">Нічого не знайдено</div>'); return; }
          show(items.map(function (it, i) { return '<div data-i="' + i + '">' + esc(it.label || it.name) + "</div>"; }).join(""));
        })
        .catch(function () { show('<div class="note">Помилка з\'єднання</div>'); });
    }
    function pick(i) {
      var it = items[i];
      if (!it) return;
      input.value = it.name;
      ref.value = it.ref;
      input.classList.add("ok");
      close();
      ref.dispatchEvent(new Event("change", {bubbles: true}));
    }
    input.addEventListener("input", function () {
      ref.value = "";
      input.classList.remove("ok");
      ref.dispatchEvent(new Event("change", {bubbles: true}));
      clearTimeout(timer);
      timer = setTimeout(search, 280);
    });
    input.addEventListener("focus", function () { if (!ref.value && min === 0) search(); });
    input.addEventListener("keydown", function (e) {
      var opts = list.querySelectorAll("[data-i]");
      if (!list.classList.contains("on") || !opts.length) return;
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        hl = (hl + (e.key === "ArrowDown" ? 1 : -1) + opts.length) % opts.length;
        opts.forEach(function (o, i) { o.classList.toggle("hl", i === hl); });
        opts[hl].scrollIntoView({block: "nearest"});
      } else if (e.key === "Enter") {
        e.preventDefault();
        pick(hl >= 0 ? hl : 0);
      } else if (e.key === "Escape") { e.stopPropagation(); close(); }
    });
    list.addEventListener("mousedown", function (e) {
      var d = e.target.closest("[data-i]");
      if (d) { e.preventDefault(); pick(parseInt(d.dataset.i, 10)); }
    });
    input.addEventListener("blur", function () { setTimeout(close, 150); });
  }
  document.querySelectorAll("[data-ac]").forEach(initAutocomplete);

  var cityRef = document.getElementById("cityRef");
  if (cityRef) {
    cityRef.addEventListener("change", function () {
      var wh = document.querySelector('[data-ac-depends="cityRef"]');
      if (!wh || cityRef.value === "") return;
      wh.querySelector("[data-ac-ref]").value = "";
      var inp = wh.querySelector("[data-ac-input]");
      inp.value = "";
      inp.classList.remove("ok");
    });
  }

  // ---------------------------------------------------------- вкладки картки
  document.querySelectorAll("#tabs [data-tab]").forEach(function (t) {
    t.addEventListener("click", function () {
      document.querySelectorAll("#tabs [data-tab]").forEach(function (x) { x.classList.toggle("on", x === t); });
      document.querySelectorAll("#tabs [data-pane]").forEach(function (p) { p.classList.toggle("on", p.dataset.pane === t.dataset.tab); });
      try { sessionStorage.setItem("crm-tab", t.dataset.tab); } catch (e) { /* ignore */ }
    });
  });
  try {
    var savedTab = (location.hash || "").replace("#", "") || sessionStorage.getItem("crm-tab");
    var tabEl = savedTab && document.querySelector('#tabs [data-tab="' + savedTab + '"]');
    if (tabEl) tabEl.click();
  } catch (e) { /* ignore */ }

  // ---------------------------------------------------------- форма замовлення
  window.OrderForm = {
    dirty: false,
    init: function (cfg) {
      var self = this;
      var form = document.getElementById("orderform");
      var tbody = document.querySelector("#items tbody");
      if (!tbody || !form) return;
      var products = {};
      (cfg.products || []).forEach(function (p) { products[p.id] = p; });
      var empty = document.getElementById("itemsEmpty");

      function markDirty() {
        self.dirty = true;
        var h = document.getElementById("dirtyHint");
        if (h) h.hidden = false;
      }

      function addRow(it, focusName) {
        var p = it.product_id ? products[it.product_id] : null;
        var tr = document.createElement("tr");
        var meta = p ? '<span class="meta-line">' + (p.sku ? esc(p.sku) + " · " : "") + "залишок " + p.available + "</span>" : "";
        tr.innerHTML =
          '<td><input type="hidden" name="item_product_id" value="' + esc(it.product_id || "") + '">' +
          '<input name="item_name" value="' + esc(it.name) + '" required placeholder="Назва позиції">' + meta + "</td>" +
          '<td class="qty num"><input name="item_qty" type="number" min="1" step="1" value="' + esc(it.qty || 1) + '"></td>' +
          '<td class="price num"><input name="item_price" inputmode="decimal" value="' + esc(it.price) + '"></td>' +
          '<td><input type="hidden" name="item_upsell" value="' + (it.upsell ? "1" : "0") + '"><input type="checkbox" class="up" ' + (it.upsell ? "checked" : "") + ' title="Допродаж"></td>' +
          '<td class="num sum"></td>' +
          '<td><button type="button" class="x" title="Прибрати">×</button></td>';
        tbody.appendChild(tr);
        recalc();
        if (focusName) tr.querySelector("[name=item_name]").focus();
      }

      function recalc() {
        var subtotal = 0;
        tbody.querySelectorAll("tr").forEach(function (tr) {
          var s = num(tr.querySelector("[name=item_qty]").value) * num(tr.querySelector("[name=item_price]").value);
          tr.querySelector(".sum").textContent = money(s);
          subtotal += s;
        });
        empty.style.display = tbody.children.length ? "none" : "";
        var disc = num(document.getElementById("discount").value);
        var total = Math.max(subtotal - disc, 0);
        var ptype = document.getElementById("paymentType").value;
        var prepay = num(document.getElementById("prepayment").value);
        var cod = ptype === "prepaid" ? 0 : Math.max(total - prepay, 0);
        document.getElementById("tSubtotal").textContent = money(subtotal);
        document.getElementById("tDiscount").textContent = disc ? "−" + money(disc) : "0";
        document.getElementById("tTotal").textContent = money(total) + " ₴";
        document.getElementById("tPrepay").textContent = money(prepay);
        document.getElementById("tCod").innerHTML = "<strong>" + money(cod) + " ₴</strong>";
      }

      (cfg.items || []).forEach(function (it) { addRow(it); });
      recalc();

      // Пошук товару для додавання
      var gs = document.getElementById("goodsSearch"), gl = document.getElementById("goodsList"), ghl = 0, gitems = [];
      function goodsRender() {
        var q = gs.value.trim().toLowerCase();
        gitems = (cfg.products || []).filter(function (p) {
          return !q || p.name.toLowerCase().indexOf(q) >= 0 || (p.sku || "").toLowerCase().indexOf(q) >= 0;
        }).slice(0, 30);
        var html = gitems.map(function (p, i) {
          return '<div data-g="' + i + '" class="' + (i === ghl ? "hl" : "") + '"><span>' + esc(p.name) + (p.upsell ? ' <span class="badge info">апсел</span>' : "") +
            '</span><small>' + money(num(p.price)) + " ₴ · " + p.available + " шт</small></div>";
        }).join("");
        var custom = gs.value.trim() ? "Довільна позиція «" + esc(gs.value.trim()) + "»" : "Довільна позиція (без товару зі складу)";
        html += '<div data-g="custom" class="' + (ghl === gitems.length ? "hl" : "") + '"><span>' + custom + "</span><small>Enter</small></div>";
        gl.innerHTML = html;
        gl.classList.add("on");
      }
      function goodsPick(key) {
        if (key === "custom") {
          addRow({name: gs.value.trim(), qty: 1, price: ""}, !gs.value.trim());
        } else {
          var p = gitems[key];
          if (!p) return;
          addRow({product_id: p.id, name: p.name, qty: 1, price: p.price, upsell: p.upsell});
        }
        markDirty();
        gs.value = "";
        ghl = 0;
        gl.classList.remove("on");
      }
      gs.addEventListener("focus", function () { ghl = 0; goodsRender(); });
      gs.addEventListener("input", function () { ghl = 0; goodsRender(); });
      gs.addEventListener("blur", function () { setTimeout(function () { gl.classList.remove("on"); }, 150); });
      gs.addEventListener("keydown", function (e) {
        var total = gitems.length + 1;
        if (e.key === "ArrowDown" || e.key === "ArrowUp") {
          e.preventDefault();
          ghl = (ghl + (e.key === "ArrowDown" ? 1 : -1) + total) % total;
          goodsRender();
          var h = gl.querySelector(".hl"); if (h) h.scrollIntoView({block: "nearest"});
        } else if (e.key === "Enter") {
          e.preventDefault();
          goodsPick(ghl < gitems.length ? ghl : "custom");
        } else if (e.key === "Escape") { e.stopPropagation(); gl.classList.remove("on"); gs.blur(); }
      });
      gl.addEventListener("mousedown", function (e) {
        var d = e.target.closest("[data-g]");
        if (d) { e.preventDefault(); goodsPick(d.dataset.g === "custom" ? "custom" : parseInt(d.dataset.g, 10)); }
      });

      tbody.addEventListener("click", function (e) {
        if (e.target.classList.contains("x")) { e.target.closest("tr").remove(); recalc(); markDirty(); }
      });
      tbody.addEventListener("change", function (e) {
        if (e.target.classList.contains("up")) e.target.previousElementSibling.value = e.target.checked ? "1" : "0";
      });
      tbody.addEventListener("input", recalc);
      ["discount", "prepayment", "paymentType"].forEach(function (id) {
        document.getElementById(id).addEventListener("input", recalc);
        document.getElementById(id).addEventListener("change", recalc);
      });
      form.addEventListener("input", markDirty);
      form.addEventListener("change", markDirty);
      form.addEventListener("submit", function () { self.dirty = false; });

      // Колір статусу
      var ss = document.getElementById("statusSelect");
      if (ss) ss.addEventListener("change", function () {
        ss.style.setProperty("--c", ss.selectedOptions[0].dataset.color || "#8f8e8a");
      });

      // «Створити ТТН» спершу зберігає незбережені зміни
      var fttn = document.getElementById("f-ttn");
      if (fttn) fttn.addEventListener("submit", function (e) {
        if (!self.dirty) return;
        e.preventDefault();
        var h = document.createElement("input");
        h.type = "hidden"; h.name = "then"; h.value = "ttn";
        form.appendChild(h);
        self.dirty = false;
        form.requestSubmit ? form.requestSubmit() : form.submit();
      });

      window.addEventListener("beforeunload", function (e) {
        if (self.dirty) { e.preventDefault(); e.returnValue = ""; }
      });

      // Ctrl+S / Cmd+S — зберегти
      document.addEventListener("keydown", function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
          e.preventDefault();
          self.dirty = false;
          form.requestSubmit ? form.requestSubmit() : form.submit();
        }
      });

      // Поля доставки залежно від способу; поля прихованих блоків вимикаються, щоб не потрапити у форму
      var method = document.getElementById("deliveryMethod");
      var blocks = form.querySelectorAll("[data-method]");
      function applyMethod() {
        blocks.forEach(function (b) {
          var on = b.dataset.method.split(" ").indexOf(method.value) >= 0;
          b.style.display = on ? "" : "none";
          b.querySelectorAll("input, select, textarea").forEach(function (i) { i.disabled = !on; });
        });
      }
      method.addEventListener("change", applyMethod);
      applyMethod();
    }
  };
})();
