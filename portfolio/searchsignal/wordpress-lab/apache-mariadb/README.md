# Apache + MariaDB WordPress Multisite Lab

Status: **prepared, not yet executed on AJ's laptop**.

The current laptop has WSL2 enabled but no Linux distribution, Docker runtime, PHP, MariaDB, or Apache installed. This lab is committed so the architecture is inspectable without pretending it has already passed runtime acceptance.

## Stack

- WordPress on PHP 8.3 + Apache
- MariaDB 10.11
- `AllowOverride All` so WordPress-generated `.htaccess` rules can be exercised
- `WP_ALLOW_MULTISITE` enabled
- Local-only port 8088

## Intended acceptance exercise

1. Start the stack.
2. Complete WordPress install.
3. Activate a subdirectory Multisite network.
4. Create Admissions, Research, and Student Affairs subsites.
5. Build/edit pages, menus, media, metadata, users and permalinks.
6. Exercise redirects and canonical changes only after recording a rollback.
7. Inspect MariaDB network/site tables.
8. Compare generated Multisite rewrite rules with `htaccess-multisite.example`.
9. Run SearchSignal against the sandbox and verify the crawler, redirect validator, schema detection, and WordPress fingerprints.
10. Record screenshots and acceptance results.

The browser-based WordPress Playground lab in the sibling directory is already usable for real WordPress/Multisite admin practice. This Apache/MariaDB lab remains a separate infrastructure acceptance gate.
