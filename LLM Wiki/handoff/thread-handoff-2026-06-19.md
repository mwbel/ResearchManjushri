# LLM Wiki Thread Handoff - 2026-06-19

## Project Goal

Build a personal multi-disciplinary knowledge base on top of the existing LLM Wiki. The current development focus is a single-discipline workflow:

- Import web articles, WeChat articles, local files, and academic paper evidence.
- Ingest source material into source pages.
- Extract candidate concepts and concept relations.
- Visualize a concept graph and make concepts navigable like Wikipedia pages.
- Keep human confirmation points for ambiguous or high-risk edits.
- Later expand from one discipline to cross-disciplinary LLM Wiki links.

## Current Runtime

- Project root: `/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjusi/LLM Wiki`
- Local UI: `http://127.0.0.1:8765/`
- Start command:

```bash
cd "/Users/Min369/Documents/同步空间/Manju/AIProjects/ResearchManjusi/LLM Wiki"
python3 scripts/wiki_web.py --host 127.0.0.1 --port 8765
```

Do not assume the server is running. Check with:

```bash
lsof -nP -iTCP:8765 -sTCP:LISTEN
```

## Implemented Capabilities

- Frontend intake for adding sources without command line.
- Fixed discipline list: adding new disciplines is not exposed in normal intake.
- Domain cards show source/page counts and allow domain deletion.
- Clicking a discipline shows all sources in that discipline.
- Source edit/delete flow exists.
- Local file upload exists.
- Word `.docx` extraction was added after the initial unsupported-file issue.
- Auto ingest can build source pages, candidate concepts, relations, and domain network updates.
- Concept graph visualization exists, modeled after easyML-style concept network, without level labels.
- Wikipedia-like concept reading pages exist, with related concepts and evidence cards.
- Current concept can be deleted through a trash icon.
- Pending concepts can be opened, kept, or deleted from the right/sidebar workflow.
- Auto concept organization preview exists, with high-confidence apply path.
- Source supplement automation exists as a draft-first workflow: generate an auto-filled draft, then human confirms before saving.
- Science main-journal candidate tracker exists and was moved under the left intake area.
- Sciverse integration exists for academic retrieval, with token handling via Keychain/environment or temporary dev input.
- WeChat crawler integration was connected for content behind WeChat access/friction.

## Key Files

- `scripts/wiki_web.py`: main local web server, API routes, UI HTML/CSS/JS generation, concept organization logic.
- `scripts/concept_ingest.py`: source-to-concept extraction and relation generation rules.
- `scripts/auto_ingest.py`: ingest orchestration.
- `scripts/sciverse_ingest.py` and `.agents/skills/sciverse/`: academic retrieval integration.
- `scripts/wechat_*` or related crawler hooks: WeChat article crawling integration.
- `wiki/domains/`: discipline network pages.
- `wiki/sources/`: generated source profile pages.
- `wiki/concepts/`: concept pages.
- `raw/sources/`: raw registered source records.
- `raw/assets/uploads/`: uploaded local files.

## Latest Fix Before Handoff

Problem: noisy candidate concepts appeared again, such as:

- `Claude或Gemini等大语言模型`
- `你可以一次解决成千上万个问题`
- `几个人工智能模型`
- `对AI模型`
- `随着AI模型`
- `这些模型`
- `过去数学家一次只钻研一个问题`

Cause: the extractor matched sentence fragments containing words like "模型" or "问题" and promoted them as candidate concepts.

Fix applied:

- `scripts/concept_ingest.py` now rejects these narrative/list/quantity phrases during future ingest.
- `scripts/wiki_web.py` now marks existing items of this kind as `delete_noise` in auto-organization preview.
- Core concept whitelist was expanded so valid concepts are not accidentally deleted:
  - `AI`
  - `人工智能`
  - `LLM`
  - `Transformer`
  - `大语言模型`
  - `语言模型`
  - `注意力机制`
  - `不完全的归纳法`
  - `停机问题`
  - `知识论`
  - `归纳法`
  - `真信念且证成`
  - `结构化的噪声引入`
  - `NLI`
  - `Noise Leading In`

Verification already run:

```bash
python3 -m py_compile scripts/wiki_web.py scripts/concept_ingest.py
```

Manual API check showed the noisy examples above become `delete_noise`, while `人工智能`, `AI`, `大语言模型`, `LLM`, `Transformer`, `不完全的归纳法`, and `停机问题` are kept.

## Product Principles Established In This Thread

1. Raw sources should remain traceable.
2. Automatically extracted concepts are provisional until promoted or confirmed.
3. Tools/products/entities such as Sciverse, RAG, Claude, Cursor, GitHub, OpenAI should not enter the concept graph by default.
4. Core technical concepts should be protected from noise deletion.
5. High-density or highly opinionated essays should not automatically create many concepts unless the evidence is strong.
6. Automation should produce drafts/previews first; human confirmation should apply changes.
7. The UI should follow an AI-tool reading flow:
   - left: disciplines and intake/actions
   - center: selected discipline/source/workbench
   - right: current concept, pending concept, evidence, and tools
8. "Pending concepts" means concepts extracted from sources but not yet stable enough as wiki concepts.
9. "Pending sources" means registered sources missing usable summary/body/extract.
10. The concept graph should show knowledge relations, not tool plumbing.

## Known Issues / Design Debt

- Noise rules are still heuristic. They need a stronger concept acceptance classifier.
- Some broad concepts, especially `AI` and `人工智能`, need merge/alias handling instead of simple keep/delete.
- Some source-derived pages remain hard to read because the concept page template exposes raw evidence before a clean definition.
- Concept relation labels may still be weak, generic, or source-sentence-shaped.
- Existing noisy concept files may remain until the user applies high-confidence organization or deletes them.
- Sciverse network calls may fail under proxy/VPN/fake-IP conditions even if token is valid.
- Generated wiki content and user-uploaded raw assets are data, not code; avoid bulk deletion unless explicitly requested or user confirms through UI.

## Recommended Next Development Plan

### Step 1: Stabilize Concept Quality

Implement a concept acceptance layer with these outcomes:

- `promote`: stable technical/theoretical concept with evidence and relations.
- `merge`: synonym, alias, translation, or narrower wording of an existing concept.
- `delete_noise`: sentence fragment, metadata, source title fragment, product/tool/entity, marketing phrase.
- `manual_review`: plausible but insufficient evidence.

Add a merge UI for cases like:

- `AI` <-> `人工智能`
- `LLM` <-> `大语言模型`
- `Attention Mechanism` <-> `注意力机制`

### Step 2: Improve Concept Pages

Change concept pages from raw extraction reports into readable wiki entries:

- lead definition in plain language
- why it matters in this discipline
- boundaries: what it is not
- source-backed evidence
- relations grouped by type
- open questions at bottom

Keep raw evidence visible but subordinate.

### Step 3: Make Auto Organization Safer

Before applying high-confidence organization:

- show exact files affected
- show counts by action
- preserve a deletion log
- support undo/restoration from a local trash or archive folder

### Step 4: Improve Source Supplement Automation

For pending sources, generate a visible draft containing:

- cleaned title
- summary
- why this source matters
- main takeaways
- candidate concepts
- candidate relations
- confidence and missing fields

Apply only after confirmation.

### Step 5: Cross-Discipline Preparation

After single-domain quality stabilizes:

- add cross-domain bridge relation type
- distinguish intra-domain relations from cross-domain analogies
- build a cross-disciplinary concept graph view
- add source provenance filters

## Safe Working Instructions For Next Thread

- Start by reading `scripts/wiki_web.py` and `scripts/concept_ingest.py`; most current behavior is there.
- Use `rg` for search.
- Use `apply_patch` for edits.
- Do not run destructive git commands.
- Do not delete user source data directly unless the UI/feature explicitly archives or confirms it.
- Do not expose or repeat the Sciverse API key in logs or responses.
- After code edits, run:

```bash
python3 -m py_compile scripts/wiki_web.py scripts/concept_ingest.py scripts/auto_ingest.py
```

- Restart the local server and verify `http://127.0.0.1:8765/`.

## Suggested First Task For New Thread

Continue from concept quality stabilization:

1. Add a merge/alias workflow for duplicate concepts.
2. Refine pending concept cards to show why a concept was introduced and what action is recommended.
3. Add an undo/archive mechanism for auto-deleted concept pages.
4. Improve concept pages so the definition is readable before evidence details.
