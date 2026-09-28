# Clean-machine restore checklist

1. Copy/extract the Forge Core package and the latest Forge Offline Bundle.
2. Install Python if the machine has none; use cached installer if available.
3. Restore `FORGE_HOME` folders from the bundle.
4. Run `forge_base/bootstrap_windows.ps1` without flags to recreate environment paths.
5. Put cached portable executables into `FORGE_HOME/bin` before downloading replacements.
6. Run `python forge_base/forge_base.py doctor`.
7. If a Linux-only dependency is needed, restore/exported WSL distro or enable WSL2.
8. If container isolation is useful, restore cached Podman images or build from `Containerfile`.
9. Restore Git repositories from normal clones or `.bundle` backups.
10. Start Forge Core and run the local render smoke test.

A restore is not considered verified merely because backups exist; periodically test this checklist on a clean environment.
