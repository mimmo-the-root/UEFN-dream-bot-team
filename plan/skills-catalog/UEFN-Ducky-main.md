# Catalogo skill — UEFN-Ducky (repo pilota)

- **Percorso analizzato:** `Downloads/ROUTING/UEFN-Ducky-main/UEFN-Ducky-main` (sola lettura, nessun file toccato).
- **Data analisi:** 2026-11-20. **Ramo kit:** `r1/oc-skills`.
- **Che cos'è:** app desktop Windows (Python + React/TypeScript + Rust + C#) in cui agenti ("duckies") costruiscono mappe UEFN: Verse, dispositivi, level design, materiali, Niagara, 3D, test, browser, Store. Tutto è plugin installabile.
- **Motore NON-UEFN presente:** nessun sorgente Unreal C++ / `.uproject` / `.uplugin` nel repo. Il lato UEFN è Python (`uefn_listener/`). Nativi: Rust (`native_launcher/`) e C# (`release/installer/host/`). Plugin Unity e Blender sono citati ma non risiedono qui.

## Licenza (letta per prima, nessun repo scartato)

**Ducky Source-Available License v1.0**, SPDX `LicenseRef-Ducky-SAL-1.0` — source-available, **non** OSI open source. Copyright 2026 Mindful Path Company, LLC.

- Consentito: leggere/studiare e citare con attribuzione, eseguire build ufficiali (anche per isole commerciali), modificare la propria copia locale, fork pubblico **solo** per contribuire ai repo ufficiali.
- Vietato senza permesso scritto: redistribuire, vendere/sublicenziare, incorporare parti in altri prodotti/servizi/dataset/corpus di training, rimuovere attribuzione, aggirare licenze/telemetria, usare i marchi Ducky.
- Art. 5: plugin, skill, siti, configurazioni e isole che **io** creo sono miei. **Art. 5a:** i skill pack first-party ufficiali (qualsiasi `skills/` o `.ducky-skill-pack`) restano sotto SAL anche se il codice del plugin è MIT.
- **Impatto sul kit:** il repo resta analizzabile, ma la FASE 3 resta obbligatoriamente "scritto da zero, nessuna frase/struttura/nome di file copiato, nessuna provenienza citata". Le idee di progetto (non il testo) sono quel che si può assimilare.

**Legenda:** "Già nel kit" = sola cartella `user-level-skills/`. Alcune cose esistono come skill opencode fuori dal kit (`scenegraph`, `animation`, `modeling`, `npc-ai`, `physics`, `vfx`, `browser`, `forge`, `datatables`): le segnalo come *fuori kit* e non le conto come già presenti. Utilità: **alta** = colma un buco reale; **media** = utile ma ridondante; **bassa** = specifica dell'app Ducky.

---

## A. Skill pack e reference (skill in senso stretto)

| Nome | Cosa fa | Quando si usa | Motore non-UEFN | Già nel kit | Utilità e motivo |
|---|---|---|---|---|---|
| `skill_packs/ducky/SKILL.md` (v43) | Skill di controllo dell'app: setup, IDE, Skills studio, chat, listener, plugin, workflow, template Verse. Impone `skill_read_subskill()` per il dettaglio e `skill_search()` quando non si sa dove guardare. | Si lavora dentro UEFN-Ducky. | Sì: app Ducky | No | **Bassa** — è la guida all'app, non una pratica UEFN trasferibile; utile solo il pattern "indice + subskill caricati su richiesta" (`mcp-tool-contracts`, `token-aware-coding`). |
| `ducky/references/ai_plugins.md` | Costruisce plugin desktop AI: percorso, regole dure, `plugin.json`, API backend, ponte pannello, tab completa. | Creare un plugin Ducky. | Sì: architettura app | No | **Bassa** — nessun equivalente UEFN; idea riutilizzabile: regole esplicite per plugin che espongono tool+skill insieme. |
| `ducky/references/app_recovery.md` | Ripristina listener offline, progetto sbagliato, tool stale dopo aggiornamento. | L'app non risponde. | Sì: app Ducky | `uefn-validation-failure-diagnosis`, `uefn-editor-logs` | **Media** — il pattern "diagnosi prima di riavviare" è trasferibile alle sessioni UEFN. |
| `ducky/references/groups_and_lanes.md` | Gruppi/swarm, riuso membri, lane di scrittura, changeset, messaggi agente-agente. | Lavoro multi-agente parallelo. | Sì: orchestrazione Ducky | No | **Media** — il kit ha reviewer/agenti ma non lane di proprietà dei file; concetto interessante per evitare conflitti. |
| `ducky/references/guided_ui.md` | Mostra una parte dell'app con "Show me", tour e tour di workflow. | Guidare l'utente nell'app. | Sì: UI app | No | **Bassa** — specifico del pannello. |
| `ducky/references/panel_guide.md` | Hookup IDE, Skills studio, plugin MCP, chat. | Configurare l'app. | Sì: app Ducky | No | **Bassa** — setup Ducky. |
| `ducky/references/plugin_data.md` | `api.data`, spazi locali/condivisi, lock, conflitti, history, dati sensibili, crittografia, read-only. | Dati condivisi tra plugin. | Sì: storage app | No | **Bassa** — infrastruttura app, non UEFN. |
| `ducky/references/plugin_examples_app.md` | Esempi: backend immagini, provider AI, suoni/hook, walkthrough, voci, coding agent, IDE. | Fare un plugin come esempio. | Sì: app Ducky | No | **Bassa** — esempi di codice app. |
| `ducky/references/plugin_examples_tools.md` | Esempi tool-only: nodi/pin workflow, trigger, template cartelle, settings/secret, connection check. | Fare un plugin solo tool. | Sì: app Ducky | No | **Bassa** — catalogo esempi. |
| `ducky/references/plugin_examples_uefn.md` | Esempi UEFN: template Verse, tool listener, pipeline Blender/Meshy. | Integrare asset esterni. | Parziale: Blender/Meshy | `uefn-asset-budget`, `forge` (fuori kit) | **Media** — il confine "asset esterno → UEFN" è coperto male nel kit. |
| `ducky/references/plugin_examples_ui.md` | Esempi UI: tab dashboard, pannello, editor di file, tema. | Fare un plugin con UI. | Sì: UI app | `console-ui`, `game-ui-designer` | **Bassa** — stili Ducky, non console kit. |
| `ducky/references/plugin_known_problems.md` | Trappole note: gate listener, sandbox, chiavi tema, backend compilati, nomi globali, effetti collaterali test, target tour. | Debug plugin. | Sì: app Ducky | `uefn-lessons` | **Media** — il *formato* "trappole note" è già nel kit; il contenuto no. |
| `ducky/references/plugin_look.md` | UI kit Ducky, layout, tab pill, icone, varianti Aspetto, stati pannello, focus, temi. | Costruire UI coerente. | Sì: UI app | `console-ui` | **Bassa** — design system diverso. |
| `ducky/references/plugin_publishing.md` | Pubblicazione solo Store, licenze firmate, cosa compila, codice compile-safe. | Pubblicare plugin. | Sì: Store Ducky | `fab-product` | **Media** — flusso analogo (package → checklist → pubblicazione), ma piattaforma diversa. |
| `ducky/references/plugin_testing.md` | Flusso valida/testa/errore dopo modifiche a plugin. | Dopo edit plugin. | Sì: app Ducky | `tests/run_all.py`, `validate_skills.py` | **Media** — il principio "ogni modifica ha un check" è già nostrano. |
| `ducky/references/publish_private.md` | Aprire/chiudere/riavviare UEFN, Upload Private Version, Launch Memory Calculation via click/capture. | Pubblicare versione privata. | No: UEFN | `fab-product`, `uefn-session-regression`, `mcp-tool-contracts` | **Alta** — sequenza operativa UEFN con popup e code private, poco coperta nel kit. |
| `ducky/references/sandbox.md` | Sandbox per chat: scaricare, installare, buildare, eseguire, studiare, verificare e mostrare web app. | Codice non fidato. | Sì: sandbox PC | No | **Media** — idea di isolamento riutilizzabile per script generati. |
| `ducky/references/self_care.md` | `ducky_health` e `ducky_self_care` per app/PC lenti o out-of-memory. | Calo performance. | Sì: PC/app | `uefn-profiling`, `performance-uefn-checklist` | **Bassa** — profila l'app, non la mappa. |
| `ducky/references/verse_templates.md` | Salvare/listare/applicare/cancellare template Verse personalizzati; mai toccare quelli Store. | Template Verse. | No: Verse | `uefn-verse-build` | **Media** — idea "template personali protetti" manca nel kit. |
| `ducky/references/web_research.md` | YouTube transcript/capitoli/frame e lookup codice GitHub via `web_video`, `browser_video_frames`, `view_image`, `web_github`. | Ricerca web/_video. | Sì: YouTube/GitHub | No | **Media** — tecnica di ricerca con fonti, utile a `fortnite-competitor-analyzer`. |
| `ducky/references/workflows.md` | Costruire/cambiare/spiegare/eseguire workflow: canvas, grafo, pin, loop, schedule, report, ricette. | Automazioni. | Sì: automazioni Ducky | No | **Bassa** — motore workflow diverso dal kit. |
| `skill_packs/ponytail/SKILL.md` (v8, MIT) | Regole YAGNI e codice minimo: "deve esistere?", riusa helper, stdlib, piattaforma, dipendenza, una riga, codice minimo; livelli `lite`/`full`/`ultra`; non semplificare mai validazione di trust boundary, perdita dati, sicurezza, accessibilità, richieste esplicite, un check eseguibile. | Scrivere o rivedere codice. | No: universale | `token-aware-coding` | **Alta** — complementa il risparmio token con una dottrina di minimalità e una lista di "non tagliare mai". |
| `ponytail/references/review.md` | Rivede un diff per over-engineering. | Revisione diff. | No: universale | No | **Alta** — gate di review specifico, assente nel kit. |
| `ponytail/references/audit.md` | Audit repository-wide di over-engineering. | Audit codebase. | No: universale | No | **Media** — estensione di `review.md`. |
| `ponytail/references/gain.md` | Benchmark dell'impatto della semplificazione. | Misurare miglioramento. | No: universale | No | **Media** — misurare prima/dopo è una pratica solida. |
| `ponytail/references/debt.md` | Raccoglie commenti `ponytail:` in un ledger di debito tecnico. | Tracciare debito. | No: universale | No | **Bassa** — richiede convenzione di commenti, il kit vieta i commenti. |
| `ponytail/references/help.md` | Promemoria di mode e subskill ponytail. | Riferimento rapido. | No: universale | No | **Bassa** — indice della skill stessa. |

---

## B. Agenti / profili "ducky" (`bundled_agent_profiles.json`, `agent_profiles.py`)

Ognuno ha modello, personalità, voce, skill, tool e memoria propri. `bundled_duckies.json` aggiunge solo stili visivi (`artist`, `cowboy`, `hacker`, `wizard`); `appearance_builtin_profiles.json` il profilo `__default__`.

| Nome | Cosa fa | Quando si usa | Motore non-UEFN | Già nel kit | Utilità e motivo |
|---|---|---|---|---|---|
| `verse-coder` | Programma Verse/gameplay: codice, errori di compilazione, collegamento dispositivi, data table. | Scrivere/debug Verse. | No: Verse | `uefn-verse-build`, `verse-patterns` | **Bassa** — già coperto da coder + skill. |
| `level-designer` | Posiziona actor e device, check spaziali, blockout, landscape. | Costruire livello. | No: UEFN | `level-design-uefn`, `uefn-level-devices`, `uefn-disciplines` | **Bassa** — coperto. |
| `material-artist` | Grafi materiale, istanze, texture, errori materiale. | Materiali. | No: UEFN | `uefn-materials`, `materials` | **Bassa** — coperto. |
| `niagara-vfx` | Sistemi particle, parametri, attivazione/reset. | VFX. | No: UEFN | `uefn-vfx-niagara`, `vfx` (fuori kit) | **Bassa** — coperto. |
| `3d-modeler` | Blender → Static Mesh: modellazione, import, UV, collisione, LOD, Nanite. | Asset 3D. | Sì: Blender | `forge` (fuori kit), `uefn-asset-budget` | **Media** — il kit non ha una skill di modellazione dedicata in `user-level-skills/`. |
| `ui-engineer` | UI/HUD in Verse (canvas, overlay, stack_box, stato per giocatore). | HUD. | No: Verse | `verse-ui-kit`, `game-ui-designer`, `uefn-ui-widgets` | **Bassa** — coperto. |
| `sound-designer` | Componenti audio, ambient/one-shot, device audio. | Audio. | No: UEFN | `camera-audio-uefn` | **Bassa** — coperto. |
| `producer` | Coordinatore opzionale di swarm; non fa mai lavoro diretto. | Lavori multi-parte. | Sì: orchestrazione | No | **Media** — idea di coordinatore che non implementa, coerente con i review gate del kit. |
| `rigging-artist` | IK Rig, IK Retargeter, socket, catene di retarget. | Rigging. | No: UEFN | `animation` (fuori kit) | **Media** — buco nel kit user-level. |
| `animation-artist` | Retarget animazioni, aggancio oggetti allo scheletro NPC. | Animazione. | No: UEFN | `animation` (fuori kit) | **Media** — buco nel kit user-level. |
| `npc-author` | Mesh custom, AnimPreset, NPCDef, AI preda/cacciatore, spawner. | NPC. | No: UEFN | `npc-ai`, `conversations` (fuori kit) | **Media** — buco nel kit user-level. |
| `tester` | QA: playtest, prova collegamenti, math di livellamento, grant, copertura spawn pad. | Test. | No: UEFN | `tester` (fuori kit), `uefn-session-regression` | **Bassa** — coperto. |
| `reviewer` | Review soltanto in lettura di swarm/changeset/isola, zero scritture. | Audit. | No: universale | `intent-reviewer`, `compliance-reviewer` | **Bassa** — coperto dai gate. |
| `developer` | Sviluppatore generico: app, backend, script, test, doc, ricerca. | Nessuno specialista calza. | Sì: software Ducky | No | **Bassa** — ruolo interno all'app. |
| `bundled_duckies.json` (4 stili) | Personalità/aspetti precaricati: artist, cowboy, hacker, wizard. | Scegliere un ducky. | Sì: app Ducky | No | **Bassa** — pura estetica. |
| `appearance_builtin_profiles.json` (`__default__`) | Profilo tema predefinito dell'app. | Tema di default. | Sì: app Ducky | `console-ui` | **Bassa** — stile diverso. |

---

## C. Comandi slash e modalità (`slashCommands.ts`, `types/panel.ts`)

| Nome | Cosa fa | Quando si usa | Motore non-UEFN | Già nel kit | Utilità e motivo |
|---|---|---|---|---|---|
| `/agent` | Lascia che l'agente modifichi file ed esegua tool. | Lavoro attivo. | Sì: modalità Ducky | Comandi `/coder` del kit | **Bassa** — equivalente funzionale. |
| `/plan` | L'agente scrive un piano prima di toccare codice. | Lavoro complesso. | Sì: modalità Ducky | `/game-plan`, regola 13 | **Bassa** — già obbligatorio nel kit. |
| `/ask` | Risposte in sola lettura, zero edit/tool. | Domande. | Sì: modalità Ducky | `/consistency` | **Bassa** — coperto. |
| `/goal <goal>` | Traccia un obiettivo della chat come attività. | Obiettivo persistente. | Sì: app Ducky | `ROADMAP.md`, `/task-list` | **Media** — idea di goal collegato alla chat, non presente. |
| `/task <title>` | Crea attività collegata alla chat corrente. | Scomporre lavoro. | Sì: app Ducky | `planner-docs` | **Bassa** — coperto e più rigoroso. |
| `/model` | Sceglie il modello della chat. | Cambiare LLM. | Sì: provider Ducky | No | **Bassa** — infrastruttura modelli. |
| `/snip` | Cattura una regione dello schermo nel composer. | Mostrare un problema visivo. | Sì: UI Windows | No | **Media** — utile nei bug report visivi/UEFN. |
| `/help` | Elenca i comandi disponibili nel contesto. | Scoprire i comandi. | Sì: app Ducky | `/help` opencode | **Bassa** — coperto. |
| `Ask / Plan / Agent` (AgentMode) | Tre modalità per messaggio, con dial di thinking-effort e coda prompt. | Ogni messaggio. | Sì: app Ducky | Regola 13 + reviewer | **Media** — il dial di effort e la coda dei prompt sono idee nuove. |

---

## D. Workflow e template pronti

### D1. Pipeline (`pipeline_templates.py`) — nuova picker

| Nome | Cosa fa | Quando si usa | Motore non-UEFN | Già nel kit | Utilità e motivo |
|---|---|---|---|---|---|
| `builtin:pipe-prompt-image` | Da prompt a immagine. | Creare artwork. | Sì: generatore immagini | `fortnite-thumbnail-pro`, `dream-illustration` | **Bassa** — coperto in parte. |
| `builtin:pipe-prompt-cutout` | Da prompt aimmagine ritagliata. | Asset con trasparenza. | Sì: generatore | `fortnite-thumbnail-pro` | **Bassa** — dettaglio. |
| `builtin:pipe-upscale` | Upscale di immagine. | Texture/thumbnail. | Sì: image ops | `fortnite-thumbnail-pro` | **Bassa** — dettaglio. |
| `builtin:pipe-sprite-sheet` | Griglia/sprite sheet da immagini. | UI sprite. | Sì: image ops | No | **Media** — tecnica utile per HUD/UI. |
| `builtin:pipe-title-card` | Titolo 1920x1080. | Video di release. | Sì: image ops | `fortnite-social-trailer` | **Bassa** — coperto. |
| `builtin:pipe-orm` | Impacchetta AO/roughness/metallic in ORM. | PBR. | Sì: texture ops | `forge`, `materials` (fuori kit) | **Media** — buco tecnico nelle skill kit. |
| `builtin:pipe-prompt-3d-uefn` | Da prompt a modello 3D importato in UEFN. | Asset veloce. | Sì: 3D cloud | `forge` (fuori kit), `uefn-asset-budget` | **Media** — il gate budget c'è, la pipeline no. |
| `builtin:pipe-image-3d-uefn` | Da immagine a 3D e import UEFN. | Riferimento visivo → mesh. | Sì: 3D cloud | `forge` (fuori kit) | **Media** — come sopra. |
| `builtin:pipe-prompt-image-3d` | Prompt → immagine → 3D → UEFN. | Concept a mesh. | Sì: 3D cloud | `forge` (fuori kit) | **Media** — come sopra. |
| `builtin:pipe-game-ready` | Remesh, scala, origine, import. | Preparare asset di gioco. | Sì: mesh ops | `uefn-asset-budget`, `forge` (fuori kit) | **Alta** — la checklist "game-ready" esatta è il punto debole del kit. |
| `builtin:pipe-restyle` | Restyle modello da prompt stilistico. | Varianti asset. | Sì: 3D cloud | No | **Bassa** — nicchia. |
| `builtin:pipe-extract-textures` | Estrae mappe di texture da un modello. | PBR da mesh. | Sì: mesh ops | No | **Media** — come `pipe-orm`. |
| `builtin:pipe-model-check` | Controlla dimensione, triangoli, rig. | Prima dell'import. | Sì: mesh ops | `uefn-asset-budget` | **Alta** — già coperto, ma conferma la priorità del gate. |
| `builtin:pipe-blender-render` | Renderizza modello in Blender aperto con addon MCP. | Mostrare asset. | Sì: Blender | `forge` (fuori kit) | **Bassa** — richiede Blender. |
| `builtin:pipe-character-prompt` | Prompt → personaggio → rig → animazione → import. | NPC. | Sì: character ops | `animation`, `npc-ai` (fuori kit) | **Media** — buco user-level. |
| `builtin:pipe-character-full` | Prompt → immagine → personaggio → rig → animazione → UEFN. | NPC completo. | Sì: character ops | `animation`, `npc-ai` (fuori kit) | **Media** — come sopra. |
| `builtin:pipe-character-picture` | Arte personaggio → 3D → rig → animazione → import. | Da concept a NPC. | Sì: character ops | `animation` (fuori kit) | **Media** — come sopra. |
| `builtin:pipe-describe-picture` | Descrizione visione di arte di gioco. | Analisi reference. | Sì: visione | `fortnite-thumbnail-pro` | **Bassa** — dettaglio. |
| `builtin:pipe-translate` | Traduce testo. | Localizzazione. | Sì: LLM | `localization` (fuori kit) | **Media** — buco user-level. |
| `builtin:pipe-extract-data` | Estrae campi nominati da testo. | Strutturare informazioni. | Sì: LLM | No | **Bassa** — generico. |
| `builtin:pipe-find-pictures` | Filtra immagini per descrizione. | Trovare reference. | Sì: visione | `fortnite-thumbnail-pro` | **Bassa** — dettaglio. |
| `builtin:pipe-pdf-summary` | Estrae testo PDF e riassume. | Documenti. | Sì: PDF | `pdf` (fuori kit) | **Bassa** — coperto fuori kit. |
| `builtin:pipe-pdf-sheet` | Immagini PDF in contact sheet. | Reference visive. | Sì: PDF | `pdf` (fuori kit) | **Bassa** — coperto fuori kit. |

### D2. Template automazioni storici (`templates.py`)

| Nome | Cosa fa | Quando si usa | Motore non-UEFN | Già nel kit | Utilità e motivo |
|---|---|---|---|---|---|
| `builtin:playtest-start` | Apre/riusa UEFN, avvia partita, attende giocatore. | Playtest. | No: UEFN | `uefn-session-regression` | **Bassa** — coperto. |
| `builtin:stop-game` | Ferma sessione; no-op se chiuso/non in gioco. | Fine playtest. | No: UEFN | `uefn-session-regression` | **Bassa** — coperto. |
| `builtin:tycoon-first-purchase` | Compila, gioca, attende log del primo acquisto. | Verifica economia tycoon. | No: UEFN/Verse | `economy-sim`, `uefn-logs` | **Alta** — verifica *osservata* del primo acquisto: manca nel kit. |
| `builtin:tycoon-income-loop` | Gioca, attende 30s, verifica log di income. | Verifica generatore. | No: UEFN/Verse | `economy-sim`, `uefn-logs` | **Alta** — come sopra. |
| `builtin:tycoon-ducky-playtest` | Controlla spawn, acquisto, income, collector, tier successivo. | QA economia completa. | No: UEFN/Verse | `economy-sim`, `uefn-session-regression` | **Alta** — sequenza QA economica assente. |
| `builtin:open-uefn-project` | Lancia UEFN e attende l'isola scelta. | Aprire progetto. | No: UEFN | `uefn-session-regression` | **Bassa** — coperto. |
| `builtin:restart-uefn` | Chiude/riapre progetto e attende listener. | Riavvio. | No: UEFN | `uefn-session-regression`, `uefn-mcp-lab-guard` | **Bassa** — coperto. |
| `builtin:publish-private` | Upload Private Version, copia codice, posta codice. | Pubblicazione privata. | No: UEFN | `fab-product` | **Alta** — sequenza precisa con codice privato, poco documentata nel kit. |
| `builtin:sandbox-verify` | Builda commit corrente in sandbox, esegue/controlla/riporta; nessun commit o deploy. | Verifica sicura. | Sì: sandbox/git | No | **Alta** — pattern "verifica senza effetti collaterali" applicabile al kit. |
| `builtin:memory-calculation` | Avvia Memory Calculation e gesti popup codice privato. | Calcolo memoria. | No: UEFN | `uefn-profiling` | **Media** — dettaglio operativo mancante. |

---

## E. Nodi del motore workflow (catalogo e libreria)

Tutti app-particellari, ma elencati integralmente. Utilità media solo dove l'idea è astrattamente riutilizzabile.

| Nome | Cosa fa | Quando si usa | Motore non-UEFN | Già nel kit | Utilità e motivo |
|---|---|---|---|---|---|
| `input.text` / `.number` / `.boolean` / `.json` | Dati in ingresso tipizzati. | Iniziare workflow. | Sì: app | No | **Bassa** — primitive UI. |
| `input.image` / `.images` / `.audio` / `.video` / `.mesh` / `.pdf` / `.svg` / `.file` | Input media e file. | Workflow multimediale. | Sì: app | No | **Bassa** — primitive UI. |
| `logic.if` / `.expression` / `.compare` | Condizioni ed espressioni. | Ramificare. | Sì: app | No | **Bassa** — logica generica. |
| `llm.ask` | Chiamata LLM. | Chiedere al modello. | Sì: provider | No | **Bassa** — infrastruttura. |
| `text.template` | Template di testo. | Comporre messaggi. | Sì: app | No | **Bassa** — primitiva. |
| `util.preview` | Anteprima valore. | Debug workflow. | Sì: app | No | **Bassa** — primitiva. |
| `start.manual` / `start.cron` / `start.chat` | Trigger manuale, schedulato, da chat. | Avviareflusso. | Sì: app | No | **Bassa** — il kit non ha scheduler. |
| `flow.input` / `flow.output` / `flow.end` | Ingresso/uscita/fine del grafo. | Strutturare grafo. | Sì: app | No | **Bassa** — primitiva. |
| `workflow.call` | Chiama un altro workflow. | Riutilizzo flussi. | Sì: app | No | **Bassa** — primitiva. |
| `spotlight.step` / `spotlight.closed` / `ui.spotlight` | Evidenzia un passo nell'UI. | Guidare l'utente. | Sì: UI app | No | **Bassa** — specifico app. |
| `ducky.prompt` / `ducky.spawn` | Chiedi a un ducky / crea un ducky. | Delegare lavoro. | Sì: app | No | **Bassa** — modello agenti diverso. |
| `pipeline.agent` / `pipeline.finish` | Agente di pipeline e sua conclusione. | Eseguire pipeline. | Sì: app | No | **Bassa** — primitiva. |
| `notify.message` | Notifica all'utente. | Avvisare. | Sì: app | No | **Bassa** — primitiva. |
| `flow.wait` / `flow.foreach` / `flow.repeat` / `flow.branch` / `flow.choose` | Attesa, cicli, diramazione, scelta. | Controllo flusso. | Sì: app | No | **Bassa** — primitiva. |
| `tool.call` | Chiama un tool. | Usare tool nel grafo. | Sì: app | `mcp-tool-contracts` | **Bassa** — concetto analogo. |
| `code.js` | Nodo codice JavaScript con librerie dichiarate. | Logica custom. | Sì: JS | No | **Bassa** — il kit non esegue JS. |
| `uefn.open_project` / `.launch` / `.close` / `.restart` | Controllo ciclo di vita editor. | Gestire UEFN. | No: UEFN | `uefn-session-regression`, `uefn-mcp-lab-guard` | **Bassa** — coperto. |
| `uefn.wait_ready` / `.wait_window` | Attesa editor/pronta finestra. | Sincronizzare. | No: UEFN | `uefn-session-regression` | **Bassa** — coperto. |
| `uefn.check` | Controllo stato editor. | Verifica. | No: UEFN | `uefn-editor-logs` | **Bassa** — coperto. |
| `fortnite.servers` | Stato server Fortnite. | Verifica servizi. | No: Fortnite | No | **Media** — informazione utile prima di un playtest. |
| `uefn.game.start` / `.stop` / `uefn.player.wait` | Avvia/ferma partita, attendi giocatore. | Playtest. | No: UEFN | `uefn-session-regression` | **Bassa** — coperto. |
| `uefn.log.expect` | Attende una riga di log attesa. | Assertive sui log. | No: UEFN | `uefn-logs` | **Alta** — il kit legge i log ma non ha un "attendi il log atteso" come gate. |
| `llm.vision` / `.extract` / `.translate` / `.pick` | Visione, estrazione, traduzione, scelta. | Analisi media/testo. | Sì: LLM | `fortnite-thumbnail-pro`, `localization` (fuori kit) | **Bassa** — coperto in parte. |
| `image.generate` / `.edit` / `.remove_bg` / `.upscale` | Generazione e editing immagini. | Artwork. | Sì: image ops | `fortnite-thumbnail-pro` | **Bassa** — coperto. |
| `image.resize` / `.crop` / `.convert` / `.split_alpha` / `.combine_alpha` / `.split_channels` / `.combine_channels` / `.concat` / `.text` | Manipolazione immagini. | Preparare texture/thumbnail. | Sì: image ops | `fortnite-thumbnail-pro` | **Bassa** — coperto. |
| `mesh.generate` / `.from_image` / `.multi_view` / `.retexture` / `.remesh` / `.uv_unwrap` / `.convert` / `.repair` / `.bake` / `.render` | Pipeline mesh cloud. | Creare/riparare mesh. | Sì: 3D cloud | `forge` (fuori kit) | **Media** — buco user-level. |
| `mesh.rig` / `.animate` | Rig e animazione cloud. | NPC. | Sì: character ops | `animation` (fuori kit) | **Media** — buco user-level. |
| `mesh.info` / `.fit_box` / `.set_origin` / `.origin_text` / `.auto_scale` / `.rotate` / `.textures_extract` / `.textures_apply` | Mesh locali: info, bbox, origine, scala, rotazione, texture. | Preparare import. | Sì: mesh ops | `uefn-asset-budget`, `forge` (fuori kit) | **Alta** — controlli "fit box / origin / auto scale" sono esattamente il gate asset. |
| `blender.open` / `.render` / `.export`, `uefn.import` | Blender → UEFN. | Importare modello. | Sì: Blender | `forge` (fuori kit) | **Media** — buco user-level. |
| `list.make` / `.get` / `.count` / `.join` / `.filter` / `.map` | Operazioni su liste. | Dati workflow. | Sì: app | No | **Bassa** — primitive. |
| `pdf.text` / `.images`, `util.save_file` | Estrazione PDF e salvataggio file. | Documenti. | Sì: PDF | `pdf` (fuori kit) | **Bassa** — coperto fuori kit. |

---

## F. Protocolli di pianificazione e regole sempre attive

| Nome | Cosa fa | Quando si usa | Motore non-UEFN | Già nel kit | Utilità e motivo |
|---|---|---|---|---|---|
| `plan_review.py` — `PLAN_PROTOCOL` | Diagnosi → Fix → Verify, dimensione delle foglie, check "Done.when", aggiornamento piano, un piano di team con sotto-piani. | Piani lunghi. | Sì: Ducky coding agent | Regola 13, `planner-docs` | **Alta** — il "leaf sizing + Done.when verificabile" manca nel kit. |
| `plans.py` — `demo-getting-started` | Mini-piano didattico: apri impostazioni, scegli ducky, avvia chat. | Onboarding app. | Sì: app | No | **Bassa** — onboarding Ducky. |
| `plans.py` — `verify-loop` | Diagnosi, Fix, Verify con check-tool come Done.when. | Ogni fix. | Sì: Ducky | Regola 10 (compila = done) | **Alta** — estende la regola 10 dal compilare al verificare. |
| `agent/hard_rules.py` (1-92) | Regole sempre attive: molte call in un turno, mai due volte, skill prima, chiedi una volta, trova workflow una volta, lane, output terminale visibile, regole plugin, commit while going, evidenza di completamento. | Ogni turno agente. | Sì: Ducky | Regole 1-15, `token-aware-coding` | **Alta** — "mai la stessa ricerca due volte" e "evidenza di done" sono buone regole nuove. |
| `agent/hard_rules.py` (94-210) | Regole isola: gate listener, Epic MCP prima, gateway editor, `execute_python` ultimo, regole compile/evidenza Verse. | Lavoro su isola. | No: UEFN | `mcp-tool-contracts`, `uefn-mcp-lab-guard`, `uefn-verse-build` | **Alta** — la gerarchia "MCP ufficiale prima, Python estremo rimedio" è più esplicita che nel kit. |
| `agent/prompt.py` | Prompt di sistema e compattazione; limite indice memoria 8000 caratteri. | Contesto lungo. | Sì: agente | `token-aware-coding` | **Media** — limite numerico esplicito utile. |
| `coding_agents/mcp_inject.py` | Iniezione config MCP per sessione per Codex/OpenCode. | Avviare sessione. | Sì: IDE | `mcp-tool-contracts`, `uefn-mcp-lab-guard` | **Bassa** — specifico Ducky/Codex. |
| `docs/architecture/write-pipeline.md` | Pipeline di scrittura, guardia per tipo progetto, protocolli, come aggiungere path, semantica fallimenti. | Scrivere file in progetto. | Sì: app | No | **Media** — idea di "guardia per tipo di progetto" assente. |
| `docs/architecture/editor-change-tracking.md` | Tracciamento modifiche editor, registry, come aggiungere cattura, revert, comandi opachi. | Revert/sync editor. | Sì: app | `uefn-editor-logs`, `uefn-session-regression` | **Media** — il revert documentato manca. |
| `docs/architecture/store.md` | Schema `ducky.db`, connessioni, crittografia, migrazioni, cosa non va nel DB. | Storage app. | Sì: SQLite | No | **Bassa** — infrastruttura. |
| `docs/architecture/search.md` | Indice ricerca skill/tool: freschezza, ranking, hint per turno, costo token, fallback, misurazione. | Trovare skill/tool. | Sì: ricerca | `token-aware-coding`, `mcp-tool-contracts` | **Alta** — il kit ha indici ma non misura la *findability*. |
| `docs/architecture/ai-file-protection.md` | Protezione file scritti da AI. | Scritture AI. | Sì: app | `uefn-mcp-lab-guard` | **Media** — principio analogo. |
| `docs/architecture/questions-and-chat-lifecycle.md` | Ciclo di vita domande/chat. | Chiedere all'utente. | Sì: app | No | **Bassa** — specifico UI. |
| `docs/architecture/panel-install-recovery.md` | Recupero installazione pannello. | Installazione rotta. | Sì: app | No | **Bassa** — specifico app. |
| `docs/architecture/workflow-cancellation.md` | Cancellazione workflow. | Interrompere flusso. | Sì: app | No | **Bassa** — specifico app. |
| `docs/adr/0001-write-through-with-lanes-and-changesets.md` | ADR: scrittura con lane e changeset. | Decisioni architetturali. | Sì: app | No | **Media** — il formato ADR è già nel kit (`docs/adr/`). |
| `docs/adr/0002-editor-change-tracking-and-revert.md` | ADR: tracking e revert editor. | Come sopra. | Sì: app | No | **Media** — come sopra. |
| `docs/adr/0003-one-local-sqlite-database.md` | ADR: un solo DB SQLite locale. | Come sopra. | Sì: app | No | **Bassa** — scelta app. |
| `docs/adr/0004-search-index-in-ducky-db.md` | ADR: indice ricerca nel DB. | Come sopra. | Sì: app | No | **Media** — legato a `search.md`. |
| `docs/testing/store-test-plan.md` | Piano test migrazioni store e baseline. | Test DB. | Sì: app | No | **Bassa** — specifico app. |
| `docs/patches/openai-question-waits.patch` | Patch/assert di configurazione per attesa domande Codex MCP. | Debug MCP Codex. | Sì: Codex | No | **Bassa** — specifico provider. |

---

## G. Routing tool, bridge e MCP

| Nome | Cosa fa | Quando si usa | Motore non-UEFN | Già nel kit | Utilità e motivo |
|---|---|---|---|---|---|
| `agent/builtin_toolsets.py` | Gruppi toggle `builtin_ducky`/`builtin_uefn` e tool bridge sempre attivi (ping, listener_command, execute_python, get_log, shutdown, hints, dismiss modal). | Definire tool base. | Sì: app | `mcp-tool-contracts` | **Media** — idea di "tool sempre attivi vs opzionali", utile. |
| `agent/core_tools.py` | Tool sempre caricati: read/edit/search/git workspace, terminale, ask-user, plan update, view image. | Ogni sessione. | Sì: app | `token-aware-coding` | **Bassa** — strumenti base. |
| `agent/tool_router.py` | Riesporta CORE_TOOLS, DESTRUCTIVE_TOOLS, EXCLUDED_TOOLS, INTENT_KEYWORDS, PLAN_TOOLS, select_tools. | Selezionare tool per intenzione. | Sì: app | `mcp-tool-contracts`, `uefn-disciplines` | **Media** — il concetto "strumenti distruttivi esclusi" è interessante. |
| `toolsets/intents.py` | Bundle opzionali per scene, asset, materiali. | Intenzione specifica. | Sì: app | `mcp-tool-contracts` | **Bassa** — coperto. |
| `toolsets/workflows.py` | Bundle nominati: core listener-online, placement, wiring, file-edit, materiali. | Workflow ricorrenti. | Sì: app | `mcp-tool-contracts` | **Bassa** — coperto. |
| `toolsets/tool_index.py` | Indice compatto dei tool MCP nei prompt. | Risparmiare token. | Sì: app | `mcp-tool-contracts`, `uefn-mcp-heavy-calls` | **Media** — tecnica di compattazione utile. |
| `toolsets/categories/{assets,creative_devices,memory,panel,project,scene,testing,verse_api,verse_devices,workspace}.py` | Dieci categorie riusabili di tool per dominio. | Organizzare tool. | Sì: app | `mcp-tool-contracts` | **Bassa** — catalogo già presente. |
| `coding_agents/*` (base, cli_pty, cli_shared, core_tools, epic, file_changes, git_lock_cleanup, mcp_bridge_host.mjs, mcp_inject, plan_edit_rules, plan_hooks, plan_review, plan_ticks, plans, proc_exec, readiness, runner, session_refresh, settings_helpers, stall_notice, team_plan_events, tick_claim_guard, tick_gate) | Infrastruttura coding agent: PTY, lock git, piano, tick, gate, sessioni, stall notice, eventi team. | Eseguire coding agent. | Sì: Ducky | `planner-docs`, regola 13 | **Media** — `tick_gate`, `stall_notice`, `git_lock_cleanup` sono idee nuove per il kit. |
| `agent/a2a_broker.py` | Broker agente-agente solo RAM, inbox per chat, thread di risposta, avvisi inattività, consegna fire-and-forget. | Comunicazione tra agenti. | Sì: app | No | **Media** — il kit ha verdict file, non messaging. |
| `agent/a2a_client.py` | Accesso al broker: in-process o POST all'API pannello. | Come sopra. | Sì: app | No | **Bassa** — dettaglio implementativo. |
| `agent/a2a_format.py` | Formatta messaggi e avvisi; `wrap_untrusted` delimita testo terzo non fidato. | Testo non fidato. | No: universale | No | **Alta** — difesa prompt injection assente nel kit. |
| `bridge/client.py` | Client HTTP al listener UEFN e helper percorsi workspace. | Comunicare con listener. | No: UEFN | `mcp-tool-contracts` | **Bassa** — coperto. |
| `bridge/dynamic_tools.py` | Espone automaticamente comandi listener senza wrapper statici. | Nuovi comandi. | No: UEFN | `mcp-tool-contracts` | **Media** — idea di autodiscovery, già parziale nel kit. |
| `bridge/call_limits.py` | Policy timeout tool MCP condivisi. | Chiamate lente. | Sì: MCP | `uefn-mcp-heavy-calls` | **Bassa** — coperto. |
| `bridge/bridge_version.py` | Bridge vecchi escono dopo aggiornamento app. | Aggiornamenti. | Sì: app | `uefn-version-upgrade` | **Media** — idea di invalidare versione bridge, applicabile al kit. |
| `bridge/shared_mcp.py` | Demone FastMCP condiviso su 127.0.0.1 con token. | Condividere MCP. | Sì: MCP | `uefn-mcp-lab-guard` | **Bassa** — infrastruttura. |
| `bridge/serial.py` | Serializza comandi listener/tool che non possono girare in parallelo. | Conflitti. | Sì: app | `uefn-mcp-lab-guard` | **Alta** — il kit non ha una nozione esplicita di "questi tool non in parallelo". |
| `bridge/status.py` | Controllo salute listener. | Diagnosi. | No: UEFN | `uefn-mcp-lab-guard` | **Bassa** — coperto. |
| `bridge/revive.py` | Riporta listener senza riavviare UEFN. | Listener morto. | No: UEFN | `uefn-validation-failure-diagnosis` | **Media** — tecnica di recupero mancante. |
| `bridge/plugin_gate.py` | Verify tool plugin registrati prima di tools/list e tools/call. | Plugin MCP. | Sì: app | `mcp-tool-contracts` | **Bassa** — specifico Ducky. |
| `bridge/editor_gateway.py` | Unica porta per tutte le chiamate all'editor UEFN. | Ogni chiamata editor. | No: UEFN | `mcp-tool-contracts`, `uefn-mcp-lab-guard` | **Alta** — rafforza il concetto di "single door" già nel kit. |
| `bridge/editor_presence.py` | Rileva editor in esecuzione dalla lista processi. | Prima di agire. | No: UEFN | `uefn-session-regression` | **Bassa** — coperto. |
| `bridge/island_locks.py` | Protegge file bloccati da altro PC con Unreal Revision Control. | Collaborazione multi-PC. | No: UEFN | No | **Media** — caso reale poco coperto. |
| `backend/tools/core/*` (app_popups, changesets, code_diagnostics_lib, code_diagnostics, editor_api_hints, hints, model_picture, sandbox_tools, self_care_tools, system, uefn_modal, uefn_popups, uefn_windows, web_github, web_http, web_lookup, web_video, workspace_code) | Tool core: popup, changeset, diagnostica codice, sandbox, web, finestra. | Supporto agente. | Misto | `uefn-editor-logs`, `uefn-lessons` | **Media** — diagnostica codice e changeset sono idee utili. |
| `backend/tools/panel/*` (archive_tree, ducky_finish_team, ducky_panel_plans, ducky_panel_terminal, ducky_panel, ducky_swarm, panel_ai_plugins, panel_automations, panel_general_storage, panel_i18n, panel_mcp, panel_plugin_check, panel_plugin_data, panel_profiles, panel_settings, panel_skills, panel_store, panel_ui, panel_verse_templates, permission_prompt, plugin_repo, spawn_nesting, swarm_build, swarm_preview, team_waits, terminal_approval) | Gestione pannello: permessi, team, swarm, skill, store, terminale. | UI/app. | Sì: app | No | **Bassa** — infrastruttura app. |
| `backend/tools/uefn/*` (actors, ai, assets_pipeline, assets, data_tables, device_editor, device_focused, editor, fortnite_client, introspection, island_placeable, level_viewport, level, memory) | Tool dominio UEFN. | Costruire isola. | No: UEFN | `uefn-level-devices`, `uefn-assets-data`, `uefn-editor-logs` | **Bassa** — coperto dal mapping MCP. |
| `backend/tools/verse/*` (compile_hints, skill_tool, template_verify, umg, verse_diagnostics, verse_digests, verse_editable, verse_focused, verse_lint, verse_stats, verse, wire_preflight) | Tool Verse: compile, digest API, diagnostica, lint, preflight collegamenti. | Scrivere Verse. | No: Verse | `uefn-verse-build`, `uefn-lessons`, `uefn-ui-widgets` | **Alta** — `wire_preflight` e `verse_lint` come gate prima del compile mancano. |
| `backend/tools/world/*` (blockout_areas, fort, level_design, pcg, worldgen) | Tool world: blockout, PCG, worldgen, Fort actors. | Costruire mondo. | No: UEFN | `level-design-uefn`, `uefn-pcg`, `uefn-disciplines` | **Bassa** — coperto. |
| `tools/animation/*`, `tools/modeling/*`, `tools/scene/*`, `tools/vfx/*`, `tools/tester/*` | Animation retarget, sequencer, modeling, scene graph, niagara, session play, suite. | Dominio specifico. | No: UEFN | Skill fuori kit (`animation`, `forge`, `scenegraph`, `vfx`, `tester`) | **Media** — confermano i buchi user-level del kit. |
| `tools/integrations/translation_service.py`, `translation_tools.py`, `tools/support/plugin_gate.py` | Traduzione e gate plugin. | Localizzazione/plugin. | Sì: servizi | `localization` (fuori kit) | **Bassa** — coperto fuori kit. |
| `backend/memory/project.py` | Memoria progetto per agente con file di voci condivisi. | Ricordare convenzioni. | Sì: Ducky | `uefn-lessons`, second brain | **Media** — memoria per progetto già concettualmente presente. |
| `backend/memory/scope.py` | Sceglie memoria progetto dal repo in cui si lavora, non solo dal progetto aperto. | Multi-repo. | Sì: Ducky | No | **Media** — dettaglio utile. |
| `backend/search/{chunker,embedder,find,hints,indexer,query,records,sealed_records}.py` + `eval/`, `fixtures/` | Indicizzazione e ricerca ibrida di skill/tool, con eval. | Trovare conoscenza. | Sì: ricerca | `token-aware-coding`, `second-brain-query` | **Alta** — la misurazione della findability manca. |
| `backend/sandbox/*` (capture, env, fetch, gitops, jobs, manifest, mcp_client, paths, policy, runtimes, service) | Sandbox di esecuzione con policy, manifest, gitops. | Codice non fidato. | Sì: sandbox | No | **Alta** — idea di policy esplicita per script generati. |
| `backend/testing/{device_semantics,device_sim,live_graph,verse_harness}.py` | Simulazione grafo dispositivi, semantica, harness Verse, grafo live. | Test senza editor. | No: UEFN | `tester` (fuori kit), `uefn-session-regression` | **Alta** — test dispositivi offline è un buco user-level. |
| `backend/voice/*` | Voce: lane, riepiloghi, trascrizione, Windows SAPI/TTS. | Parlare col ducky. | Sì: Windows | `conversations` (fuori kit) | **Bassa** — audio voce, non map. |
| `backend/store/*`, `backend/uefn_plugins/*` | Store Ducky, DB, migrazioni, firma, plugin host, ledger, VCS engine, UI kit, webview. | Plugin/app. | Sì: app | `fab-product` | **Bassa** — piattaforma diversa. |
| `backend/workspace/*` (ai_ignore, diff_workers, editor_ops, editor_record, events, human_watch, identity, journal, lanes, paths, plugin_revert, policy, run_folders, runtime, tool_record, verse_cleanup, writer, schemas) | Pipeline di scrittura con journal, lane, watch umano, revert, record tool. | Scritture sicure. | Sì: app | `uefn-mcp-lab-guard` | **Media** — journal e watch umano sono idee buone. |
| `uefn_listener/registry/*` (23 file: asset_registry, assets_pipeline, blockout_areas, data_tables, device_graph, editor_control, fort, introspection, landscape_heightmap, level_design, level, materials, modeling, niagara, pcg, scene_graph_filters, scene_graph, umg_author, umg_spec, umg, verse, worldgen_foliage_stats, worldgen) | Registri lato UEFN che espongono le operazioni all'app. | Eseguire operazioni in editor. | No: UEFN (Python) | `mcp-tool-contracts` | **Bassa** — equivalente del mapping MCP. |
| `uefn_listener/handlers/*` + `launch_listener.py` | Handler listener: actor, asset, device editor, revert, project, revisione, sistema, Verse. | Avviare/comandare listener. | No: UEFN | `uefn-mcp-lab-guard` | **Bassa** — infrastruttura. |
| `frontend/skill-pack-studio/*` (SkillPackStudio, PackEditorPane, FileEditorPane, CreateReferenceFileModal, SkillSearchHits, api, model, utils, test, CSS) | Studio UI per creare skill pack e file reference. | Scrivere skill. | Sì: UI React | No | **Bassa** — il kit scrive skill con tool, non con UI. |
| `frontend/ui_web/{mcp_catalog,native_capture_bridge,panel_api_*,group_orchestrator,lanes,team_brief,team_keeper,plugin_host_api,plugin_llm,snip_overlay,remote_ducky_window}.py` e `src/{automations,swarm,verse_editor/workflow}/*` | API pannello, orchestrazione gruppi, lane, cattura nativa, workflow Verse. | Pannello Ducky. | Sì: app | No | **Bassa** — infrastruttura app. |

---

## H. Browser, account, pubblicazione, build e test

| Nome | Cosa fa | Quando si usa | Motore non-UEFN | Già nel kit | Utilità e motivo |
|---|---|---|---|---|---|
| `ui_web/browser_overlay.py` | Pannelli WebView2 nativi ancorati alle finestre, profilo condiviso, CDP, regole script, esclusioni account/pagamento. | Browser dentro app. | Sì: WebView2/CDP | `browser` (fuori kit) | **Media** — regole di sicurezza profilo/sito utili. |
| `ui_web/browser_vault.py` | Login dei tab browser a riposo, Windows Hello, lock/relock, watcher. | Credenziali browser. | Sì: Windows | No | **Bassa** — gestione segreti app. |
| `tests/e2e/remote_view/direct_e2e.py` | E2E CDP su Edge/Chrome headless porta 9222. | Test browser remoto. | Sì: CDP | `browser` (fuori kit) | **Bassa** — specifico app. |
| `tools/core/web_video.py` | Helper video/web: transcript, contact sheet, frame, download, segmenta. | Ricerca video. | Sì: YouTube | No | **Media** — tecnica per `fortnite-social-trailer`. |
| `frontend/duckyos_account.py` | Login tenant DuckyOS, PKCE, device authorization, base uefnducky.org. | Accedere account. | Sì: cloud Ducky | `account` (fuori kit) | **Bassa** — provider diverso. |
| `backend/agent/accounts.py` | Account provider, API key, CLI login, switch automatico, marking exhausted. | Gestire provider. | Sì: provider | `account` (fuori kit) | **Bassa** — infrastruttura. |
| `backend/store/account_rows.py` | Righe per account, UNCLAIMED/PARKED, chiavi chat, seal/open, digest, claim. | Data store account. | Sì: app | No | **Bassa** — specifico app. |
| `release/publish_app.py` | Pubblica Setup.exe nello Store: fasi test/build/upload, S3, MCP release. | Rilasciare app. | Sì: Store Ducky | No | **Bassa** — piattaforma diversa. |
| `release/publish_panel.py` | Build/stage pannello telefonico nel plugin. | Remote view. | Sì: app | No | **Bassa** — specifico app. |
| `release/build_web_setup.py` | WebSetup firmato che scarica e verifica Setup dal Store. | Distribuzione. | Sì: Windows | No | **Bassa** — packaging. |
| `release/commit_before_store.py` | Commit/push clone prima upload; rifiuta tree sporco; esclude artifact e segreti. | Prima di rilasciare. | Sì: git | Regole git del kit | **Media** — il "rifiuta tree sporco" è già buona pratica. |
| `release/sign_windows.py` | Firma Authenticode (Azure/PFX/signtool), `--check`, `--require`. | Firma binari. | Sì: Windows | No | **Bassa** — non serve al kit. |
| `release/update_pack.py` | Pack/manifest zip per aggiornamenti incrementali. | Aggiornamenti app. | Sì: app | `uefn-version-upgrade` | **Bassa** — meccanica diversa. |
| `release/verify_installer_panel.py` | Estrae payload Inno e testa recupero pannello senza eseguire Setup né toccare dati utente. | Verifica installer. | Sì: Windows | No | **Media** — idea "verifica senza effetti collaterali" (come sandbox-verify). |
| `.github/workflows/store-publish.yml` | Pubblicazione Store solo manuale; fork non possono pubblicare. | CI release. | Sì: GitHub | No | **Bassa** — policy repo. |
| `.github/workflows/security.yml` | Stessi check di publish via `check_security.py --app-only`. | CI sicurezza. | Sì: GitHub | `tests/run_all.py` | **Media** — idea di gate sicurezza separato. |
| `build/build_exes.py`, `build/build_exes.ps1`, `unified.spec`, `fetch_ffmpeg.py`, `fetch_search_model.py`, `runtime_versions.py`, `upgrade_proof/*` | Build PyInstaller, artefatti, versione, proof upgrade. | Compilare app. | Sì: Python/Windows | No | **Bassa** — packaging app. |
| `scripts/audit_verse_errors.py` | Miner transcript Claude per errori compile Verse e failure `mcp__uefn`. | Trovare errori ricorrenti. | No: Verse | `uefn-lessons`, `uefn-logs` | **Alta** — minare i log per generare lezioni è applicabile al kit. |
| `scripts/check_findability.py` | Controlla findability di skill/tool (`--core`, `--installed`). | Verificare indici. | Sì: Ducky | `validate_skills.py` | **Alta** — aggiunge una dimensione che i test kit non hanno. |
| `scripts/check_licenses.py` | Assert SAL app/OS e MIT plugin desktop. | CI licenze. | Sì: repo Ducky | No | **Bassa** — licenze loro. |
| `scripts/check_security.py` | gitleaks, pip-audit, npm audit; gate per publish. | Prima di rilasciare. | Sì: CI | `privacy_scan.py` in run_all | **Media** — analogo. |
| `scripts/extract_vscode_ext.py` | Estrae grammatica/snippet/tema/language server da installazione UEFN locale; non bundle asset Epic. | Configurare editor Verse. | No: UEFN | `uefn-verse-build` | **Media** — tecnica "leggere da installazione locale, non copiare". |
| `scripts/search_eval.py` | Valuta ricerca skill/tool: engine `today`, `keyword`, `hybrid`. | Misurare ricerca. | Sì: Ducky | `token-aware-coding` | **Alta** — come `docs/architecture/search.md`. |
| `scripts/measure_ducky_memory.ps1`, `two_app_e2e.py` | Performance memoria ed E2E due app. | Profilare app. | Sì: app | No | **Bassa** — specifico app. |
| `native_launcher/crates/*` (autostart, bounds, dialogs, report, server, shim, splash, supervisor, tray, window) | Launcher Rust: avvio, bounds finestre, dialoghi, report crash, proxy API, shim WebView, splash, supervisore con restart/crash-loop, tray, finestra frameless. | Avviare app. | Sì: Rust/Windows | No | **Bassa** — nativi app. |
| `release/installer/host/*` + `host.tests/SelfCheck.cs` | Host installer C# (web release, uninstall, stats, engine, finestra) e self-check. | Installare app. | Sì: C# | No | **Bassa** — packaging Windows. |
| `tests/test_*` (appdata_guard, ducky_ask_discovery, ducky_ask_readonly, ducky_cli, ducky_discovery_catalog, ducky_mode_dispatch, ducky_permission_modes, lane_ownership, panel_port_isolation, plugin_asset_packs, project_paths_pin, publish_security_gate, release_signing, scene_graph_filters) + `e2e/`, `fixtures/`, `perf/` | Suite test delle garanzie dell'app: permessi, isolamento porte, ownership lane, path progetto, firma, publish. | Verificare app. | Sì: app | `tests/run_all.py` | **Media** — il concetto "test delle garanzie" è identico a `run_all.py`. |

---

## Sintesi per la scelta (nessuna skill ricreata in questa fase)

**Alta utilità candidata** (da valutare con te):
1. `ponytail` + `review.md` — dottrina di minimalità e gate review del diff; il kit ha solo risparmio token.
2. `agent/a2a_format.py` (`wrap_untrusted`) — difesa prompt injection per testi terzi.
3. `bridge/serial.py` + `bridge/editor_gateway.py` — regola esplicita "una porta, certi tool non in parallelo".
4. `plan_review.py` (`PLAN_PROTOCOL`, leaf sizing, `Done.when`) e `plans.py:verify-loop`.
5. `uefn.log.expect`, `tycoon-first-purchase`, `tycoon-income-loop`, `tycoon-ducky-playtest` — QA osservata via log.
6. `publish_private` + `builtin:publish-private` — sequenza Upload Private Version con popup/codice.
7. `pipe-game-ready`, `pipe-model-check`, `mesh.fit_box/set_origin/auto_scale` — gate asset prima dell'import.
8. `scripts/check_findability.py` + `docs/architecture/search.md` + `scripts/search_eval.py` — misurare la findability delle skill.
9. `scripts/audit_verse_errors.py` — trasformare errori reali in lezioni `uefn-lessons`.
10. `backend/testing/device_sim.py`, `device_semantics.py`, `live_graph.py`, `verse_harness.py` — test dispositivi offline.
11. `builtin:sandbox-verify` e `release/verify_installer_panel.py` — verifica senza effetti collaterali.
12. `hard_rules.py` (regole 1-92) — "mai due volte la stessa ricerca", "evidenza di done".

**Nota licenza:** per i punti 1-12 la FASE 3 dovrà essere riscritta da zero in inglese adattata a UEFN/Verse/Fortnite, senza riprendere testi, strutture o nomi di file del repo e senza citarne la provenienza, come da regola del kit e dall'art. 5a della SAL.

## Ricreate

| Skill | Commit | `validate_skills.py` |
|---|---|---|
| `uefn-editor-dispatch` | `1237344` | 0 errori, warning attesi (3050 char) |
| `uefn-plan-verify` | `9010c9a` | 0 errori, warning attesi (3157 char) |
| `uefn-private-publish` | `c2c995c` | 0 errori, warning attesi (3227 char) |
| `uefn-safe-verification` | `0edfbd0` | 0 errori, warning attesi (3009 char) |
| `uefn-agent-discipline` | `ee36e4a` | 0 errori, warning attesi (3408 char) |

- **Validazione finale:** 67 skill, 0 errori, 80 warning. I warning sono quelli attesi con frontmatter solo `name`/`description` (nessun `last_reviewed`/`sources`) e superamento delle 3000 char, richiesto dalla consegna.
- **Suite `python tests/run_all.py`:** completata con successo: **189/189** passi (fix Windows in `5ac8507`). Prima delle fix fallivano `test_gate.py`, `test_integrate.py` e `test_how_to_hybrid.py`; ora tutti passano.
- **Fix Windows applicate:** `tools/gate.py` accetta il percorso assoluto di `sys.executable` tramite basename; `tests/test_gate.py` usa `sys.executable` invece di `python3`; `tools/integrate.py::pid_alive` non usa più `os.kill(pid, 0)` su Windows (terminava il processo invece di controllarlo); `tests/test_integrate.py` gestisce timeout/KeyboardInterrupt e la terminazione hard di Windows; `tests/test_how_to_hybrid.py` accetta CRLF.
- **Verifiche mirate finali:** `privacy_scan.py` clean, `validate_skills.py` exit 0, `token_budget.py` exit 0, `build_manual.py --check` up to date, `test_manual.py` exit 0.
- **Baseline token:** `skill entry points` 195729 → 211871 char (+16142, ~4036 token, +8,25%), sotto la tolleranza 10%: baseline **non** alzata.
- **Indice:** 5 righe aggiunte a `docs/manual/skill-catalog.md`; manuale HTML, `docs/kit-stats.json`, `project-template/Claude/community/kit-stats.json` e wiki kit ricostruiti con i relativi builder.
- **Ripristino:** telemetry e token ledger ripristinati con `git checkout --` dopo i test; worktree esterni non toccati.
