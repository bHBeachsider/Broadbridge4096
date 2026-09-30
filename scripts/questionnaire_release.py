"""Inspect/apply the questionnaire release in the dedicated Broadbridge Neon project.

Uses db.py migration checks; direct URL for DDL, pooled URL for normal operations.
Never outputs credentials or response contents. Does not deploy an application.
"""
import argparse
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit
import requests
from dotenv import dotenv_values
from questionnaire_packet import register, packet

PROJECT = "crimson-block-71962201"
PRODUCTION = "br-old-leaf-au0q8w6y"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["inspect", "apply"])
    parser.add_argument("--target", choices=["dev", "production"], required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    values = dotenv_values(args.env_file)
    session = requests.Session()
    session.headers["Authorization"] = "Bearer " + values["NEON_API_KEY"]
    def get(path, **params):
        response = session.get("https://console.neon.tech/api/v2/projects/" + PROJECT + path, params=params, timeout=30)
        if response.status_code != 200: raise RuntimeError(f"Neon metadata HTTP {response.status_code}")
        return response.json()
    if args.target == "production":
        branch = get("/branches/" + PRODUCTION)["branch"]
        if branch["id"] != PRODUCTION or branch["name"] != "production": raise RuntimeError("Production identity mismatch")
    else:
        branches = [b for b in get("/branches")["branches"] if b["name"] == "dev"]
        if len(branches) != 1 or branches[0]["id"] == PRODUCTION: raise RuntimeError("Dev identity ambiguous")
        branch = branches[0]
    endpoints = [e for e in get("/endpoints")["endpoints"] if e["branch_id"] == branch["id"] and e["type"] == "read_write"]
    if len(endpoints) != 1: raise RuntimeError("Endpoint identity ambiguous")
    endpoint = endpoints[0]
    databases = get("/branches/" + branch["id"] + "/databases")["databases"]
    database = next(d for d in databases if d["name"] == "neondb")
    for pooled, key in [(True,"BROADBRIDGE_DATABASE_URL"),(False,"DATABASE_URL_UNPOOLED")]:
        uri = get("/connection_uri", branch_id=branch["id"], endpoint_id=endpoint["id"], database_name=database["name"], role_name=database["owner_name"], pooled=str(pooled).lower())["uri"]
        if urlsplit(uri).hostname.split(".")[0].removesuffix("-pooler") != endpoint["id"]: raise RuntimeError("Connection target mismatch")
        os.environ[key] = uri
    repo = Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(repo / "packs/oil-gas/scripts"))
    import db
    with db.connection() as conn:
        before = db.status(conn)
    result = {"project":PROJECT,"branch":branch["id"],"branch_name":branch["name"],"endpoint":endpoint["id"],"mode":args.mode,"before":before,"response_writes":0}
    if args.mode == "apply":
        if args.target == "production" and before["version"] not in ["0007_auth_link_24h.sql","0008_training_questionnaire.sql"]:
            raise RuntimeError("Unexpected production schema; inspect before applying")
        with db.connection(migration=True) as conn:
            conn.execute("SET LOCAL lock_timeout='10s'")
            conn.execute("SET LOCAL statement_timeout='30s'")
            result["after"] = db.migrate(conn)
        with db.connection() as conn:
            result["packet"] = register(conn,repo)
            result["response_revisions"] = conn.execute("SELECT count(*) FROM broadbridge.questionnaire_responses").fetchone()[0]
    else:
        p,digest = packet(repo)
        result["proposed_packet"] = {"id":p["id"],"version":p["version"],"sha256":digest,"questions":len(p["questions"])}
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(f"Questionnaire release failed ({type(exc).__name__}); credentials and contents withheld.",file=sys.stderr)
        sys.exit(1)
