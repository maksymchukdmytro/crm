(function () {
  "use strict";

  // Клік по рядку таблиці відкриває запис
  document.addEventListener("click", function (e) {
    var tr = e.target.closest("tr[data-href]");
    if (!tr) return;
    if (e.target.closest("a, input, button, select, label, textarea")) return;
    if (e.metaKey || e.ctrlKey) { window.open(tr.dataset.href, "_blank"); return; }
    window.location = tr.dataset.href;
  });

  // Підтвердження небезпечних дій
  document.addEventListener("submit", function (e) {
    var f = e.target;
    if (f.dataset.confirm && !window.confirm(f.dataset.confirm)) e.preventDefault();
  });

  // Масовий вибір у таблицях
  function updateBulk() {
    var form = document.getElementById("bulkform");
    if (!form) return;
    var n = form.querySelectorAll("input[name=ids]:checked").length;
    var bar = document.getElementById("bulkbar");
    document.getElementById("bulkcount").textContent = n;
    bar.classList.toggle("on", n > 0);
  }
  document.addEventListener("change", function (e) {
    if (e.target.matches("[data-check-all]")) {
      var table = e.target.closest("table");
      table.querySelectorAll("input[name=ids]").forEach(function (c) { c.checked = e.target.checked; });
    }
    if (e.target.matches("input[name=ids], [data-check-all]")) updateBulk();
  });

  // Автодоповнення (міста і відділення Нової Пошти)
  function initAutocomplete(root) {
    var input = root.querySelector("[data-ac-input]");
    var ref = root.querySelector("[data-ac-ref]");
    var list = root.querySelector(".ac-list");
    var url = root.dataset.ac;
    var min = parseInt(root.dataset.acMin || "2", 10);
    var timer = null, items = [], hl = -1, seq = 0;

    function close() { list.classList.remove("on"); hl = -1; }
    function show(html) { list.innerHTML = html; list.classList.add("on"); }
    function esc(s) { return String(s || "").replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }

    function search() {
      var q = input.value.trim();
      var params = new URLSearchParams({q: q});
      if (root.dataset.acDepends) {
        var dep = document.getElementById(root.dataset.acDepends);
        if (!dep || !dep.value) { show('<div class="note">Спочатку оберіть місто</div>'); return; }
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
      } else if (e.key === "Escape") { close(); }
    });
    list.addEventListener("mousedown", function (e) {
      var d = e.target.closest("[data-i]");
      if (d) { e.preventDefault(); pick(parseInt(d.dataset.i, 10)); }
    });
    input.addEventListener("blur", function () { setTimeout(close, 150); });
  }
  document.querySelectorAll("[data-ac]").forEach(initAutocomplete);

  // Коли змінюється місто — скидаємо відділення
  var cityRef = document.getElementById("cityRef");
  if (cityRef) {
    cityRef.addEventListener("change", function () {
      var wh = document.querySelector('[data-ac-depends="cityRef"]');
      if (!wh) return;
      wh.querySelector("[data-ac-ref]").value = "";
      var inp = wh.querySelector("[data-ac-input]");
      if (cityRef.value === "") return;
      inp.value = "";
      inp.classList.remove("ok");
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

  // Форма замовлення: товари, підсумки, способи доставки
  window.OrderForm = {
    init: function (cfg) {
      var tbody = document.querySelector("#items tbody");
      if (!tbody) return;
      var products = {};
      (cfg.products || []).forEach(function (p) { products[p.id] = p; });
      var empty = document.getElementById("itemsEmpty");

      function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }

      function addRow(it) {
        var p = it.product_id ? products[it.product_id] : null;
        var tr = document.createElement("tr");
        var stock = p ? '<span class="sub">' + (p.sku ? esc(p.sku) + " · " : "") + "залишок " + p.available + "</span>" : "";
        tr.innerHTML =
          '<td><input type="hidden" name="item_product_id" value="' + esc(it.product_id || "") + '">' +
          '<input name="item_name" value="' + esc(it.name) + '" required>' + stock + "</td>" +
          '<td class="qty num"><input name="item_qty" type="number" min="1" step="1" value="' + esc(it.qty || 1) + '"></td>' +
          '<td class="price num"><input name="item_price" inputmode="decimal" value="' + esc(it.price) + '"></td>' +
          '<td><input type="hidden" name="item_upsell" value="' + (it.upsell ? "1" : "0") + '"><input type="checkbox" class="up" ' + (it.upsell ? "checked" : "") + "></td>" +
          '<td class="num sum"></td>' +
          '<td><button type="button" class="x" title="Видалити">×</button></td>';
        tbody.appendChild(tr);
        recalc();
      }

      function recalc() {
        var subtotal = 0;
        tbody.querySelectorAll("tr").forEach(function (tr) {
          var q = num(tr.querySelector("[name=item_qty]").value);
          var pr = num(tr.querySelector("[name=item_price]").value);
          tr.querySelector(".sum").textContent = money(q * pr);
          subtotal += q * pr;
        });
        empty.style.display = tbody.children.length ? "none" : "";
        var disc = num(document.getElementById("discount").value);
        var total = Math.max(subtotal - disc, 0);
        var ptype = document.getElementById("paymentType").value;
        var prepay = num(document.getElementById("prepayment").value);
        var cod = ptype === "prepaid" ? 0 : Math.max(total - prepay, 0);
        document.getElementById("tSubtotal").textContent = money(subtotal);
        document.getElementById("tDiscount").textContent = disc ? "−" + money(disc) : "0";
        document.getElementById("tTotal").textContent = money(total);
        document.getElementById("tPrepay").textContent = money(prepay);
        document.getElementById("tCod").innerHTML = "<strong>" + money(cod) + "</strong>";
      }

      (cfg.items || []).forEach(addRow);
      recalc();

      document.getElementById("addProduct").addEventListener("change", function (e) {
        var p = products[e.target.value];
        if (p) addRow({product_id: p.id, name: p.name, qty: 1, price: p.price, upsell: p.upsell});
        e.target.value = "";
      });
      document.getElementById("addCustom").addEventListener("click", function () {
        addRow({name: "", qty: 1, price: ""});
        var last = tbody.querySelector("tr:last-child [name=item_name]");
        if (last) last.focus();
      });
      tbody.addEventListener("click", function (e) {
        if (e.target.classList.contains("x")) { e.target.closest("tr").remove(); recalc(); }
      });
      tbody.addEventListener("change", function (e) {
        if (e.target.classList.contains("up")) {
          e.target.previousElementSibling.value = e.target.checked ? "1" : "0";
        }
      });
      tbody.addEventListener("input", recalc);
      ["discount", "prepayment", "paymentType"].forEach(function (id) {
        document.getElementById(id).addEventListener("input", recalc);
        document.getElementById(id).addEventListener("change", recalc);
      });

      // Показ полів доставки залежно від способу. Поля прихованих блоків
      // вимикаються, щоб не потрапити у форму.
      var method = document.getElementById("deliveryMethod");
      var blocks = document.querySelectorAll("#orderform [data-method]");
      function syncMirrors(from) {
        if (!from) return;
        from.querySelectorAll("input[name]").forEach(function (src) {
          document.querySelectorAll('#orderform input[name="' + src.name + '"]').forEach(function (dst) {
            if (dst !== src && dst.type === src.type && !src.disabled) {
              if (src.name === "city_ref" || src.name === "warehouse_ref") return;
              if (dst.closest("[data-method]") === from) return;
              if (!dst.value) dst.value = src.value;
            }
          });
        });
      }
      var current = null;
      function applyMethod() {
        var prev = current;
        blocks.forEach(function (b) {
          var on = b.dataset.method.split(" ").indexOf(method.value) >= 0;
          b.style.display = on ? "" : "none";
          b.querySelectorAll("input, select, textarea").forEach(function (i) { i.disabled = !on; });
          if (on && b.dataset.method.indexOf(" ") < 0) current = b;
        });
        if (prev && prev !== current) syncMirrors(prev);
      }
      method.addEventListener("change", applyMethod);
      applyMethod();
    }
  };
})();
