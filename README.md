# Galactic Trader

### Installationshinweis
Um das Spiel zu starten ist nur **uv** notwendig. Navigiere mit dem Terminal in den Projekt-Ordner und starte das Prgoramm mit _uv run galctic-trader_ . Alle Abhängigkeiten werden automatisch installiert.

Es gibt verschiedene Möglichkeiten das Spiel zu starten:

Grafische Oberfläche mit pygame-ce (Standard):
``uv run galactic-trader`` oder
``uv run python -m galactic_trader``

Terminal-Oberfläche:
``uv run galactic-trader --ui terminal``

Außerdem ist es möglich, das Stargeld manuell zu beeinflussen. Dadurch kann man z.B. direkt mit genug Geld starten um alle Funktionen auszuprobieren. Dafür muss man hinter den gewünschten Startbefehl ``--money=1234`` anhägen. (z.B. wie folgt: ``uv run galactic-trader --money=99999``)

Die grafische Oberfläche unterstützt zusätzlich folgende Tastenkürzel:

- ``1`` bis ``4``: Markt, Produktion, Flotte und Investitionen
- ``N``: nächste Runde
- ``Ctrl+S``: speichern
- ``Ctrl+L``: laden
- ``Esc``: Dialog schließen bzw. Spiel beenden