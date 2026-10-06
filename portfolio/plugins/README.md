# Private Forge plugin source

These source packages preserve the branded GFC release and the three app-workflow plugins. This repository is private; the connection metadata is the owner's existing GFC dependency and must not be copied into a public multi-user release.

| Package | Version | Companion |
|---|---|---|
| [Grim Forge Commander V2](grim-forge-commander-v2/) | 1.0.1 | [GFC](https://grim-forge-commander.ajkivela369.chatgpt.site) |
| [GrimForge Cinema](grimforge-cinema/) | 1.0.0 | [Cinema](https://grimforge-cinema.ajkivela369.chatgpt.site) |
| [Elias](elias/) | 1.0.0 | [Elias](https://elias.ajkivela369.chatgpt.site) |
| [Evidence Auditor](evidence-auditor/) | 1.0.0 | [Evidence](https://evidence-auditor.ajkivela369.chatgpt.site) |

Each app package contains its root manifest, compatibility interface manifest, existing app dependency, real PNG icon, workflow skill, and local API reference. The compatibility manifests were read back from Plugin Creator. The GFC source is taken from the successfully uploaded 1.0.1 installable archive, preserving its metadata and defaultPrompt shape.

To prepare an update, archive the contents of the selected package directory with plugin.json at the package root, validate the archive, and update the existing plugin using its exact current release guard. Do not create replacement tunnels or duplicate plugins as a refresh strategy. Server upgrade bundles are not installable plugin archives.

The app packages add instructions over the existing GFC connection; they do not add independent MCP servers or separate permission scopes. Installing/Try in chat is an owner action and needs an actual fresh-chat test. See [associations](../COMPANION_SITES.md), [QC](../QUALITY_CONTROL.md), and [public readiness](../PUBLIC_READINESS.md).
