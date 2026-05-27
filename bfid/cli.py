"""Interface en ligne de commande : python -m bfid <sous-commande>."""

from __future__ import annotations

import argparse

import numpy as np

from . import spec, synthetic, train
from .dataset import load_samples, save_samples

_ETHICS = (
    "⚠️  Capture passive autorisée UNIQUEMENT sur VOTRE réseau, avec le "
    "consentement explicite des personnes présentes. Voir docs/ETHICS.md."
)


def _cmd_info(_: argparse.Namespace) -> int:
    print("BFI / 802.11ac VHT Compressed Beamforming — aide-mémoire\n")
    print("Sous-porteuses Ns par (largeur, Ng) :")
    for (w, ng), ns in sorted(spec.NS_TABLE.items()):
        print(f"  {w:>3} MHz, Ng={ng} -> {ns} sous-porteuses")
    print("\nBits par angle (b_psi, b_phi) :")
    for (ft, cb), (bp, bf) in spec.BIT_TABLE.items():
        print(f"  {ft}, codebook={cb} -> psi={bp} bits, phi={bf} bits")
    print("\nCapture (exemple canal 36, 80 MHz) :")
    print("  sudo airmon-ng start wlan0")
    print("  sudo iw dev wlan0mon set channel 36 80MHz")
    print("  # filtre Wireshark/tshark : wlan.fc.type_subtype == 0x000e")
    print("  scripts/setup_monitor.sh wlan0 36 80MHz")
    print("  scripts/capture_bfi.sh wlan0mon capture.pcap 300\n")
    print(_ETHICS)
    return 0


def _cmd_synth(args: argparse.Namespace) -> int:
    samples = synthetic.generate_dataset(
        n_persons=args.persons,
        traces_per_person=args.traces,
        n_frames=args.frames,
        roundtrip=not args.no_roundtrip,
        seed=args.seed,
        label_prefix=args.mode,
    )
    save_samples(args.out, samples)
    total = sum(s.n_frames for s in samples)
    print(f"{len(samples)} traces ({args.persons} {args.mode}, {total} trames) "
          f"écrites dans {args.out}")
    return 0


def _cmd_demo(args: argparse.Namespace) -> int:
    print(f"Démo bout-en-bout : {args.persons} {args.mode} (données synthétiques)\n")
    result = train.run_demo(
        n_persons=args.persons,
        traces_per_person=args.traces,
        n_frames=args.frames,
        window=args.window,
        stride=args.stride,
        seed=args.seed,
        label_prefix=args.mode,
    )
    print(result)
    print("\nMatrice de confusion (sommée sur les folds) :")
    print(result.confusion)
    return 0


def _cmd_label(args: argparse.Namespace) -> int:
    from .labeling import label_from_journal  # import paresseux (scapy)

    samples = label_from_journal(args.pcap, args.journal, has_fcs=not args.no_fcs)
    save_samples(args.out, samples)
    classes = sorted({s.person for s in samples})
    print(f"{len(samples)} traces étiquetées ({len(classes)} classes : "
          f"{', '.join(classes)}) écrites dans {args.out}")
    return 0


def _cmd_web(args: argparse.Namespace) -> int:
    from .web import create_app

    print(f"Interface web : http://{args.host}:{args.port}  (Ctrl+C pour arrêter)")
    print(_ETHICS)
    create_app().run(host=args.host, port=args.port, debug=args.debug)
    return 0


def _cmd_train(args: argparse.Namespace) -> int:
    samples = load_samples(args.data)
    print(f"{len(samples)} traces chargées depuis {args.data}")
    result = train.evaluate_samples(
        samples, window=args.window, stride=args.stride, seed=args.seed)
    print(result)
    print("\nMatrice de confusion :")
    print(result.confusion)
    return 0


def _cmd_parse(args: argparse.Namespace) -> int:
    from .pcap import iter_reports  # import paresseux (scapy)

    n = 0
    widths: dict[int, int] = {}
    srcs: set[str] = set()
    for _, src, rep in iter_reports(args.pcap, has_fcs=not args.no_fcs):
        n += 1
        widths[rep.mimo.width_mhz] = widths.get(rep.mimo.width_mhz, 0) + 1
        srcs.add(src)
        if n <= args.show:
            print(f"  trame {n}: src={src} {rep.mimo.nr}x{rep.mimo.nc} "
                  f"{rep.mimo.width_mhz}MHz Ng={rep.mimo.ng} "
                  f"{rep.mimo.feedback_name} ns={rep.num_subcarriers} "
                  f"phi{rep.phi.shape} psi{rep.psi.shape}")
    print(f"\n{n} rapports BFI ; sources={len(srcs)} ; largeurs={widths}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bfid", description="Reproduction pédagogique du sensing Wi-Fi BFI."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info", help="Tables BFI et commandes de capture").set_defaults(
        func=_cmd_info)

    s = sub.add_parser("synth", help="Génère un dataset BFI synthétique")
    s.add_argument("--out", default="dataset.npz")
    s.add_argument("--persons", type=int, default=5)
    s.add_argument("--traces", type=int, default=8)
    s.add_argument("--frames", type=int, default=200)
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--mode", choices=["person", "zone"], default="person",
                   help="person = identification, zone = localisation")
    s.add_argument("--no-roundtrip", action="store_true",
                   help="ne pas faire passer les angles par encode/parse")
    s.set_defaults(func=_cmd_synth)

    d = sub.add_parser("demo", help="Pipeline complet sur données synthétiques")
    d.add_argument("--persons", type=int, default=5)
    d.add_argument("--traces", type=int, default=8)
    d.add_argument("--frames", type=int, default=200)
    d.add_argument("--window", type=int, default=32)
    d.add_argument("--stride", type=int, default=8)
    d.add_argument("--seed", type=int, default=0)
    d.add_argument("--mode", choices=["person", "zone"], default="person",
                   help="person = identification, zone = localisation")
    d.set_defaults(func=_cmd_demo)

    t = sub.add_parser("train", help="Évalue le baseline sur un dataset .npz")
    t.add_argument("--data", required=True)
    t.add_argument("--window", type=int, default=32)
    t.add_argument("--stride", type=int, default=8)
    t.add_argument("--seed", type=int, default=0)
    t.set_defaults(func=_cmd_train)

    pp = sub.add_parser("parse", help="Parse un pcap et résume les trames BFI")
    pp.add_argument("--pcap", required=True)
    pp.add_argument("--show", type=int, default=5, help="nb de trames détaillées")
    pp.add_argument("--no-fcs", action="store_true",
                    help="le pcap n'a pas de FCS en fin de trame")
    pp.set_defaults(func=_cmd_parse)

    lb = sub.add_parser("label", help="pcap + journal CSV -> dataset.npz étiqueté")
    lb.add_argument("--pcap", required=True)
    lb.add_argument("--journal", required=True, help="CSV: t_debut,t_fin,label")
    lb.add_argument("--out", default="dataset.npz")
    lb.add_argument("--no-fcs", action="store_true")
    lb.set_defaults(func=_cmd_label)

    w = sub.add_parser("web", help="Lance l'interface web (banc de test)")
    w.add_argument("--host", default="127.0.0.1")
    w.add_argument("--port", type=int, default=5000)
    w.add_argument("--debug", action="store_true")
    w.set_defaults(func=_cmd_web)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)
