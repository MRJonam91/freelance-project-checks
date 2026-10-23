# Freelance Project Checks

**IT:** uno strumento gratuito e locale per vedere quanto incidono i giri di revisione su una commessa a compenso fisso. **EN:** a free local check of how extra revision rounds affect a fixed-fee project.

Include la skill `revision-cost-check` e un calcolatore Python deterministico utilizzabile anche senza un agente AI. Nessuna dipendenza esterna, account, rete o telemetria nel runtime. I file di esempio sono sintetici. Versione iniziale **0.1.0**; non è consulenza fiscale o contabile.

Includes the `revision-cost-check` skill and a deterministic Python calculator usable without an AI agent. The runtime has no external dependencies, accounts, network calls or telemetry. All example data is synthetic. Initial version **0.1.0**; it does not provide tax or accounting advice.

## Prova rapida / Quick start

Richiede Python **3.11+**. Esegui dalla radice del repository o dello ZIP sorgente estratto. Su alcuni sistemi usa `python3` oppure `py -3` al posto di `python`.

Requires Python **3.11+**. Run from the repository root or the extracted source ZIP root. Some systems use `python3` or `py -3` instead of `python`.

```sh
python -B skills/revision-cost-check/scripts/calculate.py skills/revision-cost-check/examples/project.json
python -B skills/revision-cost-check/scripts/calculate.py skills/revision-cost-check/examples/project.json --notes
```

Risultati dell'esempio / Example results:

| Giri extra / Extra rounds | Ore / Hours | Compenso orario effettivo / Effective hourly | Contributo / Contribution |
|---|---:|---:|---:|
| 0 | 24 | 45.00 EUR/h | 360.00 EUR |
| 1 | 27 | 40.00 EUR/h | 270.00 EUR |
| 2 | 30 | 36.00 EUR/h | 180.00 EUR |

Il compenso orario è `(compenso − costi diretti) / ore totali`. Il contributo sottrae anche il costo orario interno fornito. L'esempio mantiene invariati compenso e costi diretti: 1.200 EUR e 120 EUR. Il contributo non è utile contabile. Le ore residue e per giro sono stime; le soglie sono scelte personali, non prezzi cliente approvati.

Effective hourly is `(fee − direct costs) / total hours`. Contribution also deducts the supplied internal hourly cost. The example holds fee and direct costs fixed at EUR 1,200 and EUR 120. Contribution is not accounting profit. Remaining and per-round hours are estimates; thresholds are personal choices, not approved client prices.

## I tuoi dati / Your project

Copia [project.json](skills/revision-cost-check/examples/project.json) in `normalized-input.json` e sostituisci le cifre con i tuoi dati. Mantieni gli ID delle fonti e documenta conversioni esplicite. [Formato e formule / Input and formulas](skills/revision-cost-check/references/input.md).

Copy [project.json](skills/revision-cost-check/examples/project.json) to `normalized-input.json` and replace the synthetic figures with your own. Preserve source IDs and record explicit conversions. See [input and formulas](skills/revision-cost-check/references/input.md).

```sh
python -B skills/revision-cost-check/scripts/calculate.py normalized-input.json > revision-costs.csv
python -B skills/revision-cost-check/scripts/calculate.py normalized-input.json --json > calculation-details.json
python -B skills/revision-cost-check/scripts/calculate.py normalized-input.json --notes > check-notes.md
```

Le note automatiche sono in inglese; la skill può spiegare i risultati nella lingua richiesta. Le chiavi CSV restano stabili. Una valuta esplicita uguale per tutti gli importi è obbligatoria; il calcolatore non recupera cambi. Costi e soglie mancanti restano sconosciuti/non forniti; costo zero va fornito come zero. Intervalli ore producono estremi, senza inventare un valore centrale. Zero ore produce un compenso orario sconosciuto; importi calcolati negativi restano validi. Soglie confrontate sui valori non arrotondati, importi esposti a due decimali. Precisione aritmetica: 40 cifre decimali significative.

Automatic notes are English; the skill can explain results in the requested language. CSV keys stay stable. All monetary inputs require the same explicit currency; no exchange rates are fetched. Missing costs/thresholds remain unknown/not supplied, and zero cost must be supplied explicitly. Hour ranges produce endpoints without inventing a midpoint. Zero hours produces an unknown hourly rate; computed negative amounts remain valid. Thresholds use unrounded values while displayed amounts use two decimals. Arithmetic uses 40 significant decimal digits.

Il processo scrive soltanto stdout/stderr; le redirezioni sopra creano i file e possono sovrascrivere file omonimi. Controlla exit code **0** prima di usare l'output; **2** indica un errore di input/lettura. Dati invalidi non producono scenari. I file di lavoro elencati sono ignorati da Git, ma controlla sempre ciò che condividi. Se carichi dati in un agente ospitato, si applicano anche le condizioni di quel servizio.

The process writes only stdout/stderr; the shell redirects above create files and can replace same-named files. Check exit code **0** before using output; **2** means an input/read error. Invalid input produces no scenarios. Listed working files are ignored by Git; inspect what you share. If you upload data to a hosted agent, that service's terms also apply.

## Installa la skill / Install the skill

L'uso CLI sopra è completo e non richiede installazione della skill. Per un agente compatibile, copia `skills/revision-cost-check/` nella sua directory delle skill, insieme a `LICENSE`, `NOTICE` e `THIRD_PARTY_NOTICES.md`. Per Codex, esempio PowerShell; se la destinazione esiste, esaminala prima di sostituirla:

The CLI above is complete without installing the skill. For a compatible agent, copy `skills/revision-cost-check/` into its skills directory along with `LICENSE`, `NOTICE` and `THIRD_PARTY_NOTICES.md`. Codex PowerShell example; inspect an existing destination before replacing it:

```powershell
$skillRoot = Join-Path $env:USERPROFILE '.codex\skills'
$skillDestination = Join-Path $skillRoot 'revision-cost-check'
if (Test-Path -LiteralPath $skillDestination) { throw 'Destination already exists; inspect it first.' }
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
Copy-Item -LiteralPath 'skills/revision-cost-check' -Destination $skillDestination -Recurse
Copy-Item -LiteralPath 'LICENSE','NOTICE','THIRD_PARTY_NOTICES.md' -Destination $skillDestination
```

Invoca `$revision-cost-check` con i numeri della commessa. Disinstallazione: rimuovi solo la cartella installata `revision-cost-check` dopo averne salvato eventuali modifiche. La disponibilità automatica dipende dal caricamento delle skill dell'agente; i test del repository verificano il calcolatore e il pacchetto, non tutte le interfacce degli agenti.

Invoke `$revision-cost-check` with the project numbers. Uninstall by removing only the installed `revision-cost-check` directory after saving any changes. Automatic discovery depends on the agent's skill loading; repository tests verify the calculator and package, not every agent interface.

## Test e pacchetto / Tests and package

```sh
python -B -m unittest discover -s tests -v
python -B scripts/package.py
```

Lo script crea `dist/freelance-project-checks-0.1.0.zip` e il checksum SHA-256. Usa una lista esplicita di sorgenti: include codice, test, documentazione, licenza e notice; esclude dati di lavoro e runtime commerciali. Il test del pacchetto estrae lo ZIP ed esegue il calcolatore estratto su dati sintetici. La CI è configurata per Windows/Linux e Python 3.11/3.14; una configurazione non equivale a un'esecuzione riuscita. Stato locale iniziale: Python 3.14 su Windows; gli esiti remoti si vedono nella scheda Actions dopo la pubblicazione.

The script creates `dist/freelance-project-checks-0.1.0.zip` and a SHA-256 checksum. An explicit source allowlist includes code, tests, documentation, license and notices; it excludes working data and commercial runtimes. The package test extracts the ZIP and runs its calculator on synthetic input. CI is configured for Windows/Linux and Python 3.11/3.14; configuration is not a passing run. Initial local validation uses Python 3.14 on Windows; remote results appear in Actions after publication.

## Gratuito e workflow più ampio / Free and broader workflow

Questo progetto gratuito offre un controllo numerico completo: input normalizzato, scenari CSV e note brevi. Non impone limiti artificiali a giri, intervalli, valute coerenti o controlli. Le stesse operazioni aritmetiche sono disponibili qui senza acquisto.

This free project provides a complete numeric check: normalized input, CSV scenarios and short notes. It places no artificial paywall on round counts, ranges, consistent currencies or validation. The same arithmetic is available here without a purchase.

Se ti serve un workflow più ampio con revisione del brief e dei vincoli, scenari e bozze di opzioni da discutere con il cliente in tre artefatti coordinati, [Revision Budget Lab su Agensi](https://agensi.io/skills/revision-budget-lab-freelance-revision-cost-scenarios) è il prodotto separato dell'autore. La scheda risulta live/approved nella verifica del 23 ottobre 2026; disponibilità e condizioni possono cambiare. Questo repository non contiene la skill commerciale o le sue bozze. Il link è facoltativo: nessuna installazione o azione del calcolatore dipende da esso.

For a broader workflow with brief/constraint review, scenarios and draft client tradeoffs in three coordinated artifacts, [Revision Budget Lab on Agensi](https://agensi.io/skills/revision-budget-lab-freelance-revision-cost-scenarios) is the author's separate product. Its listing was verified live/approved on 23 October 2026; availability and terms may change. This repository does not contain the commercial skill or its drafts. The link is optional: installation and calculation do not depend on it.

## Licenza e contributi / License and contributions

Codice e documentazione originali: **GPL-3.0-or-later**, copyright 2026 ManojRollo. Vedi [LICENSE](LICENSE), [NOTICE](NOTICE), [terze parti](THIRD_PARTY_NOTICES.md) e [asset](ASSETS.md). Le condizioni GPL si applicano alla distribuzione e alle modifiche come indicato nella licenza; nomi e marchi non concedono affiliazione o endorsement. Il helper deriva dal codice originale dell'autore per Revision Budget Lab; le istruzioni gratuite sono nuove.

Original code and documentation: **GPL-3.0-or-later**, copyright 2026 ManojRollo. See [LICENSE](LICENSE), [NOTICE](NOTICE), [third parties](THIRD_PARTY_NOTICES.md) and [assets](ASSETS.md). GPL terms govern distribution and modifications as stated in the license; project names and marks do not grant affiliation or endorsement. The helper derives from the author's original Revision Budget Lab code; the free instructions are new.

Per contribuire / To contribute: [CONTRIBUTING](CONTRIBUTING.md). Supporto / Support: [SUPPORT](SUPPORT.md). Vulnerabilità / Vulnerabilities: [SECURITY](SECURITY.md). Comportamento / Conduct: [CODE_OF_CONDUCT](CODE_OF_CONDUCT.md). Novità / Changes: [CHANGELOG](CHANGELOG.md).

## Sostieni il progetto / Support the project

Se utile, puoi sostenere manutenzione e sviluppo su [GitHub Sponsors](https://github.com/sponsors/MRJonam91), [Ko-fi](https://ko-fi.com/mrjonam), [Buy Me a Coffee](https://buymeacoffee.com/mrjonam) o [PayPal](https://paypal.me/manorollo). Il supporto è volontario, non necessario per usare il progetto e non attribuisce licenze o diritti aggiuntivi. `FUNDING.yml` non conferma idoneità o approvazione dell'account GitHub Sponsors, qui non accertate.

If useful, you can support maintenance and development through [GitHub Sponsors](https://github.com/sponsors/MRJonam91), [Ko-fi](https://ko-fi.com/mrjonam), [Buy Me a Coffee](https://buymeacoffee.com/mrjonam) or [PayPal](https://paypal.me/manorollo). Support is voluntary, unnecessary for use and grants no additional license or rights. `FUNDING.yml` does not establish GitHub Sponsors account eligibility or approval, which has not been established here.
