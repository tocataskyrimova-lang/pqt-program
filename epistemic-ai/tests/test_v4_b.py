"""P0-B — Recursive Safety & Materiality.

Gate P0-B: prepare an adversarial corpus. No test secret *value* may appear in
any v4 column/audit/log fixture or receipt. We prove it for the sanitized
canonical output (the form that would be stored / receipted).
"""

import pytest

from qvch_v4.contracts import enums
from qvch_v4.contracts.canonical import canonical_json
from qvch_v4.safety.materiality import classify_materiality
from qvch_v4.safety.sanitizer import sanitize_and_hash
from qvch_v4.safety.secret_scanner import has_secret, scan

# --- Adversarial corpus: raw secret values that must NEVER survive. ---
API_KEY = "sk-" + "TESTMOCK_RESERVED_KEY_NOT_REAL_TOKEN_0123456789"
GH_TOKEN = "ghp_" + "TESTMOCK_RESERVED_TOKEN_NOT_REAL_0123456789"
AWS_KEY = "AKIA" + "IOSFODNN7EXAMPLE"
BEARER = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig"
PEM = (
    "-----BEGIN RSA PRIVATE KEY-----\n"
    "MIIBOgIBAAJBAKj34Ggxg6izwIikP2Yc6DlauZ8vIOQfx+W8qSf3GDo\n"
    "-----END RSA PRIVATE KEY-----"
)
CONNSTR = "postgresql://admin:s3cr3tpass@db.example.com:5432/app"
ENV_LINE = "DB_PASSWORD=supersecretvalue123\nAPI_KEY=anotherkey99"

ALL_SECRETS = [API_KEY, GH_TOKEN, AWS_KEY, BEARER, PEM, CONNSTR, ENV_LINE,
               "supersecretvalue123", "anotherkey99", "s3cr3tpass"]


def test_secret_scan_detects_corpus():
    payload = {
        "api_key": API_KEY,
        "nested": {"token": GH_TOKEN},
        "list": [{"aws": AWS_KEY}],
        "tool_output": PEM,
        "log": "auth failed: " + BEARER,
        "conn": CONNSTR,
        "env_block": ENV_LINE,
        "safe_note": "this is a benign observation about latency",
    }
    findings = scan(payload)
    kinds = {f.kind for f in findings}
    assert {"sensitive_key", "pem_private_key", "bearer_auth",
            "connection_string", "env_pair", "token_pattern"} <= kinds
    assert has_secret(payload)


def test_sanitize_removes_all_secret_values_and_is_clean():
    payload = {
        "api_key": API_KEY,
        "nested": {"token": GH_TOKEN},
        "list": [{"aws": AWS_KEY}],
        "tool_output": PEM,
        "log": "auth failed: " + BEARER,
        "conn": CONNSTR,
        "env_block": ENV_LINE,
        "safe_note": "benign observation",
        "metadata": '{"password": "embeddedpw999"}',
    }
    result = sanitize_and_hash(payload)

    # The second independent scan must find nothing.
    assert result.clean is True, f"second scan findings: {result.second_findings}"
    assert result.second_findings == ()

    # No raw secret value may appear anywhere in the canonical output.
    serialized = canonical_json(result.sanitized)
    for secret in ALL_SECRETS:
        assert secret not in serialized, f"secret leaked into sanitized output: {secret!r}"


def test_sensitive_key_becomes_opaque_locator():
    payload = {"api_key": API_KEY}
    result = sanitize_and_hash(payload)
    sanitized = result.sanitized
    assert sanitized["api_key"]["locator_type"] == "secret_ref"
    assert sanitized["api_key"]["never_embed"] is True
    assert sanitized["api_key"]["reference"] == "api_key"
    # fingerprint is a non-reversible hash, not the secret
    assert sanitized["api_key"]["fingerprint"].startswith("sha256:")
    assert API_KEY not in result.sanitized["api_key"]["fingerprint"]


def test_nested_json_string_is_sanized():
    payload = {"metadata": '{"token": "' + GH_TOKEN + '"}'}
    result = sanitize_and_hash(payload)
    assert result.clean is True
    serialized = canonical_json(result.sanitized)
    assert GH_TOKEN not in serialized


def test_depth_bound_does_not_crash():
    # deeply nested structure
    deep = {"a": {}}
    cur = deep["a"]
    for _ in range(40):
        nxt = {}
        cur["a"] = nxt
        cur = nxt
    cur["password"] = API_KEY
    result = sanitize_and_hash(deep)
    # depth guard triggered: the deepest secret may be redacted as opaque
    serialized = canonical_json(result.sanitized)
    assert API_KEY not in serialized


def test_materiality_secret_ref():
    payload = {"creds": {"locator_type": "secret_ref", "reference": "api_key",
                          "fingerprint": "sha256:abc", "never_embed": True}}
    assert classify_materiality(payload) == enums.MaterialityClass.SECRET_REF.value


def test_materiality_literal_artifact():
    payload = {"exact_locator": "s3://x/y", "immutable_content_hash": "sha256:abc",
               "retrieval_recipe": "fetch"}
    assert classify_materiality(payload) == enums.MaterialityClass.LITERAL_ARTIFACT.value


def test_materiality_skill_trace():
    payload = {"execution_receipt": {"exit_code": 0, "node": "node15"}}
    assert classify_materiality(payload) == enums.MaterialityClass.SKILL_TRACE.value


def test_materiality_mixed_and_semantic_default():
    mixed = {"api_key": "x", "exact_locator": "s3://x", "immutable_content_hash": "sha256:z"}
    assert classify_materiality(mixed) == enums.MaterialityClass.MIXED.value
    assert classify_materiality({"note": "just meaning"}) == enums.MaterialityClass.SEMANTIC.value


def test_llm_suggestion_is_non_binding():
    # LLM "suggests" LITERAL_ARTIFACT but payload actually holds a secret.
    payload = {"api_key": "sk-realvalue1234567890abcdefghij"}
    assert classify_materiality(payload, suggested="LITERAL_ARTIFACT") == \
        enums.MaterialityClass.SECRET_REF.value
