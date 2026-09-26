"""Publish an immutable, model-blinded public-v1 packet to the capture review UI.

No model calls or scoring. --db uses only BROADBRIDGE_DATABASE_URL; migrations
remain a separate db.py migrate operation. Verify the dev target before --db.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
FROZEN = {
    "sample.json": "3407f8d2ea56e0cc8c379f9a84b5c1808b72d5dedd7c504d1badbcb423a0e736",
    "protocol.json": "47f38b1b9d0cf7b9930200c38e68f4b126776a341a49239489d310509912f241",
    "results.json": "9cb326693fe100acc1b01b625547997a50749b538a07009a93f85f83b2cdc330",
    "run.json": "9d55add47c397c9e9d1658f25ac39f26e44e7020934154f40e3a13313c8c455c",
}


def packet_hash(packet):
    return hashlib.sha256(json.dumps(packet, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def build_packet(run_root, packet_id):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", packet_id):
        raise ValueError("Invalid packet identity")
    values = {}
    for name, expected in FROZEN.items():
        payload = (run_root / name).read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected:
            raise ValueError("Frozen public-v1 input mismatch: " + name)
        values[name] = json.loads(payload)
    sample, results, run = values["sample.json"], values["results.json"], values["run.json"]
    source_index = {s["source_id"]: s for s in sample["sources"]}
    result_index = {(r["source_id"], r["model_key"]): r for r in results}
    items = []
    for q in sample["questions"]:
        source = source_index[q["source_id"]]
        for label in ("A", "B"):
            result = result_index.get((q["source_id"], run["model_mapping_by_source"][q["source_id"]][label]), {})
            answer = next((a for a in (result.get("response") or {}).get("answers", [])
                           if a["question_id"] == q["question_id"]), None)
            items.append({**{k: q[k] for k in ("source_id", "question_id", "type", "question", "reference_answer",
                                              "hard_fail_criteria", "split", "permitted_use")},
                          "response_label": label, "answer": answer,
                          "tolerance": json.dumps(q["tolerance"], ensure_ascii=False),
                          "availability": "answered" if answer else "unavailable",
                          "checks": result.get("checks", [])})
    return {"schema": "broadbridge.public_review/1", "packet_id": packet_id,
            "title": "Public-document evaluation · v1", "training_approved": False,
            "frozen_files": FROZEN,
            "sources": [{"source_id": s["source_id"], "title": s["title"], "url": s["url"],
                         "publisher": s["publisher"], "context": s["publication_context"],
                         "blocks": [{"block_id": b["block_id"], "text": b["text"]} for b in s["blocks"]]}
                        for s in sample["sources"]], "items": items}


def register(conn, packet):
    from psycopg.types.json import Jsonb
    digest = packet_hash(packet)
    conn.execute("INSERT INTO broadbridge.public_review_packets(packet_id, packet_sha256, record) "
                 "VALUES (%s, %s, %s) ON CONFLICT (packet_id) DO NOTHING",
                 (packet["packet_id"], digest, Jsonb(packet)))
    row = conn.execute("SELECT packet_sha256, record FROM broadbridge.public_review_packets WHERE packet_id=%s",
                       (packet["packet_id"],)).fetchone()
    if row != (digest, packet):
        raise ValueError("Packet identity is already bound to different frozen content; use a new version")
    return digest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, default=ROOT / "output/openrouter-public-evaluation/public-v1-live")
    parser.add_argument("--packet-id", default="public-v1")
    parser.add_argument("--db", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    packet = build_packet(args.run_root, args.packet_id)
    if args.output:
        with args.output.open("x", encoding="utf-8") as file:
            json.dump(packet, file, ensure_ascii=False, indent=2)
            file.write("\n")
    if args.db:
        sys.path.insert(0, str(ROOT / "packs/oil-gas/scripts"))
        from db import connection
        with connection() as conn:
            register(conn, packet)
    print(json.dumps({"packet_id": packet["packet_id"], "packet_sha256": packet_hash(packet),
                      "items": len(packet["items"]), "scores_written": 0, "database_registered": args.db}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"Review packet operation failed ({type(error).__name__}); no scores generated.", file=sys.stderr)
        raise SystemExit(1)
