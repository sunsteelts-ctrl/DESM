import csv
import json
import os
import urllib.request
from desm_core_v2_01_3 import RawSignalInput
from facts_grounding_cartridge_v2_01 import FACTSContractCompiler
from run_facts_grounding_eval import (
    create_configured_kernel,
    build_ollama_transducer,
    build_heuristic_extractive_transducer,
    LocalFACTSDualJudge,
)

# --- CONFIGURAZIONE ---
CSV_FILE = "facts_grounding_public.csv"  # Cambia o lascia che usi il sample se non presente
OLLAMA_MODEL = "qwen2.5:7b"             # Il modello che hai scaricato su Ollama
MAX_EXAMPLES = 25                        # Numero di esempi da testare
USE_OLLAMA = True                        # Metti False per fare un test istantaneo senza Ollama
OUTPUT_LOG = "risultati_test_live.jsonl"


def check_ollama_running() -> bool:
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        return True
    except Exception:
        return False


def main():
    # 1. Verifica file CSV (se non hai ancora il file di Kaggle, usa il sample)
    target_csv = CSV_FILE
    if not os.path.exists(target_csv):
        if os.path.exists("sample_facts_grounding_public.csv"):
            print(f"[AVVISO] '{CSV_FILE}' non trovato. Uso 'sample_facts_grounding_public.csv'.")
            target_csv = "sample_facts_grounding_public.csv"
        else:
            print(f"[ERRORE] Nessun file CSV trovato. Esegui prima: python3 run_facts_grounding_eval.py")
            return

    # 2. Scelta del trasduttore (Ollama vs Offline Heuristic)
    if USE_OLLAMA:
        if not check_ollama_running():
            print("[ERRORE] Ollama non risponde su http://localhost:11434.")
            print("Apri un altro terminale ed esegui: ollama serve (oppure avvia l'app Ollama).")
            return
        print(f"[OK] Connesso a Ollama locale (Modello: {OLLAMA_MODEL})")
        transducer_fn = build_ollama_transducer(model_name=OLLAMA_MODEL)
    else:
        print("[OK] Modalità Offline Deterministica attiva (0% LLM)")
        transducer_fn = build_heuristic_extractive_transducer()

    # 3. Inizializzazione Kernel + Cartuccia Grounding
    kernel = create_configured_kernel(sqlite_path="desm_memory.sqlite")
    eligible_cnt = 0
    grounded_cnt = 0
    accurate_cnt = 0
    total = 0

    # 4. Esecuzione con log in tempo reale e salvataggio progressivo
    with open(target_csv, "r", encoding="utf-8") as f_in, open(OUTPUT_LOG, "w", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        for idx, row in enumerate(reader):
            if idx >= MAX_EXAMPLES:
                break
            total += 1
            sys_inst = row.get("system_instruction", row.get("system_prompt", ""))
            user_req = row.get("user_request", row.get("user_query", ""))
            ctx_doc = row.get("context_document", row.get("raw_context", ""))

            print(f"\n--- Esempio {total}/{MAX_EXAMPLES} ---")
            print(f"Domanda: {user_req[:90]}...")

            res = kernel.run(
                signal=RawSignalInput(raw_context=ctx_doc, user_query=user_req, system_prompt=sys_inst),
                transducer_fn=transducer_fn,
                contract_compiler_fn=FACTSContractCompiler.compile_contract,
            )

            verdict = LocalFACTSDualJudge.evaluate(ctx_doc, user_req, sys_inst, res)
            if verdict.is_eligible:
                eligible_cnt += 1
            if verdict.is_grounded:
                grounded_cnt += 1
            if verdict.final_accurate:
                accurate_cnt += 1

            print(f"Percorso Kernel  : {res.execution_path.value} ({res.latency_ms:.1f} ms)")
            print(f"Frame Validati   : {res.metadata['valid_frames_count']} | Quarantena (Allucinazioni bloccate): {res.metadata['quarantined_frames_count']}")
            print(f"Verdetto Giudice : {verdict.rationale}")

            # Salvataggio immediato su disco (a prova di crash)
            record = {
                "example_index": total,
                "user_request": user_req,
                "response_text": res.response_text,
                "valid_frames": res.metadata["valid_frames_count"],
                "quarantined_frames": res.metadata["quarantined_frames_count"],
                "judge_rationale": verdict.rationale,
                "final_accurate": verdict.final_accurate,
            }
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
            f_out.flush()

    if total > 0:
        summary = {
            "total_evaluated": total,
            "eligibility_rate_pct": round(100.0 * eligible_cnt / total, 2),
            "unadjusted_grounding_pct": round(100.0 * grounded_cnt / total, 2),
            "final_facts_grounding_score_pct": round(100.0 * accurate_cnt / total, 2),
            "saved_log_file": OUTPUT_LOG,
        }
        print("\n" + "=" * 60)
        print("RIEPILOGO FINALE:")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()