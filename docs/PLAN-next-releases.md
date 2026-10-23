# Piano delle prossime release - stato al 2026-10-23 (sera)

Repo: mimmo-the-root/UEFN-dream-bot-team (locale C:\UEFNDreamTeamBot). Pubblicate fino alla 1.107.5; 1.107.6 e 1.108.0 sono committate (61d9296), publish.cmd da lanciare dall'utente (assorbono tutto il lavoro 1.107.7). L'utente possiede commit, tag e release.

Come usare questo file: ripartire dalla prima riga con stato "da fare". Aggiornare lo stato qui (e nella copia della pagina di progetto `claude/PLAN-next-releases.md`) a ogni passo. Fonti: lista idee dei competitor (`claude/competitor-ideas-2026-10.md`) e richieste dell'utente del 23 ottobre.

Scadenza che guida l'ordine: Epic jam "Vibe your way to $50k", annuncio del tema 11 novembre, costruzione 12-15 novembre (consegna entro il 15 novembre 17:59 PST). Chi usa il kit nel jam può preparare strumenti e agenti prima del 12, ma non iniziare il gioco.

## Richieste dell'utente (23 ottobre)

| # | Richiesta | Stato |
|---|---|---|
| U1 | File Verse: niente più storico delle modifiche nell'intestazione, solo la descrizione in inglese di cosa fa il codice, sempre aggiornata (data e versione restano). Modifiche ed errori vanno nei log come tracciatura per l'apprendimento | fatto (1.108.0) |
| U2 | Mappa nuova: il kit chiede di installare i componenti (= `project-template`, oggi copiato a mano) - automazione per chi userà il kit nel jam | fatto (1.108.0) |
| U3 | Il kit chiede se è una mappa o un prodotto Fab | fatto (1.108.0) |
| U4 | Prodotto Fab (piccolo progetto UEFN i cui componenti il cliente aggiunge al suo): niente `project-template` nel progetto; solo un set di `.md` con le info per la pubblicazione, che diventano manuale utente/istruzioni | da fare (R3) |
| U5 | Genera gli screenshot necessari per la pubblicazione | da fare (R3) |

## Verifiche fatte (cosa c'è oggi nel kit)

- **U1.** Oggi `coder` deve tenere nell'intestazione di ogni file Verse data, versione incrementata e righe di storico ("l'intestazione è l'unico storico che abbiamo"); `compliance-reviewer` (controllo 3) segnala storici oltre 15 righe e il coder li pota; `history_trim.py` (v1.87) sposta in `Claude/docs/archive/` i lunghi paragrafi di storia nei file Verse oltre 20 KB. Tutto da cambiare: nuova regola nel coder e nel reviewer, `history_trim` diventa migrazione (toglie lo storico dalle intestazioni esistenti, lo archivia), test da aggiornare (`tests/test_history_trim.py`). Esistono già `Claude/logs/verse-errors.jsonl` (errori di build, dalla 1.103) e il ledger MCP; manca un registro delle modifiche al codice (`verse-changes.jsonl`): da creare, con hook su scritture di file `.verse` e una riga di motivo scritta dal coder. Il sistema di apprendimento (`skills_lib.py`, `learn_nudge.py`, `mcp_lessons.py`) deve leggere i due registri.
- **U2.** Oggi la configurazione parte solo se l'utente dice "leggi `Claude/SETUP-INSTRUCTIONS.md` e configura": copia dello scaffold, nome del progetto, registrazione del server MCP, cartella `Content`. `project-bootstrap` distingue progetto vuoto/non vuoto solo dopo. Manca il rilevamento automatico a inizio sessione (progetto senza `Claude/docs/SPEC.md` e senza componenti) con proposta "installo?". Da definire cosa include "componenti" (ipotesi: scaffold + hook, registrazione MCP, controllo Python abilitato in UEFN, "Load on Startup = Most Recent Project", skill utente).
- **U3.** Non esiste una domanda "mappa o prodotto Fab". Va nel bootstrap, prima di ogni altra scelta, e il tipo si registra in `Claude/docs/` (per esempio `Claude/docs/.project-type`).
- **U4.** Dalla documentazione di Fab (pagine "Publishing assets" e "Upload UEFN source to Fab"): campi del listing = titolo (ideale 30 caratteri o meno), descrizione (nessun limite, dichiarare software e risorse di terzi), categoria e sottocategorie, tag, prezzo, miniatura, galleria immagini/video, dettagli tecnici (LOD sì/no e numero), dichiarazione di contenuti per adulti. Un sorgente UEFN si carica come `.zip` con un solo progetto, senza `Saved` e `Intermediate`, nomi di file e cartelle solo alfanumerici inglesi e underscore, percorsi dei file di 140 caratteri al massimo, nessun nome generico ("Assets", "NewFolder"), testato in un progetto pulito.
- **ATTENZIONE (scoperta importante).** Un archivio "UEFN Source" **non può contenere script Python (`.py`)**. Il nostro scaffold mette in `Content/` la cartella `Claude/hooks/*.py`, `.claude/` e `CLAUDE.md`: un prodotto Fab fatto così verrebbe respinto. Conferma la decisione dell'utente (niente `project-template` nei progetti Fab). Resta utile un controllo leggero prima dell'archivio: nessun `.py`, `Claude/`, `.claude/`, `CLAUDE.md` nel progetto, nomi alfanumerici/underscore, percorsi di 140 caratteri al massimo, niente `Saved`/`Intermediate`.
- **U5.** Per le immagini abbiamo ricette provate: `CaptureViewport`, `CaptureEditorImage`, `SetCameraTransform`, `FocusOnActors`. La documentazione di Fab non dà dimensioni né numero di immagini della galleria (solo: più screenshot, panoramica a griglia per i pacchetti, la miniatura rappresenta il prodotto); per le dimensioni da usare vedere le regole del portale al momento della pubblicazione. Per le mappe (Discovery) le dimensioni vanno verificate nella documentazione Epic prima di fissarle.

## Esempi pilota (letti il 23 ottobre, solo lettura)

**root_FAB_rainbow** (C:\UEFN_Progetti): pacchetto di materiali UI. 48 asset propri in `Content/Custom_mat` (Glint 3, Material 8, MaterialInstance 32, Texture 4, Widget 1: `WB_Rainbow_example`), nessun Verse. Controlli Fab: nessun `.py`, nessun nome fuori regola, percorso più lungo 106 caratteri, cartella `Developers/mimmo` vuota. Da sistemare: texture con nomi vaghi (`new`, `MainTexture`, `raysnowe2`).

**root_rank_system** (pilota in corso): sistema di rank competitivo, drop-in. Verse proprio: 4 file (`Rank_System_Device`, `Rank_Types`, `Rank_Table`, `Rank_Leaderboard`), 24 livelli da Bronze I a Unreal III, HUD, filmato di avanzamento, classifica top 5, soglie configurabili con `@editable`. 110 asset propri in `Content/Rank_System`.
- **Le intestazioni Verse del pilota sono già nel formato nuovo**: nome del file, `Summary:` (descrizione, con le istruzioni di configurazione) e `Last modified: data - vN`, senza righe di storico. Diventano il modello di R2.1.
- **9 file superano i 140 caratteri di percorso** (massimo 146), tutti in `Content/VerseUIKit/Widgets/Buttons/ToggleButton/Art/MaterialInstances/`. Vanno rinominati prima dell'archivio.
- **`VerseUIKit` pesa 732 asset su circa 860 (85%)**: è la libreria di interfaccia, non codice scritto da noi. Fab chiede solo contenuti creati o validati da chi vende e di dichiarare le risorse di terzi: da verificare la licenza della libreria prima di includerla (non la conosco).
- Nessuno dei due progetti ha `Claude/`, `.claude/` o `CLAUDE.md` e nessuno contiene file `.md`: conferma la scelta "niente project-template nei prodotti Fab" e dice che i documenti vanno creati da zero. Entrambi hanno una cartella `.lore` (dati del controllo di versione di UEFN) alla radice: da verificare se l'archivio Fab la accetta; fino ad allora si esclude.

Cosa ne ricavo per il modo Fab:
- La configurazione si può **generare dal codice**: le dichiarazioni `@editable` (nome, tipo, valore di default) e il `Summary` dell'intestazione danno le tabelle di `Documentation/` quasi gratis. Per i materiali, i parametri si leggono con le ricette già provate di `MaterialInstanceTools`.
- Per gli screenshot dei materiali: miniature degli asset (`CaptureAssetImage`, ricetta già provata) composte in una **griglia panoramica su sfondo unito**, come suggerisce Fab per i pacchetti. Per l'interfaccia (HUD, classifica, filmato) servono catture in gioco: da verificare come ottenerle in modo ripetibile.
- Un **controllo del pacchetto** (nomi, lunghezza dei percorsi, `.py`, cartelle vietate) avrebbe già trovato i 9 file lunghi.

## Baseline di rilascio proposte

### R1 - 1.107.6 "Chiamate più sicure" (committata; pubblicazione insieme alla 1.108.0)

| # | Voce | Stato |
|---|---|---|
| R1.1 | Regola: mai ripetere una modifica dopo un timeout (`outcome_unknown`), prima si legge lo stato | fatto |
| R1.2 | Guardia: rifiutare `save_assets` senza elenco di asset | fatto (guardia + test) |
| R1.3 | Crash noti + alternative sicure (tag `Triangles`, `static_materials`, bounding box, Nanite) nella nota di `get_lod_count`; test che fallisce se una skill/agente/ricetta nomina un tool `avoid` | fatto (note, alternative sicure, test `test_avoid_tools`) |
| R1.4 | Manuale e doctor: "Load on Startup = Most Recent Project"; confronto stati di `recover` | fatto: il manuale c'era già; aggiunto il controllo nel doctor; gli stati di `recover` sono già coperti (crash_dialog, hub, opening, open_failed, other_project_open) |
| R1.5 | Trappola CPU ridotta in background (Code prova col timeout di SelectAssets) | fatto: lab-19 chiuso, la guardia funziona; SelectAssets risponde in 1,4-1,7 s anche con UEFN dietro, quindi il background non è la causa; testi corretti; la ricetta resta `unverified` |
| R1.6 | Trappole: Rotator per nome, richieste che bloccano UEFN 42.40 | fatto |
| R1.7 | Limiti MVVM nelle ricette di `uefn-ui-widgets` | fatto nella skill (come limiti riportati da altri); da confermare con un vero legame quando capita |
| R1.8 | Nota in `uefn-verse-build`: nessuna compilazione su cartella di prova | fatto |
| R1.9 | Etichetta su ogni oggetto creato dagli agenti (`kit:<id>`) | fatto nella skill `uefn-level-devices` |
| R1.10 | Cartella `docs/adr`, scansione segreti (gitleaks), CODEOWNERS | fatto (`docs/adr` con 3 pagine, workflow `security.yml` con gitleaks; CODEOWNERS c'era già) |
| R1.11 | Pulizia: `project-template/Claude/KIT-VERSION.tmp` è un file tracciato in git per errore (8 byte); toglierlo con `git rm` dall'utente | fatto (`git rm --cached` + `.gitignore`) |

### R2 - 1.108.0 "Pronto per il jam" (COMPLETA e committata il 23 ottobre; in più: timer Epic AI MegaJam e tile Changes nella pagina What's new, tutto in inglese; da pubblicare entro il 9 novembre)

| # | Voce | Stato |
|---|---|---|
| R2.1 | U1: intestazione Verse = descrizione in inglese sempre aggiornata + data vera + versione (senza righe di storico); nuovo `Claude/logs/verse-changes.jsonl` (file, ora, riassunto, motivo, esito) + `verse-errors.jsonl` letti dall'apprendimento; migrazione delle intestazioni esistenti (`history_trim` adattato: toglie le righe di storico, le archivia); coder, compliance-reviewer (controllo 3: descrizione aggiornata, data e versione, nessuno storico), test, manuale | fatto (1.108.0): helper, migrazione, regole, test, manuale, e `verse_changes.py recurring` letto dal coder per proporre lezioni |
| R2.2 | U2: rilevamento della mappa nuova a inizio sessione (nessun `Claude/docs/SPEC.md` e nessun `project-template` installato) e proposta di installarlo da solo: copia di `project-template` in `Content/`, un solo passo, ripetibile, con `--dry-run`, riusando `kit_sync`; poi i passi di `SETUP-INSTRUCTIONS` (nome progetto, registrazione MCP, controlli) senza che l'utente debba dirlo | fatto (1.108.0) |
| R2.3 | U3: domanda "mappa o prodotto Fab?" subito, PRIMA di installare qualsiasi cosa: se Fab, non si installa `project-template`; il tipo si registra fuori dal progetto Fab o in un solo file `.md` (da decidere in R3) | fatto (1.108.0) |
| R2.4 | Controllo prima della consegna del jam (codice di versione privata, video 30-60 secondi, risorse di terzi con licenza, regole Fortnite) | fatto (1.108.0) |
| R2.5 | `/devlog`: dev log automatico per il premio Glass Box | fatto (1.108.0) |
| R2.6 | Scheda concept con punteggio di fattibilità (skill + script) | fatto (1.108.0) |
| R2.7 | Manuale e README: sezione "Kit per il jam" | fatto (1.108.0) |

### R3 - 1.109.0 "Prodotti Fab e screenshot"

| # | Voce | Stato |
|---|---|---|
| R3.1 | U4: modo Fab - set specifico di `.md`: `Documentation/` (istruzioni di configurazione e uso: diventano il manuale utente del prodotto, per il cliente che aggiunge i componenti al suo progetto) e `FabListing/` (titolo, descrizione, tag, dettagli tecnici, dichiarazione risorse di terzi, elenco di cosa contiene il prodotto) | da fare |
| R3.2 | Controllo leggero del pacchetto Fab: nessun `.py`, `Claude/`, `.claude/`, `CLAUDE.md`, `.lore`; nomi alfanumerici/underscore; percorsi di 140 caratteri al massimo (calcolati col nome della cartella del progetto); niente `Saved`/`Intermediate`; nessun nome generico. Prototipo già provato a mano su entrambi i pilota (trova i 9 percorsi lunghi di root_rank_system) | da fare |
| R3.2b | Aiuto per accorciare i percorsi troppo lunghi (proposta di nuovi nomi, rinomina con `AssetTools/move`, poi riferimenti a posto) - solo con tuo ok | da fare |
| R3.2c | Verifica della licenza di `VerseUIKit` e dichiarazione delle risorse di terzi nel listing | da fare |
| R3.1b | Generare `Documentation/` dal codice: tabella delle impostazioni `@editable` con valori di default, `Summary` delle intestazioni, parametri dei materiali con le ricette provate | da fare |
| R3.3b | Griglia panoramica dei materiali/asset su sfondo unito, dalle miniature | da fare |
| R3.3 | U5: screenshot automatici per la pubblicazione (miniatura, galleria, panoramica a griglia) con le ricette di cattura già provate; dimensioni dopo verifica | da fare |
| R3.4 | Simulatore di economia (tycoon/arena) | da fare |
| R3.5 | Segnali strutturati nei log della mappa letti da `qa-regression` | da fare |
| R3.6 | Documenti di consegna per ogni mappa (planner-docs) | da fare |
| R3.7 | Vista portafoglio delle isole nella console | da fare |

### R4 - 1.110.0 e dopo (qualità e aggiornamenti)

Registro delle modifiche all'editor con "annulla sessione"; riprova delle ricette a ogni nuova versione di UEFN; importazione dei dati del Creator Portal (verificare il formato); blocco vero sull'editor; sorveglianza settimanale con attività pianificata; screenshot automatici del README e prova della console con dati veri; controllo statico del Verse; compiti di riferimento per collaudare skill e agenti; skill per NPC conversazionali (categoria Walkie-Talkie); localizzazione (verificare cosa supporta UEFN); apprendimento automatico (Fase B); via Python nell'editor e language server Verse (solo dopo misure).

## Decisioni dell'utente (23 ottobre) - chiudono le domande aperte

1. **Componenti = `project-template`**, che finora è stato sempre copiato a mano nel progetto. La mappa nuova deve proporre di installarlo da sola (e poi tenerlo aggiornato con la sincronizzazione già esistente, `kit_sync`).
2. **L'intestazione dei file Verse conserva sempre data e versione** (la data vera, la versione aumentata a ogni modifica sostanziale), più la descrizione in inglese sempre aggiornata. Si elimina solo lo storico delle modifiche: quello va nei log (`verse-changes.jsonl`, `verse-errors.jsonl`).
3. **Prodotto Fab = un piccolo progetto UEFN** i cui componenti il cliente aggiunge al proprio progetto. Quindi **non si può mettere `project-template` dentro il progetto Fab**. In modo Fab il kit non installa nulla nel progetto e crea solo un insieme specifico di file Markdown con le informazioni per la pubblicazione, che diventano anche il manuale utente / istruzioni del prodotto.

Ipotesi di lavoro per il punto 3 (da confermare quando arriviamo a R3): due gruppi di documenti. `Documentation/` = istruzioni di configurazione e uso che viaggiano con il prodotto; `FabListing/` = testi per il portale (titolo, descrizione, tag, dettagli tecnici, dichiarazione risorse di terzi), che restano fuori dall'archivio. Sono solo `.md`, con nomi solo alfanumerici e underscore.

## Pagina "Score" della console (decisa il 23 ottobre, da costruire)

Una pagina nuova della console, non legata al jam: misura l'evoluzione del progetto contro il piano, release per release. Prototipo scelto: **proposta 1 "grafico in alto"** (`docs/prototypes/score-console-1.html`, dati inventati).

Decisioni dell'utente:
- **Criteri**: niente divisione Epic/nostri. **Primary** (70 punti: i sette criteri di qualità: ambizione e innovazione, aderenza al brief/tema, fun, gameplay, visuals, level design, audio) e **Additional** (30 punti: fattibilità in UEFN, ambito rispetto al piano, retention, prontezza alla pubblicazione, documentazione/release notes). In più una traccia **bonus** fuori dai 100 (per esempio personaggi LLM).
- **Tempo = release**, non giorni: confronto con la release precedente e con il piano delle prossime. Grafico con piano, costruito, provato e previsione "a questo ritmo".
- **Un solo progetto**: niente cambio di progetto o profilo, i dati restano nel progetto. Il profilo (mappa, jam, Fab) è fisso e cambia solo le etichette.
- **Semaforo per criterio** (rosso agisci ora / giallo tieni d'occhio / verde a posto, con forme diverse per i daltonici) e numero di priorità: le soglie si stringono con l'avanzare delle release.

Da definire prima di costruire: (1) da dove vengono i traguardi del piano per release (proposta: il kit li propone dal ROADMAP/spec, l'utente conferma); (2) come si calcolano "costruito" (file e asset del progetto) e "provato" (verse-check, playtest, controlli); (3) dove si salva lo storico (proposta: `Claude/logs/score-history.jsonl`, una riga per release); (4) il punteggio dei criteri soggettivi (fun, visuals, audio) viene dato dagli agenti con motivazione e confermato dall'utente.


## Come ripartire dopo la chiusura della sessione

Aprire la pagina di progetto `claude/PLAN-next-releases.md`, rileggere le "Decisioni dell'utente", poi R1 (piccola) o R2 (jam). Prima di modificare file: `git status` pulito, test 50/50. Prossimo passo: R3 (modo Fab). Da confermare con l'utente: l'ipotesi `Documentation/` + `FabListing/`, le regole del jam (controllare l'elenco di `/jam-check` sul regolamento ufficiale), le date del timer.
