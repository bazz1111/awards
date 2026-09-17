"""Synthetic problem-bank fixtures; no real catalog content or review policy."""

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import manage  # noqa: E402


def record(identifier, title, status="Open", lean="No", eligible="No", attribution=None):
    rows = [f"| Current status | {status} |", f"| Lean proof | {lean} |",
            f"| Eligible to claim | {eligible} |"]
    if attribution:
        rows.append(f"| Attribution basis | {attribution} |")
    return (f'<a id="{identifier}"></a>\n\n## {identifier} · {title}\n\n'
            "| Field | Content |\n| --- | --- |\n" + "\n".join(rows) + "\n")


ALPHA = record("JSP-000001", "Alpha")
# The credited shape CONTRIBUTING.md fixes: the status alone, then the solver
# credits after "Proof contributors:" in the same field.
BETA = record("JSP-000002", "Beta", "Solved<br>Proof contributors: Synthetic Author",
              "Yes — [Lean source](https://example.invalid/beta.lean)", "Yes", "Synthetic basis")
GAMMA = record("JSP-000003", "Gamma", "Open")
DELTA = record("JSP-000004", "Delta", "Solved")
EPSILON = record("JSP-000005", "Epsilon")

VOLUME_ONE_HEADER = "# Mathematical problem bank · 1–3\n\n"
VOLUME_TWO_HEADER = "# Mathematical problem bank · 4–5\n\n"
VOLUME_ONE = VOLUME_ONE_HEADER + ALPHA + "\n" + BETA + "\n" + GAMMA
VOLUME_TWO = VOLUME_TWO_HEADER + DELTA + "\n" + EPSILON

ALPHA_ROW = "| JSP-000001 | [Alpha](catalog-0001-0003.md#JSP-000001) | Open | No | No | Unavailable |"
BETA_ROW = "| JSP-000002 | [Beta](catalog-0001-0003.md#JSP-000002) | Solved | Yes | Yes | Unclaimed |"
EPSILON_ROW = "| JSP-000005 | [Epsilon](catalog-0004-0005.md#JSP-000005) | Open | No | No | Unavailable |"

INDEX = f"""# Mathematical problem bank

This catalog contains **5 mathematical problems**.

Problems are numbered consecutively and grouped into volumes of 3 records (2 in the final volume), with a heading, a field table, and any review notes for each problem.

The 1 records with an **Attribution basis** row describe credits for the selected completed proof version.

## Volumes

| Problem range | File |
| --- | --- |
| 1–3 | [catalog-0001-0003.md](catalog-0001-0003.md) |
| 4–5 | [catalog-0004-0005.md](catalog-0004-0005.md) |

## Problem index

### Problems 1–3

| No. | Problem | Current status | Lean proof | Eligible to claim | Claim status |
| --- | --- | --- | --- | --- | --- |
{ALPHA_ROW}
{BETA_ROW}
| JSP-000003 | [Gamma](catalog-0001-0003.md#JSP-000003) | Open | No | No | Unavailable |

### Problems 4–5

| No. | Problem | Current status | Lean proof | Eligible to claim | Claim status |
| --- | --- | --- | --- | --- | --- |
| JSP-000004 | [Delta](catalog-0004-0005.md#JSP-000004) | Solved | No | No | Unavailable |
{EPSILON_ROW}
"""


class ProblemBankTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "problems").mkdir(parents=True)
        self.write("problems/README.md", INDEX)
        self.write("problems/catalog-0001-0003.md", VOLUME_ONE)
        self.write("problems/catalog-0004-0005.md", VOLUME_TWO)

    def write(self, relative, text):
        (self.root / relative).write_text(text, encoding="utf-8")

    def rewrite(self, relative, old, new):
        path = self.root / relative
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture does not contain {old!r}")
        self.write(relative, text.replace(old, new, 1))

    def assertRejects(self, message):
        with self.assertRaisesRegex(manage.InvalidRecord, message):
            manage.check_problems(self.root)

    def test_fixture_is_consistent(self):
        manage.check_problems(self.root)

    def test_index_must_list_every_documented_problem(self):
        self.rewrite("problems/README.md", "\n" + EPSILON_ROW, "")
        self.assertRejects("states 5 problems but lists 4 rows")

    def test_documented_total_is_enforced_against_the_volumes(self):
        self.rewrite("problems/README.md", "**5 mathematical problems**", "**6 mathematical problems**")
        self.assertRejects("must cover 6 problems")

    def test_numbering_must_be_consecutive(self):
        self.rewrite("problems/README.md", "| JSP-000003 |", "| JSP-000006 |")
        self.assertRejects("must run consecutively")

    def test_row_must_link_its_own_anchor(self):
        self.rewrite("problems/README.md",
                     "[Gamma](catalog-0001-0003.md#JSP-000003)",
                     "[Gamma](catalog-0001-0003.md#JSP-000002)")
        self.assertRejects("must link to its own anchor")

    def test_row_must_link_the_volume_covering_its_number(self):
        self.rewrite("problems/README.md",
                     "[Alpha](catalog-0001-0003.md#JSP-000001)",
                     "[Alpha](catalog-0004-0005.md#JSP-000001)")
        self.assertRejects("volume covering its number")

    def test_index_title_must_match_the_catalog_heading(self):
        self.rewrite("problems/README.md", "[Alpha]", "[Alfa]")
        self.assertRejects("title differs from the catalog heading")

    def test_status_vocabulary_is_closed(self):
        # "Progress" was a third status in an earlier presentation of the bank.
        # CONTRIBUTING.md now allows only Open or Solved, so a curator who
        # reintroduces it must be stopped rather than silently accepted.
        self.rewrite("problems/README.md",
                     "| Open | No | No | Unavailable |\n\n### Problems 4–5",
                     "| Progress | No | No | Unavailable |\n\n### Problems 4–5")
        self.assertRejects("Current status must be one of")

    def test_eligibility_vocabulary_is_closed(self):
        self.rewrite("problems/README.md", "| No | Unavailable |\n\n### Problems 4–5",
                     "| Not yet | Unavailable |\n\n### Problems 4–5")
        self.assertRejects("Eligible to claim must be one of")

    def test_eligible_yes_requires_a_solved_lean_proof(self):
        self.rewrite("problems/README.md", EPSILON_ROW,
                     EPSILON_ROW.replace("| Open | No | No | Unavailable |",
                                         "| Open | No | Yes | Unclaimed |"))
        self.assertRejects("Eligible to claim is Yes")

    def test_eligible_no_cannot_hide_a_solved_lean_proof(self):
        self.rewrite("problems/README.md", BETA_ROW,
                     BETA_ROW.replace("| Solved | Yes | Yes | Unclaimed |",
                                      "| Solved | Yes | No | Unavailable |"))
        self.assertRejects("Eligible to claim is No")

    def test_pending_verification_may_hold_a_solved_proof(self):
        # Documented as a screening judgement, so it is not derived from the row.
        self.rewrite("problems/README.md", EPSILON_ROW,
                     EPSILON_ROW.replace("| Open | No | No | Unavailable |",
                                         "| Open | No | Pending verification | Unavailable |"))
        self.write("problems/catalog-0004-0005.md", VOLUME_TWO_HEADER + DELTA + "\n"
                   + record("JSP-000005", "Epsilon", eligible="Pending verification"))
        manage.check_problems(self.root)

    def test_claim_status_must_follow_eligibility(self):
        self.rewrite("problems/README.md", ALPHA_ROW,
                     ALPHA_ROW.replace("| No | Unavailable |", "| No | Unclaimed |"))
        self.assertRejects("contradicts Eligible to claim")

    def test_eligibility_must_repeat_in_the_detail_table(self):
        self.write("problems/catalog-0001-0003.md", VOLUME_ONE_HEADER + ALPHA + "\n" + BETA + "\n"
                   + GAMMA.replace("| Eligible to claim | No |", "| Eligible to claim | Yes |"))
        self.assertRejects("must repeat Eligible to claim")

    def test_detail_status_must_match_the_index_status(self):
        self.write("problems/catalog-0001-0003.md", VOLUME_ONE_HEADER + ALPHA + "\n" + BETA + "\n"
                   + GAMMA.replace("| Current status | Open |", "| Current status | Stalled |"))
        self.assertRejects("detail Current status must be 'Open'")

    def test_status_scope_note_is_rejected(self):
        # A bare " — " extension was an earlier presentation. CONTRIBUTING.md
        # allows only the fixed "Proof contributors:" marker to extend the status.
        self.write("problems/catalog-0001-0003.md", VOLUME_ONE_HEADER + ALPHA + "\n" + BETA + "\n"
                   + GAMMA.replace("| Current status | Open |",
                                   "| Current status | Open — synthetic scope note |"))
        self.assertRejects("detail Current status must be 'Open'")

    def test_solver_attribution_prefix_is_rejected(self):
        # "Solved by …" predates the marker; only the marker form is documented.
        self.write("problems/catalog-0001-0003.md", VOLUME_ONE_HEADER + ALPHA + "\n" + BETA + "\n"
                   + GAMMA)
        self.rewrite("problems/catalog-0001-0003.md",
                     "| Current status | Solved<br>Proof contributors: Synthetic Author |",
                     "| Current status | Solved by Synthetic Author |")
        self.assertRejects("detail Current status must be 'Solved'")

    def test_credited_detail_status_is_accepted(self):
        # The documented credited shape: the status, then the fixed marker.
        self.write("problems/catalog-0001-0003.md", VOLUME_ONE_HEADER + ALPHA + "\n" + BETA + "\n"
                   + GAMMA.replace("| Current status | Open |",
                                   "| Current status | Open<br>Proof contributors: Synthetic Author |"))
        manage.check_problems(self.root)

    def test_stale_eligibility_marker_is_rejected(self):
        # A former "Yes" screening flag left behind by an earlier edit.
        self.write("problems/catalog-0001-0003.md", VOLUME_ONE_HEADER
                   + record("JSP-000001", "Alpha",
                            lean="No. Yes — [Lean source](https://example.invalid/alpha.lean)")
                   + "\n" + BETA + "\n" + GAMMA)
        self.assertRejects("or extend it with ' — '")

    def test_documented_qualification_wording_is_accepted(self):
        self.write("problems/catalog-0004-0005.md", VOLUME_TWO_HEADER + DELTA + "\n"
                   + record("JSP-000005", "Epsilon",
                            lean="Reported; standalone Lean source not located. "
                                 "The reviewed commentary derives this problem from elsewhere."))
        self.rewrite("problems/README.md", EPSILON_ROW,
                     EPSILON_ROW.replace("| Open | No | No |",
                                         "| Open | Reported; standalone source not located | No |"))
        manage.check_problems(self.root)

    def test_missing_detail_record_is_rejected(self):
        self.write("problems/catalog-0001-0003.md", VOLUME_ONE_HEADER + ALPHA + "\n" + BETA)
        self.assertRejects("missing detail record for JSP-000003")

    def test_catalog_records_must_stay_in_order(self):
        self.write("problems/catalog-0004-0005.md", VOLUME_TWO_HEADER + EPSILON + "\n" + DELTA)
        self.assertRejects("must run consecutively")

    def test_documented_attribution_count_must_match(self):
        self.rewrite("problems/README.md",
                     "The 1 records with an **Attribution basis** row",
                     "The 2 records with an **Attribution basis** row")
        self.assertRejects("states 2 records with an Attribution basis row")

    def test_final_volume_claim_must_match(self):
        self.rewrite("problems/README.md", "(2 in the final volume)", "(1 in the final volume)")
        self.assertRejects("final volume must hold 1 problems")

    def test_volume_table_must_match_its_section_heading(self):
        self.rewrite("problems/README.md", "| 4–5 |", "| 4–6 |")
        self.assertRejects("does not match volume range")


class RepositoryProblemBankTests(unittest.TestCase):
    """Run the same check against the bank this repository actually publishes."""

    def test_index_matches_the_committed_catalogs(self):
        volumes, rows, _ = manage.problem_index(ROOT)
        self.assertGreater(len(volumes), 0, "no volume range was read from the index")
        self.assertGreater(len(rows), 0, "no problem row was read from the index")
        try:
            manage.check_problems(ROOT)
        except manage.InvalidRecord as error:
            self.fail(str(error))


if __name__ == "__main__":
    unittest.main()
