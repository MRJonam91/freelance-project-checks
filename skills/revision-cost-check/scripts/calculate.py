"""Source-linked revision scenarios. Standard library only; no external actions."""
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 ManojRollo
# Derived from the owner's Revision Budget Lab calculator. See NOTICE.
import argparse
import csv
from decimal import Decimal, DecimalException, ROUND_HALF_UP, localcontext
import io
import json
from pathlib import Path
import re
import sys

COLUMNS = ['round_extra', 'total_hours', 'effective_hourly', 'direct_costs',
           'internal_time_cost', 'contribution', 'assumptions']

def number(value, name):
    if isinstance(value, bool) or value is None:
        raise ValueError(name + ': provide a nonnegative decimal value')
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', str(value)):
        raise ValueError(name + ': use ASCII decimals with a dot and no grouping or exponent')
    try:
        result = Decimal(str(value))
    except (DecimalException, ValueError):
        raise ValueError(name + ': use canonical decimals with a dot and no grouping') from None
    if not result.is_finite() or result < 0:
        raise ValueError(name + ': value must be finite and nonnegative')
    return result

def entry(data, name, currency=None, hours=False):
    item = data.get(name)
    if not isinstance(item, dict):
        raise ValueError(name + ': supply an object with value and source')
    if not isinstance(item.get('source'), str) or not item['source'].strip():
        raise ValueError(name + ': source ID is required')
    if hours:
        if item.get('unit') != 'hours':
            raise ValueError(name + ': normalize to explicit hours before calculation')
    else:
        code = item.get('currency')
        if not isinstance(code, str) or len(code) != 3 or not code.isascii() or not code.isalpha() or code != code.upper():
            raise ValueError(name + ': currency must be an uppercase three-letter code')
        if currency is not None and code != currency:
            raise ValueError(name + ': mixed currencies; provide normalized figures first')
    return item

def compact(value):
    return format(value, 'f').rstrip('0').rstrip('.') if '.' in format(value, 'f') else format(value, 'f')

def amount(value, currency, rate=False):
    rounded = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return format(rounded, '.2f') + ' ' + currency + ('/h' if rate else '')

def relation(value, threshold):
    if threshold is None:
        return 'not_supplied'
    if value is None:
        return 'unknown'
    return 'below' if value < threshold else 'at' if value == threshold else 'above'

def _calculate(data):
    if not isinstance(data, dict):
        raise ValueError('Input must be a JSON object')
    fee_item = entry(data, 'fee')
    currency = fee_item['currency']
    parsed = {'fee': number(fee_item.get('value'), 'fee')}
    sources = {'fee': fee_item['source']}
    for name in ['direct_costs', 'actual_hours', 'remaining_hours']:
        item = entry(data, name, currency, hours=name.endswith('_hours'))
        parsed[name] = number(item.get('value'), name)
        sources[name] = item['source']
    per_round = entry(data, 'hours_per_round', hours=True)
    sources['hours_per_round'] = per_round['source']
    if 'value' in per_round:
        if 'min' in per_round or 'max' in per_round:
            raise ValueError('hours_per_round: provide either value or min/max')
        low = high = number(per_round['value'], 'hours_per_round')
    else:
        low = number(per_round.get('min'), 'hours_per_round.min')
        high = number(per_round.get('max'), 'hours_per_round.max')
        if low > high:
            raise ValueError('hours_per_round: min exceeds max')
    for name in ['internal_hour_cost', 'minimum_effective_hourly', 'minimum_contribution']:
        if name in data:
            item = entry(data, name, currency)
            parsed[name] = number(item.get('value'), name)
            sources[name] = item['source']
        else:
            parsed[name] = None
    rounds = data.get('rounds', [0, 1, 2])
    if not isinstance(rounds, list) or not rounds or any(type(n) is not int or n < 0 for n in rounds) or len(set(rounds)) != len(rounds):
        raise ValueError('rounds: provide distinct nonnegative integers')
    note = data.get('note', '')
    if not isinstance(note, str):
        raise ValueError('note must be literal text')
    rows, details, warnings = [], [], []
    base_hours = parsed['actual_hours'] + parsed['remaining_hours']
    net = parsed['fee'] - parsed['direct_costs']
    for count in rounds:
        bounds = [('min', low), ('max', high)] if count and low != high else [('', low)]
        for bound, round_hours in bounds:
            label = str(count) + ('_' + bound if bound else '')
            total = base_hours + count * round_hours
            effective = net / total if total else None
            internal = total * parsed['internal_hour_cost'] if parsed['internal_hour_cost'] is not None else None
            contribution = net - internal if internal is not None else None
            row_warnings = ['zero_total_hours'] if not total else []
            assumptions = (note + '; ' if note else '') + 'sources: ' + '; '.join(name + '=' + ref for name, ref in sources.items())
            assumptions += '; actual hours supplied; remaining/round hours estimates; no additional direct costs modeled'
            if assumptions[:1] in ('=', '+', '-', '@', '\t', '\r', '\n') or assumptions.lstrip().startswith(('=', '+', '-', '@')):
                assumptions = "'" + assumptions
                if 'csv_text_escaped' not in warnings:
                    warnings.append('csv_text_escaped')
            rows.append({'round_extra': label, 'total_hours': compact(total),
                         'effective_hourly': amount(effective, currency, True) if effective is not None else 'unknown',
                         'direct_costs': amount(parsed['direct_costs'], currency),
                         'internal_time_cost': amount(internal, currency) if internal is not None else 'unknown',
                         'contribution': amount(contribution, currency) if contribution is not None else 'unknown',
                         'assumptions': assumptions})
            details.append({'scenario': label, 'round_hours': compact(round_hours),
                            'effective_hourly_unrounded': str(effective) if effective is not None else None,
                            'minimum_effective_hourly': relation(effective, parsed['minimum_effective_hourly']),
                            'minimum_contribution': relation(contribution, parsed['minimum_contribution']),
                            'warnings': row_warnings})
    return {'currency': currency, 'columns': COLUMNS, 'rows': rows, 'details': details,
            'sources': sources, 'warnings': warnings,
            'basis': 'managerial scenario; unchanged supplied fee/direct costs; estimates are not commitments'}

def calculate(data):
    try:
        with localcontext() as context:
            context.prec = 40
            return _calculate(data)
    except DecimalException:
        raise ValueError('Arithmetic exceeds supported decimal precision; review the input magnitudes') from None

def to_csv(result):
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(result['rows'])
    return output.getvalue()

def to_notes(result):
    """Summarize calculated states without inventing a recommendation or inputs."""
    lines = ['# Revision cost check', '',
             'Model: unchanged supplied fee and direct costs; estimated hours are scenarios.',
             'Hourly rate = (fee - direct costs) / total hours. Contribution also deducts supplied internal time cost.',
             'Amounts display two decimals; threshold states use unrounded values.', '']
    for row, detail in zip(result['rows'], result['details']):
        lines.append('- Scenario ' + detail['scenario'] + ': ' + row['total_hours'] + ' hours; '
                     + row['effective_hourly'] + '; contribution: ' + row['contribution']
                     + '; hourly threshold: ' + detail['minimum_effective_hourly']
                     + '; contribution threshold: ' + detail['minimum_contribution'] + '.')
        if detail['warnings']:
            lines.append('  Check: ' + ', '.join(detail['warnings']) + '.')
    if result['warnings']:
        lines.extend(['', 'Checks: ' + ', '.join(result['warnings']) + '.'])
    lines.extend(['', 'Unknown stays unknown; not_supplied means no threshold was provided.',
                  'This is a project scenario, not an accounting profit or an approved client price.'])
    return '\n'.join(lines) + '\n'

def unique_object(pairs):
    """Reject contradictory duplicate JSON keys at any object depth."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key: ' + key)
        result[key] = value
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='Canonical source-linked JSON input')
    output = parser.add_mutually_exclusive_group()
    output.add_argument('--json', action='store_true', help='Include unrounded scenario details and threshold states')
    output.add_argument('--notes', action='store_true', help='Print concise English Markdown checks')
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding='utf-8-sig'), parse_float=Decimal,
                          parse_constant=lambda token: (_ for _ in ()).throw(ValueError('Non-finite JSON number')),
                          object_pairs_hook=unique_object)
        result = calculate(data)
    except (ValueError, OSError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(to_notes(result) if args.notes else to_csv(result), end='')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
