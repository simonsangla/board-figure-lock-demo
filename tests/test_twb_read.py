"""twb-read: reads calculations, tables, joins and relationships from a Tableau file alone,
and flags a Tableau calculation that differs from the defined metric. Stdlib only, no network."""
import importlib.machinery
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TWB_READ = os.path.join(ROOT, "bin", "twb-read")
DEMO = os.path.join(ROOT, "board-figure-lock", "tableau", "revenue_demo.twb")
MAP_FILE = os.path.join(ROOT, "board-figure-lock", "tableau", "map.json")

loader = importlib.machinery.SourceFileLoader("twb_read", TWB_READ)
tr = importlib.util.module_from_spec(importlib.util.spec_from_loader("twb_read", loader))
loader.exec_module(tr)

METRICS = {"revenue": {"expr": "sum(actual_revenue)"}}

# Same layout as Tableau's own 2024.2 sample (tableau/connector-plugin-sdk, tdvt/TDVT Results.twb):
# the wrapper tag carries a feature-flag prefix, the inner object/relationship tags do not.
RELATIONSHIP_TWB = """<workbook version='18.1'><datasources>
<datasource caption='orders' inline='true' name='textscan.1'>
  <connection class='federated'><named-connections><named-connection name='t'>
    <connection class='textscan' filename='orders.csv' /></named-connection></named-connections>
    <relation connection='t' name='orders.csv' table='[orders#csv]' type='table' /></connection>
  <_.fcp.ObjectModelEncapsulateLegacy.true...object-graph>
    <objects>
      <object caption='orders.csv' id='orders_A'><properties context=''>
        <relation connection='t' name='orders.csv' table='[orders#csv]' type='table' /></properties></object>
      <object caption='customers.csv' id='customers_B'><properties context=''>
        <relation connection='t' name='customers.csv' table='[customers#csv]' type='table' /></properties></object>
    </objects>
    <relationships><relationship>
      <expression op='='><expression op='[customer_id]' /><expression op='[id]' /></expression>
      <first-end-point object-id='orders_A' /><second-end-point object-id='customers_B' unique-key='true' />
    </relationship></relationships>
  </_.fcp.ObjectModelEncapsulateLegacy.true...object-graph>
</datasource></datasources></workbook>"""


class TestRead(unittest.TestCase):
    def test_demo_lists_tables_join_calculations_and_skips_parameters(self):
        (ds,) = tr.read(tr.load_twb(DEMO))
        self.assertEqual([t["table"] for t in ds["tables"]], ["[main].[fct_monthly_revenue]", "[main].[products]"])
        self.assertEqual(ds["joins"], [{"join": "inner", "on": "[fct_monthly_revenue].[product_id] = [products].[product_id]"}])
        self.assertEqual([c["name"] for c in ds["calculations"]], ["Revenue", "Revenue incl. tax"])
        self.assertEqual(ds["connections"], [{"class": "duckdb", "dbname": "demo.duckdb", "schema": "main"}])

    def test_twbx_is_read_from_the_zip(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "demo.twbx")
            with zipfile.ZipFile(path, "w") as z:
                z.write(DEMO, "demo.twb")
                z.writestr("Data/extract.hyper", b"not read")
            self.assertEqual(tr.read(tr.load_twb(path)), tr.read(tr.load_twb(DEMO)))

    def test_relationships_behind_a_prefixed_object_graph(self):
        (ds,) = tr.read(ET.fromstring(RELATIONSHIP_TWB))
        self.assertEqual(ds["relationships"], [{"left": "orders.csv", "right": "customers.csv", "on": "[customer_id] = [id]"}])
        self.assertEqual({t["table"] for t in ds["tables"]}, {"[orders#csv]", "[customers#csv]"})


class TestCheck(unittest.TestCase):
    def setUp(self):
        self.src = tr.read(tr.load_twb(DEMO))

    def verdict(self, mapping):
        return tr.check(self.src, mapping, METRICS)[0][3]

    def test_same_definition_matches(self):
        self.assertEqual(self.verdict({"revenue": {"calculation": "Revenue", "fields": {"[actual_revenue]": "actual_revenue"}}}), "MATCH")

    def test_different_definition_is_an_alert(self):
        self.assertEqual(self.verdict({"revenue": {"calculation": "Revenue incl. tax", "fields": {"[actual_revenue]": "actual_revenue"}}}), "MISMATCH")

    def test_unmapped_metric_is_missing(self):
        self.assertEqual(self.verdict({}), "MISSING")
        self.assertEqual(self.verdict({"revenue": {"calculation": "No such calc"}}), "MISSING")

    def test_cli_exit_code_follows_the_verdict(self):
        ok = subprocess.run([TWB_READ, DEMO, "--check", MAP_FILE], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        self.assertIn("revenue\tsum(actual_revenue)\tSUM([actual_revenue])\tMATCH", ok.stdout)


def ds_xml(caption, table, formula, extra=""):
    return ("<datasource caption='%s' name='%s'><connection class='federated'>"
            "<relation name='t' table='[main].[%s]' type='table'/></connection>%s"
            "<column caption='Revenue' name='[Calculation_1]'><calculation class='tableau' formula='%s'/></column>"
            "</datasource>") % (caption, caption, table, extra, formula)


def wb(*sources):
    return tr.read(ET.fromstring("<workbook><datasources>%s</datasources></workbook>" % "".join(sources)))


METRICS_T = {"revenue": {"expr": "sum(actual_revenue)", "table": "fct_monthly_revenue"}}
MAP = {"revenue": {"calculation": "Revenue", "fields": {"[actual_revenue]": "actual_revenue"}}}


class TestReviewFindings(unittest.TestCase):
    """One test per finding of an earlier code review."""

    def test_same_caption_in_two_datasources_is_ambiguous_not_match(self):
        src = wb(ds_xml("A", "fct_monthly_revenue", "SUM([actual_revenue])"), ds_xml("B", "fct_monthly_revenue", "SUM([y])"))
        self.assertEqual(tr.check(src, MAP, METRICS_T)[0][3], "AMBIGUOUS")
        pick = {"revenue": dict(MAP["revenue"], datasource="A")}
        self.assertEqual(tr.check(src, pick, METRICS_T)[0][3], "MATCH")

    def test_same_formula_on_another_table_is_mismatch(self):
        src = wb(ds_xml("A", "stg_forecast", "SUM([actual_revenue])"))
        row = tr.check(src, MAP, METRICS_T)[0]
        self.assertEqual(row[3], "MISMATCH")
        self.assertIn("does not read fct_monthly_revenue", row[4])

    def test_prefixed_relation_join_is_read_once(self):
        join = ("<_.fcp.ObjectModelEncapsulateLegacy.false...relation join='inner' type='join'><clause type='join'>"
                "<expression op='='><expression op='[a].[k]'/><expression op='[b].[k]'/></expression></clause>"
                "<relation name='a' table='[main].[a]' type='table'/><relation name='b' table='[main].[b]' type='table'/>"
                "</_.fcp.ObjectModelEncapsulateLegacy.false...relation>")
        twice = "<objects><object id='o'><properties>%s</properties></object></objects>" % join.replace("false", "true")
        (ds,) = wb(ds_xml("A", "x", "1", extra="<connection class='federated'>%s</connection>%s" % (join, twice)))
        self.assertEqual(ds["joins"], [{"join": "inner", "on": "[a].[k] = [b].[k]"}])
        self.assertTrue({"[main].[a]", "[main].[b]"} <= {t["table"] for t in ds["tables"]})

    def test_qualified_field_and_literals(self):
        f = {"[actual_revenue]": "actual_revenue"}
        self.assertEqual(tr.norm("SUM([duckdb.demo].[actual_revenue])", f), tr.norm("sum(actual_revenue)", {}))
        self.assertNotEqual(tr.norm("IF [r]='North East' THEN 1 END", {}), tr.norm("IF [r]='northeast' THEN 1 END", {}))
        self.assertEqual(tr.norm("SUM([ds].[Sales])", {"[ds].[Sales]": "actual_revenue"}), "sum(actual_revenue)")
        self.assertEqual(tr.norm("[a] + [b]", {"[a]": "[b]", "[b]": "c"}), "[b]+c")  # one pass, no chaining

    def test_unary_operator_is_kept(self):
        self.assertEqual(tr.clause(ET.fromstring("<expression op='NOT'><expression op='[a]'/></expression>")), "NOT([a])")

    def test_map_errors_are_clear(self):
        with self.assertRaises(SystemExit):
            tr.check(tr.read(tr.load_twb(DEMO)), {"revenu": {"calculation": "Revenue"}}, METRICS)
        self.assertEqual(tr.check(tr.read(tr.load_twb(DEMO)), {"revenue": {"fields": {}}}, METRICS)[0][3], "MISSING")

    def test_dtd_is_refused(self):
        with self.assertRaises(SystemExit):
            tr.parse(b"<?xml version='1.0'?><!DOCTYPE w [<!ENTITY a 'x'>]><workbook>&a;</workbook>")

    def test_check_json(self):
        out = subprocess.run([TWB_READ, DEMO, "--check", MAP_FILE, "--json"], capture_output=True, text=True)
        self.assertEqual(json.loads(out.stdout)[0]["verdict"], "MATCH")


if __name__ == "__main__":
    unittest.main()
