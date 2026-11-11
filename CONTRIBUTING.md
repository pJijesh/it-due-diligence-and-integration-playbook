# Contributing

Thanks for taking an interest. This is a small, deliberately plain tool and playbook: standard library only, deterministic output, and documents that read as neutral practitioner guidance. Changes should keep it that way.

## Ground rules

1. **No real data, ever.** Do not commit material from a real deal, target, buyer, supplier or person. The example is fictional, and any new example should use invented names and figures.
2. **Standard library only** for the `dd_playbook` package. Test tooling is fine under the `dev` extra.
3. **Deterministic output.** The same inputs must give byte-identical files. Sort anything whose order matters and never write timestamps into outputs.
4. **Vendor-neutral.** Say "ERP" or "finance system", not a product name. Do not quote prices, standards text or legal wording. If a document states a fact about a law or standard, say where it was verified.
5. **Not legal, tax or HR advice.** Keep the scope note in the documents. Findings go to the relevant adviser to interpret.
6. **British English, plain tone, no long dashes.** A test fails if an em dash or en dash appears in any text file. Use commas, colons, full stops or brackets.

## Development setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q
```

## Changing the question bank

The bank is `data/question-bank.csv` with the columns `id, domain, question, why_it_matters, evidence_to_request, weight, red_flag_if`. Keep questions answerable on the 0 to 4 scale, specific and evidence-based. Write each `red_flag_if` as an observation that could be seen, not a feeling. If you add or remove questions, regenerate the example outputs and update the counts quoted in `docs/due-diligence-guide.md` (the tests check the bank, not the prose).

## Changing behaviour

The files under `examples/output/` are compared with a fresh run by the tests, so a behaviour change needs them regenerated in the same commit:

```bash
python scripts/regenerate_examples.py
python -m pytest -q
```

If figures in the README or `docs/worked-example.md` change, update them from the new output. Every figure in the documentation must come from a real run.

The diagrams are Mermaid sources in `docs/images/`. Render them with the Mermaid CLI and commit both files:

```bash
mmdc -i docs/images/workflow.mmd -o docs/images/workflow.svg
mmdc -i docs/images/100-day-timeline.mmd -o docs/images/100-day-timeline.svg
```

## Pull request checklist

- [ ] Tests added or updated and passing
- [ ] Example outputs regenerated if behaviour changed
- [ ] Documentation figures updated from real output
- [ ] No real names, data or credentials in the diff
- [ ] No long dashes, no product names, scope note kept

## Reporting concerns

The tool reads local CSV and JSON files and makes no network calls. If you find a way for crafted input to cause harm, please open a private security advisory on the repository rather than a public issue.
