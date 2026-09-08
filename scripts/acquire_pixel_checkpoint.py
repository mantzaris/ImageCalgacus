"""Acquire the single author-published PixelCNN++ checkpoint; no inference.
Source: pclucas14/pixel-cnn-pp README at 7cb4436f062fda9b63ecc9e3b75d2c2dcb379931.
Downloads only to the specified new output path. Weights are never redistributed.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import struct
import urllib.request
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

FOLDER = "W7IhST7R"
PUBLIC_FOLDER_KEY = "PV7Pbet8Q07GxVLGnmQrZg"


def unbase(value):
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def api(command):
    req = urllib.request.Request(
        "https://g.api.mega.co.nz/cs?id=1&n=" + FOLDER,
        data=json.dumps([command]).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        result = json.load(response)[0]
    if not isinstance(result, dict):
        raise RuntimeError("MEGA API failed: " + str(result))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    nodes = [n for n in api({"a": "f", "c": 1, "r": 1})["f"] if n["t"] == 0]
    if len(nodes) != 1:
        raise RuntimeError("checkpoint listing changed; inspect before selecting")
    node = nodes[0]
    decrypt = Cipher(algorithms.AES(unbase(PUBLIC_FOLDER_KEY)), modes.ECB()).decryptor()
    full_key = decrypt.update(unbase(node["k"].split(":")[1])) + decrypt.finalize()
    words = struct.unpack(">8I", full_key)
    file_key = struct.pack(">4I", *(words[i] ^ words[i + 4] for i in range(4)))
    attr_dec = Cipher(algorithms.AES(file_key), modes.CBC(bytes(16))).decryptor()
    attrs = attr_dec.update(unbase(node["a"])) + attr_dec.finalize()
    if not attrs.startswith(b"MEGA"):
        raise RuntimeError("invalid checkpoint attributes")
    name = json.loads(attrs[4:].rstrip(b"\0"))["n"]
    info = api({"a": "g", "g": 1, "n": node["h"]})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    decrypt = Cipher(algorithms.AES(file_key), modes.CTR(struct.pack(">4I", words[4], words[5], 0, 0))).decryptor()
    digest = hashlib.sha256()
    count = 0
    with urllib.request.urlopen(info["g"], timeout=60) as response, args.output.open("xb") as target:
        while True:
            block = response.read(1024 * 1024)
            if not block:
                break
            clear = decrypt.update(block)
            target.write(clear)
            digest.update(clear)
            count += len(clear)
        final = decrypt.finalize()
        target.write(final)
        digest.update(final)
        count += len(final)
    if count != node["s"]:
        raise RuntimeError("download size mismatch; partial file retained")
    manifest = {"upstream_revision": "7cb4436f062fda9b63ecc9e3b75d2c2dcb379931",
                "source": "https://github.com/pclucas14/pixel-cnn-pp",
                "author_filename": name, "mega_file_handle": node["h"],
                "bytes": count, "sha256": digest.hexdigest(),
                "integrity": "TLS acquisition; exact size and local SHA-256; no published checksum",
                "license": "Repository non-sale license; no separate checkpoint notice observed; weights excluded from redistribution"}
    args.output.with_suffix(".provenance.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
