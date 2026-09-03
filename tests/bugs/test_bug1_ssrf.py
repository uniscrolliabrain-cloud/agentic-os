"""Bug 1 - SSRF DNS Rebinding en connectors/core/http.py: _is_ssrf() no resuelve DNS, vulnerable a dominios con TTL 0 que luego resuelven a 127.0.0.1"""

def test_bug1_ssrf_dns_rebinding():
    assert False, "TODO Bug 1"
