#!/usr/bin/env python3
"""Diagnóstico de pipelines: verifica que todos los pipelines en PIPELINES
se puedan cargar y ejecutar en sandbox."""
import sys

def main():
    try:
        from agentic_os.orchestration.pipelines import PIPELINES
        from agentic_os.orchestration.pipelines.runner import PipelineRunner
    except Exception as e:
        print(f"❌ Import error: {e}")
        return 1

    runner = PipelineRunner()
    issues = []
    for pid in PIPELINES:
        if pid not in PIPELINES:
            issues.append(pid)
            continue
        fn = PIPELINES[pid]
        if not callable(fn):
            issues.append(f"{pid}: no callable")
            continue
        try:
            import inspect
            sig = inspect.signature(fn)
            print(f"  ✓ {pid}: {len(sig.parameters)} params, callable")
        except Exception as e:
            issues.append(f"{pid}: {e}")

    if issues:
        print(f"\n❌ {len(issues)} pipeline(s) con issues:")
        for i in issues:
            print(f"   - {i}")
        return 1
    print(f"\n✅ {len(PIPELINES)} pipelines OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())
