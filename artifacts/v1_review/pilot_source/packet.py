"""The approved 292-byte AES-256-GCM packet; no model dependencies."""
from dataclasses import dataclass
import os
from pathlib import Path
import struct

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AAD = b"ImageCalgacus/packet/v1"
HEADER = struct.Struct(">BBHHH")
PACKET_BYTES = 292
PACKET_RANKS = 584
TEXT, GRAYSCALE = 1, 2


@dataclass(frozen=True)
class Payload:
    kind: int
    data: bytes
    width: int = 0
    height: int = 0

    def validate(self):
        if type(self.data) is not bytes:
            raise ValueError("payload must be bytes")
        if self.kind == TEXT:
            if not 32 <= len(self.data) <= 128 or self.width or self.height:
                raise ValueError("UTF-8 payload requires 32..128 bytes and zero dimensions")
            self.data.decode("utf-8", errors="strict")
        elif self.kind == GRAYSCALE:
            if len(self.data) != 256 or (self.width, self.height) != (16, 16):
                raise ValueError("grayscale payload must be exactly 16x16 bytes")
        else:
            raise ValueError("unknown payload kind")
        return self


def plaintext(payload):
    payload.validate()
    return HEADER.pack(1, payload.kind, len(payload.data), payload.width, payload.height) + payload.data.ljust(256, b"\0")


def seal(payload, key, nonce):
    if len(key) != 32 or len(nonce) != 12:
        raise ValueError("requires 32-byte key and 12-byte nonce")
    result = nonce + AESGCM(key).encrypt(nonce, plaintext(payload), AAD)
    if len(result) != PACKET_BYTES:
        raise AssertionError("internal packet size")
    return result


def open_packet(packet, key, expected_kind):
    if len(packet) != PACKET_BYTES or len(key) != 32:
        raise ValueError("wrong packet/key length")
    # InvalidTag propagates; no plaintext is returned on authentication failure.
    clear = AESGCM(key).decrypt(packet[:12], packet[12:], AAD)
    version, kind, length, width, height = HEADER.unpack(clear[:8])
    if version != 1 or kind != expected_kind or length > 256:
        raise ValueError("invalid authenticated header")
    if any(clear[8 + length:]):
        raise ValueError("nonzero authenticated slot padding")
    return Payload(kind, clear[8:8 + length], width, height).validate()


class NewRun:
    """Single live encoding run, no loading or resuming an old run key."""
    def __init__(self, directory, random_bytes=os.urandom):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False, mode=0o700)
        self.random_bytes = random_bytes
        self.key = random_bytes(32)
        if len(self.key) != 32:
            raise ValueError("invalid key generator")
        self.nonces = set()
        key_path = self.directory / "run.key"
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(self.key)

    def encrypt(self, payload):
        for _ in range(100):
            nonce = self.random_bytes(12)
            if len(nonce) != 12:
                raise ValueError("invalid nonce generator")
            if nonce not in self.nonces:
                self.nonces.add(nonce)
                return seal(payload, self.key, nonce)
        raise ValueError("nonce generator repeatedly collided")
