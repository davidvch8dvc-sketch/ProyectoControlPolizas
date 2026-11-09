# ProyectoControlPolizas

This is a data/input repository, not a codebase. There is no source code, no package manager, no build, test, lint, or typecheck tooling, and no entrypoints.

## Contents

- `Insumos_Control_Polizas/Maestro_Clientes.xlsx` — master client list.
- `Insumos_Control_Polizas/polizas/` — PDF insurance policies, named `Poliza_<PREFIX>-2026-<NNNN>.pdf`.
  - Prefixes present: `AIS` (5 files), `PCS` (9 files), `SPC` (6 files) — 20 PDFs total.

## Guidance for agents

- Do not invent or run `npm`, `pip`, `mvn`, `dotnet`, or similar commands — none of these toolchains are configured here.
- There are no tests to run, no CI workflows, and no pre-commit hooks.
- If you need to modify or consume these files, treat them as static inputs: read the Excel with a spreadsheet library and parse the PDFs with a PDF library of your choosing; nothing in this repo dictates which.
- No branches, PRs, or release process are documented in this repo.
