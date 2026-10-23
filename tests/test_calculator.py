"""Regression tests for observable numeric and command-line behavior."""
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 ManojRollo
from pathlib import Path
import csv,importlib.util,io,json,subprocess,sys,tempfile,unittest

sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'skills/revision-cost-check/scripts/calculate.py'

def money(value,source='R1',currency='EUR'):
    return {'value':str(value),'currency':currency,'source':source}

def hours(value,source='R2'):
    return {'value':str(value),'unit':'hours','source':source}

def example():
    return {'fee':money(1200),'direct_costs':money(120),'actual_hours':hours(20),'remaining_hours':hours(4),'hours_per_round':hours(3,'R3'),'internal_hour_cost':money(30,'R4'),'minimum_effective_hourly':money(40,'R4'),'minimum_contribution':money(250,'R4')}

class CalculatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('revision_calculator',SCRIPT)
        cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)

    def test_demo_arithmetic_and_distinct_threshold_boundaries(self):
        result=self.module.calculate(example());rows=result['rows']
        self.assertEqual([r['total_hours'] for r in rows],['24','27','30'])
        self.assertEqual([r['effective_hourly'] for r in rows],['45.00 EUR/h','40.00 EUR/h','36.00 EUR/h'])
        self.assertEqual([r['contribution'] for r in rows],['360.00 EUR','270.00 EUR','180.00 EUR'])
        self.assertEqual(result['details'][1]['minimum_effective_hourly'],'at')
        self.assertEqual(result['details'][1]['minimum_contribution'],'above')
        self.assertEqual(result['details'][2]['minimum_contribution'],'below')

    def test_missing_internal_cost_does_not_become_zero(self):
        data=example();del data['internal_hour_cost']
        result=self.module.calculate(data)
        self.assertTrue(all(r['internal_time_cost']=='unknown' and r['contribution']=='unknown' for r in result['rows']))
        self.assertEqual(result['details'][0]['minimum_contribution'],'unknown')

    def test_range_preserves_both_extremes_without_midpoint(self):
        data=example();data['hours_per_round']={'min':'2','max':'5','unit':'hours','source':'R3'}
        rows=self.module.calculate(data)['rows']
        self.assertEqual([(r['round_extra'],r['total_hours']) for r in rows],[('0','24'),('1_min','26'),('1_max','29'),('2_min','28'),('2_max','34')])

    def test_zero_baseline_does_not_block_valid_extra_rounds(self):
        data=example();data['actual_hours']=hours(0);data['remaining_hours']=hours(0)
        result=self.module.calculate(data)
        self.assertEqual(result['rows'][0]['effective_hourly'],'unknown')
        self.assertIn('zero_total_hours',result['details'][0]['warnings'])
        self.assertEqual(result['rows'][1]['effective_hourly'],'360.00 EUR/h')

    def test_costs_exceeding_fee_produce_signed_results(self):
        data=example();data['fee']=money(100);data['direct_costs']=money(200)
        row=self.module.calculate(data)['rows'][0]
        self.assertEqual(row['effective_hourly'],'-4.17 EUR/h')
        self.assertEqual(row['contribution'],'-820.00 EUR')

    def test_missing_threshold_has_no_verdict(self):
        data=example();del data['minimum_effective_hourly'];del data['minimum_contribution']
        details=self.module.calculate(data)['details']
        self.assertTrue(all(d['minimum_effective_hourly']=='not_supplied' and d['minimum_contribution']=='not_supplied' for d in details))

    def test_rejects_missing_or_invalid_input_without_silent_defaults(self):
        variants=[]
        for field in ['fee','direct_costs','actual_hours','remaining_hours','hours_per_round']:
            d=example();del d[field];variants.append(d)
        for val in ['-1','NaN','Infinity',True,'1,200','abc','1_000','١٢','+1','.5','1e3']:
            d=example();d['fee']['value']=val;variants.append(d)
        d=example();d['actual_hours']['unit']='minutes';variants.append(d)
        d=example();d['direct_costs']['currency']='USD';variants.append(d)
        d=example();d['internal_hour_cost']['currency']='USD';variants.append(d)
        d=example();d['minimum_effective_hourly']['currency']='USD';variants.append(d)
        d=example();d['fee']['source']='';variants.append(d)
        d=example();d['rounds']=[True];variants.append(d)
        d=example();d['rounds']=[1.5];variants.append(d)
        d=example();d['hours_per_round']={'min':'5','max':'2','unit':'hours','source':'R3'};variants.append(d)
        for data in variants:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):self.module.calculate(data)

    def test_requested_rounds_are_preserved(self):
        data=example();data['rounds']=[0,4]
        self.assertEqual([r['round_extra'] for r in self.module.calculate(data)['rows']],['0','4'])

    def test_csv_quotes_and_escapes_supplied_text_but_keeps_signed_numbers(self):
        data=example();data['note']='=SUM(A1:A5), "literal"';data['fee']=money(100);data['direct_costs']=money(200)
        result=self.module.calculate(data);text=self.module.to_csv(result)
        rows=list(csv.DictReader(io.StringIO(text)))
        self.assertEqual(len(rows),3)
        self.assertTrue(rows[0]['assumptions'].startswith("'=SUM(A1:A5)"))
        self.assertIn('csv_text_escaped',result['warnings'])
        self.assertEqual(rows[0]['effective_hourly'],'-4.17 EUR/h')
        self.assertIn('R1',rows[0]['assumptions'])

    def test_thresholds_use_unrounded_values(self):
        data=example();data['fee']=money('39.9999');data['direct_costs']=money(0)
        data['actual_hours']=hours(1);data['remaining_hours']=hours(0)
        data['minimum_effective_hourly']=money(40)
        result=self.module.calculate(data)
        self.assertEqual(result['rows'][0]['effective_hourly'],'40.00 EUR/h')
        self.assertEqual(result['details'][0]['minimum_effective_hourly'],'below')

    def test_each_currency_is_explicit_and_same_code_is_preserved(self):
        data=example()
        for item in data.values():
            if isinstance(item,dict) and 'currency' in item:item['currency']='USD'
        self.assertEqual(self.module.calculate(data)['rows'][0]['effective_hourly'],'45.00 USD/h')
        for code in [None,'eur','EU','EURO','€','１２３','123']:
            data=example();data['fee']['currency']=code
            with self.subTest(code=code),self.assertRaises(ValueError):self.module.calculate(data)

    def test_zero_internal_cost_is_supplied_and_calculates_contribution(self):
        data=example();data['internal_hour_cost']=money(0)
        row=self.module.calculate(data)['rows'][0]
        self.assertEqual(row['internal_time_cost'],'0.00 EUR')
        self.assertEqual(row['contribution'],'1080.00 EUR')

    def test_csv_literal_note_handles_formula_prefixes_and_newlines(self):
        for prefix in ['=','+','-','@','\t','\r','\n','  =']:
            data=example();data['note']=prefix+'literal, "quoted"\nnext line'
            result=self.module.calculate(data)
            row=list(csv.DictReader(io.StringIO(self.module.to_csv(result))))[0]
            self.assertTrue(row['assumptions'].startswith("'"+prefix))
            self.assertIn('next line',row['assumptions'])

    def invoke(self,path,*args):
        return subprocess.run([sys.executable,'-B',str(SCRIPT),str(path),*args],capture_output=True,text=True,encoding='utf-8')

    def test_cli_computes_real_csv_and_does_not_write_input_directory(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".test-") as directory:
            target=Path(directory)/'input.json';target.write_text(json.dumps(example()),encoding='utf-8')
            before=target.read_bytes()
            result=self.invoke(target)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(len(list(csv.DictReader(io.StringIO(result.stdout)))),3)
            self.assertEqual(target.read_bytes(),before)
            self.assertEqual([p.name for p in Path(directory).iterdir()],['input.json'])

    def test_cli_reports_invalid_json_nonfinite_and_missing_file_cleanly(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".test-") as directory:
            target=Path(directory)/'input.json'
            for payload in ['{broken','{"fee": NaN}','[]','null']:
                target.write_text(payload,encoding='utf-8')
                result=self.invoke(target)
                self.assertEqual(result.returncode,2,result.stdout)
                self.assertEqual(result.stdout,'')
                self.assertIn('error',json.loads(result.stderr))
                self.assertNotIn('Traceback',result.stderr)
            result=self.invoke(Path(directory)/'absent.json')
            self.assertEqual(result.returncode,2)
            self.assertIn('error',json.loads(result.stderr))

    def test_cli_json_preserves_details_and_accepts_utf8_bom(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".test-") as directory:
            target=Path(directory)/'input.json';target.write_text(json.dumps(example()),encoding='utf-8-sig')
            result=self.invoke(target,'--json')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['details'][1]['minimum_effective_hourly'],'at')

    def test_short_notes_report_unknown_cost_and_separate_thresholds(self):
        data=example();del data['internal_hour_cost']
        notes=self.module.to_notes(self.module.calculate(data))
        self.assertIn('contribution: unknown',notes)
        self.assertIn('hourly threshold: at',notes)
        self.assertIn('contribution threshold: unknown',notes)
        self.assertIn('unchanged',notes)

    def test_cli_notes_selects_notes_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".test-") as directory:
            target=Path(directory)/'input.json';target.write_text(json.dumps(example()),encoding='utf-8')
            result=self.invoke(target,'--notes')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('45.00 EUR/h',result.stdout)
            self.assertIn('below',result.stdout)

    def test_duplicate_json_keys_fail_instead_of_choosing_a_value(self):
        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".test-") as directory:
            target=Path(directory)/'input.json'
            payload=json.dumps(example())
            payload=payload[:-1]+',"rounds":[0],"rounds":[9]}'
            target.write_text(payload,encoding='utf-8')
            result=self.invoke(target)
            self.assertEqual(result.returncode,2)
            self.assertIn('Duplicate',json.loads(result.stderr)['error'])

if __name__=='__main__':unittest.main(verbosity=2)
