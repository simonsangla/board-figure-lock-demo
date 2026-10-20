# Board Figure Lock (demo)

**English** | [Français](#français)

## The concept
A board deck already holds figures that people trust ("Q1 revenue: 53,546.30"). When an AI assistant or a BI tool answers a question about the same metric, its answer is **released only if it reproduces those published figures**. Otherwise it is held or blocked, and a person decides.

Four parts, all plain files:

1. **Board figures** (`board-figure-lock/data/board_figures.csv`): what was published, with an owner per figure.
2. **One metric definition** (`board-figure-lock/data/metrics.json`): `revenue = sum(actual_revenue)`. A question about a metric that is not defined is refused, never guessed.
3. **The gate** (`bin/bfl`): recomputes every board figure through the defined metric, then judges each AI answer:
   - `RELEASED`: matches the board (gap < 0.01);
   - `REFUSED`: the engine correctly declined a metric that is not defined;
   - `HOLD`: nothing to lock against, or the board figure itself is disputed (its owner decides);
   - `BLOCKED`: wrong number, SQL error, or an answer to an undefined metric;
   - `MISSED`: the engine declined a metric that is defined.
4. **The Tableau file check** (`bin/twb-read`): reads a `.twb`/`.twbx` file alone and says whether its calculation equals the defined metric (`MATCH`, `MISMATCH`, `AMBIGUOUS`, `MISSING`).

The technology does not matter: it is CSV, JSON and two `sum ... group by` queries. Python's built-in `sqlite3` runs it here; DuckDB is used if installed; any SQL warehouse can run the same queries.

## Run it
Python 3 only (tested with 3.13). No install, no network, no account, no secret.

```sh
git clone https://github.com/simonsangla/board-figure-lock-demo.git
cd board-figure-lock-demo
./demo            # or: make demo     (force the stdlib engine: ./demo --db sqlite)
```

You will see:
- **Reconcile**: 3 figures OK, 1 `GAP` (BF03 is 3.90 off on purpose: the gate must catch it), 1 `REFUSED` (units: no defined metric).
- **Gate and score** for 3 engines: recorded answers of a local LLM (`qwen2.5-coder:7b`, 35 answers, 25 correct, 0 wrong released), a deterministic semantic layer (7 answers, 5 correct), and a deliberately wrong control (4 answers, 3 blocked).
- **Tableau check**: the workbook's `Revenue` calculation `MATCH`es the defined metric.

Tests: `make test`.

## Files
| Path | What |
|---|---|
| `demo` | the one command |
| `bin/bfl` | reconcile, answer, score (the gate) |
| `bin/twb-read` | Tableau workbook reader and metric check |
| `board-figure-lock/` | data, questions, recorded answers, Tableau workbook and map |
| `tests/` | unit tests (stdlib `unittest`) |
| `Makefile` | `make demo`, `make test` |
| `LICENSE`, `NOTICE.md` | MIT licence, data origin |

Data: synthetic, from the public MIT demo `simonsangla/dbt-revenue-variance-demo` (see `NOTICE.md`). License: MIT.

---

## Français

### Le concept
Un comité de direction a déjà des chiffres publiés auxquels il fait confiance (« CA T1 : 53 546,30 »). Quand une IA ou un outil BI répond à une question sur le même indicateur, sa réponse **n'est libérée que si elle redonne exactement ces chiffres publiés**. Sinon elle est mise en attente ou bloquée, et une personne tranche.

Quatre pièces, toutes de simples fichiers :

1. **Les chiffres du comité** (`board_figures.csv`) : ce qui a été publié, avec un responsable par chiffre.
2. **Une seule définition d'indicateur** (`metrics.json`) : `revenue = sum(actual_revenue)`. Une question sur un indicateur non défini est refusée, jamais devinée.
3. **La porte** (`bin/bfl`) : recalcule chaque chiffre du comité avec l'indicateur défini, puis juge chaque réponse de l'IA :
   - `RELEASED` (libérée) : identique au comité (écart < 0,01) ;
   - `REFUSED` (refus correct) : l'IA a refusé un indicateur non défini ;
   - `HOLD` (en attente) : rien à comparer, ou le chiffre du comité est lui-même contesté (son responsable tranche) ;
   - `BLOCKED` (bloquée) : mauvais chiffre, erreur SQL, ou réponse à un indicateur non défini ;
   - `MISSED` (raté) : l'IA a refusé un indicateur pourtant défini.
4. **Le contrôle du fichier Tableau** (`bin/twb-read`) : lit un `.twb`/`.twbx` seul et dit si son calcul est égal à l'indicateur défini.

La technologie ne compte pas : ce sont des CSV, du JSON et deux requêtes `sum ... group by`. Ici, le `sqlite3` intégré à Python suffit ; DuckDB est utilisé s'il est installé ; n'importe quel entrepôt SQL peut lancer les mêmes requêtes.

### Le lancer
Python 3 seulement (testé avec 3.13). Rien à installer, pas de réseau, pas de compte, pas de secret.

```sh
git clone https://github.com/simonsangla/board-figure-lock-demo.git
cd board-figure-lock-demo
./demo            # ou : make demo     (tests : make test)
```

Vous verrez : la réconciliation (3 chiffres OK, 1 écart voulu sur BF03, 1 refus), la porte et le score de 3 moteurs (un LLM local enregistré, une couche sémantique, un contrôle volontairement faux), puis le contrôle Tableau (`MATCH`).

Données : synthétiques, issues de la démo publique MIT `simonsangla/dbt-revenue-variance-demo` (voir `NOTICE.md`). Licence : MIT.
