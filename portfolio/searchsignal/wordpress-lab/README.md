# SearchSignal WordPress Multisite Lab

This is a **real WordPress Multisite training environment** powered by the official WordPress Playground. It is intentionally separate from Dartmouth/Geisel production systems.

## Launch

https://playground.wordpress.net/?blueprint-url=https://raw.githubusercontent.com/ajkivela369-coder/servicebridge-advocate/main/portfolio/searchsignal/wordpress-lab/blueprint.json

The Blueprint enables Multisite, logs into the admin area, and creates three demo subsites:

- Admissions Demo
- Research Demo
- Student Affairs Demo

## Practice goals

Use the lab for hands-on WordPress work: page creation/editing, heading hierarchy, menus/navigation, media/alt text, permalinks, metadata/plugin experiments, multisite network administration, site creation, user/editor guidance, and safe escalation decisions.

## Technology boundary

WordPress Playground runs WordPress/PHP in a browser/WebAssembly environment and uses SQLite rather than MariaDB/MySQL. It is useful for real WordPress and Multisite administration practice, but it **does not prove Apache or MariaDB production administration**.

A separate Apache + MariaDB lab can be added when a suitable local container/Linux runtime is installed. Until then, SearchSignal labels Apache/PHP/MariaDB as technical-lab knowledge rather than production experience.
