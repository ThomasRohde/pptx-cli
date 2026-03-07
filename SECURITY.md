# Security Policy

## Reporting a vulnerability

Please do **not** open public GitHub issues for suspected security problems.

Instead, contact the maintainer privately through the repository security contact or a private channel you control.

Include:

- affected version or commit
- reproduction steps
- impact assessment
- whether the issue affects local files, generated decks, dependency handling, or CI usage

## Scope

Security concerns for this project may include:

- malicious `.pptx` package parsing behavior
- zip bombs or oversized package handling
- path traversal during archive extraction
- unsafe file-write behavior or overwrite risks
- command execution or shell injection issues
- malformed manifest/spec input leading to unintended writes

## Coordinated disclosure

We prefer coordinated disclosure and will work to validate, remediate, and communicate fixes responsibly.

## Hardening guidance

- treat input `.pptx`, YAML, and JSON files as untrusted
- avoid writing outside explicit output directories
- preserve safe temp-file and atomic-write semantics
- validate paths and archive members before extraction
