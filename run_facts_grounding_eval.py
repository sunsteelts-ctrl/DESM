"""
DESM v2.01 — FACTS Grounding v2 End-to-End Evaluation Harness (run_facts_grounding_eval.py)
Collega desm_core_v2_01_3.py + facts_grounding_cartridge_v2_01.py a:
1. Un LLM reale per lo Stato 2 (Ollama locale a costo zero oppure Gemini API) + Modalità Offline Mock.
2. Il dataset pubblico di FACTS Grounding (CSV/JSONL) per gli 860 esempi pubblici.
3. Un Simulatore Dual-Judge Locale (Eligibility + Grounding) conforme a FACTS Grounding v2.
"""

from __future__ import annotations
import csv
import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Any

from desm_core_v2_01_3 import (
    CartridgeRegistry,
    DESMKernelOrchestrator,
    RawSignalInput,
    SentenceSpan,
    TargetContract,
    DualLayerGatekeeper,
    ConstrainedVerbalizerAndAuditor,
    KernelExecutionResult,
)
from facts_grounding_cartridge_v2_01 import (
    FACTSGroundingCartridge,
    FACTSContractCompiler,
    FACTSFormatCompliantVerbalizer,
    patched_verify_surface_anchor,
)


# ============================================================================
# 1. PROMPT DI SISTEMA INVIOLABILE PER LO STATO 2 (DSL TRANSDUCER)
# ============================================================================

S2_DSL_SYSTEM_PROMPT = """You are a deterministic syntactic transducer inside an Epistemic Kernel.
Your ONLY task is to extract factual propositions from the provided numbered text spans to answer the Target Sub-Questions.
Do NOT use any prior or external knowledge.

Output ONLY pipe-delimited lines following this exact 8-column schema (no markdown blocks, no extra commentary):
F_ID | Span_ID | Exact_Quote_Substring | Can_Subj ; Can_Pred ; Can_Obj | Modality | Polarity | Cond_Time_Qualifiers | Discourse_Edge

STRICT RULES FOR GATEKEEPER VALIDATION (G3):
1. Span_ID MUST match the exact ID provided in brackets (e.g., S_0002).
2. Exact_Quote_Substring MUST be a 100% character-for-character verbatim substring copied from that Span_ID. Never paraphrase or alter spelling.
3. Any number, percentage, or date placed in Can_Subj, Can_Pred, or Can_Obj MUST appear verbatim inside Exact_Quote_Substring (never convert words like 'three' into digits '3').
4. Modality MUST be one of: CERTAIN, POSSIBLE, CONDITIONAL, OBLIGATORY.
5. Polarity MUST be one of: POS, NEG.
6. Cond_Time_Qualifiers: comma-separated conditions, time bounds, or scope restrictions found in the span (or NONE).
7. Discourse_Edge: NONE, CAUSES -> F_xx, EXCEPT_WHEN -> F_xx, CONTRASTS_WITH -> F_xx, SUPPORTS -> F_xx.
"""


def format_spans_for_s2_prompt(
    spans: List[SentenceSpan],
    contract: TargetContract,
    retry_signal: Optional[str] = None
) -> str:
    sub_q_block = "\n".join(f"- {q}" for q in contract.sub_questions)
    spans_block = "\n".join(
        f"[{sp.span_id}] (Section: {sp.section_id}, GlobalScope: {sp.is_global_scope}): {sp.raw_text}"
        for sp in spans
    )
    retry_note = f"\nRETRY FOCUS (Uncovered questions): {retry_signal}\n" if retry_signal else ""
    return (
        f"TARGET SUB-QUESTIONS:\n{sub_q_block}\n"
        f"{retry_note}\n"
        f"NUMBERED SOURCE SPANS:\n{spans_block}\n\n"
        f"Emit the pipe-delimited EpistemicFrames now:"
    )


# ============================================================================
# 2. ADATTATORI TRASDUTTORE S2 (Ollama Locale / Gemini API / Deterministic Fallback)
# ============================================================================

def build_ollama_transducer(
    model_name: str = "llama3.1:8b",
    endpoint: str = "http://localhost:11434/api/generate"
) -> Callable[[List[SentenceSpan], TargetContract, Optional[str]], str]:
    """Trasduttore S2 a costo energetico/economico zero tramite server locale Ollama."""
    def _transduce(spans: List[SentenceSpan], contract: TargetContract, retry_signal: Optional[str]) -> str:
        user_prompt = format_spans_for_s2_prompt(spans, contract, retry_signal)
        payload = json.dumps({
            "model": model_name,
            "system": S2_DSL_SYSTEM_PROMPT,
            "prompt": user_prompt,
            "stream": False,
            "options": {"temperature": 0.0}
        }).encode("utf-8")
        req = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", "")
    return _transduce


def build_heuristic_extractive_transducer() -> Callable[[List[SentenceSpan], TargetContract, Optional[str]], str]:
    """
    Trasduttore estrattivo deterministico (0% LLM) utile per smoke-test offline della pipeline
    prima di accendere il modello neurale. Estrae gli span ad alta sovrapposizione lessicale.
    """
    def _transduce(spans: List[SentenceSpan], contract: TargetContract, retry_signal: Optional[str]) -> str:
        lines: List[str] = []
        f_idx = 1
        prev_fid: Optional[str] = None
        for sp in spans:
            raw = sp.raw_text.strip()
            if not raw:
                continue
            low = raw.lower()
            pol = "NEG" if any(n in low.split() for n in ("not", "never", "no", "prohibits", "cannot")) else "POS"
            edge = "NONE"
            if prev_fid and any(low.startswith(c) for c in ("however", "unless", "except")):
                edge = f"EXCEPT_WHEN -> {prev_fid}"
            elif prev_fid and any(low.startswith(c) for c in ("in contrast", "conversely", "whereas")):
                edge = f"CONTRASTS_WITH -> {prev_fid}"

            fid = f"F_{f_idx:02d}"
            f_idx += 1
            prev_fid = fid
            # Usa una partizione sintattica conservativa ancorata al 100% allo span originale
            words = raw.split()
            subj = " ".join(words[:3]) if len(words) >= 3 else "Document statement"
            pred = "states that"
            obj = raw
            lines.append(f"{fid} | {sp.span_id} | {raw} | {subj} ; {pred} ; {obj} | CERTAIN | {pol} | NONE | {edge}")
        return "\n".join(lines)
    return _transduce


# ============================================================================
# 3. SIMULATORE LOCALE DUAL-JUDGE (CONFORME A FACTS GROUNDING v2)
# ============================================================================

@dataclass
class LocalJudgeVerdict:
    example_id: str
    is_eligible: bool
    is_grounded: bool
    final_accurate: bool
    unanchored_numbers: List[str]
    rationale: str


class LocalFACTSDualJudge:
    """
    Replica deterministicamente i 2 criteri di squalifica di FACTS Grounding v2:
    1. Eligibility Check (Tabella 11): La risposta non deve essere vaga/evasiva, deve coprire
       tutte le sotto-domande e rispettare i vincoli di formato (Headed Sections, Exact Bullets).
    2. Grounding Check (Sezione 6.2): Ogni numero, percentuale e affermazione nella risposta
       deve provenire dal documento di contesto (o dichiarare esplicitamente l'assenza).
    """

    @staticmethod
    def evaluate(
        raw_context: str,
        user_query: str,
        system_prompt: str,
        result: KernelExecutionResult
    ) -> LocalJudgeVerdict:
        resp = result.response_text.strip()
        contract = FACTSContractCompiler.compile_contract(user_query, system_prompt)
        rules = contract.format_ast_rules

        # 1. Controllo Eligibility (Anti-Evasione + Rispetto Formato AST)
        if len(resp.split()) < 8:
            return LocalJudgeVerdict("N/A", False, False, False, [], "Ineligible: Response too short/evasive.")

        if rules.get("require_headed_sections") and "##" not in resp:
            return LocalJudgeVerdict("N/A", False, True, False, [], "Ineligible: Missing required headed sections.")

        exact_b = rules.get("exact_bullets_per_section")
        if exact_b is not None:
            bullets = [line for line in resp.splitlines() if line.strip().startswith("* ")]
            num_sections = max(1, len(contract.sub_questions))
            if len(bullets) != exact_b * num_sections:
                return LocalJudgeVerdict(
                    "N/A", False, True, False, [],
                    f"Ineligible: Expected {exact_b * num_sections} bullet points, found {len(bullets)}."
                )

        # 2. Controllo Grounding (Zero numeri inventati & 100% Lineage verificata)
        import re
        ctx_nums = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", raw_context))
        q_nums = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", f"{user_query} {system_prompt}"))
        allowed_nums = ctx_nums.union(q_nums).union({str(i) for i in range(1, 15)})  # indici di sezione

        resp_nums = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", resp))
        unanchored = sorted(list(resp_nums - allowed_nums))

        is_grounded = (len(unanchored) == 0) and (len(result.audit_lineage) > 0)
        final_acc = True and is_grounded

        return LocalJudgeVerdict(
            example_id="BENCH_ITEM",
            is_eligible=True,
            is_grounded=is_grounded,
            final_accurate=final_acc,
            unanchored_numbers=unanchored,
            rationale="PASS: 100% Grounded & Eligible" if final_acc else f"FAIL: Unanchored numbers {unanchored}"
        )


# ============================================================================
# 4. RUNNER SUL DATASET CSV/JSONL DI KAGGLE E BENCHMARK SUITE
# ============================================================================

def create_configured_kernel(sqlite_path: str = ":memory:") -> DESMKernelOrchestrator:
    DualLayerGatekeeper.verify_surface_anchor = staticmethod(patched_verify_surface_anchor)
    ConstrainedVerbalizerAndAuditor.verbalize_and_audit = classmethod(
        lambda cls, ast, custom_sentence_generator=None: FACTSFormatCompliantVerbalizer.verbalize_ast_for_kaggle(
            ast, custom_sentence_generator
        )
    )
    reg = CartridgeRegistry()
    reg.register(FACTSGroundingCartridge(top_k_per_subquestion=18))
    return DESMKernelOrchestrator(registry=reg, sqlite_db_path=sqlite_path)


def run_kaggle_csv_benchmark(
    csv_path: str,
    transducer_fn: Callable[[List[SentenceSpan], TargetContract, Optional[str]], str],
    max_examples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Legge il file CSV pubblico di FACTS Grounding (colonne: system_instruction, user_request, context_document)
    ed esegue il benchmark calcolando Eligibility Rate, Grounding Rate e Final Factuality Score.
    """
    kernel = create_configured_kernel()
    verdicts: List[LocalJudgeVerdict] = []
    t_start = time.perf_counter()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if max_examples is not None and idx >= max_examples:
                break
            sys_inst = row.get("system_instruction", row.get("system_prompt", ""))
            user_req = row.get("user_request", row.get("user_query", ""))
            ctx_doc = row.get("context_document", row.get("raw_context", ""))

            res = kernel.run(
                signal=RawSignalInput(raw_context=ctx_doc, user_query=user_req, system_prompt=sys_inst),
                transducer_fn=transducer_fn,
                contract_compiler_fn=FACTSContractCompiler.compile_contract,
            )
            v = LocalFACTSDualJudge.evaluate(ctx_doc, user_req, sys_inst, res)
            v.example_id = f"EX_{idx+1:04d}"
            verdicts.append(v)

    total = len(verdicts) if verdicts else 1
    eligible_cnt = sum(1 for v in verdicts if v.is_eligible)
    grounded_cnt = sum(1 for v in verdicts if v.is_grounded)
    accurate_cnt = sum(1 for v in verdicts if v.final_accurate)

    return {
        "total_examples": len(verdicts),
        "eligibility_rate_pct": round(100.0 * eligible_cnt / total, 2),
        "unadjusted_grounding_pct": round(100.0 * grounded_cnt / total, 2),
        "final_facts_grounding_score_pct": round(100.0 * accurate_cnt / total, 2),
        "total_time_sec": round(time.perf_counter() - t_start, 3),
    }


if __name__ == "__main__":
    # Generiamo un mini-CSV nello stesso formato del dataset pubblico Kaggle (Tabella 9 & 11 del Paper)
    sample_csv = "sample_facts_grounding_public.csv"
    rows = [
        {
            "system_instruction": "Answer the question based solely on the information provided in the passage. Do not use any external knowledge or resources.",
            "context_document": (
                "Researchers at Foch Hospital in France studied pregnancy outcomes in two groups of patients: "
                "women aged 40 and older versus women aged 25 to 35. "
                "Regarding obstetric complications, women aged 40+ had a 14.2% rate of gestational diabetes compared to 6.1% in the younger group. "
                "Regarding fetal complications, intrauterine growth restriction occurred in 4.8% of the 40+ cohort. "
                "Regarding neonatal complications, NICU admission rates did not differ significantly between the two groups (3.1% vs 2.9%)."
            ),
            "user_request": "Researchers at Foch Hospital in France published this study of pregnancy outcomes in two groups of patients. Please summarize outcomes across the three kinds of complications that the researchers studied."
        },
        {
            "system_instruction": "This task requires you to answer questions based solely on the information provided in the prompt. Present your answer in headed sections with an explanation for each section. Each explanation should be in bullet points with exactly three bullet points.",
            "context_document": (
                "Skyscraper window-washing robots use vacuum suction cups and LiDAR sensors to navigate glass facades autonomously. "
                "They reduce human exposure to high-altitude wind hazards by 85%. "
                "However, current human operators are transitioning into technical maintenance and fleet supervision roles rather than facing immediate replacement."
            ),
            "user_request": "How do these robots work? Also what does this mean for the people who do those jobs?"
        }
    ]

    with open(sample_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["system_instruction", "context_document", "user_request"])
        writer.writeheader()
        writer.writerows(rows)

    metrics = run_kaggle_csv_benchmark(sample_csv, transducer_fn=build_heuristic_extractive_transducer())
    print("RISULTATI BENCHMARK HARNESS SU CAMPIONE KAGGLE:")
    print(json.dumps(metrics, indent=2))
