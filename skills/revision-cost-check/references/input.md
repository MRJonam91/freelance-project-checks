# Input / Formato dati

JSON encodes one explicit interpretation of the supplied project numbers. Each value has a nonempty source ID. Keep the matching source statement or conversion in the check notes. Example data is synthetic.

| Field | Required | Meaning |
|---|---|---|
| `fee` | yes | Fixed project fee on the user's stated tax basis |
| `direct_costs` | yes | Supplied direct project costs, including explicit zero |
| `actual_hours` | yes | Hours already spent |
| `remaining_hours` | yes | Estimated hours still needed, before extra rounds |
| `hours_per_round` | yes | Estimated hours for each additional round, as one value or min/max |
| `internal_hour_cost` | no | Supplied internal cost per hour, in the same currency |
| `minimum_effective_hourly` | no | User's hourly-rate threshold, in the same currency per hour |
| `minimum_contribution` | no | User's contribution threshold, in the same currency |
| `rounds` | no | Distinct nonnegative integer counts; default `[0, 1, 2]` |
| `note` | no | Literal non-sensitive text carried into CSV assumptions |

Money fields: `{"value":"800","currency":"EUR","source":"S1"}`. Hours: `{"value":"12.5","unit":"hours","source":"S2"}`. Range: `{"min":"1","max":"3","unit":"hours","source":"S3"}`. Use either `value` or both range bounds for `hours_per_round`; all other numeric objects take `value`.

Use ASCII decimal strings with a dot and no grouping: `"0"`, `"0.5"`, `"1200.00"`. Negative inputs, exponents, underscores, signs, locale digits, `NaN`, infinity and ambiguous grouping are rejected. All money fields need the same explicit uppercase three-letter currency code. Codes are labels validated for format, not checked against a live currency registry. No currency rate is fetched. Convert minutes to hours explicitly before constructing input. Required omissions and duplicate JSON keys produce errors; omitted optional cost/thresholds remain unknown/not supplied.

For each round count `n`, total hours = actual + remaining + n × round hours. Net before internal time = fee − direct costs. Effective hourly = net / total hours. Internal time cost = total hours × internal hourly cost. Contribution = net − internal time cost. If internal hourly cost is absent, internal time cost and contribution remain `unknown`. At zero hours only the hourly division is unknown; other computable values remain valid.

CSV columns are `round_extra,total_hours,effective_hourly,direct_costs,internal_time_cost,contribution,assumptions`. A range creates `1_min`/`1_max` endpoints per nonzero round; round zero appears once. `min`/`max` describe hours, not the monetary result. Display uses ROUND_HALF_UP at two decimals. JSON preserves the computed decimal rate and separate `below`, `at`, `above`, `unknown` or `not_supplied` threshold states. Arithmetic uses 40-digit decimal precision, not infinite exact fractions; extreme magnitudes can exceed it and produce an input error.

CSV quotes commas, quotes and line breaks. Potential spreadsheet formula prefixes in the free-text assumptions cell are escaped with an apostrophe; signed computed amounts remain signed. Raw supplied text stays in the JSON sources. Treat exported content as data when opening or transforming it.

## Italiano

Ogni importo/ora deve avere una fonte; gli esempi sono sintetici. I campi obbligatori mancanti richiedono chiarimento, incluso il costo diretto zero esplicito. Ore residue e per giro sono stime. La valuta è un codice esplicito uguale per tutti gli importi; nessun cambio viene cercato o inventato. Numeri canonici con punto decimale, ore esplicite e soglie personali facoltative. Il costo interno assente lascia il contributo sconosciuto. Zero ore lascia sconosciuto il compenso orario; risultati calcolati negativi restano validi. Le due soglie si valutano separatamente sui valori non arrotondati. L'ipotesi mantiene compenso e costi diretti invariati nei giri aggiuntivi; non determina imposte, utile contabile o un prezzo approvato.
