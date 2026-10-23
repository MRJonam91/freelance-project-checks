# Security / Sicurezza

Security fixes initially target the latest release only. This small local utility reads a JSON file and writes stdout/stderr; it has no network operations, telemetry, account access, plugin loading or shell execution. It is not an operating-system sandbox. A host AI agent or shell has its own permissions and data handling.

For a vulnerability, use GitHub private vulnerability reporting on this repository if enabled. Otherwise open a minimal issue requesting a private contact path, without exploit details, credentials or personal data. Do not post a real customer file. No response-time guarantee or currently enabled private-reporting feature is claimed. A synthetic reproducer, Python version and affected version help assessment.

Untrusted files can be large enough to exhaust resources; run only within your intended local environment. Free-text CSV assumptions are formula-prefix escaped, and CSV quoting preserves delimiters; verify imported spreadsheet content and transformations. Negative calculated amounts are intentionally signed. Do not treat arbitrary files as trusted instructions.

Le correzioni riguardano inizialmente l'ultima release. Il tool legge JSON e scrive stdout/stderr, senza rete, telemetria o comandi shell; non è una sandbox del sistema operativo. Per vulnerabilità usa le segnalazioni private GitHub se abilitate, altrimenti una issue minima che chieda un contatto privato senza dettagli sfruttabili o dati reali. Nessuna garanzia sui tempi o sull'abilitazione di funzioni private. File enormi possono esaurire risorse. I testi CSV con prefissi formula sono protetti e i valori calcolati negativi rimangono firmati: verifica contenuti e conversioni nel foglio di calcolo.
