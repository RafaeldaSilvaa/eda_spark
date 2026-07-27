# AI Commentary Specification

## Purpose

The AI Commentary capability adds a staff-level AI co-analyst layer on top of the deterministic EDA report. It generates per-section natural-language commentary for all 9 report sections plus a cross-cutting executive analysis. The heuristic engine remains the baseline — AI commentary enhances but never replaces deterministic output.

## Requirements

### Requirement: AI Commentary Generation

When `ai_enabled=True` and OmniRoute is reachable, the system MUST generate per-section commentary for every EDA report section AND an executive analysis. The system prompt MUST instruct the model to act as a staff-level data engineer/analyst with 15+ years experience, capable of identifying non-obvious patterns, suggesting hypotheses, and extracting business implications.

#### Scenario: Per-section commentary produced

- GIVEN an EDAReport with all 9 sections populated AND `ai_enabled=True` AND OmniRoute reachable
- WHEN `AnalysisPresenter.present()` completes
- THEN each section SHALL have AI commentary in `AiCommentary`
- AND the executive analysis SHALL identify cross-cutting patterns

#### Scenario: Prompt persona applied

- GIVEN a prompt sent to OmniRoute
- THEN the system prompt MUST encode a staff-level data engineer/analyst persona with 15+ years experience
- AND request critical thinking, non-obvious pattern identification, and business implications

### Requirement: Embedded Runtime — Zero Config

The system SHALL bundle Node.js and install/start OmniRoute automatically — no user setup required beyond `pip install spark-eda`.

#### Scenario: First-use lazy install

- GIVEN a fresh `pip install spark-eda` with no prior OmniRoute installation
- WHEN `ai_enabled=True` and the first EDA analysis runs
- THEN the system SHALL find the bundled Node.js (from `node-bin`), run `npm install omniroute` in the package cache directory, and start the OmniRoute subprocess on `localhost:20128`
- AND subsequent runs SHALL reuse the cached installation

#### Scenario: Lazy start

- GIVEN `ai_enabled=True`
- WHEN `EDAConfig` is created
- THEN OmniRoute SHALL NOT start until the first AI call
- AND the subprocess SHALL be managed via `atexit` for cleanup

#### Scenario: Install failure

- GIVEN the npm install of `omniroute` fails (npm registry unreachable, disk full)
- WHEN the AI call is attempted
- THEN a warning SHALL be logged AND the report SHALL render without commentary

#### Scenario: Subprocess healthcheck timeout

- GIVEN OmniRoute subprocess starts but does not respond on `localhost:20128` within 30 seconds
- WHEN the AI call is attempted
- THEN a warning SHALL be logged AND the report SHALL render without commentary

### Requirement: Graceful Degradation

The system SHALL degrade gracefully without crashing when OmniRoute is unavailable or disabled.

#### Scenario: OmniRoute unreachable

- GIVEN `ai_enabled=True` AND OmniRoute is unreachable (connection refused, DNS failure)
- WHEN analysis runs
- THEN a warning SHALL be logged AND the report SHALL render without commentary

#### Scenario: HTTP errors

- GIVEN OmniRoute returns an HTTP error (timeout, 4xx, or 5xx)
- WHEN the client receives the error
- THEN a warning SHALL be logged AND execution SHALL continue with empty commentary

#### Scenario: Disabled via config

- GIVEN `ai_enabled=False` in `EDAConfig`
- WHEN `AnalysisPresenter.present()` runs
- THEN no call to OmniRoute SHALL be made AND `AiCommentary` SHALL be `None`

### Requirement: Timeout Configuration

The HTTP client SHALL support a configurable timeout with a default of 30 seconds.

#### Scenario: Default timeout

- GIVEN no custom timeout is configured
- WHEN `OmniRouteClient` makes a request
- THEN the HTTP call SHALL timeout after 30 seconds

#### Scenario: Custom timeout

- GIVEN `EDAConfig.omniroute_timeout` specifies a custom value
- WHEN `OmniRouteClient` makes a request
- THEN the configured duration SHALL be used

### Requirement: Renderer Integration

All three renderers MUST display AI commentary when present and MUST NOT show an AI section when absent.

#### Scenario: Commentary rendered

- GIVEN `AiCommentary` is present
- WHEN rendering to HTML, Text, and JSON
- THEN each section SHALL display commentary inline, executive analysis SHALL appear as a dedicated section, and JSON SHALL include commentary fields

#### Scenario: Commentary absent

- GIVEN `AiCommentary` is `None`
- WHEN rendering to HTML, Text, and JSON
- THEN no AI commentary SHALL appear AND no empty AI sections SHALL be shown

### Requirement: Data Edge Case Handling

The system SHALL generate coherent AI commentary regardless of edge-case data states.

#### Scenario: Empty dataset

- GIVEN a dataset with 0 rows
- WHEN AI commentary is generated
- THEN the commentary SHALL acknowledge the empty state without misleading inferences

#### Scenario: Single column

- GIVEN a dataset with exactly 1 column
- WHEN AI commentary is generated
- THEN the commentary SHALL handle the limited structure gracefully without correlation analysis

#### Scenario: All null values

- GIVEN a dataset where all values are null
- WHEN AI commentary is generated
- THEN the commentary SHALL reflect the null state without fabricated inferences

### Requirement: AI Disclosure

AI-generated commentary MUST be clearly distinguished from deterministic output.

#### Scenario: Hallucination disclaimer

- GIVEN AI commentary is present
- WHEN rendering in HTML or Text format
- THEN each commentary block MUST be visually labeled as "AI-generated suggestion"
