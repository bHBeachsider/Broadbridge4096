"""Register the versioned questionnaire, without changing existing responses."""
import hashlib
import json
from pathlib import Path
from psycopg.types.json import Jsonb


def packet(repo: Path):
    record = json.loads((repo / "apps/capture/lib/pressure-questionnaire.json").read_text(encoding="utf-8"))
    encoded = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return record, hashlib.sha256(encoded).hexdigest()


def register(conn, repo: Path):
    record, digest = packet(repo)
    conn.execute("INSERT INTO broadbridge.questionnaire_packets(questionnaire_id,version,packet_sha256,record) VALUES(%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                 (record["id"], record["version"], digest, Jsonb(record)))
    saved = conn.execute("SELECT packet_sha256,record FROM broadbridge.questionnaire_packets WHERE questionnaire_id=%s AND version=%s", (record["id"], record["version"])).fetchone()
    if saved != (digest, record):
        raise RuntimeError("Questionnaire version already contains different content; use a new version")
    return {"id": record["id"], "version": record["version"], "sha256": digest, "questions": len(record["questions"])}
