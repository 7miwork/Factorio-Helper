# Factorio AI Blueprint Generator

Lokale Windows-Anwendung zur Analyse einer Factorio-Installation. Diese erste Entwicklungsphase erkennt die Installation, Factorio-Version und installierte Mods samt Versionen und Dependencies. Die Anwendung verwendet fuer Phase 1 nur die Python-Standardbibliothek.

## Installation und Start

```text
cd "Z:\Codes\My Projects\Factorio Helper"
python -m app.main
```

Im Fenster den Factorio-Installationsordner waehlen und `Analyze Installation` ausfuehren. Der Pfad wird in `config/settings.json` gespeichert. Die GUI und der CLI-Scan verwenden dieselbe Erkennung.

## GUI-Struktur (app/gui)

Die grafische Oberflaeche ist als Notebook mit getrennten Tabs in `app/gui/` organisiert:

- `factorio_tab.py` - Installationsordner waehlen und Installation analysieren (Version, Pfad)
- `mods_tab.py` - Scan-Ergebnisse: Mods samt Versionen, Status und Abhaengigkeiten
- `generator_tab.py` - Blueprint aus Anforderungen erzeugen
- `knowledge_tab.py` - Knowledge Base aus den installierten Daten aufbauen
- `ai_tab.py` - KI-Provider und Modelle waehlen/aktualisieren
- `library_tab.py` - Blueprint Library auflisten und Blueprint Book erzeugen
- `settings_tab.py` - Einstellungen und Projektpfade

`main_window.py` baut das Hauptfenster zusammen und teilt den gemeinsamen Zustand
(Einstellungen, letzter Scan). `app/main.py` ist nur noch der Einstiegspunkt
(CLI + GUI-Start).

## Grafik-Vorschau & KI-Lern-Notizen

Das `app/graphics/`-Paket loest Prototyp-Grafikreferenzen (`__base__/...`,
`__mod__/...`) gegen Installation und installierte Mods auf, extrahiert
Bilddateien (aus Ordnern oder Mod-Zips) in einen Cache und stellt sie als
Vorschau bereit. Im Knowledge-Tab kann nach dem Aufbau der Knowledge Base ein
Prototyp ausgewaehlt werden; Metadaten und – falls verfuegbar – die Spielgrafik
(Icon) werden angezeigt, wahlweise in mehreren Skalierungen (1x-4x).

Unterstuetzte Formate: PNG (nativ) und – fuer Spritesheets – unkomprimierte
DDS-Texel (ueber einen kl. Decoder in `app/graphics/dds.py`). Fuers
Hochskalieren wird optional `Pillow` genutzt (`python -m pip install pillow`).
Lua-Data-Stage-Prototypen werden auch direkt aus Mod-Zips gelesen
(`app/factorio/lua_parser.py`).

Eigene Eingaben fuer die KI werden als "Lern-Notizen" im AI-Settings-Tab
gespeichert (`data/learn/notes.md`). Diese fliessen bei der naechsten Planung
als `learning_notes` in den KI-Kontext ein, damit die KI aus deinen
Anmerkungen lernen kann.

## CLI

```text
python -m app.main scan "C:\Program Files (x86)\Steam\steamapps\common\Factorio"
python -m app.main models
python -m app.main providers
python -m app.main knowledge "C:\Program Files (x86)\Steam\steamapps\common\Factorio"
python -m app.main validate blueprint.txt
python -m app.main generate requirements.txt
```

Die Versionsnummer wird aus `data/base/info.json` gelesen. Mods werden als Verzeichnisse oder ZIP-Dateien aus dem `mods`-Ordner gelesen. `mod-list.json` bestimmt den Aktivierungsstatus; unbekannte Mod-Namen werden nicht hartcodiert.

## Knowledge Base

Der Befehl `knowledge` erzeugt `data/factorio/knowledge.db` mit Mod-Metadaten und
typisierten Prototypen fuer Items, Entities, Rezepte, Technologien, Fluids,
Ressourcen und Module. Neben JSON-Exporten werden native Lua-Data-Stage-Dateien
(`data:extend{ ... }`) ueber einen toleranten Teilmengen-Parser
(`app/factorio/lua_parser.py`) ausgelesen – dadurch stehen auch die Icons der
Echt-Daten fuer die Grafik-Vorschau zur Verfuegung. Die Datenbank ist lokal und
wird bei erneutem Aufbau aktualisiert.

## Blueprint-Kern

Blueprints werden als Factorio-JSON erzeugt, validiert und mit dem offiziellen Format (`0` + zlib + Base64) kodiert. `validate` akzeptiert sowohl Blueprint-JSON als auch eine Blueprint-String-Datei und beendet sich bei Fehlern mit Exit-Code 1.

## Layout Engine

Der Blueprint-Generator unterstuetzt `compact`, `balanced`, `expandable`, `main_bus` und `city_block`. Die Strategie wird im strukturierten Plan ueber `layout_strategy` gesetzt und erzeugt reproduzierbare Entity-Positionen.

## KI-Provider

`ProviderManager` waehlt Provider und Modell anhand von `config/ai_providers.json` und kann Rollen getrennt aufloesen. Unterstuetzt werden Ollama, LM Studio, OpenRouter, Hugging Face Inference, Groq, Together AI und beliebige OpenAI-kompatible Endpoints. Der Mock-Provider arbeitet ohne Netzwerk und ist fuer Tests voreingestellt.

Der `ProductionPlanner` uebergibt Kontext, Benutzeranforderungen und Layout-Strategie an den Provider. Die Antwort muss dem strukturierten JSON-Plan entsprechen; ungueltige JSON-Antworten oder unbekannte Layout-Strategien werden vor dem Blueprint-Generator abgewiesen.

Mit `generate` wird eine Anforderungsdatei zusammen mit der Knowledge Base an den konfigurierten Planner gesendet. Der strukturierte Plan wird anschliessend lokal in Blueprint-JSON und Blueprint-String umgewandelt, validiert und unter `blueprints/generated` gespeichert.

Rezeptdaten koennen in ein einheitliches Modell normalisiert werden. Der Produktionsrechner loest einfache Rezeptketten rekursiv auf und berechnet Rohstoffbedarf aus einem Zielwert pro Minute; fehlende Rezepte werden als externe Inputs ausgewiesen.

JSON-Prototyp-Exporte werden sowohl aus Mod-Verzeichnissen als auch direkt aus ZIP-Mods gelesen. Dadurch bleibt die Quelle jedes Datensatzes bis zum Mod und zur Datei nachvollziehbar.

## Blueprint Library und Books

`LibraryManager` speichert jeden validierten Blueprint in einem eigenen Ordner mit `blueprint.json`, importierbarem `blueprint.txt`, `metadata.json` und `README.md`. Mehrere Blueprint-JSONs koennen mit `create_book` in ein Factorio-Blueprint-Book zusammengefasst und als JSON sowie Blueprint-String exportiert werden.

## KI-Konfiguration

`config/ai_providers.json` enthaelt Ollama, LM Studio, OpenAI-kompatibel, Custom und Mock mit Rollen fuer Planner, Validator und Description. Ollama-Modelle koennen ohne Download ueber `GET /api/tags` abgefragt werden. API-Schluessel werden nur ueber Umgebungsvariablen referenziert. Lokale Geheimnisse gehoeren in `.env`, niemals in die Konfiguration oder den Quellcode.

```text
FACTORIO_AI_API_KEY=
```

Die Vorlage steht in `.env.example`. Ollama und LM Studio sind lokal kostenlos nutzbar. OpenRouter, Hugging Face, Groq und Together AI bieten je nach Konto, Modell und Zeitpunkt kostenlose Kontingente oder freie Modelle; das ist nicht garantiert und kann sich aendern. Modelle werden nicht automatisch installiert.

Die Cloud-Provider sind standardmaessig deaktiviert. Zum Aktivieren den jeweiligen Eintrag in `config/ai_providers.json` auf `enabled: true` setzen und den passenden Schluessel als Umgebungsvariable bereitstellen. `providers` zeigt die konfigurierte Providerliste, ohne Netzwerkaufrufe oder Schluessel auszugeben.

## Tests und Entwicklung

```text
python -m unittest discover -s tests -v
```

Die Tests erstellen eine temporaere Factorio-Struktur mit ZIP-Mod und pruefen Version, Mod-Version und Dependencies. Weitere Phasen bauen darauf die Knowledge Base, Blueprint-Modelle, Layout Engine, Provider-Aufrufe und Library auf.

## Fehlerbehebung

- `Scan failed`: Einen echten Factorio-Installationsordner mit `data` und `mods` waehlen.
- Keine Mods: Pruefen, ob der Ordner `mods` direkt unterhalb der Installation liegt.
- Keine Ollama-Modelle: Ollama starten und `http://localhost:11434` erreichbar machen.