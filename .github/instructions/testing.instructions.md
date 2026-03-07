---
applyTo: "tests/**/*.py"
---

# Testing instructions

- Test machine-readable output contracts, not just happy-path text
- Cover at least one failure case for every new command behavior
- Prefer deterministic fixtures and golden outputs for schemas/envelopes
- Keep tests small and focused unless they are explicit integration tests
- When changing command names, flags, or envelope fields, update the tests in the same change
