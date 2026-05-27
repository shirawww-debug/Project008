"""Application Flask : dashboard de test, visu des signatures, analyse pcap.

Outil LOCAL. Aucune authentification : à lancer sur 127.0.0.1 uniquement, sur
sa propre machine. Voir docs/ETHICS.md.
"""

from __future__ import annotations

import os
import tempfile

from flask import Flask, jsonify, render_template, request
from werkzeug.utils import secure_filename

from .. import synthetic, train
from ..dataset import BfiSample
from . import viz

MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 Mo
_ALLOWED_PCAP = {".pcap", ".pcapng", ".cap"}


def _clamp(value, lo, hi, default, cast=int):
    try:
        return min(max(cast(value), lo), hi)
    except (TypeError, ValueError):
        return default


def _demo_params(data: dict) -> dict:
    return dict(
        n_persons=_clamp(data.get("persons"), 2, 12, 5),
        traces_per_person=_clamp(data.get("traces"), 2, 30, 8),
        n_frames=_clamp(data.get("frames"), 20, 2000, 200),
        window=_clamp(data.get("window"), 4, 256, 32),
        stride=_clamp(data.get("stride"), 1, 128, 8),
        seed=_clamp(data.get("seed"), 0, 10**6, 0),
        label_prefix="zone" if data.get("mode") == "zones" else "person",
    )


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/demo")
    def api_demo():
        params = _demo_params(request.get_json(silent=True) or {})
        prefix = params["label_prefix"]
        result = train.run_demo(**params)
        labels = [f"{prefix}_{i}" for i in range(result.n_classes)]
        return jsonify(
            mode=prefix,
            accuracy=result.accuracy,
            chance=1.0 / result.n_classes,
            n_classes=result.n_classes,
            per_fold=result.per_fold,
            confusion_png=viz.confusion_figure(result.confusion, labels),
            folds_png=viz.folds_figure(
                result.per_fold, result.accuracy, 1.0 / result.n_classes),
        )

    @app.post("/api/signature")
    def api_signature():
        data = request.get_json(silent=True) or {}
        prefix = "zone" if data.get("mode") == "zones" else "person"
        n_classes = _clamp(data.get("persons"), 2, 12, 5)
        idx = _clamp(data.get("index"), 0, n_classes - 1, 0)
        frames = _clamp(data.get("frames"), 20, 2000, 200)
        seed = _clamp(data.get("seed"), 0, 10**6, 0)
        sample = synthetic.generate_sample(
            label=idx, person=f"{prefix}_{idx}", n_frames=frames, seed=seed)
        return jsonify(
            label=sample.person,
            signature_png=viz.signature_figure(sample),
            timeseries_png=viz.angle_timeseries_figure(sample),
        )

    @app.post("/api/pcap")
    def api_pcap():
        if "pcap" not in request.files:
            return jsonify(error="Aucun fichier 'pcap' envoyé."), 400
        f = request.files["pcap"]
        name = secure_filename(f.filename or "")
        if os.path.splitext(name)[1].lower() not in _ALLOWED_PCAP:
            return jsonify(error="Extension attendue : .pcap/.pcapng/.cap"), 400

        tmp = tempfile.NamedTemporaryFile(suffix=".pcap", delete=False)
        try:
            f.save(tmp.name)
            tmp.close()
            return _analyze_pcap(tmp.name, request.files.get("journal"))
        except ImportError as exc:
            return jsonify(error=str(exc)), 400
        except Exception as exc:  # noqa: BLE001 - renvoie l'erreur au front
            return jsonify(error=f"Échec du parsing : {exc}"), 400
        finally:
            os.unlink(tmp.name)

    return app


def _analyze_pcap(pcap_path: str, journal_file):
    """Parse un pcap ; si un journal CSV est fourni, étiquette et évalue."""
    from ..pcap import iter_reports  # import paresseux (scapy)

    reports = list(iter_reports(pcap_path))  # [(ts, src, report)]
    if not reports:
        return jsonify(error="Aucune trame BFI VHT trouvée dans la capture."), 400

    widths: dict[int, int] = {}
    sources: dict[str, int] = {}
    for _ts, src, rep in reports:
        widths[rep.mimo.width_mhz] = widths.get(rep.mimo.width_mhz, 0) + 1
        sources[src] = sources.get(src, 0) + 1

    payload = dict(
        n_reports=len(reports),
        sources=sources,
        widths={f"{w} MHz": c for w, c in sorted(widths.items())},
    )

    # Visualisation de la source la plus active.
    import numpy as np
    top_src = max(sources, key=sources.get)
    reps = [rep for _ts, src, rep in reports if src == top_src]
    sample = BfiSample(
        phi=np.stack([r.phi for r in reps]),
        psi=np.stack([r.psi for r in reps]),
        label=0, person=top_src or "source",
    )
    payload["signature_png"] = viz.signature_figure(sample)
    payload["timeseries_png"] = viz.angle_timeseries_figure(sample)

    # Branchement réel : si un journal est fourni, on étiquette et on évalue.
    if journal_file and journal_file.filename:
        from ..labeling import assign_labels, read_journal
        jtmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        try:
            journal_file.save(jtmp.name)
            jtmp.close()
            journal = read_journal(jtmp.name)
            samples = assign_labels([(ts, rep) for ts, _s, rep in reports], journal)
            if len({s.label for s in samples}) >= 2:
                result = train.evaluate_samples(samples)
                labels = sorted({s.person for s in samples})
                payload["eval"] = dict(
                    accuracy=result.accuracy,
                    chance=1.0 / result.n_classes,
                    per_fold=result.per_fold,
                    confusion_png=viz.confusion_figure(result.confusion, labels),
                )
            else:
                payload["eval_note"] = (
                    "Journal fourni mais < 2 classes étiquetées : "
                    "évaluation impossible.")
        finally:
            os.unlink(jtmp.name)

    return jsonify(payload)


app = create_app()
