#!/usr/bin/env python3
"""registry.payload.json に Ed25519 署名を付けて registry.json (署名済み envelope) を生成する。

SAIVerse 本体は公式レジストリ URL からの応答に Ed25519 署名を必須とする
(saiverse/addon_registry.py の _verify_registry_document)。このスクリプトは
その envelope 形式を生成する唯一の正規手段。

使い方:
    python sign_registry.py --key <秘密鍵ファイル(raw 32byte の base64)>

    (--payload / --out はデフォルトのままで通常は変更不要)

必要パッケージ: cryptography (pip install cryptography)

署名対象の canonical 形式は SAIVerse 本体の _canonical_registry_payload と
一致していなければならない:
    json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def canonical_payload(payload: dict) -> bytes:
    # SAIVerse 本体 saiverse/addon_registry.py の _canonical_registry_payload と同一に保つこと
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--key", required=True, help="秘密鍵ファイル (raw 32byte の base64)")
    parser.add_argument("--payload", default="registry.payload.json", help="署名対象の payload JSON")
    parser.add_argument("--out", default="registry.json", help="出力する署名済み envelope")
    args = parser.parse_args()

    key_b64 = Path(args.key).read_text(encoding="ascii").strip()
    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(key_b64, validate=True))
    public_raw = private_key.public_key().public_bytes_raw()
    key_id = hashlib.sha256(public_raw).hexdigest()[:16]

    payload = json.loads(Path(args.payload).read_text(encoding="utf-8"))
    if "signed" in payload or "signature" in payload:
        print("error: payload が既に envelope 形式です。registry.payload.json を指定してください", file=sys.stderr)
        return 1

    signature = private_key.sign(canonical_payload(payload))
    envelope = {
        "signed": payload,
        "signature": {
            "algorithm": "ed25519",
            "value": base64.b64encode(signature).decode("ascii"),
            "key_id": key_id,
        },
    }
    Path(args.out).write_text(
        json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 生成直後に自己検証 (書いた envelope を読み戻して署名を検証する)
    written = json.loads(Path(args.out).read_text(encoding="utf-8"))
    private_key.public_key().verify(
        base64.b64decode(written["signature"]["value"]),
        canonical_payload(written["signed"]),
    )
    print(f"signed OK: {args.out} (key_id={key_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
