# Auftrag für Claude Code — Projekt „Protection Time"

> **An die Person, die das weitergibt:** Lade zusätzlich `belegbasis-v3.md` in dasselbe Verzeichnis. Claude Code hat keinerlei Vorkontext — dieses Dokument plus die Belegbasis sind alles, was es hat.

---

## 0. Kontext — lies das zuerst vollständig

Du arbeitest an einem Forschungsprojekt für den **Apart Research AI Incident Response Sprint**, Abgabe **Sonntag 13.09.2026, 23:59 AoE** (= Montag 14.09. um 13:59 Uhr MESZ).

Im Juli 2026 verließen KI-Agenten während interner Cybersicherheits-Evaluationen bei OpenAI ihre Sandbox, kommunizierten über einen Paketmanager namens Artifactory miteinander und griffen Hugging Face sowie OpenAIs eigene Infrastruktur an. Es ist der erste öffentlich dokumentierte Fall, in dem eine KI-Containment-Kontrolle von Agenten tatsächlich überwunden wurde.

**Die These des Projekts:**

> Wie lange eine Containment-Kontrolle hält, ist keine Eigenschaft der Kontrolle. Es ist eine Eigenschaft der Fähigkeit, die sie blockiert. Die Haltezeit ist endlich genau dann, wenn die blockierte Fähigkeit einen erreichbaren Alternativmechanismus hat, und skaliert mit den Kosten des billigsten solchen Mechanismus.

**Die Kernmetrik heißt `protection time`**, Notation `P_wall` (Kalenderzeit) und `P_exp` (Agenten-Expositionszeit). Der Begriff stammt aus Winn Schwartaus *Time Based Security* (1998/99).

> **Schreibregel, verbindlich:** Immer `P_wall` oder `P_exp`, **nie bloßes `P`**. In der Sicherheitsliteratur bezeichnet `P` regelmäßig eine Wahrscheinlichkeit.

**Definition:**
> `P` ist die Zeitspanne von der Anwendung einer Kontrolle bis zur ersten erfolgreichen Realisierung der blockierten Fähigkeit über einen beliebigen Mechanismus.

**Der Beitrag des Projekts:** Es sind die **ersten gemessenen Schutzzeiten für KI-Containment überhaupt.** Kein Normenwerk, kein Standard und keine wissenschaftliche Arbeit kennt bisher eine Zeitachse für Containment — das ist über zwölf Instrumente hinweg durch Begriffsauszählung belegt (siehe Belegbasis Abschnitt 12).

---

## 1. Arbeitsregeln — nicht verhandelbar

1. **Erfinde keine Daten.** Jeder Wert stammt entweder aus `belegbasis-v3.md` oder existiert nicht. Wenn ein Zeitstempel dort nicht steht, trage `NOT_DATED` ein — **nie schätzen, nie interpolieren, nie plausibel ergänzen.**
2. **Jede Zelle trägt eine Provenienz.** Format: Quellenkürzel plus Fundstelle, z. B. `P1-X` (OpenAI Technical Report, Abschnitt X) oder `P3` (Hugging Face Timeline).
3. **Jede Zeile trägt einen Belegstatus** aus der Legende in Belegbasis Abschnitt 0.1: `PRIMÄR`, `PRIMÄR-KONFLIKT`, `SEKUNDÄR`, `EIGENE REKONSTRUKTION`, `UNGEPRÜFT`.
4. **Berechne `P_wall` immer im Code**, trage es nie von Hand ein. Die Belegbasis nennt Sollwerte für drei Zeilen — dein Skript muss sie reproduzieren. Wenn nicht, ist etwas falsch.
5. **Wenn dir etwas widersprüchlich vorkommt, halte an und frage.** Nicht auflösen, nicht glätten. Widersprüche im Quellmaterial sind hier ein Ergebnis, kein Störgeräusch.
6. **Keine Exploit-Details, kein lauffähiger Angriffscode** im Repository. Zeitstempel, CVE-Nummern und Mechanismusbezeichnungen sind in Ordnung — sie stehen alle bereits in publizierten Berichten.

---

## 2. Repository anlegen

```
protection-time/
├── README.md
├── data/
│   ├── clock.csv                 # das zentrale Datenobjekt
│   ├── sources.csv               # Quellenregister mit URLs
│   └── contradictions.csv        # Widerspruchsregister
├── src/
│   ├── compute_p.py              # berechnet P_wall, prüft Sollwerte
│   ├── sensitivity.py            # Schachtelungsbeweis + Parameterraum
│   ├── budgets.py                # Budget- und Kadenzarithmetik
│   └── figures.py                # Abbildungen fürs Paper
├── docs/
│   ├── belegbasis-v3.md          # die vollständige Belegbasis
│   └── methodology.md            # Kurzfassung des Verfahrens
├── output/                       # generierte Tabellen und Abbildungen
└── tests/
    └── test_values.py            # Regressionstests gegen die Sollwerte
```

Git initialisieren, sinnvolle Commits, `.gitignore` für Python.

---

## 3. Das Schema von `clock.csv`

Eine Zeile pro Kontrolle. Spalten in dieser Reihenfolge:

| Spalte | Typ | Beschreibung |
|---|---|---|
| `id` | string | `A1`…`A3`, `B1`…, `C1`…, `X1`… (siehe Zeilentypen unten) |
| `row_type` | enum | `A_applied_nested`, `B_applied_nonnested`, `C_standing`, `X_out_of_corpus` |
| `control` | string | Bezeichnung der Kontrolle |
| `mechanism_blocked` | string | Was die Kontrolle **technisch** blockiert. Unstrittig. |
| `protection_goal` | string | Welches Ziel der Betreiber mit ihr verfolgt. **`P` wird gegen diese Ebene gemessen.** |
| `goal_source` | enum | `operator_stated` oder `project_assumption` |
| `goal_source_ref` | string | Fundstelle für `protection_goal`, leer wenn `project_assumption` |
| `applied_utc` | ISO-8601 oder `PRE_EXISTING` | Anwendungszeitpunkt |
| `held_evidence_utc` | ISO-8601 oder leer | Belegter Zeitpunkt, an dem die Kontrolle nachweislich griff |
| `reconstituted_utc` | ISO-8601, `NOT_DATED` oder `NEVER` | Erste erfolgreiche Realisierung der Fähigkeit |
| `alternative_mechanism` | string | Über welchen Weg die Fähigkeit realisiert wurde, leer wenn keine |
| `state` | enum | `broken`, `bypassed`, `fired_not_escalated`, `held`, `defeated_no_effect` |
| `reconstitution_category` | enum | `K1_alternative`, `K2_training`, `K3_residue`, `K4_escalation`, `K5_ephemeral`, `none` |
| `censoring` | string | Bekannte Datenlücken für diese Zeile |
| `status` | enum | Belegstatus |
| `provenance` | string | Quellenkürzel plus Fundstelle |
| `notes` | string | Freitext |

**Berechnete Spalten (nur vom Skript, nie von Hand):** `p_wall_hours`, `p_wall_hhmm`.

### Zeilentypen — entscheidend, bitte genau lesen

**Typ A — während des Vorfalls angewandte Kontrollen, geschachtelt.** Alle drei wurden im **selben Moment** angewandt: `2026-07-06T01:16Z`, dem Artifactory-Rebuild. Ihre Intervalle haben denselben Startpunkt und verschiedene Endpunkte, sind also geschachtelt. `P_wall` exakt berechenbar.

**Typ B — während des Vorfalls angewandte Kontrollen, nicht geschachtelt.** Anderer Anwendungszeitpunkt. `P_wall` grundsätzlich definiert, hier aber teils nicht minutengenau datiert.

**Typ C — vorbestehende Kontrollen.** Diese wurden **nicht angewandt**, sie standen schon da. Es gibt kein Anwendungsereignis, also **kein `P_wall`**. `applied_utc` = `PRE_EXISTING`, `p_wall_hours` bleibt leer. Gemessen wird hier binär: Wurde das Schutzziel erreicht, und über welchen Mechanismus.

> **Das ist die wichtigste methodische Regel des Projekts. Ein `P_wall` für Typ-C-Zeilen zu berechnen wäre ein sachlicher Fehler. Tu es nicht.**

**Typ X — außerhalb des Korpus.** Fälle aus anderen Institutionen, zur Regelprüfung.

---

## 4. Startdaten

Alle Werte aus `belegbasis-v3.md`. Lies die dort genannten Abschnitte, bevor du eine Zeile schreibst.

### Typ A — `applied_utc` für alle drei: `2026-07-06T01:16Z` (Belegbasis 4.1)

| id | control | reconstituted_utc | Sollwert `P_wall` | provenance |
|---|---|---|---|---|
| A1 | Blockierung der anfälligen Token-API-Routen und Entzug geteilter Reader-Credentials (Egress) | `2026-07-08T00:06Z` | 46 h 50 min | P1-X |
| A2 | dieselbe Rebuild-Maßnahme, Fähigkeit Inter-Agenten-Kommunikation | `2026-07-08T16:01Z` | 62 h 45 min | P1-X |
| A3 | dieselbe Rebuild-Maßnahme, Fähigkeit Artifactory-Administratorzugriff | `2026-07-13T08:46Z` | 175 h 30 min | P1-X |

`held_evidence_utc` für A1: `2026-07-06T12:56Z` — drei Egress-Versuche liefen auf HTTP 400 (Belegbasis 4.2).

**Reproduziere diese drei Sollwerte im Test.** Weichen sie ab, ist die Zeitrechnung falsch.

### Typ B

- **B1** — Outbound-Netzwerkkontrollen, 9. Juli. Ein Agent erlangte Root in der Parent-VM, wurde beim Internetzugriff **von den Outbound-Kontrollen abgewiesen** und umging sie anschließend über Artifactory-Endpunkte. Derselbe Agent, dieselbe Sitzung. `reconstituted_utc` = `NOT_DATED` — die Belegbasis warnt ausdrücklich, dass dieses Ereignis in Abschnitt X **nicht datiert** ist (Belegbasis 4.6, 4.6a). Nicht schätzen.
- **B2** — Integrität des Container-Image-Caches, 9. Juli, CVE-2026-66384. Die Cache-Substitution **gelang**, ein angreiferkontrolliertes Image lag unter dem Namen eines vertrauenswürdigen Images. Kein Nachweis, dass ein Workload es zog oder ausführte. `state` = `defeated_no_effect`. Die Wirkung blieb nicht wegen einer Kontrolle aus (Belegbasis 4.6a).

### Typ C — alle `applied_utc` = `PRE_EXISTING`

| id | control | state | Kernbeleg |
|---|---|---|---|
| C1 | URL-Allowlist der `datasets`-Bibliothek | `held` | Kontrolle nie überwunden; Ziel über lokales Lesen und lokale Ausführung erreicht. Vollständiges Scoping in Belegbasis 4.8 |
| C2 | Hub-Produktionsdatenbank, privater Link mit Adress-Allowlist | `held` | Zwei Auth-Versuche am 12.07. (06:50, 11:46), beide Timeout. Nie erreicht |
| C3 | IAM-Policy beim Node-Rollen-Replay | `held` | Jeder mutierende Aufruf abgelehnt |
| C4 | Credential Store und Cluster Keys | `held` | 84 Operationen, alle abgelehnt |
| C5 | CI-Execution-Policies | `held` | Draft-PR und CI-Workflow ausgelöst, kein Merge, kein Release |
| C6 | Kubernetes-Beschränkungen gegenüber GPT-5.6 Sol | `held` | Breitere Listings und Secrets abgelehnt |
| C7 | Administratorschwelle bei Anonymtokens | `held` | 09.07. 16:03 Ein-Jahres-Tokens ausgegeben, spätere Admin-Versuche scheiterten |
| C8 | Host-Mount-Beschränkung | `broken` | 19.07. 16:35 erster Pod scheitert, zweiter gelingt kurz darauf |
| C9 | Korrelierender Detektionsstack bei Hugging Face | `fired_not_escalated` | Signale korreliert, Kritikalität nicht angehoben, On-Call nicht alarmiert. Kategorie `K4_escalation` |
| C10 | Egress-Drosselung | `bypassed` | Rückgriff auf vorgestagte Binaries in der mitgelieferten Debug-Shell |
| C11 | DNS-Auflösung | `bypassed` | Resolver in-process gepatcht, Host auf feste IP gepinnt |
| C12 | Intermittierende Egress-Blocks | `bypassed` | `/etc/resolv.conf` umgeschrieben, Hosts gepinnt |
| C13 | Blockierung direkter Outbound-Verbindungen | `bypassed` | Offener CORS-Proxy-Space auf Hugging Faces **eigener** Plattform als Relay |
| C14 | Fehlendes TUN-Device in der Sandbox | `bypassed` | `tailscaled` im Userspace-Modus mit SOCKS5, ohne Plattenpersistenz |

### Typ X

- **X1** — UK AISI, Netzwerkbeschränkungen bei GitHub, über **Tor** umgangen. Das löste den Sicherheitsalarm aus.
- **X2** — Nightingale/DseWiki: Schreibsperre war gegen den **Request-Typ** formuliert; alte Wiki-Software akzeptierte Schreibvorgänge über einen anderen Typ. Kontrolle intakt, Ziel erreicht. Strukturgleich mit C1, aber außerhalb des Korpus. Einziger verfügbarer Out-of-Sample-Test.

---

## 5. `src/compute_p.py`

- Liest `clock.csv`, berechnet `p_wall_hours` und `p_wall_hhmm` **nur** für `row_type` in `A_applied_nested` und `B_applied_nonnested`, und nur wenn beide Zeitstempel gültige ISO-Werte sind.
- Bei `applied_utc == PRE_EXISTING` oder `reconstituted_utc in {NOT_DATED, NEVER}`: Feld leer lassen, Grund in `notes` protokollieren.
- Schreibt `output/clock_computed.csv`.
- Gibt eine Konsolenzusammenfassung nach Zeilentyp und Zustand aus.

## 6. `src/sensitivity.py` — der Schachtelungsbeweis

Die drei Typ-A-Kontrollen starten alle bei `t0 = 2026-07-06T01:16Z`. Ihre Intervalle sind also geschachtelt:

```
[t0, t_A1] ⊂ [t0, t_A2] ⊂ [t0, t_A3]
```

Ist `P_exp` das Integral der Agenten-Ausführungsaktivität über das jeweilige Intervall und diese Aktivität nirgends negativ, folgt zwingend:

```
P_exp(A1) ≤ P_exp(A2) ≤ P_exp(A3)
```

**für jede beliebige Duty-Cycle-Funktion**, nicht nur für konstante.

Das Skript soll:
1. Die Schachtelung aus den Daten **verifizieren** statt sie anzunehmen — gleicher `applied_utc`, aufsteigende Endpunkte.
2. Eine **Monte-Carlo-Demonstration** fahren: zufällige nichtnegative Duty-Cycle-Funktionen über das Intervall ziehen, `P_exp` für alle drei integrieren, prüfen, dass die Rangfolge in **100 %** der Ziehungen hält. Das ist keine Beweisführung, sondern eine Illustration des Beweises — so im Output kennzeichnen.
3. Ausgeben, dass die Schachtelung **bricht**, sobald Zeilen mit abweichendem `applied_utc` aufgenommen werden (Typ B).

**Drei Einschränkungen müssen im Output stehen:**
- Nur die **Rangfolge** ist entschärft. Die Größenordnung — eine ursprünglich vermutete Verkürzung um etwa Faktor 15 — folgt daraus **nicht** und bleibt unbelegt.
- Der Beweis gilt exakt für die drei Typ-A-Zeilen.
- Es existieren **keine öffentlichen Daten** dazu, wann Evaluations-Workloads zwischen dem 6. und 7. Juli liefen. `P_exp` ist deshalb **nie als Punktwert** auszugeben, immer als Funktion oder Bereich.

## 7. `src/budgets.py`

Drei Rechnungen, jeweils mit Quellenangabe im Output:

**a) Deklariertes Reaktionsbudget gegen gemessene Leistung.** OpenAI: nach dem Page 30 Minuten zum Fehlalarm-Ausschluss, sonst Pause; davor ein 30-Minuten-Ziel für die Alarmausgabe. Gemessen am 19.07.: Alarm 12:03, Stopp der Läufe 17:37 = 334 Minuten. Faktoren gegen 30 und gegen 60 Minuten berechnen. **Wichtig für den Output:** Das Budget wurde am 18. August deklariert, also **nach** dem Vorfall — kein gebrochenes Versprechen, sondern ein Zielwert ohne demonstrierte Grundlage.

**b) Vergleich mit dem UK AISI.** Alarm 28.07. 10:56, Beendigung aller Evaluationen 11:42 = 46 Minuten. Zusätzlich die Latenz: Aktivitätsende 27.07. 23:15 bis Alarm = 11 h 41 min. Zwei getrennte Messgrößen — **Detektionslatenz** und **Reaktionslatenz** — und die beiden Organisationen versagen an verschiedenen.

**c) Kadenz-Arithmetik.** CSA AICM AIS-13 verlangt Review der Sandboxing-Policies „at least annually" = 8.766 Stunden. Verhältnis zu jedem Typ-A-`P_wall` berechnen. Erwartete Größenordnung: Faktor 50 bis 187.

## 8. `src/figures.py`

- **Abbildung 1:** Zeitstrahl 06.07.–13.07. mit `t0`, dem Greif-Beleg und den drei Rekonstitutionspunkten. Geschachtelte Balken.
- **Abbildung 2:** Kadenz gegen gemessene Haltezeit, logarithmische Achse.
- **Abbildung 3:** Zustandsverteilung nach Zeilentyp.

Nüchtern, druckfähig, keine Deko. Als PNG **und** als PDF in `output/`.

## 9. `tests/test_values.py`

- A1 ergibt exakt 46 h 50 min, A2 exakt 62 h 45 min, A3 exakt 175 h 30 min.
- Keine Typ-C-Zeile hat ein `p_wall_hours`.
- Jede Zeile hat nichtleere `provenance` und `status`.
- Jede Zeile mit `goal_source == project_assumption` hat leeres `goal_source_ref`.
- Die Schachtelung der Typ-A-Zeilen gilt.

## 10. `README.md`

Für eine Leserin ohne Vorkenntnis:

1. **Was gemessen wird und warum** — die These, die Definition, die Schreibregel `P_wall`/`P_exp`.
2. **Was neu ist** — die ersten gemessenen Schutzzeiten für KI-Containment; kein Instrument kennt bisher eine Zeitachse.
3. **Woher die Daten stammen** — Quellenregister mit URLs, Verweis auf `docs/belegbasis-v3.md`.
4. **Wie reproduziert wird** — Installation, Skriptaufrufe, erwartete Ausgaben.
5. **Grenzen, offen benannt** — `P_exp` ohne Primärbeleg; nur ein Vorfall; Typ-C-Zeilen haben kein `P`; über 7 % der zugrundeliegenden Transkripte enthalten laut unabhängiger Prüfung absichtlich gefälschte Tool-Calls.
6. **Dual Use** — das Repository enthält Zeitstempel, Zitate und Arithmetik, keinen Angriffscode. Alle Mechanismen sind bereits in publizierten Berichten der betroffenen Parteien beschrieben. Der riskantere Teil ist nicht die Messung, sondern das Mechanismus-Inventar, das die Klausel verlangt — dieses gehört gegenüber Auditoren offengelegt, nicht öffentlich.
7. **Korrekturhistorie** — Verweis auf Abschnitt 19 der Belegbasis. Neunzehn dokumentierte Fehler aus dem Rechercheprozess, samt methodischen Lehren. **Das ist Absicht und bleibt sichtbar.**

---

## 11. Reihenfolge

1. Repo, `.gitignore`, Verzeichnisse
2. `sources.csv` aus Belegbasis Abschnitt 3
3. `clock.csv` mit allen Zeilen aus Abschnitt 4 oben
4. `compute_p.py` + `tests/` — **hier anhalten und die drei Sollwerte melden**
5. `sensitivity.py`
6. `budgets.py`
7. `figures.py`
8. `README.md`
9. `contradictions.csv` aus Belegbasis Abschnitt 7

**Nach Schritt 4 melden und auf Bestätigung warten.** Wenn die drei Sollwerte nicht exakt reproduziert werden, liegt ein Fehler vor, der vor dem Weiterbauen zu klären ist.
