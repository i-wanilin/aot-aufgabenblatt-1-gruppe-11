# Experiment 1 – Einfluss der Distanz von Nahrungsquellen auf die Nahrungsausbeutung

## Motivation

Ziel dieses Experiments ist die Untersuchung des Einflusses der Distanz zwischen Nest und Nahrungsquelle auf das Verhalten und die Effizienz der Ameisenkolonie. Dabei soll analysiert werden, ob näher gelegene Quellen schneller gefunden und effizienter ausgebeutet werden als weiter entfernte Quellen. Zusätzlich wird betrachtet, wie sich die Anzahl der Ameisen auf die Gesamtleistung des Schwarms auswirkt.

Die Forschungsfrage lautet:

> *Wie verhält sich eine Ameisenkolonie, wenn Nahrung in unterschiedlicher Entfernung vom Nest liegt? Werden alle Quellen gleich gut erreicht oder bevorzugt die Kolonie die nähere?*

Die Hypothese besagt, dass näher gelegene Quellen signifikant früher entdeckt werden und über die Zeit mehr Nahrung zum Nest beitragen als weiter entfernte Quellen.

---

## Verlauf der Simulationen

Für das Experiment wurden mehrere Simulationen mit unterschiedlichen Distanzen der zweiten Nahrungsquelle durchgeführt (`close`, `mid`, `far`). Die Population bestand zunächst aus 20 Ameisen (`N=20`). Zusätzlich wurde ein Vergleich mit 40 Ameisen (`N=40`) durchgeführt, um den Einfluss der Populationsgröße zu untersuchen.

Zu Beginn der Simulation bewegen sich die Ameisen zufällig durch die Gridwelt und hinterlassen Nest-Pheromone. Sobald eine Ameise eine Nahrungsquelle entdeckt und Nahrung erfolgreich ins Nest zurückbringt, entsteht eine stabile Pheromonspur zwischen Quelle und Nest. Weitere Ameisen folgen anschließend bevorzugt diesen Trails, wodurch sich die Lieferungsrate erhöht.

In allen drei Distanzvarianten konnte beobachtet werden, dass die näher gelegene Quelle deutlich früher entdeckt wurde. Die weiter entfernte Quelle wurde teilweise erst nach längerer Explorationszeit erreicht. Gleichzeitig etablieren sich zu nahe gelegenen Quellen stabilere und häufiger genutzte Pheromonpfade.

---

## Ergebnisse

Die Ergebnisse der Simulationen sind in Abbildung 1, Abbildung 2 und Abbildung 3 dargestellt.

Die kumulative Nahrungsausbeutung in Abbildung 1 zeigt deutlich, dass die näher gelegenen Quellen wesentlich mehr Nahrung zum Nest beitragen als die weiter entfernten Quellen.

Im `close`-Experiment wurden nach 4000 Ticks ungefähr 175 Nahrungseinheiten von der nahen Quelle geliefert, während die entfernte Quelle nur einen sehr kleinen Beitrag leistete. Im `mid`-Experiment wurden etwa 131 Nahrungseinheiten von der nahen Quelle und lediglich 28 von der entfernten Quelle transportiert. Im `far`-Experiment sank die Gesamtmenge weiter ab; gleichzeitig benötigte die Kolonie deutlich länger, um die entfernte Quelle effizient auszubeuten.

Abbildung 3 bestätigt diese Beobachtungen zusätzlich. Die erste Lieferung der nahen Quelle erfolgte bereits nach ungefähr 60–70 Ticks, während die weiter entfernten Quellen teilweise erst nach etwa 800–1300 Ticks erreicht wurden. Damit steigt die Suchzeit deutlich mit zunehmender Distanz an.

Auch die Rolling-Rate in Abbildung 2 zeigt Unterschiede zwischen den Szenarien. Die nahe Quelle erzeugt über lange Zeit stabile und hohe Lieferungsraten. Dagegen zeigen weiter entfernte Quellen stärkere Schwankungen und längere Phasen mit niedriger Aktivität. Dies deutet darauf hin, dass lange Wege weniger stabile Pheromonpfade erzeugen und häufiger neu entdeckt werden müssen.

Zusätzlich wurde ein Vergleich zwischen `N=20` und `N=40` Ameisen durchgeführt. Mit 40 Ameisen erhöhte sich die Gesamtmenge der gelieferten Nahrung deutlich. Im `mid`-Szenario stieg die Menge von 159 auf 268 Nahrungseinheiten. Gleichzeitig wurde die erste Lieferung der nahen Quelle deutlich früher erreicht (`t_first` von 66 auf 18 Ticks). Allerdings stieg auch die Anzahl der toten Ameisen von 3 auf 7, was auf höheren Energieverbrauch und stärkere Konkurrenz innerhalb der Kolonie hinweist.

---

## Interpretation hinsichtlich der Forschungsfrage

Die Ergebnisse bestätigen die aufgestellte Hypothese deutlich. Nähere Nahrungsquellen werden wesentlich schneller gefunden und effizienter ausgebeutet als weiter entfernte Quellen. Der Hauptgrund hierfür liegt in der kürzeren Wegdistanz, wodurch Ameisen schneller stabile Pheromonpfade etablieren können. Diese Trails verstärken sich im Laufe der Zeit selbst, da erfolgreiche Ameisen weitere Pheromone hinterlassen und dadurch zusätzliche Ameisen anziehen.

Weiter entfernte Quellen leiden dagegen unter längeren Suchzeiten und instabileren Pheromonspuren. Da Ameisen mehr Zeit für Hin- und Rückweg benötigen, ist die Wahrscheinlichkeit höher, dass Pheromone verdunsten oder Trails unterbrochen werden. Dadurch bleibt die Nahrungsausbeutung weniger effizient.

Der Vergleich der Populationsgrößen zeigt zusätzlich, dass größere Ameisenpopulationen die Exploration und Nahrungssuche beschleunigen können. Mehr Ameisen erhöhen die Wahrscheinlichkeit, neue Quellen frühzeitig zu entdecken und stabile Pfade aufzubauen. Gleichzeitig entstehen jedoch zusätzliche Nachteile wie erhöhter Energieverbrauch und mehr tote Agenten.

Insgesamt zeigen die Experimente, dass sich die Ameisenkolonie nicht gleichmäßig auf alle Quellen verteilt, sondern bevorzugt näher gelegene und effizient erreichbare Nahrungsquellen ausbeutet. Dadurch bestätigt das Experiment die Forschungsfrage und demonstriert die selbstorganisierende Optimierung des Schwarms durch Pheromonkommunikation.


# Experiment 2 – Wiederherstellung von Pheromonspuren nach Unterbrechungen

## Motivation

Ziel dieses Experiments ist die Untersuchung des Verhaltens der Ameisenkolonie bei bereits vorhandenen oder zeitweise unterbrochenen Pheromonspuren. Dabei soll analysiert werden, ob ein vorhandener Trail die Nahrungssuche beschleunigt und ob sich die Kolonie nach einer temporären Störung der Pheromonkommunikation wieder erholen kann.

Im Mittelpunkt steht die Frage, ob die selbstorganisierte Navigation der Ameisen robust gegenüber kurzzeitigen Ausfällen der Pheromone bleibt.

---

## Verlauf der Simulationen

Für das Experiment wurden drei Szenarien betrachtet:

- `coldstart`: Die Simulation startet ohne vorhandene Pheromonspuren.
- `warmstart`: Bereits zu Beginn existiert ein Pheromonpfad zwischen Nest und Nahrungsquelle.
- `outage`: Während der Simulation wird die Pheromonkommunikation für einen kurzen Zeitraum deaktiviert.

Im Coldstart-Szenario bewegen sich die Ameisen zunächst zufällig durch die Gridwelt, bis die erste Ameise die Nahrungsquelle entdeckt und eine stabile Spur etabliert. Im Warmstart-Szenario existiert bereits zu Beginn ein Trail, wodurch die Ameisen wesentlich schneller eine effiziente Route nutzen können.

Im Outage-Szenario ist in Abbildung 2 eine temporäre Unterbrechung der Pheromone sichtbar (grau markierter Bereich). Während dieser Phase sinkt die Lieferungsrate kurzfristig ab. Nach Ende der Unterbrechung stabilisiert sich die Nahrungsausbeutung jedoch erneut, da die Ameisen bestehende Wege wiederfinden und neue Pheromonspuren aufbauen.

---

## Ergebnisse

Die Ergebnisse sind in Abbildung 4, Abbildung 5 und Abbildung 6 dargestellt.

Die kumulative Nahrungsausbeutung in Abbildung 4 zeigt, dass das Warmstart-Szenario die höchste Gesamtmenge an transportierter Nahrung erreicht. Nach 3000 Ticks wurden dort ungefähr 91 Nahrungseinheiten ins Nest geliefert. Im Vergleich dazu erreichten sowohl das Coldstart- als auch das Outage-Szenario etwa 81 Nahrungseinheiten.

Der Unterschied wird besonders deutlich beim Vergleich der ersten erfolgreichen Lieferung (`t_first`) in Abbildung 6. Im Coldstart-Szenario erfolgte die erste Lieferung erst nach ungefähr 268 Ticks, während sie im Warmstart- und Outage-Szenario bereits nach etwa 136 Ticks erreicht wurde. Dies zeigt, dass vorhandene Trails die Exploration deutlich beschleunigen.

Die Rolling Delivery Rate in Abbildung 5 bestätigt diese Beobachtungen zusätzlich. Das Warmstart-Szenario erzeugt frühzeitig hohe Lieferungsraten, da die Ameisen sofort einem vorhandenen Trail folgen können. Im Coldstart-Szenario steigt die Lieferungsrate erst später an, nachdem ein stabiler Pfad aufgebaut wurde.

Im Outage-Szenario ist während der Unterbrechung der Pheromone ein kurzfristiger Einbruch der Lieferungsrate sichtbar. Nach dem Ende der Störung steigt die Aktivität jedoch erneut an und nähert sich wieder den anderen Szenarien an. Die Kolonie ist daher in der Lage, verlorene Trails schrittweise wiederherzustellen.

---

## Interpretation hinsichtlich der Forschungsfrage

Die Ergebnisse zeigen deutlich, dass vorhandene Pheromonspuren die Effizienz der Nahrungssuche erheblich verbessern. Bereits etablierte Trails reduzieren die Explorationszeit und ermöglichen den Ameisen eine schnellere Orientierung zwischen Nest und Nahrungsquelle.

Das Warmstart-Szenario bestätigt somit die Annahme, dass kollektives Wissen in Form von Pheromonen die Gesamtleistung der Kolonie steigert. Durch die direkte Nutzung existierender Pfade werden Nahrung schneller gefunden und effizienter transportiert.

Das Outage-Szenario zeigt zusätzlich, dass das System robust gegenüber temporären Störungen bleibt. Obwohl die Lieferungsrate während der Pheromonunterbrechung sichtbar sinkt, kann sich die Kolonie nach kurzer Zeit wieder stabilisieren. Die Ameisen kompensieren den Verlust der Trails durch erneute Exploration und den Wiederaufbau der Pheromonpfade.

Damit demonstriert das Experiment die Selbstorganisationsfähigkeit des Schwarms. Die Ameisenkolonie ist nicht vollständig von einzelnen Trails abhängig, sondern kann sich dynamisch an Veränderungen der Umgebung anpassen und unterbrochene Kommunikationsstrukturen wiederherstellen.

# Experiment 3 – Einfluss von Pheromonverdunstung und dynamischen Hindernissen

## Motivation

Ziel dieses Experiments ist die Untersuchung der Stabilität und Skalierbarkeit des Ameisenalgorithmus unter schwierigen Umweltbedingungen. Dabei wird analysiert, wie sich unterschiedliche Pheromonverdunstungsraten sowie dynamische Hindernisse auf die Effizienz der Nahrungssuche auswirken.

Im Mittelpunkt steht die Frage, wie robust die selbstorganisierte Navigation der Ameisen gegenüber instabilen oder unterbrochenen Pheromonspuren bleibt.

Hierfür wurden vier Szenarien untersucht:

- `evap_low`: niedrige Verdunstungsrate,
- `evap_mid`: mittlere Verdunstungsrate,
- `evap_high`: hohe Verdunstungsrate,
- `blockade`: dynamische Blockade eines Bereichs der Gridwelt.

---

## Verlauf der Simulationen

Zu Beginn bewegen sich die Ameisen zufällig durch die Umgebung und erzeugen schrittweise Pheromonspuren zwischen Nest und Nahrungsquellen. Je nach Verdunstungsrate bleiben diese Trails unterschiedlich lange stabil.

Im `evap_low`-Szenario bleiben Pheromone lange erhalten. Dadurch entstehen stabile und gut erkennbare Pfade, denen viele Ameisen folgen können. Im `evap_mid`-Szenario verdunsten die Trails schneller, wodurch ein Gleichgewicht zwischen Exploration und Stabilität entsteht.

Im `evap_high`-Szenario verschwinden die Pheromone dagegen sehr schnell. Dadurch verlieren Ameisen häufiger bestehende Wege und müssen erneut explorieren. Dies führt zu instabileren Bewegungsmustern und geringerer Gesamteffizienz.

Zusätzlich wurde im `blockade`-Szenario ein dynamisches Hindernis aktiviert. Während der blockierten Phase war ein Teil der bisher genutzten Route nicht mehr passierbar. Die Ameisen mussten alternative Wege finden und neue Pheromonpfade aufbauen.

---

## Ergebnisse

Die Ergebnisse sind in Abbildung 7, Abbildung 8 und Abbildung 9 dargestellt.

Die kumulative Nahrungsausbeutung in Abbildung 7 zeigt deutliche Unterschiede zwischen den Verdunstungsraten. Das `evap_mid`-Szenario erreichte mit ungefähr 113 Nahrungseinheiten die höchste Gesamtleistung. Das `evap_low`-Szenario erzielte etwa 101 Nahrungseinheiten, während das `evap_high`-Szenario nur ungefähr 53 Nahrungseinheiten transportierte.

Die Ergebnisse zeigen somit, dass sowohl zu geringe als auch zu hohe Verdunstungsraten problematisch sein können. Bei niedriger Verdunstung bleiben zwar stabile Trails bestehen, jedoch können ineffiziente oder veraltete Wege ebenfalls lange erhalten bleiben. Bei hoher Verdunstung verschwinden Pheromonspuren dagegen zu schnell, wodurch die Ameisen häufig erneut explorieren müssen.

Abbildung 9 bestätigt diese Beobachtungen zusätzlich anhand des Zeitpunkts der ersten erfolgreichen Lieferung (`t_first`). Im `evap_mid`-Szenario wurde die erste Quelle bereits nach ungefähr 369 Ticks stabil erreicht, während im `evap_high`-Szenario die zweite Quelle erst nach mehr als 1500 Ticks gefunden wurde. Dies zeigt die Schwierigkeiten beim Aufbau stabiler Trails bei hoher Verdunstung.

Die Rolling Delivery Rate in Abbildung 8 verdeutlicht außerdem die Auswirkungen dynamischer Hindernisse. Im grau markierten Bereich der Blockade sinkt die Lieferungsrate sichtbar ab. Nach einiger Zeit stabilisiert sich die Aktivität jedoch erneut, da alternative Wege gefunden und neue Pheromonpfade etabliert werden.

Das `blockade`-Szenario erreichte insgesamt ungefähr 97 Nahrungseinheiten und liegt damit unterhalb der mittleren Verdunstungsrate, aber deutlich über dem `evap_high`-Szenario. Dies zeigt, dass die Ameisenkolonie auch unter dynamischen Umweltbedingungen weiterhin funktionsfähig bleibt.

---

## Interpretation hinsichtlich der Forschungsfrage

Die Ergebnisse zeigen deutlich, dass die Wahl der Verdunstungsrate einen starken Einfluss auf die Stabilität und Effizienz des Schwarms hat. Eine mittlere Verdunstungsrate stellt den besten Kompromiss zwischen Exploration neuer Wege und Stabilität bestehender Trails dar.

Zu geringe Verdunstung führt dazu, dass veraltete oder ineffiziente Wege zu lange erhalten bleiben. Dadurch reagiert die Kolonie langsamer auf Veränderungen der Umgebung. Zu hohe Verdunstung verhindert dagegen den Aufbau langfristig stabiler Pheromonspuren, wodurch die Orientierung der Ameisen erschwert wird.

Das Experiment mit dynamischen Hindernissen zeigt zusätzlich, dass der Ameisenalgorithmus robust gegenüber Veränderungen der Umgebung bleibt. Trotz temporärer Blockaden gelingt es der Kolonie, alternative Wege zu entdecken und neue Kommunikationsstrukturen aufzubauen. Die selbstorganisierte Navigation funktioniert somit auch unter instabilen Bedingungen weiterhin zuverlässig.

Insgesamt demonstriert das Experiment sowohl die Stärken als auch die Grenzen des Ameisenalgorithmus. Die Ergebnisse verdeutlichen, dass selbstorganisierte Schwärme flexibel auf Veränderungen reagieren können, ihre Effizienz jedoch stark von geeigneten Systemparametern wie der Pheromonverdunstung abhängt.

---

# Appendix

## Abbildung 1 – Kumulative Nahrungsausbeutung (`cumulative.png`)

Zeigt die kumulative Menge der ins Nest transportierten Nahrung pro Quelle über die Zeit. Die näher gelegenen Quellen liefern deutlich mehr Nahrung als weiter entfernte Quellen.

---

## Abbildung 2 – Rolling Delivery Rate (`rate.png`)

Zeigt die zeitabhängige Lieferungsrate der Ameisenkolonie. Nähere Quellen erzeugen stabilere und höhere Lieferungsraten als weiter entfernte Quellen.

---

## Abbildung 3 – Zeitpunkt der ersten Lieferung (`t_first.png`)

Vergleicht den Zeitpunkt der ersten erfolgreichen Lieferung (`t_first`) für alle Quellen. Weiter entfernte Quellen werden signifikant später entdeckt.

---

## Abbildung 4 – Kumulative Nahrungsausbeutung (`cumulative.png`)

Vergleicht die kumulative Menge der ins Nest transportierten Nahrung für Coldstart-, Warmstart- und Outage-Szenarien. Warmstart erreicht die höchste Gesamtleistung.

---

## Abbildung 5 – Rolling Delivery Rate (`rate.png`)

Zeigt die zeitabhängige Lieferungsrate der Ameisenkolonie. Der grau markierte Bereich kennzeichnet die temporäre Pheromonunterbrechung im Outage-Szenario.

---

## Abbildung 6 – Zeitpunkt der ersten Lieferung (`t_first.png`)

Vergleicht den Zeitpunkt der ersten erfolgreichen Lieferung (`t_first`) zwischen den drei Szenarien. Warmstart und Outage erreichen deutlich schnellere erste Lieferungen als Coldstart.

---

## Abbildung 7 – Kumulative Nahrungsausbeutung (`cumulative.png`)

Vergleicht die insgesamt ins Nest transportierte Nahrung für unterschiedliche Verdunstungsraten sowie das Blockade-Szenario.

---

## Abbildung 8 – Rolling Delivery Rate (`rate.png`)

Zeigt die zeitabhängige Lieferungsrate der Ameisenkolonie. Der grau markierte Bereich kennzeichnet die aktive dynamische Blockade im `blockade`-Szenario.

---

## Abbildung 9 – Zeitpunkt der ersten Lieferung (`t_first.png`)

Vergleicht den Zeitpunkt der ersten erfolgreichen Lieferung (`t_first`) zwischen den verschiedenen Verdunstungsraten und dem Blockade-Szenario.
