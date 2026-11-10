---
icon: lucide/file-pen-line
---

# Contribute documentation

Documentation lives next to the design sources so that changes can be reviewed in
the same pull request as the work they describe.

## Local workflow

1. Create and activate a Python virtual environment.
2. Install `requirements-docs.txt`.
3. Run `zensical serve` from the repository root.
4. Edit Markdown under `docs/` and review the live preview.
5. Before committing, run the same strict build used by CI:

```bash
zensical build --clean --strict
```

## Writing guidelines

- Document the current repository state, not an uncommitted plan.
- Put the source of truth close to the subsystem it describes.
- Give every image meaningful alternative text.
- Prefer relative links between documentation pages.
- Mark preliminary, unsafe, or unvalidated designs clearly.
- Keep headings descriptive so search results remain useful.
- Use Mermaid diagrams for architecture that changes with the source; use
  exported images for visual design work that cannot be represented clearly in
  text.

## How publishing works

Pull requests that change documentation run a strict build. After a change is
merged into `main`, the same workflow uploads the generated `site/` directory and
deploys it to GitHub Pages.

The generated `site/` directory is intentionally ignored. Do not commit it.

## Add a page

1. Create a Markdown file under the appropriate `docs/` section.
2. Add it to `nav` in `zensical.toml`.
3. Link it from an existing overview page when appropriate.
4. Run the strict build and correct broken links or configuration warnings.

