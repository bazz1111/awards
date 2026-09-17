# Record maintenance

[Home](../README.md)

This guide describes the file layout, lifecycle, and validation requirements for public candidate and award records. Only records published in this repository form part of its public candidate and award lists.

## Layout and lifecycle

```text
awards/<YYYY-MM>/batch.yaml
awards/<YYYY-MM>/<award-id>/
candidates/verified-pending/<entry-id>/
candidates/observation/<entry-id>/
    award.yaml
    citation.md
    recipients.md
    verification/record.yaml
    verification/statement.yaml        # required for a formal claim
    verification/statements/<id>.yaml  # only when retaining superseded statements
```

The last file layout applies to all three entry locations. A stable ID occurs in exactly one location. `observation` and `verified-pending` are pool names, not status values. The `verified-pending` pool contains formal candidates under active verification or with verification completed but written recipient confirmation still pending. The pool name alone does not establish successful verification; consult the record's status and evidence. An entry awaiting written recipient confirmation stays in candidates until the announcement requirements are met.

The **Eligible to claim** flags **Yes** and **Pending verification** in the [problem bank](../problems/README.md) are screening markers, separate from these pools and lifecycle statuses. Neither creates a formal nomination or public candidate record. A problem enters the public candidate list only when its record is published under `candidates/`.

| Location | Status |
| --- | --- |
| Observation candidates | `draft`, `under-verification`, `pending-recipient-confirmation` |
| Formal candidates | `under-verification`, `pending-recipient-confirmation` |
| Confirmed awards | `announced`, `disputed`, `paid`, `revoked` |

An award batch is created only for actual, verified, confirmed, announced awards. Revoked awards stay in their original batch: append `revocation` with the reason, evidence and verification failure point; preserve the original decision, recipients and verification. The problem bank is separate from award records.

## Source files

| File | Purpose |
| --- | --- |
| `award.yaml` | Problem, published decision, confirmed recipient contributions, evidence references, conflicts, lifecycle and revocation. |
| `citation.md` | English decision rationale, or a clearly marked candidate review narrative. |
| `recipients.md` | English attribution with placeholders before confirmation. |
| `verification/record.yaml` | Pinned source, toolchain and library, axiom audit, statement comparison, independent checkers, environment, isolation, attribution and external artifact pointers. May be `null` while review is pending; confirmed records require completed evidence. |
| `verification/statement.yaml` | Versioned formal statement, original problem source, definition reviews, pinned library and public review signatures. |

Both Markdown files must be written in English and include a nonempty `## English` section. Structured records use the English fields `title_en`, `reason_en`, `text_en`, and `note_en` where applicable. Examples are in [templates](templates/). Angle-bracket placeholders in advanced templates deliberately fail validation. The draft template is for adapting to real mathematical results; do not publish the synthetic example as a live entry.

The [award schema](../data/schema/award.schema.json), [verification schema](../data/schema/verification-record.schema.json), and [statement schema](../data/schema/statement.schema.json) are the authoritative field shapes. All record objects reject unknown fields. YAML aliases, duplicate keys, misplaced YAML files and record symlinks are rejected.

## Publication boundaries

- `decision` is `null` for candidates. Announced awards record only the published `level` (1–4) and an HTTPS `announcement` link. This is a record of a decision, not an instruction to calculate a grade.
- Each recipient has an `id`, `affiliation`, `contribution_en`, and `confirmation`. Describe the evidenced contribution without recording private agreements or payment arrangements. Unconfirmed identities use placeholders; confirmed identities require a matching public profile.
- Public `confirmation` and profile `publication_consent` links point to authorized attestations. Private signed documents, emails, addresses, payment details, and internal assessment materials never enter repository files or commits.
- Assessment calculations, dimension values, adjustments, and payment allocations are outside this public record format. Unknown structured fields are rejected. Reviewers must also inspect free text for private material.
- A formal evidence reference requires a statement even in candidates. Completed evidence is required for `pending-recipient-confirmation` and announced awards; failed or incomplete evidence may remain under review.
- Published statements cannot be edited in place. Retain the previous content under `verification/statements/<old-id>.yaml` with status `superseded`, issue a new active ID in `statement.yaml`, and set `supersedes` to the previous ID.
- CI checks recorded signatures, profiles and evidence consistency. Authority, independence, consent, current checker releases, safe versions, and mathematical equivalence require substantive review.

## Local commands and CI

Use Python 3.10 or later:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/manage.py validate
python scripts/manage.py links
python scripts/manage.py problems
python scripts/manage.py build
python scripts/manage.py check
python -m unittest discover -s tests -v
```

`validate` checks source schemas and cross-file business constraints. `links` checks local Markdown file links, reference links, images and heading anchors. External URL availability and raw HTML links are outside this offline check. `problems` checks the problem bank index in `problems/README.md` against the volume catalogs: consecutive numbering, anchors, links, titles, the status vocabulary and the credited status shape, eligibility and claim status, and the counts the index states about itself. The test suite runs the same check against the committed bank, so drift between the index and its catalogs fails CI. `build` validates and writes deterministic `data/*.json`; `check` compares the committed files with regeneration without modifying them. No timestamps or machine-local paths enter the generated data.

`python scripts/manage.py history --base <full-commit-sha>` compares published decisions, statements and retained award history with a Git base revision. CI runs this on PRs and pushes with an available base, using full history. It compares snapshots; reviewers must still check intermediate commits for private information and confirm business event dates.

The three workflows validate records and links, generate downloadable data artifacts, and check committed data consistency. They use read-only repository permissions and do not push generated commits. Submit source and generated JSON in one PR. This CI does not execute proof repositories, certify mathematical truth, or perform payouts. Large logs and formal artifacts belong in permanent external archives; store archive ID, SHA-256 and byte count only.

See [platform setup](platform-setup.md) for the GitHub settings that cannot be established by committing files.
