import sys, traceback
sys.path.insert(0, r"C:\Users\Alfonso\Desktop\git hub repos\agentic-os-cline\src")
try:
    import agentic_os.domains.agencia as a
    from agentic_os.kernel.ontology.domain_models import (
        ENTITY_TYPE_REGISTRY,
        validate_registry_integrity,
    )
    validate_registry_integrity()
    kinds = sorted(k for k in ENTITY_TYPE_REGISTRY if k.startswith("agencia."))
    out = "PROBE_OK kinds=" + ",".join(kinds)
except Exception as e:
    out = "PROBE_FAIL " + type(e).__name__ + ": " + str(e) + "\n" + traceback.format_exc()
with open(r"C:\Users\Alfonso\Desktop\git hub repos\agentic-os-cline\_probe_result.txt", "w", encoding="utf-8") as f:
    f.write(out)
print("written")
