# Report Rendering Specification

## Purpose

Transform EDA analysis results into structured, human-readable reports. DTOs live at the adapter layer; renderers produce HTML and plain-text output.

## Requirements

| ID | Requirement | Strength |
|----|-------------|----------|
| RR-1 | EDAReport MUST contain: `schema`, `profiling`, `quality`, `classification`, `metadata` sections | MUST |
| RR-2 | Each section DTO MUST be independently constructable and serializable to dict | MUST |
| RR-3 | HTML renderer MUST produce valid HTML5 with inline CSS (no external dependencies) | MUST |
| RR-4 | Text renderer MUST produce a monospace-formatted summary suitable for CLI/console | MUST |
| RR-5 | Renderers MUST escape HTML characters in column names and values | MUST |
| RR-6 | Reports SHALL include a timestamp and duration metadata field | SHOULD |

## Scenarios

### RR-1: Happy path — HTML rendering

- GIVEN a populated EDAReport with profiling, quality scores, and column classification
- WHEN `HtmlRenderer.render(report)` is called
- THEN valid HTML5 is returned containing an overview table, per-column profile tables, and quality score breakdown

### RR-2: Happy path — text rendering

- GIVEN the same EDAReport
- WHEN `TextRenderer.render(report)` is called
- THEN plain text is returned with the same information in a monospace layout

### RR-3: Edge case — special characters in column names

- GIVEN an EDAReport where a column is named `<script>alert(1)</script>`
- WHEN `HtmlRenderer.render(report)` is called
- THEN the rendered HTML contains `&lt;script&gt;alert(1)&lt;/script&gt;` (escaped)

### RR-4: Error case — empty report

- GIVEN an EDAReport with only metadata and no data sections
- WHEN rendering to HTML or text
- THEN the renderer produces a minimal report with "No data available" message
- AND no exception is raised

## Input / Output Contracts

| Input | Type | Output | Type |
|-------|------|--------|------|
| EDAReport | Domain DTO (`dict`-like) | HTML string | `str` |
| EDAReport | Domain DTO | Text string | `str` |

## Clean Architecture Layer Mapping

| Layer | Responsibility |
|-------|---------------|
| Adapters | EDAReport DTO, section DTOs (`ProfilingSection`, `QualitySection`, `ClassificationSection`, `ReportMetadata`) |
| Adapters | `HtmlRenderer`, `TextRenderer` implementations |
| Framework | Wiring, output file handling |

## Acceptance Criteria

- [ ] EDAReport to_dict / from_dict round-trip is lossless
- [ ] HTML report validates as HTML5 (no unclosed tags, no unescaped entities)
- [ ] Text report fits within 120-char width
- [ ] Report rendering completes under 1s for a 20-column profile
- [ ] Each section renders independently (section-level render methods)
