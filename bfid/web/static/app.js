"use strict";

// Onglets
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById(tab.dataset.tab).classList.add("active");
  });
});

function formToObject(form) {
  const o = {};
  new FormData(form).forEach((v, k) => (o[k] = v));
  return o;
}

function setStatus(el, msg, isError) {
  el.textContent = msg;
  el.classList.toggle("error", !!isError);
}

function pct(x) { return (x * 100).toFixed(1) + " %"; }

// --- Dashboard ---
document.getElementById("demo-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = document.getElementById("demo-status");
  const result = document.getElementById("demo-result");
  setStatus(status, "Génération + entraînement en cours…");
  result.innerHTML = "";
  try {
    const r = await fetch("/api/demo", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formToObject(e.target)),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "Erreur serveur");
    setStatus(status, `Mode : ${d.mode} · ${d.n_classes} classes`);
    result.innerHTML = `
      <div class="card">
        <div class="metric">${pct(d.accuracy)}
          <small>accuracy (hasard ${pct(d.chance)})</small></div>
        <p>Validation croisée groupée par trace — pas de fuite entre train/test.</p>
      </div>
      <img src="${d.confusion_png}" alt="matrice de confusion">
      <img src="${d.folds_png}" alt="accuracy par fold">`;
  } catch (err) {
    setStatus(status, err.message, true);
  }
});

// --- Signatures ---
document.getElementById("sig-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = document.getElementById("sig-status");
  const result = document.getElementById("sig-result");
  setStatus(status, "Génération de la signature…");
  result.innerHTML = "";
  try {
    const r = await fetch("/api/signature", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formToObject(e.target)),
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "Erreur serveur");
    setStatus(status, `Classe : ${d.label}`);
    result.innerHTML = `
      <img src="${d.signature_png}" alt="signature">
      <img src="${d.timeseries_png}" alt="séries temporelles">`;
  } catch (err) {
    setStatus(status, err.message, true);
  }
});

// --- Pcap ---
document.getElementById("pcap-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const status = document.getElementById("pcap-status");
  const result = document.getElementById("pcap-result");
  setStatus(status, "Analyse de la capture…");
  result.innerHTML = "";
  try {
    const r = await fetch("/api/pcap", { method: "POST", body: new FormData(e.target) });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "Erreur serveur");
    let html = `<div class="card">
        <div class="metric">${d.n_reports}<small> rapports BFI</small></div>
        <pre>sources: ${JSON.stringify(d.sources, null, 2)}
largeurs: ${JSON.stringify(d.widths, null, 2)}</pre>
      </div>`;
    if (d.signature_png) html += `<img src="${d.signature_png}" alt="signature">`;
    if (d.timeseries_png) html += `<img src="${d.timeseries_png}" alt="séries">`;
    if (d.eval) {
      html += `<div class="card">
        <div class="metric">${pct(d.eval.accuracy)}
          <small>accuracy étiquetée (hasard ${pct(d.eval.chance)})</small></div>
        </div>
        <img src="${d.eval.confusion_png}" alt="confusion">`;
    } else if (d.eval_note) {
      html += `<div class="card">${d.eval_note}</div>`;
    }
    result.innerHTML = html;
    setStatus(status, "Terminé.");
  } catch (err) {
    setStatus(status, err.message, true);
  }
});
