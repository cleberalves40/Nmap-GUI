# Changelog

## 1.1.0 - 2026-10-21

### Added
- Structured host and port results with text filtering.
- Persistent scan history and XML comparison for host and port changes.
- Named scan profiles stored in application data.
- Target-list files, target exclusions, IPv6, top-port selection, and version intensity controls.
- Manual Nmap upstream version check; updates remain user-managed.
- Tag-triggered GitHub release workflow that validates the package version.

### Changed
- Drain Nmap stdout and stderr concurrently and apply the configured scan timeout.
- Preserve quoted extra arguments and reject malformed quoting.
- Export raw Nmap text or validated XML separately from GUI annotations.
- Run unit tests in CI across the configured Python matrix.