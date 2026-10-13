# Lektorat-Prompt für Buchprojekte nach dem write-book-template

Projektunabhängige Fassung des Rezensions- und Lektoratsprompts mit dem vollständigen Arbeitsablauf bis zum Release.
Entstanden 2026-10-01 bis 2026-10-07 an „Die Formbare Ewigkeit“ (DE, EN, ES, FR) mit den Werkzeugen manuscripta und
manuscript-tools. Platzhalter in geschweiften Klammern einmal im Projektblock ausfüllen; Abschnitte, die für das
Projekt nicht gelten, streichen.

Anwendung: Projektblock und den Block unter „Prompt“ an das Modell geben; für ein ganzes Buch zusätzlich den
Arbeitsablauf. Die Rückmeldung landet als Datei unter `config/lektorat-bericht-<datum>-<lang>.md`.

---

## Projektblock

```text
TITEL:              {Titel der Ausgabe, wie veröffentlicht}
SPRACHE / lang:     {Deutsch / de}
SERIE, BAND:        {Serienname in dieser Sprache, Band N}
AUTOR:              {Name}
GENRE, HALTUNG:     {z. B. philosophisches Sachbuch, essayistisch; Denkraum, keine Lehre; idealistische Perspektive}
ANREDE:             {du / Sie / you / tú / vous}
ÜBERSETZT AUS:      {Sprache des Originals, oder: Original}
REFERENZAUSGABEN:   {bereits bearbeitete Ausgaben mit Branch, z. B. DE develop-de, EN develop}
ARBEITSBRANCH:      {Branch des Autors, z. B. migrate-es-v5.1.0}; Ziel nach dem Merge: {develop-xx}
ZIELFORMATE:        {eBook, Taschenbuch, Hardcover, Hörbuch}
RUBRIKEN:           {## Was bleibt {#was-bleibt-kapitel-N}, ## Ausblick {#ausblick-kapitel-N}}
BEGRIFFE:           {ein Name je Konzept, z. B. Bewusstsein, Gehirn-Upload, digitaler Zwilling, Simulationshypothese, KI}
ENDGÜLTIGE H1:      {Liste aller Teil- und Kapiteltitel mit IDs, für Querverweise}
KAUFDATEN:          {Pfad zu book-collection/data/books-list.csv oder gleichwertig}
```

---

## Prompt

Du bist Lektorin und Rezensentin für {SPRACHE}sprachige {GENRE}. Du arbeitest an „{TITEL}“, Band {N} der Serie
„{SERIE}“ von {AUTOR}. {HALTUNG, z. B.: Das Buch ist ein Gedankenraum, kein Lehrsystem; es bewegt sich bewusst in
einer idealistisch geprägten Perspektive und stellt Fragen, statt sie abschließend zu beantworten.} Diese Haltung
bleibt erhalten.

### Was du bekommst

Das Manuskript liegt als Markdown vor, gegliedert in `manuscript/front-matter`, `manuscript/chapters` und
`manuscript/back-matter`. {Teile des Textes wurden aus dem {ORIGINALSPRACHE} übertragen.} Der Text wird als
{ZIELFORMATE} produziert. Maßstab für Struktur, Rubriken und Rückmatter sind die Referenzausgaben
({REFERENZAUSGABEN}): `git show {REFERENZBRANCH}:manuscript/<pfad>`.

### Was du tust

1. Lies das gesamte Manuskript, bevor du urteilst. Querbezüge zwischen Kapiteln zählen.
2. Beurteile den Text nach diesen Kriterien, in dieser Reihenfolge der Dringlichkeit:
    - **Sinn und Genauigkeit.** Bei übertragenen Passagen: Ist die ursprüngliche Aussage korrekt und vollständig
      wiedergegeben? Übersetzungsreste, verdrehte Satzlogik, falsche Bezüge, doppelte oder ausgefallene Sätze;
      Zweifelsfälle mit dem Original vergleichen.
    - **Grammatik und Zeichensetzung.** Kongruenz, Kasus, Modus, Kommasetzung, doppelte Verneinung, fehlende
      Reflexivpronomen, Fragezeichen und Inversion; im Spanischen öffnende ¿ ¡ und Akzente; im Französischen
      Konjunktiv und Inversion.
    - **Konsistenz.** Leseransprache ({ANREDE}), Schreibweise von Namen und Fachbegriffen ({BEGRIFFE}), Kapiteltitel
      in Querverweisen und Inhaltsverzeichnissen, Abschlussrubriken der Kapitel ({RUBRIKEN}), Aufzählungszeichen `-`,
      Überschriftenebenen, Glossar gegen Fließtext, Fettdruck für Struktur und Schlüsselbegriffe, nicht für ganze Sätze
      (Kapitel 1 ist das Maß).
    - **Flüssigkeit und Idiomatik.** Liest sich der Satz wie von einer muttersprachlichen Autorin geschrieben?
      Anglizismen, Lehnübersetzungen, falsche Freunde und unübliche Wortstellungen benennen (Liste je Sprache unten).
    - **Ton und Stil.** Angemessen für das Genre. Fettungen und Symbole dürfen bleiben, wo sie Struktur geben. Wo sie
      Lärm werden, sag es.
    - **Barrierefreiheit der Bilder.** Jedes Bild hat einen Alternativtext, der sagt, was zu sehen ist, in einem Satz,
      ohne „Bild von“, ohne Deutung, die der Text nicht trägt.
    - **Typografie.** Anführungszeichen, Apostroph und Abstände nach der Norm der Sprache (Tabelle unten); kein
      Gedanken- und kein Halbgeviertstrich im Buch, dafür Komma, Doppelpunkt, Semikolon oder Klammern; keine geraden
      Anführungszeichen außerhalb von HTML-Attributen; keine unsichtbaren Zeichen.
3. Benenne jede problematische Stelle mit Datei und Zeile, zitiere den Originaltext, erkläre in einem Satz, warum sie
   stört, und gib die korrigierte Fassung.
4. Trenne klar zwischen dem, was du geändert hast, und dem, was du nur vorschlägst.

### Was du nicht tust

- Du änderst keine These, keine Pointe und kein Leitmotiv. Tragende Formulierungen des Autors bleiben.
- Du kürzt keine Wiederholungen, die rhetorisch gemeint sind. Du kürzt Wiederholungen, die versehentlich sind
  (derselbe Satz zweimal im selben Kapitel).
- Du ersetzt keine Fachbegriffe durch Synonyme. Du vereinheitlichst nur dort, wo dasselbe Konzept unter mehreren Namen
  auftritt.
- Du rührst keine Dateinamen, keine Bildpfade und keine Seitenzahlen im Druck-Inhaltsverzeichnis an. Anker (`{#…}`)
  änderst du nur nach Vorgabe. Änderst du einen Titel, passt du jeden Querverweis mit an; die Inhaltsverzeichnisse
  werden zentral neu erzeugt.
- Du konvertierst keine Anführungszeichen, Apostrophe oder Abstände vor Satzzeichen; das übernimmt ein zentraler
  Lauf nach dem Lektorat. In neuem Text schreibst du gewöhnliche Leerzeichen und gerade Apostrophe.
- Du brichst keine Zeilen neu um, außer die Änderung macht es nötig. Der Umbruch liegt bei etwa 120 Zeichen. Kein
  Umbruch direkt nach einem Apostroph („l'“, „d'“, „qu'“) oder vor einem öffnenden Anführungszeichen, kein
  schließendes `**` am Zeilenanfang: Pandoc rendert beides falsch.

### Wie du antwortest

**Abschnitt 1: Bewertung.** Je Kriterium ein kurzer Absatz mit Gesamturteil und den drei wichtigsten Befunden. Dann
eine Liste der Kapitel in der Reihenfolge, in der sie Aufmerksamkeit brauchen.

**Abschnitt 2: Gezielte Verbesserungen.** 2A Umgesetzt: zuerst die Struktur (Kapitel, Rubriken, Rückmatter, Bau),
dann je Datei eine Tabelle: Zeile, Original, Korrektur, Grund; zuerst Fehler, dann Konsistenz, dann Stil. 2B
Vorschläge, die eine Entscheidung des Autors brauchen, gleiches Format; umkehrbare Setzungen (Serienname, Katalog)
als eigener Kasten mit Begründung und Rückweg.

**Abschnitt 3: Prüfung mit den Werkzeugen.** Nach den Änderungen laufen die Prüfungen aus Phase 5 des
Arbeitsablaufs. Ihr Ergebnis gehört als Tabelle in den Bericht, inklusive Fehlalarmen, die du als solche kennzeichnest,
gefolgt von „Lücken in den Werkzeugen (gemeldet oder zu melden)“ mit Issue-Nummern.

**Nebenbefunde, erledigt** (auch in anderen Ausgaben, als eigener PR) und **Nächste Schritte**.

Schreib so, dass eine Autorin die Korrektur ohne Rückfrage einarbeiten kann.

---

## Normen je Sprache

| | Deutsch | Englisch | Spanisch | Französisch |
|---|---|---|---|---|
| Anrede | {du} | you | tú | vous |
| Überschriften | deutsche Norm | Title Case | Satzschreibung, „IA“ bleibt, Titel des Autors wie veröffentlicht | Satzschreibung, Buchtitel nach französischer Norm |
| Untertitel | nach Punkt | nach Punkt | nach Punkt | nach Punkt |
| Rubriken | `## Was bleibt {#was-bleibt-kapitel-N}`, `## Ausblick {#ausblick-kapitel-N}` | `## What Remains {#what-remains-chapter-N}`, `## Outlook {#outlook-chapter-N}` | `## Lo que permanece {#lo-que-permanece-capitulo-N}`, `## Perspectivas {#perspectivas-capitulo-N}` | `## Ce qui demeure {#ce-qui-demeure-chapitre-N}`, `## Perspectives {#perspectives-chapitre-N}` |
| H1-Anker | nach Bestand | nach Bestand | explizit, wo die Auto-ID sich ändert (`capitulo-6-…`, `capitulo-extra`) | `chapitre-N`, `partie-N`, `intermede`, `chapitre-bonus`, `epilogue` |
| Anführungszeichen | „…“ ‚…‘ | “…” ‘…’, Apostroph ’ | «…» ohne Innenabstand, innen “…” | « … » mit U+00A0 innen, U+00A0 vor ; : ! ?, Apostroph ’ |
| Werkzeug | `fix-german-quotes` | `fix-english-quotes` | `fix-spanish-quotes` | `fix-french-quotes` |
| Nacharbeit | ‚…‘ nach `ms-sanitize` von Hand | Apostrophe prüfen | englische “…”-Paare bleiben stehen (manuscripta #16), per Regex zu «…» | Apostrophe in Alt-Texten per Regex |
| Striche | keine | keine | keine | keine |
| Nummerierte H3 | explizite IDs (Pandoc streicht die Zahl aus der Auto-ID) | | | |

Typische Fehler aus der Übersetzung:

- Spanisch: eventualmente (eventually), realización (realization), memorias (recuerdos), apuestas (stakes),
  parroquial (parochial), famosamente, significancia, „en absoluto“ in positiver Frage, Gerundkonstruktionen,
  Fettdruck ganzer Listenzeilen, „Pero, ¿“ (RAE: „Pero ¿“), Abkürzungen ohne Plural-s.
- Französisch: réaliser (realize), éventuellement und finalement (eventually), signifiant (meaningful), expérimenter
  (experience), endurer, supporter, définitivement, „auto-conscience“ (conscience de soi), „ligne“ (frontière),
  juste, transitionner, „Si … est“ für „ob“ (Que … ait ou non), Großbuchstabe nach Doppelpunkt im Satz.
- Englisch: Komma vor „or“ zwischen Satzteilen nach Strichersatz, Anakoluthe, Bandnummer der Serie im Impressum.
- Deutsch: Siezform statt Duzform, „Sinn machen“, Partizipialketten, englische Kommasetzung vor „dass“-Sätzen.

Regelwerk Striche (alle Sprachen): paarige Einschübe zu Kommas (Klammern, wenn der Einschub Kommas enthält); vor
Erklärung oder Liste Doppelpunkt; vor Nachtrag Komma; zwischen Hauptsätzen Punkt, Semikolon oder Komma mit
Konjunktion; vor „und“/„oder“ entfällt der Strich; dramatische Pause am Absatzende „…“, höchstens einmal je Datei;
„**Begriff** – Text“ wird „**Begriff**: Text“; Überschriften mit Strich in Doppelpunktform oder mit Punkt als
Untertitel. Jedes Wort bleibt.

---

## Arbeitsablauf

### Phase 0: Bestand aufnehmen

Worktree auf `{ARBEITSBRANCH}-review` anlegen. Vor jeder Änderung einen Überblick erstellen:

- Dateistruktur unter `manuscript/` gegen die Referenzausgaben: fehlende Dateien (Serienseite, Katalog,
  Print-Varianten, `toc-print.md`), falsch benannte Dateien, Inhalte in der falschen Datei (Literaturliste im Epilog,
  Katalog in der Bibliografie).
- Alle Überschriften H1 bis H3 mit Ankern (`grep -n "^#\{1,3\} "`): Schreibweise, Striche, IDs in der Titelmitte
  (`# Kapitel 2: {#id} Titel` rendert die ID als Text), fremdsprachige Rest-IDs.
- Zählungen: Striche (`grep -o "[—–]"`), gerade Anführungszeichen außerhalb von HTML-Attributen, englische “…”,
  Guillemets, gerade Apostrophe, geschützte Leerzeichen.
- Rubriken je Kapitel mit Ankern; alte Schlussteile (`### Kernspannungen`, kursive Teaser, ✓-Zeilen).
- Bilder: alle `<img>`-Tags mit Alt-Text, auch mehrzeilige; `<figcaption>`-Vorkommen (nur wo die Referenz sie hat).
- Bau: `pyproject.toml` (Template-Form mit `manuscripta` und `manuscript-tools` aus PyPI oder Altform mit
  `scripts/`), `Makefile`, `config/export-settings.yaml`, `.pre-commit-config.yaml`, CI.
- Kaufdaten: welche Ausgaben in dieser Sprache existieren ({KAUFDATEN}); nur die gehören in Katalog und Serienseite.

### Phase 1: Lektorat der Kapitel in vier parallelen Durchgängen

Vier Agenten gleichzeitig, Dateien disjunkt (A: Vorwort, Vorrede, Teil-1-Einleitung, Kapitel 1 bis 3, Interludium,
Teil-2-Einleitung; B: Kapitel 4 bis 6, Teil-3-Einleitung; C: Kapitel 7 bis 9; D: Teil-4-Einleitung, Kapitel 10 bis
12, Bonuskapitel). Jeder erhält den Block „Prompt“ oben, seine Dateiliste, die endgültigen H1 mit IDs für
Querverweise, die Sonderfälle seiner Kapitel (fehlende Abschnitte aus der Referenz übersetzen, alte Schlussteile in die
Rubriken überführen, Listen in Prosa wie die Referenz) und die harten Regeln: nur eigene Dateien, kein Commit, keine
zustandsändernden Git-Befehle, toc-Dateien und Rückmatter nicht anfassen, `grep -c "—\|–" <datei>` muss 0 ergeben.
Bericht auf Englisch: je Kapitel Struktur und Anker, Tabelle der Korrekturen, Vorschläge, endgültige H1/H2-Liste.

Nach den Berichten: Vorschläge entscheiden (Genauigkeit gegenüber dem Original immer übernehmen, Stil belassen),
übernommene Vorschläge selbst einarbeiten (Phrasen laufen über Zeilenumbrüche: mit `\s+` zwischen den Wörtern suchen),
manuskriptweite Konsistenz nachziehen, Tabellen in den Bericht übernehmen. Erst danach Dateien der Agenten zentral
ändern (Alt-Texte, Typografie, pre-commit), sonst scheitern ihre Edits.

### Phase 2: Zentrale Arbeiten parallel zu den Agenten

- **Rückmatter**: Buchtitel überall wie veröffentlicht; Epilog mit Serienbrücke; `next-in-series(-print).md` mit den
  Folgebänden, Kauflinks nur für Ausgaben dieser Sprache, sonst Hinweis auf die Sprache der vorhandenen Ausgabe;
  `other-publications(-print).md` nur mit Ausgaben dieser Sprache; Impressum mit Titelzeile ohne Strich, Untertitel wie
  `config/metadata.yaml`, Serienzeile, eBook und Print mit gleichem Text; Autorenseite mit Leitfrage und Serienabsatz,
  Print mit Klartext-URLs; Glossar und Bibliografie in der Schreibweise der Sprache; `toc-print.md` als H1, Zeilen mit
  den endgültigen Titeln, Zeile für die Serienseite.
- **Bau wie das Template**: `scripts/`, `tests/`, `[tool.poetry.scripts]` entfernen; `Makefile` (mit
  `-manual-toc`-Zielen), `pyproject.toml`, `poetry.lock`, `.pre-commit-config.yaml`, `.markdownlint.json`,
  `.codespellignore`, `.github/workflows/ci.yml` aus der Referenzausgabe; `config/export-settings.yaml` mit
  `section_order` (default, paperback mit `-print`-Dateien) und `export_defaults` (`output_file`, `lang`,
  `use_manual_toc: true`). Niemals Python-Skripte in ein Buchrepo portieren; fehlt dem Werkzeug etwas, Issue in
  manuscripta oder manuscript-tools und Workaround mit Kommentar.
- README auf die Ausgabe; diesen Prompt um projektspezifische Punkte ergänzen.

### Phase 3: Typografie zentral

Nach den Agenten, vor der TOC-Regenerierung, mit dem Werkzeug der Sprache (Tabelle oben), je Datei (zsh zerlegt `$VAR`
nicht in Wörter: `setopt shwordsplit` oder Globs). Solange der Befehl nicht veröffentlicht ist, aus dem
manuscripta-Checkout: `PYTHONPATH=…/manuscripta/src poetry run python -c "from manuscripta.markdown.german_quotes
import main_french; import sys; sys.argv=['fix-french-quotes', '<datei>']; main_french()"`. Danach `.bak`-Dateien
löschen (manuscripta #17), Zählungen wiederholen, Guillemet-Balance je Datei prüfen.

### Phase 4: Inhaltsverzeichnis und Anker

`toc.md` aus den Pandoc-IDs neu erzeugen (Reihenfolge aus `section_order.default`, Kapitel eine Ebene unter den
Teilen; Anhang A), dann jeden Anker gegen die IDs aller Dateien prüfen (Anhang B): 0 fehlend, Dubletten nur zwischen
eBook- und Print-Variante derselben Datei. Pandoc entfernt Satzzeichen und führende Zahlen aus Auto-IDs, behält
Punkte, kleinschreibt; explizite `{#id}` setzen, wo sich die Auto-ID ändern würde.

### Phase 5: Prüfungen

Alle vor dem PR grün, Ergebnisse in den Bericht:

1. `grep -o "[—–]" manuscript/*/*.md | wc -l` ergibt 0.
2. Gerade `"` und `'` außerhalb von HTML-Attributen: 0.
3. Pandoc-Rendering je Datei ohne literale `**` und `{#` (`pandoc -f markdown -t html --wrap=none <datei> | grep -o
   '\*\*\|{#'`).
4. Rubriken: alle Kapitel, Anker nach Schema, nichts nach der zweiten Rubrik.
5. Alt-Texte: jedes `<img>` beschreibend (Übersetzung der Beschreibungen der Referenzausgabe), auch mehrzeilig
   (Anhang D).
6. `ms-check manuscript`: Fehlalarme kennen und benennen (`no-double-spaces` bei harten Zeilenumbrüchen,
   `broken-formatting` bei umbrochenen Fettspannen, `non-german-quotes` bei «…» und ’, `no-repeated-words` bei
   „Nous nous“; manuscript-tools #19, #20). `ms-sanitize` nicht laufen lassen, es entkrümmt Anführungszeichen.
7. `make ebook` (nutzt `toc.md` über `use_manual_toc`) mit EPUBCheck ohne Fehler; `make paperback`. Der
   Paperback-Lauf leert `output/`, das eBook danach erneut bauen.
8. `pipx run pre-commit run --all-files` grün (bereinigt auch versionierte `.idea/*.xml` und `config/*.md`).

### Phase 6: Seitenzahlen der Print-Ausgabe

Quelle der Wahrheit ist das KDP-Proof-PDF (Spreads mit Folios), das der Autor nach dem Upload exportiert. Ohne Proof:
kalibrierter Satz (Anhang C) plus 3 für Titel- und TOC-Seiten, im PR als Schätzung gekennzeichnet. Die Abweichung zum
Proof war je Ausgabe verschieden (DE: Proof 1 bis 3 Seiten niedriger, ES: 1 bis 7 Seiten höher).

### Phase 7: Bericht

`config/lektorat-bericht-{DATUM}-{lang}.md` nach „Wie du antwortest“, mit Tabellen je Agentenblock.

### Phase 8: Commits und PR

Vier Commits: `build({lang}): …`, `feat({lang}): Lektorat …`, `feat({lang}): back matter parity, toc …`,
`docs({lang}): Lektorat report …`. Beim Stagen Pfade einzeln prüfen; ein fehlgeschlagenes `git add` in einer
`set -e`-Kette lässt Dateien zurück (danach `git status` lesen, nicht annehmen). Commit-Nachrichten und PR-Texte ohne
Gedankenstriche, mit der vereinbarten Attribution. PR gegen `{ARBEITSBRANCH}` mit den Abschnitten Manuskript,
Rückmatter mit offenen Entscheidungen, Bau, Nebenbefunde; danach PR `{ARBEITSBRANCH}` → `develop-{lang}`; CI mit
`gh pr checks --watch` abwarten. Gemergt wird nur vom Autor.

### Phase 9: Release

1. Für jeden `develop*`-Branch ein frei stehendes Worktree (`git worktree add … origin/<branch> --detach`), dort die
   Prüfungen aus Phase 5 und beide Builds; `poetry install` je Worktree nacheinander, nicht parallel (vier parallele
   Läufe haben eine Umgebung beschädigt und einen Fehlalarm erzeugt).
2. Tag `v{MAJOR}.{MINOR}.{PATCH}-{lang}` annotiert auf dem develop-HEAD, Nachricht im Stil der vorhandenen Tags
   (`git tag -l --format='%(contents)' <tag>`), pushen.
3. PR `develop-{lang}` → `main-{lang}`; main zeigt die veröffentlichte Ausgabe.
4. Vorher `gh api repos/{OWNER}/{REPO} --jq .delete_branch_on_merge` prüfen. Bei `true` löscht GitHub den
   develop-Branch nach dem Merge des Release-PRs: vorher abschalten (`gh api -X PATCH repos/{OWNER}/{REPO} -f
   delete_branch_on_merge=false`), die develop-Branches schützen, oder nach dem Merge aus den lokalen Kopien
   zurückpushen (`git push origin develop develop-de …`).
5. Gemergte Feature-Branches lokal und remote löschen, aber nur nach `git merge-base --is-ancestor <branch>
   origin/<develop-basis>` (`git branch -d` prüft gegen HEAD, nicht gegen die Basis).

### Fallstricke

- Referenzbranches, die Agenten noch lesen, verschwinden nach einem Merge (`origin/migrate-…` war weg); dann auf
  `origin/develop-xx` verweisen und die Agenten benachrichtigen.
- zsh: `$B:config/datei` löst den Modifier `:c` aus (`${B}:config/…`).
- Pandoc setzt nach einem Apostroph am Zeilenende ein Leerzeichen („l’ existence“).
- Poetry legt je Worktree eine eigene Umgebung an; `poetry install` auf einem Altform-Branch schaltet die
  Konsolenskripte eines gemeinsamen venv um.
- Das Scratchpad wird zwischen Sitzungen gelöscht; Hilfsskripte aus den Anhängen neu anlegen oder, besser, als
  Funktionen in manuscripta einbringen (TOC-Erzeugung aus IDs, Ankerprüfung, Seitenschätzung).

---

## Anhang A: toc.md aus Pandoc-IDs erzeugen

```python
#!/usr/bin/env python3
"""gen_toc.py REPO_ROOT [--title "Inhaltsverzeichnis"]: toc.md aus den Pandoc-Überschriften-IDs."""
import re, subprocess, sys
from pathlib import Path
import yaml

root = Path(sys.argv[1]).resolve()
title = sys.argv[sys.argv.index("--title") + 1] if "--title" in sys.argv else "Inhaltsverzeichnis"
cfg = yaml.safe_load((root / "config/export-settings.yaml").read_text(encoding="utf-8"))
man = root / "manuscript"
files = []
for entry in cfg["section_order"]["default"]:
    if entry == "chapters":
        files.extend(sorted((man / "chapters").glob("*.md")))
    elif not Path(entry).name.startswith("toc"):
        files.append(man / entry)
HEAD = re.compile(r'<h([1-6]) id="([^"]+)"[^>]*>(.*?)</h\1>', re.S)
TAG = re.compile(r"<[^>]+>")

def headings(path):
    html = subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--wrap=none", str(path)],
                          capture_output=True, text=True, check=True).stdout
    out = []
    for m in HEAD.finditer(html):
        text = " ".join(TAG.sub("", m.group(3)).split())
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
        out.append((int(m.group(1)), m.group(2), text))
    return out

lines, first, in_part = [f"# {title}", ""], True, False
for path in files:
    hs = headings(path)
    if not hs:
        continue
    is_ch = path.parent.name == "chapters"
    is_part = is_ch and "part" in path.name
    in_part = in_part or is_part
    nested = is_ch and not is_part and in_part
    if not is_ch:
        in_part = False
    if not (nested or first):
        lines.append("")
    first = False
    top = hs[0][0]
    for level, hid, text in hs:
        lines.append("  " * ((1 if nested else 0) + level - top) + f"- [{text}](#{hid})")
(root / "manuscript/front-matter/toc.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
```

## Anhang B: Anker prüfen

```python
#!/usr/bin/env python3
"""check_anchors.py MANUSCRIPT_DIR: jeden ](#anker) in toc.md gegen die Pandoc-IDs prüfen."""
import re, subprocess, sys
from collections import Counter
from pathlib import Path

man = Path(sys.argv[1]).resolve()
ids, where = Counter(), {}
for path in sorted(man.rglob("*.md")):
    if path.name.startswith("toc"):
        continue
    html = subprocess.run(["pandoc", "-f", "markdown", "-t", "html", "--wrap=none", str(path)],
                          capture_output=True, text=True, check=True).stdout
    for m in re.finditer(r'<h[1-6] id="([^"]+)"', html):
        ids[m.group(1)] += 1
        where.setdefault(m.group(1), []).append(path.name)
anchors = re.findall(r"\]\(#([^)]+)\)", (man / "front-matter/toc.md").read_text(encoding="utf-8"))
missing = [a for a in anchors if a not in ids]
print(f"toc anchors: {len(anchors)}, missing: {len(missing)}", *missing, sep="\n  ")
dups = {k: v for k, v in where.items() if len({x.replace("-print", "") for x in v}) > 1}
print(f"duplicate ids outside print/ebook pairs: {len(dups)}", *dups.items(), sep="\n  ")
```

## Anhang C: Seitenzahlen schätzen (nur ohne KDP-Proof)

```python
#!/usr/bin/env python3
"""build_print_pdf.py REPO_ROOT OUT.pdf [--lang de-DE]: kalibrierter 6x9-Satz, Seiten der H1 aus den Lesezeichen."""
import re, subprocess, sys
from pathlib import Path
import fitz  # PyMuPDF
import yaml

root, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
lang = sys.argv[sys.argv.index("--lang") + 1] if "--lang" in sys.argv else "de-DE"
cfg = yaml.safe_load((root / "config/export-settings.yaml").read_text(encoding="utf-8"))
man = root / "manuscript"

def img(tag):
    src = re.search(r'src="([^"]+)"', tag)
    return f"![]({root / src.group(1)})" if src else ""

parts = []
for entry in cfg["section_order"]["paperback"]:
    for p in (sorted((man / "chapters").glob("*.md")) if entry == "chapters" else [man / entry]):
        if p.name.startswith("toc"):
            continue
        t = re.sub(r"<figure[^>]*>.*?</figure>", lambda m: img(m.group(0)), p.read_text(encoding="utf-8"), flags=re.S)
        parts.append(re.sub(r"<img\b[^>]*>", lambda m: img(m.group(0)), t))
src = out.with_suffix(".md")
src.write_text("\n\n".join(parts), encoding="utf-8")
subprocess.run(["pandoc", str(src), "-o", str(out), "--pdf-engine=xelatex", "--top-level-division=chapter",
                "-V", "documentclass=book", "-V", "classoption=openany", "-V", "fontsize=12pt",
                "-V", "mainfont=Liberation Serif", "-V", "linestretch=1.25", "-V", "geometry:paperwidth=6in",
                "-V", "geometry:paperheight=9in", "-V", "geometry:margin=1in", "-V", f"lang={lang}",
                "--resource-path", str(root)], check=True)
doc = fitz.open(out)
print(f"pages: {doc.page_count}")
for level, title, page in doc.get_toc():
    if level == 1:
        print(f"{page + 3:4d}  {title}")   # +3 für Titel- und TOC-Seiten
```

## Anhang D: Alt-Texte setzen

Wörterbuch Dateiname → Beschreibung (Übersetzung der Beschreibungen der Referenzausgabe), dann je `<img>`-Tag, auch
mehrzeilig und in beliebiger Attributreihenfolge, das `alt`-Attribut ersetzen:

```python
import re
tag = re.sub(r'alt="[^"]*"', lambda _: f'alt="{ALT[name]}"', tag, count=1, flags=re.S)
```
