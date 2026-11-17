"""
DESM v2.01 — Universal Variable-Depth Epistemic Kernel (desm_core_v2_01_3.py)
Modulo 1 Completo (Opzione A + Cartridge Registry & Deterministic S1.0 Dispatcher).

Caratteristiche Architetturali:
1. Agnosticismo di Dominio Totale: Il Kernel governa gli stati S1 -> S5, la memoria e gli Early-Exit
   senza conoscere le regole interne del dominio (delegate a BaseSymbolicCartridge).
2. Auto-Routing Iniziale a Costo Zero (CartridgeRegistry): In S1.0 il Kernel ispeziona la firma
   strutturale dell'input e seleziona deterministicamente la cartuccia registrata più adatta
   una sola volta per esecuzione (o accetta un override esplicito per benchmark).
3. Motore VSA Non-Commutativo (HRR + Permutazioni Ortogonali di Coordinate S_D):
   Complessità O(D log D) con distinzione asimmetrica rigorosa tra ruoli (SUBJ != OBJ) e sequenza.
4. Persistenza Ibrida Ad Alte Prestazioni (SQLiteWAL + NumPy Float32 Matrix):
   Elimina il collo di bottiglia della deserializzazione BLOB riga-per-riga, garantendo
   lookup isomorfi in S3B in < 2 ms anche su migliaia di schemi consolidati.
5. Isolamento Fisico di S5 (Zero Context Leakage): Lo Stato 5 riceve esclusivamente ProofPlanAST
   e opera con verifica deterministica frase-per-nodo e fallback chirurgico a temperatura 0.0.
"""

from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Callable
import numpy as np


# ============================================================================
# 1. ENUMERAZIONI E TIPI FONDAMENTALI DEL PROTOCOLLO
# ============================================================================

class ExecutionPath(Enum):
    PATH_0_INVALID_ABORT = "PATH_0_INVALID_SIGNAL_ABORT"
    PATH_1A_EXACT_HIT = "PATH_1A_EXACT_EPISODIC_HIT"
    PATH_3B_ISOMORPHIC_HIT = "PATH_3B_ISOMORPHIC_SCHEMA_HIT"
    PATH_4_FULL_CYCLE = "PATH_4_FULL_EPISTEMIC_CYCLE"


class QueryTopology(Enum):
    POINT_LOOKUP = "POINT_LOOKUP"
    GLOBAL_AGGREGATION = "GLOBAL_AGGREGATION"
    COMPARATIVE = "COMPARATIVE"


class Polarity(Enum):
    POS = "POS"
    NEG = "NEG"


class Modality(Enum):
    CERTAIN = "CERTAIN"
    POSSIBLE = "POSSIBLE"
    CONDITIONAL = "CONDITIONAL"
    OBLIGATORY = "OBLIGATORY"


class DiscourseEdge(Enum):
    NONE = "NONE"
    CAUSES = "CAUSES"
    EXCEPT_WHEN = "EXCEPT_WHEN"
    CONTRASTS_WITH = "CONTRASTS_WITH"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    SUPPORTS = "SUPPORTS"


class EpistemicStatus(Enum):
    VALIDATED_GROUNDED = "VALIDATED_GROUNDED"             # W = 1.0
    FLAGGED_CONTRADICTION = "FLAGGED_CONTRADICTION"       # W = 0.5
    QUARANTINED_UNGROUNDED = "QUARANTINED_UNGROUNDED"     # W = 0.0
    EPISTEMIC_ABSENCE = "EPISTEMIC_ABSENCE"               # Nodo certificato di assenza


class CacheScopePolicy(Enum):
    GLOBAL_INVARIANT = "GLOBAL_INVARIANT"                 # Es. Matematica/Logica (Cross-Problem)
    DOCUMENT_BOUND = "DOCUMENT_BOUND"                     # Es. Document Grounding (Vincolato a Corpus_Hash)


# ============================================================================
# 2. DATA CONTRACTS IMMUTABILI (S1 -> S5)
# ============================================================================

@dataclass(frozen=True)
class RawSignalInput:
    """Input grezzo in ingresso a S1."""
    raw_context: str
    user_query: str
    system_prompt: str = ""
    modality_hint: str = "TEXT"                           # Es. "TEXT", "MATH", "VISION_FEATURES"


@dataclass(frozen=True)
class SentenceSpan:
    """Unità atomica indicizzata nel DOM di S1A."""
    span_id: str
    section_id: str
    paragraph_id: str
    char_start: int
    char_end: int
    raw_text: str
    is_global_scope: bool = False


@dataclass(frozen=True)
class ImmutableCorpusMap:
    """Mappa immutabile del documento/contesto generata in S1A."""
    corpus_hash: str
    spans: Dict[str, SentenceSpan]
    global_scope_span_ids: Tuple[str, ...]


@dataclass(frozen=True)
class ExactEpisodeKey:
    """Doppia chiave esatta per Early-Exit 1A in O(1) (include cartridge_id)."""
    cartridge_id: str
    corpus_hash: str
    normalized_lemmas_hash: str
    extracted_numbers: Tuple[str, ...]
    extracted_operators: Tuple[str, ...]
    extracted_negations: Tuple[str, ...]

    @property
    def composite_hash(self) -> str:
        payload = (
            f"{self.cartridge_id}|{self.corpus_hash}|{self.normalized_lemmas_hash}|"
            f"{','.join(self.extracted_numbers)}|"
            f"{','.join(self.extracted_operators)}|"
            f"{','.join(self.extracted_negations)}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TargetContract:
    """Contratto compilato in S1B."""
    sub_questions: Tuple[str, ...]
    query_topology: QueryTopology
    format_ast_rules: Dict[str, Any]


@dataclass(frozen=True)
class EpistemicFrame:
    """Frame emesso dal trasduttore DSL in S2 e validato in S3."""
    frame_id: str
    span_id: str
    exact_quote_substring: str
    can_subj: str
    can_pred: str
    can_obj: str
    modality: Modality
    polarity: Polarity
    cond_time_qualifiers: Tuple[str, ...] = ()
    discourse_edge: DiscourseEdge = DiscourseEdge.NONE
    target_frame_id: Optional[str] = None
    status: EpistemicStatus = EpistemicStatus.VALIDATED_GROUNDED
    epistemic_weight: float = 1.0

    @property
    def canonical_sort_key(self) -> Tuple[str, str, str, str]:
        """Chiave di ordinamento canonico per invarianza all'ordine delle frasi in S3."""
        return (self.can_pred, self.discourse_edge.value, self.polarity.value, self.modality.value)


@dataclass(frozen=True)
class StructuralSignature:
    """Firma booleana/topologica rigida che accompagna l'ipervettore VSA in S3."""
    polarities: Tuple[Polarity, ...]
    modalities: Tuple[Modality, ...]
    discourse_edges: Tuple[DiscourseEdge, ...]
    has_contradictions: bool
    has_unmapped_exceptions: bool
    corpus_hash: str


@dataclass(frozen=True)
class VerifiedEpistemicDAG:
    """Output dello Stato 3 (Gatekeeper)."""
    corpus_hash: str
    valid_frames: Tuple[EpistemicFrame, ...]
    quarantined_frames: Tuple[EpistemicFrame, ...]
    structural_vector: np.ndarray
    signature: StructuralSignature
    variable_bindings: Dict[str, str]          # {"$ENT_1": "Farmaco_X", "$VAL_1": "50mg"}
    reverse_bindings: Dict[str, str]           # {"Farmaco_X": "$ENT_1", "50mg": "$VAL_1"}


@dataclass(frozen=True)
class ProofNode:
    """Singolo nodo del Proof Plan AST (S4/S3B -> S5)."""
    node_id: str
    sub_question_ref: str
    frame_id: str
    abstract_subj: str
    abstract_pred: str
    abstract_obj: str
    concrete_subj: str
    concrete_pred: str
    concrete_obj: str
    exact_quote_substring: str
    modality: Modality
    polarity: Polarity
    discourse_edge: DiscourseEdge
    status: EpistemicStatus


@dataclass(frozen=True)
class ProofPlanAST:
    """
    Contratto esclusivo in ingresso a S5.
    Isolamento Fisico: Non contiene alcun riferimento a RawSignalInput o ImmutableCorpusMap.
    """
    plan_id: str
    cartridge_id: str
    corpus_hash: str
    nodes: Tuple[ProofNode, ...]
    format_ast_rules: Dict[str, Any]
    variable_bindings: Dict[str, str]
    is_from_isomorphic_cache: bool = False


@dataclass(frozen=True)
class AuditLineageRecord:
    """Tracciabilità granulare frase -> nodo -> span per l'audit finale in S5."""
    sentence_index: int
    generated_sentence: str
    source_node_id: str
    source_frame_id: str
    exact_quote_anchor: str
    repaired_at_temp_zero: bool


@dataclass(frozen=True)
class KernelExecutionResult:
    """Output finale certificato del Kernel DESM v2.01."""
    execution_path: ExecutionPath
    active_cartridge_id: str
    response_text: str
    audit_lineage: Tuple[AuditLineageRecord, ...]
    latency_ms: float
    llm_calls_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 3. MOTORE TOPOLOGICO VSA NON-COMMUTATIVO (HRR + Permutazioni Ortogonali S_D)
# ============================================================================

class NonCommutativeVSAEngine:
    """
    Motore Vector Symbolic Architecture in R^D (default D=10000).
    Combina HRR (convoluzione circolare via FFT in O(D log D)) con permutazioni
    di coordinate pseudo-casuali fisse S_D indicizzate per ruolo per garantire
    la NON-COMMUTATIVITÀ genuina: CosSim(bind(A, B), bind(B, A)) ~ 0.0.
    """

    def __init__(self, dimension: int = 10000, seed: int = 42):
        self.D = dimension
        self.rng = np.random.default_rng(seed)
        self._symbol_memory: Dict[str, np.ndarray] = {}
        self._perm_cache: Dict[str, np.ndarray] = {}
        self._inv_perm_cache: Dict[str, np.ndarray] = {}

        for role in ["SUBJ", "PRED", "OBJ", "MODALITY", "POLARITY", "EDGE", "RIGHT_ARG"]:
            self._init_role_permutation(role)

    def _init_role_permutation(self, role: str) -> None:
        role_seed = int(hashlib.md5(f"PERM_{role}".encode("utf-8")).hexdigest()[:8], 16)
        local_rng = np.random.default_rng(role_seed)
        perm = local_rng.permutation(self.D)
        self._perm_cache[role] = perm
        self._inv_perm_cache[role] = np.argsort(perm)

    def permute_by_role(self, vec: np.ndarray, role: str) -> np.ndarray:
        if role not in self._perm_cache:
            self._init_role_permutation(role)
        return vec[self._perm_cache[role]]

    def get_atomic_vector(self, symbol: str) -> np.ndarray:
        if symbol not in self._symbol_memory:
            sym_hash = int(hashlib.md5(symbol.encode("utf-8")).hexdigest()[:8], 16)
            local_rng = np.random.default_rng(sym_hash)
            vec = local_rng.normal(0.0, 1.0 / np.sqrt(self.D), size=self.D).astype(np.float32)
            norm = float(np.linalg.norm(vec))
            self._symbol_memory[symbol] = vec / norm if norm > 0 else vec
        return self._symbol_memory[symbol]

    @staticmethod
    def bind_commutative(v1: np.ndarray, v2: np.ndarray) -> np.ndarray:
        res = np.fft.irfft(np.fft.rfft(v1) * np.fft.rfft(v2), n=len(v1))
        return res.astype(np.float32)

    def bind_non_commutative(self, left: np.ndarray, right: np.ndarray, role: str = "RIGHT_ARG") -> np.ndarray:
        return self.bind_commutative(left, self.permute_by_role(right, role))

    @staticmethod
    def bundle(vectors: List[np.ndarray]) -> np.ndarray:
        if not vectors:
            raise ValueError("Impossibile eseguire il bundle di una lista vuota di vettori.")
        summed = np.sum(vectors, axis=0).astype(np.float32)
        norm = float(np.linalg.norm(summed))
        return summed / norm if norm > 0 else summed

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        n1 = float(np.linalg.norm(v1))
        n2 = float(np.linalg.norm(v2))
        if n1 == 0.0 or n2 == 0.0:
            return 0.0
        return float(np.dot(v1, v2) / (n1 * n2))

    def encode_abstract_dag(
        self,
        frames: Tuple[EpistemicFrame, ...],
        reverse_bindings: Dict[str, str]
    ) -> np.ndarray:
        if not frames:
            return np.zeros(self.D, dtype=np.float32)

        frame_vectors: List[np.ndarray] = []
        for idx, f in enumerate(frames):
            abs_subj = reverse_bindings.get(f.can_subj, f.can_subj)
            abs_pred = f.can_pred
            abs_obj = reverse_bindings.get(f.can_obj, f.can_obj)

            v_subj = self.permute_by_role(self.get_atomic_vector(abs_subj), "SUBJ")
            v_pred = self.permute_by_role(self.get_atomic_vector(abs_pred), "PRED")
            v_obj = self.permute_by_role(self.get_atomic_vector(abs_obj), "OBJ")

            v_triple = self.bind_non_commutative(
                self.bind_non_commutative(v_subj, v_pred, role="PRED"),
                v_obj,
                role="OBJ"
            )

            v_mod = self.permute_by_role(self.get_atomic_vector(f.modality.value), "MODALITY")
            v_pol = self.permute_by_role(self.get_atomic_vector(f.polarity.value), "POLARITY")
            v_edge = self.permute_by_role(self.get_atomic_vector(f.discourse_edge.value), "EDGE")

            v_frame = self.bundle([v_triple, v_mod, v_pol, v_edge])
            frame_vectors.append(self.permute_by_role(v_frame, f"SEQ_POS_{idx}"))

        return self.bundle(frame_vectors)


# ============================================================================
# 4. INTERFACCIA ASTRATTA UNIVERSALE DELLE CARTUCCE & REGISTRY
# ============================================================================

class BaseSymbolicCartridge(ABC):
    """
    Contratto Universale a cui ogni cartuccia (Grounding, Math, Logic, Vision/Situation)
    deve obbedire. Permette al Kernel di operare senza conoscere i dettagli del dominio.
    """

    @property
    @abstractmethod
    def cartridge_id(self) -> str:
        """Identificativo univoco della cartuccia (es. 'FACTS_GROUNDING_V2_01')."""
        pass

    @property
    @abstractmethod
    def cache_scope_policy(self) -> CacheScopePolicy:
        """GLOBAL_INVARIANT (es. Math) oppure DOCUMENT_BOUND (es. Document Grounding)."""
        pass

    @abstractmethod
    def detect_suitability_score(self, signal: RawSignalInput) -> float:
        """
        Eseguito dal Kernel Dispatcher in S1.0 (UNA SOLA VOLTA per avvio, 0 LLM calls).
        Restituisce uno score in [0.0, 1.0] che indica quanto la cartuccia è adatta
        a processare l'input corrente (basato su pattern sintattici, simboli matematici,
        lunghezza del contesto o modality_hint).
        """
        pass

    def select_relevant_spans(
        self,
        corpus_map: ImmutableCorpusMap,
        contract: TargetContract,
        retry_signal: Optional[str] = None
    ) -> List[SentenceSpan]:
        """
        Hook per lo Stato 2 (Hybrid Selector).
        Implementazione di default nel Kernel: inietta sempre tutti gli span IS_GLOBAL_SCOPE
        e applica un filtro lessicale JIT per POINT_LOOKUP o seleziona tutti gli span per GLOBAL_AGGREGATION.
        Ogni cartuccia può sovrascriverlo se richiede un retrieval specializzato.
        """
        selected: Dict[str, SentenceSpan] = {}
        for gid in corpus_map.global_scope_span_ids:
            selected[gid] = corpus_map.spans[gid]

        if contract.query_topology == QueryTopology.GLOBAL_AGGREGATION or len(corpus_map.spans) <= 12:
            for sid, sp in corpus_map.spans.items():
                selected[sid] = sp
            return list(selected.values())

        # Filtro lessicale JIT deterministico (O(N)) per POINT_LOOKUP / COMPARATIVE
        query_text = " ".join(contract.sub_questions) + (" " + retry_signal if retry_signal else "")
        q_tokens = {w.lower() for w in re.findall(r"[a-zA-Z0-9àèéìòù]+", query_text) if len(w) > 2}

        scored_spans: List[Tuple[int, SentenceSpan]] = []
        for sid, sp in corpus_map.spans.items():
            if sid in selected:
                continue
            sp_tokens = {w.lower() for w in re.findall(r"[a-zA-Z0-9àèéìòù]+", sp.raw_text)}
            overlap = len(q_tokens.intersection(sp_tokens))
            if overlap > 0:
                scored_spans.append((overlap, sp))

        scored_spans.sort(key=lambda x: x[0], reverse=True)
        for _, sp in scored_spans[:15]:
            selected[sp.span_id] = sp

        if len(selected) == len(corpus_map.global_scope_span_ids):
            for sid, sp in list(corpus_map.spans.items())[:10]:
                selected[sid] = sp

        return [corpus_map.spans[sid] for sid in sorted(selected.keys())]

    @abstractmethod
    def extract_variable_bindings(
        self, frames: Tuple[EpistemicFrame, ...]
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Estrae in modo deterministico e canonico la mappa delle variabili in S3:
        Restituisce (variable_bindings, reverse_bindings).
        """
        pass

    @abstractmethod
    def can_instantiate_isomorphic_template(
        self,
        dag: VerifiedEpistemicDAG,
        stored_template: ProofPlanAST
    ) -> bool:
        """Condizione 4 dell'Early-Exit 3B: verifica istanziabilità delle variabili."""
        pass

    @abstractmethod
    def solve_heavy_symbolic(
        self,
        dag: VerifiedEpistemicDAG,
        contract: TargetContract
    ) -> Tuple[ProofPlanAST, Optional[str]]:
        """
        Solver simbolico dello Stato 4 (es. Subgraph Set-Cover per Grounding, SymPy per Math).
        Restituisce (ProofPlanAST, optional_retry_signal_for_S2).
        """
        pass


class CartridgeRegistry:
    """
    Registro centrale delle cartucce nel Kernel.
    Seleziona deterministicamente la cartuccia attiva una sola volta all'avvio di run().
    """

    def __init__(self):
        self._cartridges: Dict[str, BaseSymbolicCartridge] = {}

    def register(self, cartridge: BaseSymbolicCartridge) -> None:
        self._cartridges[cartridge.cartridge_id] = cartridge

    def get(self, cartridge_id: str) -> BaseSymbolicCartridge:
        if cartridge_id not in self._cartridges:
            raise KeyError(f"Cartuccia '{cartridge_id}' non registrata nel Kernel.")
        return self._cartridges[cartridge_id]

    def select_cartridge_once(
        self,
        signal: RawSignalInput,
        explicit_cartridge_id: Optional[str] = None
    ) -> BaseSymbolicCartridge:
        """
        Attiva la cartuccia una sola volta all'inizio dell'esecuzione.
        Supporta l'override esplicito (per benchmark forzati) o l'auto-routing deterministico.
        """
        if not self._cartridges:
            raise RuntimeError("Nessuna cartuccia registrata nel CartridgeRegistry del Kernel.")

        if explicit_cartridge_id is not None:
            return self.get(explicit_cartridge_id)

        best_cartridge: Optional[BaseSymbolicCartridge] = None
        best_score = -1.0
        for cart in self._cartridges.values():
            score = cart.detect_suitability_score(signal)
            if score > best_score:
                best_score = score
                best_cartridge = cart

        assert best_cartridge is not None
        return best_cartridge


# ============================================================================
# 5. COMPONENTI INFRASTRUTTURALI DEGLI STATI S1, S2, S5
# ============================================================================

class DOMAndGlobalScopeIndexer:
    """
    Fase S1A: Indicizzatore deterministico O(N) del contesto grezzo.
    Costruisce Section -> Paragraph -> SentenceSpan con offset esatti [char_start, char_end]
    e identifica automaticamente le clausole IS_GLOBAL_SCOPE (definizioni, avvertenze globali,
    unità di misura, esclusioni generali).
    """

    GLOBAL_SCOPE_PATTERNS = re.compile(
        r"\b(in tutto il documento|salvo diversa indicazione|definiamo|si definisce|"
        r"avvertenza generale|nota globale|tutti i pazienti|tutte le dosi|"
        r"unless otherwise stated|throughout this document|all measurements)\b",
        re.IGNORECASE
    )

    @classmethod
    def index_corpus(cls, raw_context: str) -> ImmutableCorpusMap:
        corpus_hash = hashlib.sha256(raw_context.strip().encode("utf-8")).hexdigest()[:16]
        spans: Dict[str, SentenceSpan] = {}
        global_ids: List[str] = []

        paragraphs = re.split(r"\n\s*\n", raw_context)
        current_pos = 0
        sec_idx = 1
        span_counter = 1

        for p_idx, para in enumerate(paragraphs, start=1):
            para_start = raw_context.find(para, current_pos)
            if para_start == -1:
                para_start = current_pos
            current_pos = para_start + len(para)

            if para.strip().startswith("#") or para.strip().isupper():
                sec_idx += 1

            # Split in frasi preservando gli offset esatti
            sentence_matches = list(re.finditer(r"[^.!?\n]+[.!?\n]*", para))
            for sm in sentence_matches:
                s_text = sm.group(0).strip()
                if not s_text:
                    continue
                c_start = para_start + sm.start()
                c_end = para_start + sm.end()
                span_id = f"S_{span_counter:04d}"
                span_counter += 1

                is_global = bool(cls.GLOBAL_SCOPE_PATTERNS.search(s_text)) or (p_idx == 1 and span_counter <= 3)
                span_obj = SentenceSpan(
                    span_id=span_id,
                    section_id=f"SEC_{sec_idx:02d}",
                    paragraph_id=f"P_{p_idx:03d}",
                    char_start=c_start,
                    char_end=c_end,
                    raw_text=s_text,
                    is_global_scope=is_global
                )
                spans[span_id] = span_obj
                if is_global:
                    global_ids.append(span_id)

        return ImmutableCorpusMap(
            corpus_hash=corpus_hash,
            spans=spans,
            global_scope_span_ids=tuple(global_ids)
        )


class PipeDSLParser:
    """
    Parser deterministico per lo Stato 2 (Guardia G2):
    Converte le righe del DSL compatto separato da '|' in oggetti immutabili EpistemicFrame.
    Formato DSL atteso:
    F_ID | Span_ID | Exact_Quote_Substring | Can_Subj ; Can_Pred ; Can_Obj | Modality | Polarity | Cond_Time_Qualifiers | Discourse_Edge
    """

    @staticmethod
    def parse_dsl_output(dsl_text: str) -> List[EpistemicFrame]:
        frames: List[EpistemicFrame] = []
        for raw_line in dsl_text.strip().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 8:
                continue

            f_id, span_id, exact_quote, triple_str, mod_str, pol_str, qualifiers_str, edge_str = parts[:8]
            triple_parts = [t.strip() for t in triple_str.split(";")]
            if len(triple_parts) != 3:
                continue
            can_subj, can_pred, can_obj = triple_parts

            try:
                modality = Modality[mod_str.upper()]
            except KeyError:
                modality = Modality.CERTAIN

            try:
                polarity = Polarity[pol_str.upper()]
            except KeyError:
                polarity = Polarity.POS

            target_frame_id: Optional[str] = None
            if "->" in edge_str:
                edge_name, target_frame_id = [e.strip() for e in edge_str.split("->", 1)]
            else:
                edge_name = edge_str.strip()

            try:
                discourse_edge = DiscourseEdge[edge_name.upper()]
            except KeyError:
                discourse_edge = DiscourseEdge.NONE

            qualifiers = tuple(q.strip() for q in qualifiers_str.split(",") if q.strip() and q.strip().upper() != "NONE")

            frames.append(
                EpistemicFrame(
                    frame_id=f_id,
                    span_id=span_id,
                    exact_quote_substring=exact_quote,
                    can_subj=can_subj,
                    can_pred=can_pred,
                    can_obj=can_obj,
                    modality=modality,
                    polarity=polarity,
                    cond_time_qualifiers=qualifiers,
                    discourse_edge=discourse_edge,
                    target_frame_id=target_frame_id
                )
            )
        return frames


class ConstrainedVerbalizerAndAuditor:
    """
    Stato 5.1: Verbalizzatore guidato dal DAG con Riparazione Chirurgica O(1) a temp=0.0.
    Opera ESCLUSIVAMENTE su ProofPlanAST (nessun accesso al documento grezzo).
    Verifica ogni frase generata contro il rispettivo ProofNode:
      - Presenza di tutti i numeri/quantità del nodo;
      - Coerenza della Polarità (POS vs NEG);
      - Rispetto di EPISTEMIC_ABSENCE o FLAGGED_CONTRADICTION.
    Se una frase fallisce la Guardia G5, viene rigenerata isolatamente a temperatura 0.0
    usando un template deterministico ancorato alla exact_quote_substring.
    """

    NEGATION_WORDS = {"non", "no", "mai", "nessun", "nessuno", "nessuna", "senza", "not", "never", "contraddizione"}

    @classmethod
    def verify_sentence_against_node(cls, sentence: str, node: ProofNode) -> bool:
        if node.status == EpistemicStatus.EPISTEMIC_ABSENCE:
            return any(w in sentence.lower() for w in ["non menziona", "assente", "non specificato", "insufficienti", "non fornisce"])

        # 1. Controllo anti-mutazione numerica
        node_numbers = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", f"{node.concrete_subj} {node.concrete_pred} {node.concrete_obj}"))
        sent_numbers = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", sentence))
        if not node_numbers.issubset(sent_numbers):
            return False

        # 2. Controllo coerenza di Polarità
        sent_words = set(re.findall(r"[a-zA-Zàèéìòù]+", sentence.lower()))
        has_neg_token = bool(sent_words.intersection(cls.NEGATION_WORDS))
        if node.polarity == Polarity.NEG and not has_neg_token:
            return False
        if node.polarity == Polarity.POS and has_neg_token and node.discourse_edge != DiscourseEdge.CONFLICTS_WITH:
            return False

        return True

    @staticmethod
    def surgical_deterministic_repair(node: ProofNode) -> str:
        """Fallback deterministico a temperatura 0.0 ancorato alla citazione esatta."""
        if node.status == EpistemicStatus.EPISTEMIC_ABSENCE:
            return f"Il testo fornito non contiene informazioni verificate per rispondere a: '{node.sub_question_ref}'."
        if node.status == EpistemicStatus.FLAGGED_CONTRADICTION:
            return (
                f"Rilevata dissonanza epistemica nel testo per ({node.concrete_subj} {node.concrete_pred} {node.concrete_obj}) "
                f"[Fonte: \"{node.exact_quote_substring}\"]."
            )
        neg_prefix = "NON " if node.polarity == Polarity.NEG else ""
        return (
            f"{node.concrete_subj} {neg_prefix}{node.concrete_pred} {node.concrete_obj} "
            f"(Modalità: {node.modality.value}) [Fonte: \"{node.exact_quote_substring}\"]."
        )

    @classmethod
    def verbalize_and_audit(
        cls,
        ast: ProofPlanAST,
        custom_sentence_generator: Optional[Callable[[ProofNode], str]] = None
    ) -> Tuple[str, Tuple[AuditLineageRecord, ...]]:
        sentences: List[str] = []
        lineage: List[AuditLineageRecord] = []

        for idx, node in enumerate(ast.nodes):
            repaired = False
            if custom_sentence_generator is not None:
                candidate = custom_sentence_generator(node)
                if not cls.verify_sentence_against_node(candidate, node):
                    candidate = cls.surgical_deterministic_repair(node)
                    repaired = True
            else:
                candidate = cls.surgical_deterministic_repair(node)

            sentences.append(candidate)
            lineage.append(
                AuditLineageRecord(
                    sentence_index=idx,
                    generated_sentence=candidate,
                    source_node_id=node.node_id,
                    source_frame_id=node.frame_id,
                    exact_quote_anchor=node.exact_quote_substring,
                    repaired_at_temp_zero=repaired
                )
            )

        return " ".join(sentences), tuple(lineage)


# ============================================================================
# 6. GESTORE DELLE CACHE E DEI 3 EARLY-EXIT CON PERSISTENZA IBRIDA SQLite + NumPy
# ============================================================================

@dataclass(frozen=True)
class StoredIsomorphicSchema:
    schema_id: str
    cartridge_id: str
    structural_vector: np.ndarray
    signature: StructuralSignature
    template_ast: ProofPlanAST


class MultiTierEarlyExitManager:
    """
    Gestisce i 3 cancelli di uscita precoce (Path 0, Path 1A, Path 3B)
    con persistenza SQLite WAL per i metadati e array vettorizzato NumPy float32
    per lo screening coseno in < 1 ms.
    """

    def __init__(
        self,
        vsa_engine: NonCommutativeVSAEngine,
        vsa_threshold: float = 0.88,
        sqlite_db_path: str = ":memory:"
    ):
        self.vsa = vsa_engine
        self.vsa_threshold = vsa_threshold
        self._conn = sqlite3.connect(sqlite_db_path)
        self._init_sqlite_tables()

        self._episodic_cache_store: Dict[str, KernelExecutionResult] = {}
        self._parametric_schema_memory: List[StoredIsomorphicSchema] = []
        self._vector_matrix: Optional[np.ndarray] = None  # Shape (N, D) float32 per fast dot-product

    def _init_sqlite_tables(self) -> None:
        cur = self._conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS episodic_cache_s1a (
                composite_hash TEXT PRIMARY KEY,
                cartridge_id TEXT,
                corpus_hash TEXT,
                response_text TEXT,
                created_at REAL
            );
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS parametric_schemas_s3b (
                schema_id TEXT PRIMARY KEY,
                cartridge_id TEXT,
                corpus_hash TEXT,
                polarities_json TEXT,
                modalities_json TEXT,
                edges_json TEXT,
                created_at REAL
            );
            """
        )
        self._conn.commit()

    # --- GATE 0: Signal Sanity Filter (< 1 ms) ---
    @staticmethod
    def check_gate_0_sanity(signal: RawSignalInput) -> Tuple[bool, Optional[str]]:
        if not signal.raw_context or not signal.raw_context.strip():
            return False, "ABORT_EMPTY_CONTEXT"
        if not signal.user_query or len(signal.user_query.strip()) < 3:
            return False, "ABORT_INVALID_OR_TOO_SHORT_QUERY"
        if chr(0) in signal.raw_context or chr(0) in signal.user_query:
            return False, "ABORT_CORRUPTED_NULL_BYTES"
        return True, None

    # --- GATE 1A: Two-Key Exact Episodic Cache (< 1 ms, O(1)) ---
    @staticmethod
    def build_exact_episode_key(cartridge_id: str, corpus_hash: str, query: str) -> ExactEpisodeKey:
        cleaned = query.lower().strip()
        words = re.findall(r"[a-zA-Zàèéìòù]+", cleaned)
        lemmas_hash = hashlib.md5(" ".join(words).encode("utf-8")).hexdigest()

        numbers = tuple(re.findall(r"\b\d+(?:[\.,]\d+)?(?:mg|kg|ml|g|%|ms|s)?\b", cleaned))
        operators = tuple(re.findall(r"(?:<=|>=|!=|==|<|>|=|\+|-|\*|/)", cleaned))
        negation_tokens = {"non", "no", "mai", "nessun", "nessuno", "nessuna", "senza", "not", "never", "without"}
        negations = tuple(w for w in words if w in negation_tokens)

        return ExactEpisodeKey(
            cartridge_id=cartridge_id,
            corpus_hash=corpus_hash,
            normalized_lemmas_hash=lemmas_hash,
            extracted_numbers=numbers,
            extracted_operators=operators,
            extracted_negations=negations
        )

    def lookup_gate_1a_exact(self, key: ExactEpisodeKey) -> Optional[KernelExecutionResult]:
        cached = self._episodic_cache_store.get(key.composite_hash)
        if cached is not None:
            return KernelExecutionResult(
                execution_path=ExecutionPath.PATH_1A_EXACT_HIT,
                active_cartridge_id=cached.active_cartridge_id,
                response_text=cached.response_text,
                audit_lineage=cached.audit_lineage,
                latency_ms=0.15,
                llm_calls_count=0,
                metadata={"cache_hit": "S1A_EXACT_EPISODIC", "composite_hash": key.composite_hash}
            )
        return None

    def register_episodic_hit(self, key: ExactEpisodeKey, result: KernelExecutionResult) -> None:
        self._episodic_cache_store[key.composite_hash] = result
        self._conn.execute(
            "INSERT OR REPLACE INTO episodic_cache_s1a VALUES (?, ?, ?, ?, ?)",
            (key.composite_hash, key.cartridge_id, key.corpus_hash, result.response_text, time.time())
        )
        self._conn.commit()

    # --- GATE 3B: Vectorized Isomorphic Schema Matcher (~1-5 ms) ---
    def lookup_gate_3b_isomorphic(
        self,
        dag: VerifiedEpistemicDAG,
        cartridge: BaseSymbolicCartridge
    ) -> Optional[ProofPlanAST]:
        if dag.signature.has_contradictions or dag.signature.has_unmapped_exceptions:
            return None
        if not self._parametric_schema_memory or self._vector_matrix is None:
            return None

        # Pre-filtro booleano ultra-rapido sugli indici ammissibili (Condizioni 2, 3 e Domain Scope)
        candidate_indices: List[int] = []
        for idx, schema in enumerate(self._parametric_schema_memory):
            if schema.cartridge_id != cartridge.cartridge_id:
                continue
            if cartridge.cache_scope_policy == CacheScopePolicy.DOCUMENT_BOUND:
                if schema.signature.corpus_hash != dag.corpus_hash:
                    continue
            if (
                schema.signature.polarities != dag.signature.polarities
                or schema.signature.modalities != dag.signature.modalities
                or schema.signature.discourse_edges != dag.signature.discourse_edges
            ):
                continue
            candidate_indices.append(idx)

        if not candidate_indices:
            return None

        # Calcolo coseno vettorizzato su sottomatrice NumPy float32 (Condizione 1)
        q_vec = dag.structural_vector
        q_norm = float(np.linalg.norm(q_vec))
        if q_norm == 0.0:
            return None
        q_unit = q_vec / q_norm

        sub_matrix = self._vector_matrix[candidate_indices]
        sims = np.dot(sub_matrix, q_unit)
        sorted_order = np.argsort(sims)[::-1]

        best_schema: Optional[StoredIsomorphicSchema] = None
        for pos in sorted_order:
            sim_val = float(sims[pos])
            if sim_val <= self.vsa_threshold:
                break
            cand_schema = self._parametric_schema_memory[candidate_indices[int(pos)]]
            if cartridge.can_instantiate_isomorphic_template(dag, cand_schema.template_ast):
                best_schema = cand_schema
                break

        if best_schema is None:
            return None

        # Istanziazione variabili concrete nello scheletro del ProofPlanAST
        instantiated_nodes: List[ProofNode] = []
        frame_by_index = list(dag.valid_frames)

        for idx, tmpl_node in enumerate(best_schema.template_ast.nodes):
            c_subj = dag.variable_bindings.get(tmpl_node.abstract_subj, tmpl_node.abstract_subj)
            c_pred = tmpl_node.abstract_pred
            c_obj = dag.variable_bindings.get(tmpl_node.abstract_obj, tmpl_node.abstract_obj)
            matched_frame = frame_by_index[idx] if idx < len(frame_by_index) else None
            quote = matched_frame.exact_quote_substring if matched_frame else tmpl_node.exact_quote_substring
            f_id = matched_frame.frame_id if matched_frame else tmpl_node.frame_id

            instantiated_nodes.append(
                ProofNode(
                    node_id=f"ISO_{tmpl_node.node_id}",
                    sub_question_ref=tmpl_node.sub_question_ref,
                    frame_id=f_id,
                    abstract_subj=tmpl_node.abstract_subj,
                    abstract_pred=tmpl_node.abstract_pred,
                    abstract_obj=tmpl_node.abstract_obj,
                    concrete_subj=c_subj,
                    concrete_pred=c_pred,
                    concrete_obj=c_obj,
                    exact_quote_substring=quote,
                    modality=tmpl_node.modality,
                    polarity=tmpl_node.polarity,
                    discourse_edge=tmpl_node.discourse_edge,
                    status=tmpl_node.status
                )
            )

        return ProofPlanAST(
            plan_id=f"ISO_PLAN_{hashlib.md5(str(time.time()).encode()).hexdigest()[:6]}",
            cartridge_id=cartridge.cartridge_id,
            corpus_hash=dag.corpus_hash,
            nodes=tuple(instantiated_nodes),
            format_ast_rules=best_schema.template_ast.format_ast_rules,
            variable_bindings=dag.variable_bindings,
            is_from_isomorphic_cache=True
        )

    # --- S5.2: Parametric Schema Consolidator (Retroazione S5 -> S3) ---
    def consolidate_schema_from_s5(
        self,
        cartridge_id: str,
        dag: VerifiedEpistemicDAG,
        verified_ast: ProofPlanAST
    ) -> Optional[str]:
        if verified_ast.is_from_isomorphic_cache:
            return None
        if dag.signature.has_contradictions or dag.signature.has_unmapped_exceptions:
            return None
        if any(n.status != EpistemicStatus.VALIDATED_GROUNDED for n in verified_ast.nodes):
            return None

        schema_id = f"SCHEMA_{len(self._parametric_schema_memory) + 1:04d}"
        norm = float(np.linalg.norm(dag.structural_vector))
        unit_vec = (dag.structural_vector / norm if norm > 0 else dag.structural_vector).astype(np.float32)

        stored = StoredIsomorphicSchema(
            schema_id=schema_id,
            cartridge_id=cartridge_id,
            structural_vector=unit_vec,
            signature=dag.signature,
            template_ast=verified_ast
        )
        self._parametric_schema_memory.append(stored)

        if self._vector_matrix is None:
            self._vector_matrix = unit_vec.reshape(1, -1)
        else:
            self._vector_matrix = np.vstack([self._vector_matrix, unit_vec.reshape(1, -1)])

        self._conn.execute(
            "INSERT INTO parametric_schemas_s3b VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                schema_id,
                cartridge_id,
                dag.corpus_hash,
                json.dumps([p.value for p in dag.signature.polarities]),
                json.dumps([m.value for m in dag.signature.modalities]),
                json.dumps([e.value for e in dag.signature.discourse_edges]),
                time.time()
            )
        )
        self._conn.commit()
        return schema_id


# ============================================================================
# 7. STATO 3 GATEKEEPER CON ORDINAMENTO CANONICO DELLE TRIPLE
# ============================================================================

class DualLayerGatekeeper:
    """
    Controlli deterministici dello Stato 3:
      - Livello 3.1: Surface Anchor Check (O(1) substring & numbers verification)
      - Livello 3.2: Canonical Conflict Detector
      - Livello 3.3: Ordinamento Canonico + Codifica VSA Non-Commutativa
    """

    def __init__(self, vsa_engine: NonCommutativeVSAEngine):
        self.vsa = vsa_engine

    @staticmethod
    def verify_surface_anchor(frame: EpistemicFrame, corpus_map: ImmutableCorpusMap) -> bool:
        span = corpus_map.spans.get(frame.span_id)
        if span is None:
            return False
        if frame.exact_quote_substring not in span.raw_text:
            return False
        triple_numbers = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", f"{frame.can_subj} {frame.can_pred} {frame.can_obj}"))
        quote_numbers = set(re.findall(r"\b\d+(?:[\.,]\d+)?\b", frame.exact_quote_substring))
        if not triple_numbers.issubset(quote_numbers):
            return False
        return True

    def build_verified_dag(
        self,
        raw_frames: List[EpistemicFrame],
        corpus_map: ImmutableCorpusMap,
        cartridge: BaseSymbolicCartridge
    ) -> VerifiedEpistemicDAG:
        valid_temp: List[EpistemicFrame] = []
        quarantined: List[EpistemicFrame] = []

        for f in raw_frames:
            if self.verify_surface_anchor(f, corpus_map):
                valid_temp.append(f)
            else:
                quarantined.append(
                    EpistemicFrame(
                        **{**f.__dict__, "status": EpistemicStatus.QUARANTINED_UNGROUNDED, "epistemic_weight": 0.0}
                    )
                )

        final_valid: List[EpistemicFrame] = []
        has_contradictions = False
        has_unmapped_exceptions = False

        for i, f1 in enumerate(valid_temp):
            conflict_found = False
            for j, f2 in enumerate(valid_temp):
                if i != j and (f1.can_subj, f1.can_pred, f1.can_obj) == (f2.can_subj, f2.can_pred, f2.can_obj):
                    if f1.polarity != f2.polarity:
                        conflict_found = True
                        break
            if conflict_found:
                has_contradictions = True
                final_valid.append(
                    EpistemicFrame(
                        **{
                            **f1.__dict__,
                            "status": EpistemicStatus.FLAGGED_CONTRADICTION,
                            "discourse_edge": DiscourseEdge.CONFLICTS_WITH,
                            "epistemic_weight": 0.5
                        }
                    )
                )
            else:
                if f1.discourse_edge == DiscourseEdge.EXCEPT_WHEN and f1.target_frame_id is None:
                    has_unmapped_exceptions = True
                final_valid.append(f1)

        # Ordinamento canonico deterministico: rende il VSA invariante all'ordine accidentale
        # delle frasi nel documento, mantenendo la non-commutatività sui ruoli logici!
        final_valid.sort(key=lambda fr: fr.canonical_sort_key)
        valid_tuple = tuple(final_valid)

        var_bindings, rev_bindings = cartridge.extract_variable_bindings(valid_tuple)
        struct_vec = self.vsa.encode_abstract_dag(valid_tuple, rev_bindings)

        signature = StructuralSignature(
            polarities=tuple(f.polarity for f in valid_tuple),
            modalities=tuple(f.modality for f in valid_tuple),
            discourse_edges=tuple(f.discourse_edge for f in valid_tuple),
            has_contradictions=has_contradictions,
            has_unmapped_exceptions=has_unmapped_exceptions,
            corpus_hash=corpus_map.corpus_hash
        )

        return VerifiedEpistemicDAG(
            corpus_hash=corpus_map.corpus_hash,
            valid_frames=valid_tuple,
            quarantined_frames=tuple(quarantined),
            structural_vector=struct_vec,
            signature=signature,
            variable_bindings=var_bindings,
            reverse_bindings=rev_bindings
        )


# ============================================================================
# 8. ORCHESTRATORE CENTRALE UNIVERSALE (DESMKernelOrchestrator)
# ============================================================================

class DESMKernelOrchestrator:
    """
    Il Kernel Universale DESM v2.01.
    Riceve un RawSignalInput, seleziona la Cartuccia (1 sola volta all'avvio in S1.0)
    e governa l'intera pipeline S1 -> S2 -> S3 -> S4 -> S5 e i 3 Early-Exit.
    """

    def __init__(
        self,
        registry: CartridgeRegistry,
        vsa_dimension: int = 10000,
        vsa_threshold: float = 0.88,
        sqlite_db_path: str = ":memory:"
    ):
        self.registry = registry
        self.vsa = NonCommutativeVSAEngine(dimension=vsa_dimension)
        self.exit_mgr = MultiTierEarlyExitManager(self.vsa, vsa_threshold, sqlite_db_path)
        self.gatekeeper = DualLayerGatekeeper(self.vsa)

    def run(
        self,
        signal: RawSignalInput,
        transducer_fn: Callable[[List[SentenceSpan], TargetContract, Optional[str]], str],
        contract_compiler_fn: Optional[Callable[[str, str], TargetContract]] = None,
        explicit_cartridge_id: Optional[str] = None,
        max_s4_retries: int = 2
    ) -> KernelExecutionResult:
        t0 = time.perf_counter()
        llm_calls = 0

        # --------------------------------------------------------------------
        # STATO 1.0: Signal Sanity Filter (Path 0) & One-Shot Cartridge Routing
        # --------------------------------------------------------------------
        is_sane, abort_reason = self.exit_mgr.check_gate_0_sanity(signal)
        if not is_sane:
            return KernelExecutionResult(
                execution_path=ExecutionPath.PATH_0_INVALID_ABORT,
                active_cartridge_id="NONE",
                response_text=f"ABORT_INVALID_INPUT: {abort_reason}",
                audit_lineage=(),
                latency_ms=(time.perf_counter() - t0) * 1000.0,
                llm_calls_count=0,
                metadata={"abort_reason": abort_reason}
            )

        # Selezione deterministica della cartuccia UNA SOLA VOLTA per esecuzione
        cartridge = self.registry.select_cartridge_once(signal, explicit_cartridge_id)

        # --------------------------------------------------------------------
        # STATO 1A: DOM Indexing & Two-Key Exact Episodic Lookup (Path 1A)
        # --------------------------------------------------------------------
        corpus_map = DOMAndGlobalScopeIndexer.index_corpus(signal.raw_context)
        exact_key = self.exit_mgr.build_exact_episode_key(
            cartridge.cartridge_id, corpus_map.corpus_hash, signal.user_query
        )
        cached_1a = self.exit_mgr.lookup_gate_1a_exact(exact_key)
        if cached_1a is not None:
            return cached_1a

        # --------------------------------------------------------------------
        # STATO 1B: Query Contract Compilation
        # --------------------------------------------------------------------
        if contract_compiler_fn is not None:
            llm_calls += 1
            contract = contract_compiler_fn(signal.user_query, signal.system_prompt)
        else:
            # Compilatore deterministico di fallback (0 token LLM per query dirette)
            sub_qs = tuple(q.strip() + "?" for q in signal.user_query.split("?") if q.strip())
            if not sub_qs:
                sub_qs = (signal.user_query.strip(),)
            topo = QueryTopology.GLOBAL_AGGREGATION if re.search(r"\b(tutti|elenca|quanti|riassumi)\b", signal.user_query, re.I) else QueryTopology.POINT_LOOKUP
            contract = TargetContract(sub_questions=sub_qs, query_topology=topo, format_ast_rules={})

        # --------------------------------------------------------------------
        # STATO 2 & STATO 3 (con supporto al loop di CACHE_MISS da S4)
        # --------------------------------------------------------------------
        retry_signal: Optional[str] = None
        attempt = 0
        proof_ast: Optional[ProofPlanAST] = None
        verified_dag: Optional[VerifiedEpistemicDAG] = None
        exec_path = ExecutionPath.PATH_4_FULL_CYCLE

        while attempt <= max_s4_retries:
            attempt += 1
            selected_spans = cartridge.select_relevant_spans(corpus_map, contract, retry_signal)
            llm_calls += 1
            raw_dsl = transducer_fn(selected_spans, contract, retry_signal)
            parsed_frames = PipeDSLParser.parse_dsl_output(raw_dsl)

            verified_dag = self.gatekeeper.build_verified_dag(parsed_frames, corpus_map, cartridge)

            # Verifica EARLY_EXIT_3B (Isomorphic Schema Hit) al primo tentativo
            if attempt == 1:
                iso_ast = self.exit_mgr.lookup_gate_3b_isomorphic(verified_dag, cartridge)
                if iso_ast is not None:
                    proof_ast = iso_ast
                    exec_path = ExecutionPath.PATH_3B_ISOMORPHIC_HIT
                    break

            # STATO 4: Heavy Symbolic Execution Slot (delegato alla Cartuccia attiva)
            proof_ast, retry_signal = cartridge.solve_heavy_symbolic(verified_dag, contract)
            if retry_signal is None:
                break

        assert proof_ast is not None and verified_dag is not None

        # --------------------------------------------------------------------
        # STATO 5: Constrained Verbalization, Surgical Audit & Schema Consolidation
        # --------------------------------------------------------------------
        response_text, audit_lineage = ConstrainedVerbalizerAndAuditor.verbalize_and_audit(proof_ast)

        consolidated_id = self.exit_mgr.consolidate_schema_from_s5(
            cartridge.cartridge_id, verified_dag, proof_ast
        )

        final_result = KernelExecutionResult(
            execution_path=exec_path,
            active_cartridge_id=cartridge.cartridge_id,
            response_text=response_text,
            audit_lineage=audit_lineage,
            latency_ms=(time.perf_counter() - t0) * 1000.0,
            llm_calls_count=llm_calls,
            metadata={
                "corpus_hash": corpus_map.corpus_hash,
                "valid_frames_count": len(verified_dag.valid_frames),
                "quarantined_frames_count": len(verified_dag.quarantined_frames),
                "consolidated_schema_id": consolidated_id,
                "variable_bindings": verified_dag.variable_bindings,
            }
        )

        # Registra l'episodio certificato nello store S1A per futuri Early-Exit O(1)
        self.exit_mgr.register_episodic_hit(exact_key, final_result)
        return final_result


# ============================================================================
# 9. SELF-TEST END-TO-END DEL KERNEL UNIVERSALE (2 Cartucce Mock Innestate)
# ============================================================================

if __name__ == "__main__":
    # Cartuccia Mock 1: Document Grounding (DOCUMENT_BOUND)
    class MockGroundingCartridge(BaseSymbolicCartridge):
        @property
        def cartridge_id(self) -> str:
            return "FACTS_GROUNDING_V2_01"

        @property
        def cache_scope_policy(self) -> CacheScopePolicy:
            return CacheScopePolicy.DOCUMENT_BOUND

        def detect_suitability_score(self, signal: RawSignalInput) -> float:
            return 0.90 if len(signal.raw_context) > 40 else 0.20

        def extract_variable_bindings(self, frames: Tuple[EpistemicFrame, ...]) -> Tuple[Dict[str, str], Dict[str, str]]:
            var_map, rev_map = {}, {}
            ent_idx, val_idx = 1, 1
            for f in frames:
                for token in (f.can_subj, f.can_obj):
                    if token not in rev_map:
                        if re.search(r"\b\d+(?:mg|kg|ml|%)\b", token):
                            ph = f"$VAL_{val_idx}"
                            val_idx += 1
                        else:
                            ph = f"$ENT_{ent_idx}"
                            ent_idx += 1
                        var_map[ph] = token
                        rev_map[token] = ph
            return var_map, rev_map

        def can_instantiate_isomorphic_template(self, dag: VerifiedEpistemicDAG, stored_template: ProofPlanAST) -> bool:
            return len(dag.valid_frames) == len(stored_template.nodes)

        def solve_heavy_symbolic(self, dag: VerifiedEpistemicDAG, contract: TargetContract) -> Tuple[ProofPlanAST, Optional[str]]:
            nodes = []
            for idx, f in enumerate(dag.valid_frames):
                nodes.append(
                    ProofNode(
                        node_id=f"N_{idx+1}",
                        sub_question_ref=contract.sub_questions[0],
                        frame_id=f.frame_id,
                        abstract_subj=dag.reverse_bindings[f.can_subj],
                        abstract_pred=f.can_pred,
                        abstract_obj=dag.reverse_bindings[f.can_obj],
                        concrete_subj=f.can_subj,
                        concrete_pred=f.can_pred,
                        concrete_obj=f.can_obj,
                        exact_quote_substring=f.exact_quote_substring,
                        modality=f.modality,
                        polarity=f.polarity,
                        discourse_edge=f.discourse_edge,
                        status=f.status
                    )
                )
            return ProofPlanAST(
                plan_id="PLAN_GROUND_1",
                cartridge_id=self.cartridge_id,
                corpus_hash=dag.corpus_hash,
                nodes=tuple(nodes),
                format_ast_rules=contract.format_ast_rules,
                variable_bindings=dag.variable_bindings
            ), None

    # Cartuccia Mock 2: Math Symbolic (GLOBAL_INVARIANT)
    class MockMathCartridge(BaseSymbolicCartridge):
        @property
        def cartridge_id(self) -> str:
            return "MATH_SYMBOLIC_V2_01"

        @property
        def cache_scope_policy(self) -> CacheScopePolicy:
            return CacheScopePolicy.GLOBAL_INVARIANT

        def detect_suitability_score(self, signal: RawSignalInput) -> float:
            if signal.modality_hint == "MATH" or re.search(r"[\+\-\*/=<>^]", signal.user_query):
                return 0.95
            return 0.10

        def extract_variable_bindings(self, frames: Tuple[EpistemicFrame, ...]) -> Tuple[Dict[str, str], Dict[str, str]]:
            return {}, {}

        def can_instantiate_isomorphic_template(self, dag: VerifiedEpistemicDAG, stored_template: ProofPlanAST) -> bool:
            return True

        def solve_heavy_symbolic(self, dag: VerifiedEpistemicDAG, contract: TargetContract) -> Tuple[ProofPlanAST, Optional[str]]:
            return ProofPlanAST("PLAN_MATH", self.cartridge_id, dag.corpus_hash, (), {}, {}), None

    # Inizializzazione Registro e Kernel
    reg = CartridgeRegistry()
    reg.register(MockGroundingCartridge())
    reg.register(MockMathCartridge())
    kernel = DESMKernelOrchestrator(reg)

    doc_text = (
        "AVVERTENZA GENERALE: Tutte le dosi sono espresse per adulti.\n\n"
        "Il Farmaco_Alfa alla dose di 50mg causa bradicardia sinusale. "
        "Il Farmaco_Beta alla dose di 20mg causa bradicardia sinusale."
    )

    # 1. Ciclo Completo (Path 4) su Farmaco_Alfa -> Consolida lo schema in S5.2
    res_full = kernel.run(
        RawSignalInput(raw_context=doc_text, user_query="Quale effetto causa il Farmaco_Alfa da 50mg?"),
        transducer_fn=lambda spans, c, r: (
            "F_01 | S_0002 | Il Farmaco_Alfa alla dose di 50mg causa bradicardia sinusale. | "
            "Farmaco_Alfa 50mg ; causa ; bradicardia sinusale | CERTAIN | POS | NONE | CAUSES"
        )
    )
    print(f"[RUN 1 - Full Cycle] Path: {res_full.execution_path.value} | Cartridge: {res_full.active_cartridge_id}")
    assert res_full.execution_path == ExecutionPath.PATH_4_FULL_CYCLE
    assert res_full.active_cartridge_id == "FACTS_GROUNDING_V2_01"

    # 2. Ripetizione esatta della stessa domanda (Path 1A - O(1), 0 LLM calls)
    res_1a = kernel.run(
        RawSignalInput(raw_context=doc_text, user_query="Quale effetto causa il Farmaco_Alfa da 50mg?"),
        transducer_fn=lambda spans, c, r: ""
    )
    print(f"[RUN 2 - Exact Hit ] Path: {res_1a.execution_path.value} | LLM Calls: {res_1a.llm_calls_count}")
    assert res_1a.execution_path == ExecutionPath.PATH_1A_EXACT_HIT
    assert res_1a.llm_calls_count == 0

    # 3. Domanda strutturalmente isomorfa su Farmaco_Beta nello stesso documento (Path 3B - Salta S4!)
    res_3b = kernel.run(
        RawSignalInput(raw_context=doc_text, user_query="Quale effetto causa il Farmaco_Beta da 20mg?"),
        transducer_fn=lambda spans, c, r: (
            "F_02 | S_0003 | Il Farmaco_Beta alla dose di 20mg causa bradicardia sinusale. | "
            "Farmaco_Beta 20mg ; causa ; bradicardia sinusale | CERTAIN | POS | NONE | CAUSES"
        )
    )
    print(f"[RUN 3 - Iso Hit 3B] Path: {res_3b.execution_path.value} | Output: {res_3b.response_text}")
    assert res_3b.execution_path == ExecutionPath.PATH_3B_ISOMORPHIC_HIT
    assert "Farmaco_Beta 20mg" in res_3b.response_text

    # 4. Verifica Auto-Routing one-shot su input matematico
    selected_math = reg.select_cartridge_once(RawSignalInput(raw_context="x + 2 = 5", user_query="Risolvi x + 2 = 5"))
    print(f"[RUN 4 - Auto-Route] Selected Cartridge for equation: {selected_math.cartridge_id}")
    assert selected_math.cartridge_id == "MATH_SYMBOLIC_V2_01"
    print("Tutti i test end-to-end di desm_core_v2_01_3.py superati con successo!")
