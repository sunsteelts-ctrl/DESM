# DESM (v2.1) — Deterministic Epistemic State Machine

**A Neuro-Symbolic Micro-Kernel Architecture for Causal Transparency, Inference Economy, and Zero-Trust LLM Orchestration.**

> **Archive Notice:** This repository contains the complete theoretical specification and reference prototype (`v2.01.3`) of the DESM architecture. The project has fulfilled its primary research objective—formalizing a strict state-machine isomorphism between classical cognitive process models and verifiable neuro-symbolic computing—and is released as a permanent open-source archive for researchers and systems engineers to study, fork, or adapt.

---

## 1. The Engineering Problem: Why Standard LLM Pipelines Fail at Scale
Current AI orchestration treats Large Language Models as monolithic reasoning engines, collapsing **syntactic perception** (parsing unstructured surface text) and **epistemic judgment** (logical deduction, constraint satisfaction, and factual synthesis) into a single autoregressive forward pass. This creates three structural failures in high-stakes engineering:
1. **Causal Opacity & Late-Stage Confabulation:** As context windows scale, self-attention dispersion causes models to blend distant spans, invent numerical interpolations, or drop critical legal/medical qualifiers (`unless`, `except when`) during final text generation.
2. **Unbounded Inference Cost:** Every query—whether a trivial exact recurrence, an isomorphic logical pattern, or a corrupted prompt—is routed through multi-billion-parameter matrix multiplications with $O(N^2)$ attention complexity.
3. **Absence of Formal Epistemic States:** Probabilistic token predictors lack native primitives to distinguish *verified deduction* from *source contradiction* or *epistemic absence* (when the required premise is mathematically missing from the ground truth).

---

## 2. The DESM Paradigm: Strict Epistemic Decoupling
**DESM (Deterministic Epistemic State Machine)** solves these three bottlenecks by inverting the role of the LLM:
* **Demote the LLM to a Stateless Syntactic Transducer ($S_2$):** The language model (`temperature=0.0`) is stripped of decision-making authority. Its sole function is to compile raw text spans into rigid, 7-field `EpistemicFrame` tuples anchored to exact source substrings.
* **Deterministic Gatekeeping & Quarantine ($S_3$):** Before any reasoning occurs, pure-Python deterministic guards verify in microseconds that every extracted quote exists verbatim in the source span and that every number in the logical triple is a strict subset of the numbers present in the quote (`triple_numbers ⊆ quote_numbers`). Hallucinated frames are quarantined on the spot.
* **Physical Isolation of Final Synthesis ($S_5$):** The final verbalizer receives **only** the immutable `ProofPlanAST` (`frozen=True`). It holds **zero memory pointers** to the raw input document (`RawSignalInput`) or corpus map (`ImmutableCorpusMap`), making late-stage context leakage physically impossible.

---

## 3. System Architecture & The Cognitive Isomorphism
DESM translates formal principles from classical *Abhidharma* cognitive process theory (*Citta-vīthi* variable-depth state transitions and *Paṭṭhāna* conditional relations) into strict software engineering invariants, removing all philosophical nomenclature in favor of deterministic execution mechanics:

| Cognitive Process Principle | DESM Engineering Equivalent | Structural Function & Invariant |
| :--- | :--- | :--- |
| **Mogha-vāra / Paritta** *(Variable-Depth Process Termination)* | **Multi-Tier Early-Exit (`Gate 0`, `Gate 1A`, `Gate 3B`)** | Signals do not blindly traverse the full pipeline. Empty/corrupt inputs abort at Gate 0; exact recurrences exit at Gate 1A in microseconds; structural isomorphisms exit at Gate 3B before heavy solving. |
| **Ahetuka Intake** *(Rootless / Zero-Bias Perception, T4–T7)* | **State 1 & State 2 (`DOMIndexer` + `PipeDSLParser`)** | Early ingestion stages are strictly stripped of generative creativity or heuristic bias. They register raw spans, character offsets, and syntactic tuples in read-only mode. |
| **Voṭṭhapana** *(Deterministic Gatekeeping, T8)* | **State 3 (`DualLayerGatekeeper`)** | The pivot between passive reception and active computation. Filters out noise/hallucinations and compiles verified frames into an `ImmutableEpistemicDAG`. |
| **Javana** *(Active Symbolic Resolution, T9–T15)* | **State 4 (`BaseSymbolicCartridge` Slot)** | Domain-specific symbolic co-processor (e.g., Document Grounding solver, SymPy, SAT/Z3). Resolves `SUPPORTS`, `CONFLICTS_WITH`, and `EXCEPT_WHEN` edges into a locked `ProofPlanAST`. |
| **Tadārammaṇa** *(TTL-Gated Memory Registration, T16–T17)* | **State 5.2 (`Schema Consolidation Loop`)** | Feeds verified execution traces back into State 1A/3B caches so future isomorphic queries bypass heavy deduction. |

### The 5-State Execution Pipeline
```text
[Raw Signal Input]
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STATE 1: Structural Indexing & Gate 0 / Gate 1A                         │
│ • Gate 0 (Sanity Check): Instant rejection of empty/corrupted inputs.   │
│ • DOM Indexer: Maps immutable paragraph/sentence spans & global scope.  │
│ • Gate 1A (Exact Episodic Cache): SHA-256 lookup with explicit guards   │
│   for numbers, operators, and negations (prevents dense-vector blindness│
│   on "5mg" vs "50mg").                                                  │
└──────┬──────────────────────────────────────────────────────────────────┘
       │ (Cache Miss)
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STATE 2: Syntactic Transduction (Pipe-DSL / Constrained Extraction)     │
│ • Selects relevant discourse windows (BM25 + adjacency expansion).      │
│ • LLM extracts 7-field EpistemicFrames:                                 │
│   Span_ID | Exact_Quote | Subj;Pred;Obj | Modality |Qualifiers|Polarity │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STATE 3: Dual-Layer Deterministic Gatekeeper & Gate 3B (VSA)            │
│ • Layer 3.1 (Surface Anchor): Verifies exact substring existence and    │
│   enforces triple_numbers ⊆ quote_numbers. Quarantines hallucinations.  │
│ • Layer 3.2 (Structural Graph): Builds an ImmutableEpistemicDAG.        │
│ • Gate 3B (Isomorphic VSA Cache): Encodes abstract graph topology into  │
│   a 10,000-D Holographic Reduced Representation (FFT circular           │
│   convolution + orthogonal role permutations) for structural reuse.     │
└──────┬──────────────────────────────────────────────────────────────────┘
       │ (Requires Heavy Deduction)
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STATE 4: Domain-Specific Symbolic Cartridge (Pluggable Slot)            │
│ • Executes deterministic domain logic over the validated DAG.           │
│ • Explicitly surfaces EPISTEMIC_ABSENCE (missing data) and              │
│   FLAGGED_CONTRADICTION (source conflicts) as first-class AST nodes.    │
└──────┬──────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ STATE 5: Constrained Verbalizer, Lineage Auditor & Schema Consolidation │
│ • Blind to raw source text; renders only the locked ProofPlanAST.       │
│ • Audits sentence-to-node lineage (character offsets & modality match). │
│ • Consolidates verified schemas back into State 1A / 3B memory.         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Mathematical & Architectural Mechanisms in `v2.01.3`
* **Non-Commutative 10,000-D VSA Engine (`NonCommutativeVSAEngine`):** Standard element-wise hyperdimensional binding is commutative ($A \otimes B = B \otimes A$), making it blind to causal asymmetry ($X \text{ causes } Y \neq Y \text{ causes } X$). DESM implements circular convolution via Fast Fourier Transform (`rfft`/`irfft`) paired with fixed orthogonal role permutations ($\Pi_{\text{subj}}, \Pi_{\text{pred}}, \Pi_{\text{obj}}$) and canonical topological sorting, achieving directional invariance in $O(D \log D)$ time.
* **Scoped Memory Isolation (`GLOBAL_INVARIANT` vs. `DOCUMENT_BOUND`):** Prevents cross-document schema contamination by restricting State 3B isomorphic hits either to universal formal laws (Math/Physics) or to matching document hashes (`doc_hash`).
* **1 Universal Kernel + $N$ Domain Cartridges:** The core engine (`desm_core_v2_01_3.py`) is completely domain-agnostic. Domain algebras are encapsulated inside pluggable `BaseSymbolicCartridge` modules registered via `CartridgeRegistry`.

---

## 5. Architectural Post-Mortem: Known Trade-offs in v2.1
To assist researchers building upon this repository, the following limitations of the `v2.01.3` prototype are explicitly documented:
1. **The Semantic Von Neumann Bottleneck in $S_2$:** Compressing natural language into rigid Pipe-DSL tuples via a 7B local LLM without grammar-constrained decoding (GBNF) risks dropping subtle cross-sentence coreferences or malformed lines.
2. **Open Predicate Ontology vs. VSA Isomorphism:** For State 3B (`NonCommutativeVSAEngine`) to recognize structural isomorphism across different texts, canonical predicates (`can_pred`) must map to a closed ontology. In open-ended narrative tasks, synonym variation ("causes" vs. "triggers") produces orthogonal vectors, making VSA caching highly effective in formal domains (Math/Logic) but low-yield in single-pass document summarization.
3. **Lexical Bottleneck in Span Selection:** The `v2.01.3` Grounding Cartridge uses lightweight lexical/BM25 overlap for sub-question alignment. Paraphrased queries that fail lexical threshold can trigger a `FULL_SCAN` retry, which saturates local LLM context windows if unthrottled.
4. **Snapshot Integration Notes:** In this archive, `facts_grounding_cartridge_v2_01_3.py` acts as a self-contained patch generator that outputs `facts_grounding_cartridge_v2_01.py`. Moreover, binding `FACTSFormatCompliantVerbalizer` into `DESMKernelOrchestrator.run()` requires a direct hook in `BaseSymbolicCartridge` to override the Kernel's default diagnostic repair output in State 5.

---

## 6. Theoretical Horizon (DESM 3.0 Blueprint for Future Forks)
While active development on this repository is concluded, the theoretical trajectory points toward four high-efficiency evolutions for future neuro-symbolic and non-Von Neumann implementations:
1. **Dual-Bus Routing (*Pañcadvāra* vs. *Manodvāra* Bypass):** Separate the ingestion bus into a *Sensory/Document Pipeline* (full $S_1 \rightarrow S_5$ for raw unstructured text) and a *Pure Symbolic Pipeline* (*Manodvāra*), allowing formal queries, mathematical expressions, and multi-hop iterative cycles to bypass DOM indexing and LLM transduction entirely ($0$ LLM calls).
2. **Composable *Cetasika* Logit Masks (Dynamic Constrained Decoding):** Replace static State 2 system prompts with modular grammar masks (GBNF / JSON Schema logit processors). Load only the minimal 4-field extraction grammar by default, dynamically mounting conditional (`cond_time_qualifiers`) or adversarial (`DiscourseEdge`) grammar modules only when surface markers are detected in State 1.
3. **TTL-Gated Cache Purity (*Tadārammaṇa* Threshold):** Enforce a strict execution Time-To-Live (TTL) and epistemic purity threshold on State 5.2. Cycles that require retries, surgical repairs in $S_5$, or exhibit `quarantined_frames > 0` still return an output to the user, but are **barred from writing to long-term SQLite/VSA memory**, preventing progressive cache degradation.
4. **State 4 Resolution via Progressive Compute Pruning & Energy Relaxation (*Jhāna* Dynamics):** Instead of solving complex constraint graphs in State 4 via imperative loops or external LLM retries ($S_4 \rightarrow S_2$), compile the State 3 validated DAG into an Energy-Based Hamiltonian / Modern Hopfield Network (or QUBO matrix for thermodynamic/quantum annealing hardware). Once the constraint structure is locked in $S_3$, disconnect the LLM and progressively anneal search degrees of freedom—collapsing the graph into its zero-contradiction ground state passively, or certifying mathematical emptiness (`EPISTEMIC_ABSENCE`) without combinatorial explosion.

---

## 7. Repository Inventory & Quick Verification
* `desm_core_v2_01_3.py` — **Module 1:** Universal Kernel, immutable data contracts, 10,000-D FFT VSA engine, SQLite/NumPy Early-Exit Manager, Dual-Layer Gatekeeper, and Orchestrator.
* `facts_grounding_cartridge_v2_01_3.py` — **Module 2:** Document Grounding Cartridge generator & format-compliant synthesis engine.
* `test_runner.py` — Local evaluation harness for Ollama (`qwen2.5:7b`) on the DeepMind FACTS Grounding dataset.
* `risultati_test_live.jsonl` / `TEST_OLLAMA.txt` — Live execution logs showing real-time State 3 hallucination quarantine.
* `requirements.txt` — Dependencies (`numpy`, `pydantic`, `sympy`, `datasets`, `tqdm`).

To run the Kernel's built-in mathematical and architectural verification suite (verifying VSA non-commutativity, numerical guard disambiguation, and the 4 Early-Exit paths without requiring an LLM):

```bash
pip install -r requirements.txt
python desm_core_v2_01_3.py
```

---

## License
Released under the **MIT License**.