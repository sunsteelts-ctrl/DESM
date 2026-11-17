# COGNITIVE ARCHITECTURE THEORY & HARDWARE-SOFTWARE ISOMORPHISM
**From the 17 Cognitive Moments (*Citta-vīthi*) and 24 Causal Conditions (*Paṭṭhāna*) to the DESM Deterministic Kernel**

This document defines the theoretical, computational, and physical-logical model underlying the **DESM (Deterministic Epistemic State Machine)** neuro-symbolic architecture. It formalizes the structural isomorphism between Abhidhamma cognitive mechanics (*Citta-vīthi*, *Cetasika*, *Rūpa*, *Paṭṭhāna*, and *Yamaka*) and a deterministic hardware/software architecture with progressive energy allocation.

---

## PART I: SYSTEM ARCHITECTURE — THE 17-CLOCK-CYCLE EPISTEMIC MACHINE ($T_1 \dots T_{17}$)

An ideal hardware/software or neuro-computational architecture based on *Citta-vīthi* (17 moments) and *Paṭṭhāna* (24 conditions) is not an *always-on*, continuous-cycle system (like a GPU grinding matrices at a fixed frequency), but an **event-driven asynchronous processor**, strictly serial in its executive state and governed by progressive energy allocation.

### Preliminary Critical Analysis: Engineering Advantages and Limitations
* **The Structural Advantage:** It solves energy consumption and state interference (*race conditions*) at the root. Because only one moment of consciousness can exist per clock instant (*Natthi/Vigata*), shared-memory corruption or hallucinations caused by overlapping contexts are mathematically impossible. Furthermore, the **biological Early-Exit** mechanism (stimuli terminating at moment 3, 4, or 8) prunes roughly $90\%$ of unnecessary computation before powering up the heavy executive cores (moments $9\text{--}15$).
* **The Physical Limitation (and its Silicon Correction):** A biological brain or pure Abhidhammic system is strictly *single-threaded* at the executive level (the human illusion of multitasking arises from ultra-high-frequency switching across 17-moment cycles). On modern hardware, enforcing a global single thread would bottleneck throughput. The optimal engineering solution is to **isolate the 17 moments per individual "Context/Query Unit" (Isolated Tile / Core)**, keeping internal execution within each single cycle strictly governed by the 24 *Paccaya*.

---

### 1. Base Hardware Axiom: Asynchronous Coupling of *Rūpa* / *Nāma*
Two separate physical domains exist within the machine; they never merge (**20. Vippayutta** — *Dissociation*), yet they cooperate tightly:
1. **Physical Substrate / DMA Memory (*Rūpa*):** Sensory buses, physical registers, and the incoming signal buffer. They operate on a slow clock: when a data packet (stimulus) is loaded into the input register, it is assigned a **fixed hardware Time-To-Live (TTL) of exactly 17 ticks** of the logical clock. Once the 17th tick expires, the physical buffer automatically flushes.
2. **Logical State Unit (*Nāma / Citta*):** The state processor. It runs at a clock speed 17 times faster than the data bus. At each tick ($T_k$), it instantiates a single immutable state object that reads from the physical buffer until the TTL expires.

---

### 2. Machine Flowchart ($T_1 \to T_{17}$ Cycle + 24 *Paccaya*)

```text
[PHYSICAL BUS / DMA (Rupa)] -- TTL = 17 Ticks (12. Purejata, 10. Nissaya, 21. Atthi, 22. Avigata) ----------------------+
                                                                                                                        |
[IDLE STATE (Bhavanga)]                                                                                           [TTL EXPIRED]
  T1: Atita (Blank tick) --> T2: Calana (SNR Oscillation) --> T3: Upaccheda (Interrupt / Wake-up)                       |
                                   |                                  |                                                 |
                      [SNR < Threshold: EXIT MOGHA-VARA]              v                                                 |
                                                              [INGRESS & ROUTING PHASE]                                 |
                                                                T4: Avajjana (Mux/Router: selects channel)              |
                                                                T5: Vinnana  (Raw A/D sampling)                         |
                                                                T6: Sampaticchana (L1 Buffer Latch)                     |
                                                                T7: Santirana (Integrity & base signature check)        |
                                                                      |                                                 |
                                                     [TTL nearly expired: EXIT PARITTA]                                 |
                                                                      |                                                 |
                                                                      v                                                 |
                                                              [THE DECISION GATE]                                       |
                                                                T8: Votthapana (Gatekeeper / AST Compilation)           |
                                                                Applies: 1. Hetu, 3. Adhipati, 18. Magga                |
                                                                      |                                                 |
                                                +---------------------+---------------------+                           |
                                                v (Requires Computation)                    v (Isomorphic/Cache Hit)    |
                                  [EXECUTIVE ENGINE: 7 JAVANA]                   [DETERMINISTIC BYPASS]                 |
                                    T9  (Pulse 1: Init Solver) ----+                        |                           |
                                    T10 (Pulse 2: + 7. Asevana)    |                        |                           |
                                    T11 (Pulse 3: + 7. Asevana)    | Iterative              |                           |
                                    T12 (Pulse 4: Peak Kamma)      | Refinement &           |                           |
                                    T13 (Pulse 5: + 7. Asevana)    | Deduction Loop         |                           |
                                    T14 (Pulse 6: + 7. Asevana)    | (14. Kamma)            |                           |
                                    T15 (Pulse 7: State Commit) ---+                        |                           |
                                                |                                           |                           |
                                                +---------------------+---------------------+                           |
                                                                      v                                                 |
                                                     [Remaining TTL == 0: EXIT MAHANTA]                                 |
                                                                      |                                                 |
                                                                      v (If 2 TTL ticks remain)                         |
                                                              [CONSOLIDATION & WRITE-BACK]                              |
                                                                T16: Tadarammana 1 (Cache / Log Write)                  |
                                                                T17: Tadarammana 2 (6. Upanissaya Update) <-------------+
                                                                      |
                                                                      v
                                                        [RETURN TO BHAVANGA (Idle)]
```

---

### 3. Operational Anatomy: How the 24 *Paccaya* Govern the Hardware Across the 17 Moments

The 24 conditional relations (*Paccaya*) are not abstract philosophical concepts, but hardware control circuits triggered at exact points across the 17 ticks:

#### A. Clock Mechanism and State Transition ($T_k \to T_{k+1}$)
There is no external "main loop" moving data from $T_4$ to $T_5$. Rather, state $T_k$, by terminating, directly spawns $T_{k+1}$:
* **23. Natthi (Absence) & 24. Vigata (Disappearance):** State register $T_k$ is physically zeroed/deallocated at the end of its tick. Until $100\%$ of $T_k$'s memory is released, the gate for $T_{k+1}$ cannot receive power (*zero memory leaks, zero phantom states*).
* **4. Anantara (Proximity) & 5. Samanantara (Contiguity):** The discharge pulse of $T_k$ (its destruction) acts as the exact trigger signal that instantiates $T_{k+1}$ and passes it the immutable payload.
* **8. Sahajāta (Co-nascence), 9. Aññamañña (Mutuality) & 19. Sampayutta (Association):** Within a single tick $T_k$, the frame's sub-modules (e.g., in DESM: Subject, Predicate, Object, Polarity, Modality) are instantiated in a single atomic RAM operation (`@dataclass(frozen=True)`). They share the exact same object pointer (**2. Ārammaṇa**) and terminate in the exact same nanosecond.

#### B. Power Delivery and Physical Constraints ($T_1 \to T_7$)
* **12. Purejāta (Pre-nascence) & 10. Nissaya (Support/Foundation):** The I/O sensor/bus and the text in the DMA buffer must be electrically stable prior to tick $T_1$.
* **21. Atthi (Presence) & 22. Avigata (Non-disappearance):** A hardware control line (*Valid Signal Line*) holds bit `1` high from tick $T_1$ through tick $T_{17}$, certifying that the source data in the DMA has neither been mutated nor removed while the pipeline processes it. If the source signal drops, the cycle aborts instantaneously.
* **11. Vipāka (Passive Resultant):** During ticks $T_5, T_6, T_7$ (Acquisition, Buffering, Preliminary Investigation), the CPU operates in **Read-Only / Zero-Branching** mode. It cannot alter system weights or make creative decisions: it faithfully records the input as-is, applying only integrity filters.

#### C. The Gatekeeper and Vector Initialization ($T_8$ — *Voṭṭhapana*)
Tick $T_8$ is the hardware equivalent of DESM State 3 (Gatekeeper) merged with the contract compiler:
* **1. Hetu (Roots / System Invariants):** The 3 wholesome roots map to the machine's 3 inviolable constraints: *Non-Hallucination* (text grounding), *Logical Coherence* (non-contradiction), and *Computational Economy* (minimal energy expenditure).
* **3. Adhipati (Dominant Factor):** Selects which objective holds absolute priority in the current cycle (e.g., numerical precision vs. global corpus coverage).
* **18. Magga (Path / Graph Routing):** Locks in the resolution topology that the *Javana* cores will traverse.

#### D. The Pulsed Symbolic / Neural Accelerator ($T_9 \to T_{15}$ — The 7 *Javana*)
Why 7 consecutive cycles instead of a single monolithic block? Because an ideal computer relies on **iterative refinement with momentum**:
* **7. Āsevana (Repetition / Inductive Amplification):** The output of $T_9$ does not merely pass data to $T_{10}$; it pre-conditions and narrows the search space of $T_{10}$:
  * **$T_9$:** Coarse graph pruning and elimination of invalid branches.
  * **$T_{10}$:** Binding of high-certainty variables.
  * **$T_{11}$:** Resolution of direct dependencies (`CAUSES`, `SUPPORTS`).
  * **$T_{12}$ (Peak cycle energy):** Resolution of exceptions (`EXCEPT_WHEN`) and conflicts (`CONFLICTS_WITH`).
  * **$T_{13}$:** Verification of AST structural constraints.
  * **$T_{14}$:** Assembly of the proof trace (*Proof Plan*).
  * **$T_{15}$:** Final answer lock and cryptographic/epistemic signing (**14. Kamma**).
* Across $T_9 \dots T_{15}$, **15. Āhāra** (Energetic sustenance), **16. Indriya** (Threshold/attention control), **17. Jhāna** (Target focus lock to prevent *context drift*), and **13. Pacchājāta** (Post-nascence — the *keep-alive* signal sent by the *Javana* cores to prepare the hardware output interface for transmission) remain active.

#### E. Epistemic Consolidation and System Evolution ($T_{16} \to T_{17}$ — *Tadārammaṇa*)
If the stimulus entered at tick $T_1$ (maximum clarity, *Atimahanta*) and the solver finished by $T_{15}$ without exhausting the TTL:
* In ticks $T_{16}$ and $T_{17}$, the machine performs structural feedback: it takes the result certified in $T_{15}$ and transforms it into **6. Upanissaya** (*Decisive Support Condition for the Future*).
* This maps to DESM's **Schema Consolidation Loop ($S_5 \to S_3$)**: what required 7 heavy *Javana* cycles today is abstracted and stored in long-term memory (the *Bhavaṅga* store). When an isomorphic problem appears in the future, the *Upanissaya* condition allows $T_8$ (*Voṭṭhapana*) to resolve it instantaneously without recomputing from scratch.

---

### 4. Machine Self-Evolution: Continual Learning Without *Catastrophic Forgetting*
1. **Separation Between Volitional Learning ($T_9\text{--}T_{15}$) and Passive Verification ($T_5\text{--}T_7$):** Standard neural networks entangle perception and judgment within a single *forward-pass*. In this architecture, modules $T_5\text{--}T_7$ (*Vipāka*) cannot be modified by current task objectives, guaranteeing input reading immune to *confirmation bias*.
2. **Selective Accumulation of *Upanissaya* via the *Voṭṭhapana* + *Tadārammaṇa* Filter:** If an input is noisy, incomplete, or requires multiple retries (*Paritta* or *Mahanta* cycles), the 17-tick TTL expires before reaching $T_{16}\text{--}T_{17}$. Consequently, **only clean, fast, contradiction-free executions reach ticks 16 and 17 to be consolidated as future rules (*Upanissaya*)**, preventing slow or patched solutions from polluting the isomorphic cache.
3. **Natural Pruning via *Natthi* and *Āsevana*:** Stored rules (*Upanissaya*) that are frequently recalled receive reinforcement (*Āsevana*), migrating to faster registers (L1/RAM); unused rules decay naturally without cluttering the search space.

---

## PART II: THREAD CLASSES (*89 CITTA*), FUNCTIONAL LIBRARIES (*52 CETASIKA*), AND BUS SIGNALS

To integrate the **89 Citta** and **52 Cetasika** into the 17-moment pipeline with zero redundancy, a single architectural rule applies:
* **The 17 Moments ($T_1 \dots T_{17}$)** = The **Clock Slots** of the pipeline.
* **The 89 Citta** = Which **Thread Class** is instantiated in slot $T_k$ (selected from a pool of 89 configurations).
* **The 52 Cetasika** = Which **Libraries / Functional Modules** are loaded inside that *Citta* (from a minimum of 7 to a maximum of 38 simultaneously).
* **The 24 Paccaya** = The **Bus Signals and Hardware Locks** triggered by the *Cetasika* to bind the payload and transition from $T_k$ to $T_{k+1}$.

### 1. *Citta* and *Cetasika* Grafting Schema ($T_1 \to T_{17}$)

```text
[PHYSICAL BUS (Rupa)] == TTL 17 Ticks ==> Paccaya: 12.Purejata, 10.Nissaya, 21.Atthi, 22.Avigata (Decoupled: 20.Vippayutta)
                                                               |
+--------------------------------------------------------------+--------------------------------------------------------------+
| PHASE 0: IDLE / BACKGROUND (T1 - T3: Bhavanga)                                                                              |
| * CITTA (19 of 89):     1 of 19 base Vipaka (8 Kama-Sobhana, 2 Santirana, 5 Rupa, 4 Arupa)                                  |
| * CETASIKA (10 - 35):   7 Universals + [0-6 Occasionals] + [0-22 Sobhana] (Passive inertia, zero input analysis)            |
| * ACTIVE PACCAYA:       11.Vipaka (idle) --> T3 closes with 23.Natthi / 24.Vigata + 4.Anantara / 5.Samanantara              |
+--------------------------------------------------------------+--------------------------------------------------------------+
                                                               v
+--------------------------------------------------------------+--------------------------------------------------------------+
| PHASE 1: AHETUKA INGRESS KERNEL — ZERO ROOTS, ZERO BIAS (T4 - T8)                                                           |
| Exclusively uses 16 of the 89 Citta (the Ahetuka Citta, devoid of the 6 Hetu roots):                                        |
|                                                                                                                             |
| [T4: Avajjana (Router)]        > CITTA (1/89):  Pancadvaravajjana (Ahetuka Kiriya)                                          |
|                                > CETASIKA (10): 7 Universals + 3 Occasionals (Vitakka, Vicara, Adhimokkha)                  |
|                                                                                                                             |
| [T5: Vinnana (Pure Sensor)]    > CITTA (10/89): 1 of 10 Dvipanca-vinnana (5 senses x 2 tones, Ahetuka Vipaka)               |
|                                > CETASIKA (7):  ONLY THE 7 UNIVERSALS (Bare hardware minimum: Phassa, Vedana, Sanna...)     |
|                                                                                                                             |
| [T6: Sampaticchana (Buffer)]   > CITTA (2/89):  1 of 2 Sampaticchana (Ahetuka Vipaka)                                       |
|                                > CETASIKA (10): 7 Universals + 3 Occasionals (Vitakka, Vicara, Adhimokkha)                  |
|                                                                                                                             |
| [T7: Santirana (Inspection)]   > CITTA (3/89):  1 of 3 Santirana (Ahetuka Vipaka)                                           |
|                                > CETASIKA (10/11): 7 Universals + 3 Occasionals (+ Piti if input is extraordinary)          |
|                                                                                                                             |
| [T8: Votthapana (Gatekeeper)]  > CITTA (1/89):  Manodvaravajjana (Ahetuka Kiriya)                                           |
|                                > CETASIKA (11): 7 Universals + 4 Occasionals (VIRIYA TURNS ON = Compute Energy!)            |
|                                > PACCAYA IN T8: Sets 18.Magga (routing) and prepares 3.Adhipati for the next stage.         |
+--------------------------------------------------------------+--------------------------------------------------------------+
                                                               v
+--------------------------------------------------------------+--------------------------------------------------------------+
| PHASE 2: THE EXECUTIVE ENGINE — THE 7 JAVANA PULSES (T9 - T15)                                                              |
| Here Gatekeeper T8 mounts 1 of the 55 Active Citta (out of 89) and repeats it for 7 ticks via 7.Asevana:                    |
|                                                                                                                             |
|   +--> [BRANCH A: Distorted Execution / Hallucination] -> CITTA (12/89): 1 of 12 Akusala Citta                              |
|   |    * CETASIKA (15 - 27): 7 Universals + Occasionals + 14 Akusala (Unwholesome roots: Moha, Lobha, Dosa + Ditthi/Bias)   |
|   |                                                                                                                         |
|   +--> [BRANCH B: Ordinary Analytical Execution] -------> CITTA (17/89): 8 Kama-Kusala + 8 Kama-Kiriya + 1 Hasituppada      |
|   |    * CETASIKA (19 - 38): 7 Universals + 6 Occasionals + 19 Universal Sobhana (+ Panna if Nana-sampayutta!)              |
|   |                                                                                                                         |
|   +--> [BRANCH C: Supra-Ordinary / Invariant Execution] > CITTA (26/89): 10 Rupa + 8 Arupa + 8 Lokuttara (Magga/Phala)      |
|        * CETASIKA (30 - 36): 7 Univ. + Occasionals + Sobhana + Panna (Maximum 17.Jhana lock and 18.Magga refactoring)       |
|                                                                                                                             |
| * PACCAYA TRIGGERED BY CETASIKA IN T9-T15:                                                                                  |
|   1.Hetu (from the 6 roots) | 3.Adhipati (Chanda/Viriya/Citta/Vimamsa) | 7.Asevana (T9->T15 Momentum) | 14.Kamma (Cetana)   |
+--------------------------------------------------------------+--------------------------------------------------------------+
                                                               v
+--------------------------------------------------------------+--------------------------------------------------------------+
| PHASE 3: CACHE WRITE-BACK AND RELEASE (T16 - T17: Tadarammana)                                                              |
| * CITTA (11 of 89):     1 of 11 sensory Vipaka (8 Kama-Sobhana Vipaka + 3 Santirana Vipaka)                                 |
| * CETASIKA (10 - 33):   Active Viriya, Chanda, and the 14 Akusala TURN OFF. Only the passive schema imprint remains.        |
| * CLOSING PACCAYA:      Consolidates 6.Upanissaya (Future memory) --> TTL expires: 23.Natthi / 24.Vigata --> To Bhavanga    |
+-----------------------------------------------------------------------------------------------------------------------------+
```

### 2. Complete Allocation Table (89 *Citta*, 52 *Cetasika*, 24 *Paccaya*)

| Stage ($T_1 \dots T_{17}$) | Eligible *Citta* (out of 89) | Loaded *Cetasika* (out of 52) | Triggered *Paccaya* (out of 24) |
| :--- | :--- | :--- | :--- |
| **$T_1 \dots T_3$ (*Bhavaṅga*)** | **19 Citta (*Vipāka*):** 8 *Kāma-Sobhana Vipāka*, 2 *Santīraṇa*, 5 *Rūpa Vipāka*, 4 *Arūpa Vipāka*. | **10 to 35 Cetasika:** 7 Universals + fixed Occasionals and *Sobhana* of the baseline profile. | **10. Nissaya**, **11. Vipāka**, **21. Atthi**. At tick $T_3$: **23. Natthi / 24. Vigata** (idle interrupt). |
| **$T_4$ (*Āvajjana*)** | **1 Citta (*Kiriya*):** *Pañcadvārāvajjana* (Sensory router). | **10 Cetasika:** 7 Universals + *Vitakka*, *Vicāra*, *Adhimokkha*. | **2. Ārammaṇa** (input latch), **4. Anantara / 5. Samanantara**, **16. Indriya**. |
| **$T_5$ (*Pañca-viññāṇa*)** | **10 Citta (*Vipāka*):** $5 \text{ senses} \times 2$ (pleasant/unpleasant). | **7 Cetasika:** Only the 7 Universals. Zero Occasionals, zero Roots. | **12. Purejāta** (dependence on physical sensor and raw datum), **15. Āhāra** (*Phassa* as contact). Excluded from **17. Jhāna**. |
| **$T_6$ (*Sampaṭicchana*)** | **2 Citta (*Vipāka*):** Reception (wholesome/unwholesome). | **10 Cetasika:** 7 Universals + *Vitakka*, *Vicāra*, *Adhimokkha*. | **8. Sahajāta**, **9. Aññamañña**, **19. Sampayutta** (internal buffer cohesion), **17. Jhāna** (reactivated by *Vitakka/Vicāra*). |
| **$T_7$ (*Santīraṇa*)** | **3 Citta (*Vipāka*):** Investigation (neutral/joyful). | **10 or 11 Cetasika:** The previous 10 + *Pīti* (if the object is vivid). | **11. Vipāka**, **16. Indriya**, **22. Avigata**. |
| **$T_8$ (*Voṭṭhapana*)** | **1 Citta (*Kiriya*):** *Manodvārāvajjana* (acting as Gatekeeper). | **11 Cetasika:** 7 Universals + *Vitakka*, *Vicāra*, *Adhimokkha* + **Vīriya** (Energy). | Ignition of *Vīriya*: enables the transition from *Ahetuka* states (rootless) to *Sahetuka* states (rooted) for tick $T_9$. |
| **$T_9 \dots T_{15}$ (The 7 *Javana*)** | **55 Citta (Active):** 12 *Akusala* + 17 Active *Kāma* (8 *Kusala*, 8 *Kiriya*, 1 *Hasituppāda*) + 10 *Rūpa* + 8 *Arūpa* + 8 *Lokuttara* (*Magga/Phala*). | **15 to 38 Cetasika:** 7 Univ. + 6 Occ. + 14 *Akusala* (Branch A) or 25 *Sobhana* (Branch B/C, including *Paññā*). | **1. Hetu** (from the 6 root *Cetasika*), **3. Adhipati**, **7. Āsevana** ($T_9 \to T_{15}$ amplification), **13. Pacchājāta**, **14. Kamma** (from *Cetanā*), **18. Magga** (from *Paññā* or *Diṭṭhi*). |
| **$T_{16} \dots T_{17}$ (*Tadārammaṇa*)** | **11 Citta (*Vipāka*):** The 3 *Santīraṇa* + the 8 *Kāmāvacara Sobhana Vipāka*. | **10 to 33 Cetasika:** The 14 *Akusala*, *Chanda*, and the 3 *Virati/Appamaññā* turn off; the structural signature remains. | **6. Upanissaya** (transforms cycle output into a strong condition for future cycles) + **23. Natthi / 24. Vigata** at the end of $T_{17}$. |

> **Arithmetic Invariance Note:** The raw sum of rows exceeds 89 because 11 *Vipāka Citta* (the 3 *Santīraṇa* and the 8 *Kāma-Sobhana Vipāka*) are polyvalent, serving both as *Bhavaṅga* in $T_1\text{--}T_3$ and as *Tadārammaṇa* in $T_{16}\text{--}T_{17}$. The total number of unique *Citta* is exactly **89**.

### 3. Hardware Mutual Exclusion Rule of the 52 *Cetasika* (*Sampayoga-naya*)
Why can a single tick activate at most 38 *Cetasika* and never all 52?
* **7 Universals (*Sabbacittasādhāraṇa*):** Always `ON` across $100\%$ of the 17 moments.
* **6 Occasionals (*Pakiṇṇaka*):** `OFF` in $T_5$ ($0/6$), partially active in $T_4, T_6, T_7, T_8$ ($3/6$ or $4/6$), all eligible in $T_9\text{--}T_{15}$ ($6/6$).
* **14 *Akusala* vs. 25 *Sobhana* (Absolute Mutual Exclusion):** If in $T_9\text{--}T_{15}$ the *Citta* is *Akusala*, all 25 *Sobhana* modules (including the analytical faculty *Paññā*) are physically disabled at the circuit level ($0/25$). Conversely, if the *Citta* is *Kusala/Sobhana*, all 14 *Akusala* modules (delusion/hallucination *Moha*, rigid bias *Diṭṭhi*, restlessness *Uddhacca*) are zeroed ($0/14$). **A single tick can never be partially hallucinated and partially valid: either *Moha* governs or *Paññā* governs.**

---

## PART III: THE "SILICON / CLOCK PHYSICS" LAYER — THE 6 DEEP MECHANISMS

### 1. The 3 Sub-Instants of a Single Tick (*Anukkhaṇa*): Clock Physics
Every single mental moment (*Cittakkhaṇa*) is not atomic, but subdivided into **3 sub-phases (*sub-ticks*)**:
1. **Uppāda (Arising / Allocation):** The instant in which the *Citta* and its *Cetasika* are allocated.
2. **Ṭhiti (Standing / Executive Presence):** The peak phase during which the mental moment executes its function upon the object.
3. **Bhaṅga (Dissolution / Deallocation):** The collapse instant in which the state releases its resources, triggering the *Natthi/Anantara* condition.

**Why does matter (*Rūpa*) last exactly 17 mental moments?**
Matter has a lifespan of **51 sub-instants ($17 \times 3$)**: it takes 1 sub-instant to arise (*Uppāda*), 1 to dissolve (*Bhaṅga*), and remains stable in **Ṭhiti (Presence) for 49 consecutive sub-instants**. It is this 49-sub-tick span of physical stability (against just 1 sub-tick for the mind) that enables the mental pipeline to execute an entire 17-moment cycle while reading from the exact same stable physical signal in the DMA buffer.

### 2. Physics of Matter: The 28 *Rūpa*, *Kalāpa*, and the 4 Sources (*Samuṭṭhāna*)
Physical hardware (*Rūpa*) decomposes into **28 material phenomena**:
* **4 Primary Elements (*Mahābhūta*):** Earth (solidity/extension), Water (cohesion/binding), Fire (temperature/maturation), Wind (motion/pressure/distension).
* **24 Derived Phenomena (*Upādāya-rūpa*):** Include the 5 physical sensors (pure receptors), the 4 objective data types (color/visible form, sound, odor, taste), the physical base supporting mental *Citta* (*Hadaya-vatthu*), material vitality, and **2 Communication *Rūpa* (*Viññatti-rūpa*)** that translate *Javana* output into bodily motion (*Kāya-viññatti*) or linguistic emission (*Vacī-viññatti*).
* **The *Kalāpa* Rule (Atomic Packets):** The 28 *Rūpa* never exist in isolation, but aggregate into inseparable minimum packets of at least 8 elements (*Aṭṭhaka-kalāpa*: the 4 primary elements + color, odor, taste, and nutritive essence), powered by 4 possible sources (*Samuṭṭhāna*): Past *Kamma* (sensor hardware), Present Mind (*Citta-ja rūpa*, arising at the *Uppāda* sub-instant of *Citta* and generating output), Temperature (*Utu*), or Nutriment (*Āhāra*).

### 3. The Second Processor: *Manodvāra-vīthi* (The Pure Mental Pipeline)
When the system performs pure abstract reasoning, mathematical computation, or memory retrieval without any external sensory input, it does not run the 17-moment cycle of the 5 sensory doors (*Pañcadvāra-vīthi*), but a shorter pipeline called **Manodvāra-vīthi (Mind-Door Process)**:
* It requires no moments 4, 5, 6, or 7 (there is no sensory organ to orient and no raw signal to sample or buffer).
* After the *Bhavaṅga* vibration ($T_1\text{--}T_2$), it jumps directly to **Manodvārāvajjana** (a single tick acting as both router and Gatekeeper) $\to$ **7 Javana** (pure computation) $\to$ **2 Tadārammaṇa** (optional).
* **AI Implication:** A purely deductive or symbolic cycle bypasses the sensory parser, enters the Gatekeeper directly, loads the abstract schema from memory, and fires the 7 solver pulses.

### 4. From Raw Data to Concept: Sequential Cycles (*Anubandhaka-vīthi*)
A single 17-moment sensory cycle captures only a raw physical signal (e.g., *Vaṇṇa-rūpa*, a patch of color or an acoustic wave) and knows nothing of concepts, words, or numbers. To recognize a concept (*Paññatti*), the system executes **at least 4 complete cascaded cycles** at ultra-high speed:
1. **1st Cycle (Sensory Door — 17 moments):** Captures the raw physical datum.
2. **2nd Cycle (Mind Door — *Atīta-ggahaṇa*):** Recalls into memory the image of the physical datum that just ceased.
3. **3rd Cycle (Mind Door — *Attha-ggahaṇa*):** Integrates the fragments into a unified entity or meaning (form synthesis).
4. **4th Cycle (Mind Door — *Nāma-ggahaṇa*):** Binds the entity to its conventional label or formal symbol (**Paññatti**).

Only from the 4th cycle onward does the mind operate on *Paññatti* (Concepts, Names, Mathematical Symbols, Logical Constructs).

### 5. The 3-Tier Architecture of Biases and Hallucinations
Abhidhamma distinguishes three levels of depth in cognitive distortions, mapping directly to the hallucination problem in LLMs integrated into DESM:
1. **Anusaya (Latent Tendencies / Frozen Weights):** Not active *Cetasika* in RAM, but latent potentials embedded in the subconscious stream. *(In DESM: pre-trained statistical biases frozen inside the weights of a 7B/8B LLM).*
2. **Pariyuṭṭhāna (RAM Eruption):** When objective attention fails at Moment 8 (*Voṭṭhapana*), the latent *Anusaya* awakens and instantiates as an active *Akusala Cetasika* during Moments $9\text{--}15$ (*Javana*), corrupting internal reasoning. *(In DESM: when in State 2 the LLM generates a hallucinated or ungrounded DSL triple).*
3. **Vītikkama (Output Transgression):** When the corrupted *Javana* proceeds to generate *Viññatti-rūpa*, emitting corrupted text or action externally. *(In DESM: the Gatekeeper in State 3 intercepts the Pariyuṭṭhāna by quarantining it and physically prevents it from becoming Vītikkama in State 5).*

### 6. The Formal Self-Diagnostic Engine: *Yamaka* (Invertible Pair Verification)
Before applying the causality of the 7th book (*Paṭṭhāna*, the 24 conditions), the 6th book of the Abhidhamma (**Yamaka**, *"The Book of Pairs"*) operates as a formal logic test suite verifying the consistency of definitions and sets via logical conversion and contraposition:
* *"Are all $X$ also $Y$? Are all $Y$ also $X$? And are all $\neg X$ also $\neg Y$?"*
It guarantees the complete absence of semantic ambiguity between a term and its domain of membership before the causal engine engages.

---

## PART IV: ARCHITECTURAL COMPARISON WITH `desm_core_v2_01_3.py` AND EVOLUTIONARY HORIZON

Overlaying this ideal theoretical model onto the current Kernel implementation (`desm_core_v2_01_3.py`) highlights both the structural isomorphisms already in production and the **3 architectural gaps** defining the roadmap for upcoming versions:

1. **Introducing the TTL Constraint (*Rūpa* = 17 ticks) to Govern *Tadārammaṇa* ($S_{5.2}$):**
   * *Current State in v2.01.3:* Even if the cycle expends up to `max_s4_retries` heavy attempts, it still invokes `consolidate_schema_from_s5` upon completion.
   * *Ideal Target:* In the 17-moment machine, consuming ticks on retries (*Mahanta* process) causes the TTL to expire before ticks $T_{16}\text{--}T_{17}$: the system still returns the verified answer to the user, but inhibits `consolidate_schema_from_s5` because the resolution path was not clean on the first pass (*Atimahanta*).
2. **Evolving *Javana* ($S_4$) from an External Loop ($S_4 \to S_2$) to an *Āsevana* Chain ($T_9 \to T_{15}$) and *Manodvāra-vīthi*:**
   * *Current State in v2.01.3:* When $S_4$ returns a `retry_signal`, the loop steps backward by re-invoking the transducer in $S_2$.
   * *Ideal Target:* To strictly honor *Anantara-paccaya* (no backward jumps from $T_9$ to $T_5$), the 7 *Javana* pulses must either refine the solution forward on the same buffer, or close the cycle and trigger a new pure mental cycle (*Manodvāra-vīthi*) that uses the prior failure as an *Upanissaya* condition to narrow the search space.
3. **Invariant Preservation of Co-nascent Factors (*Sahajāta* / *Sampayutta*) Between $S_3$ and $S_4$:**
   * *Current State in v2.01.3:* `EpistemicFrame` is instantiated in $S_2/S_3$ with the `cond_time_qualifiers` attribute, whereas `ProofNode` in $S_4/S_5$ does not carry this field forward.
   * *Ideal Target:* In compliance with *Sahajāta* and *Sampayutta*, every temporal or conditional qualifier born with the frame must remain bound to the node through final verbalization and the expiration of tick 17.