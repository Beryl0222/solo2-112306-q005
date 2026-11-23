"""检查采集资料的身份、形状和可交叉引用性。"""

import json
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def read_fixture(name):
    return json.loads((ROOT / "fixtures" / name).read_text(encoding="utf-8"))


class FixtureContractTests(unittest.TestCase):
    def test_record_manifest(self):
        manifest = read_fixture("manifest.json")
        primary = read_fixture("primary.json")
        revision = read_fixture("revision.json")
        self.assertEqual(manifest["fixture"], "expert_dispatch")
        self.assertEqual(manifest["records"], ["primary.json", "revision.json"])
        self.assertTrue(manifest["synthetic"])
        self.assertEqual(revision["replaces"], primary["capture"])
        self.assertNotEqual(revision["capture"], primary["capture"])

    def test_related_input_records(self):
        primary = read_fixture("primary.json")
        revision = read_fixture("revision.json")
        expert_ids = {e["id"] for e in primary["experts"]}
        caps = primary["priority_caps"]
        all_rows = {}
        for fragment in primary["microbatches"] + revision["arrivals"]:
            source = fragment["source"]
            for row in fragment["rows"]:
                self.assertEqual(np.asarray(row["vector"]).shape, (2,))
                self.assertFalse(row["scores"].keys() - expert_ids)
                self.assertLessEqual(row["priority"], caps[source]["priority"])
                self.assertLessEqual(max(row["scores"].values()), caps[source]["score"])
                self.assertNotIn(row["id"], all_rows)
                all_rows[row["id"]] = row
        for reply in revision["reply_scenarios"]:
            self.assertIn(reply["expert"], expert_ids)
            self.assertFalse(reply["rows_by_vector"].keys() - all_rows.keys())
