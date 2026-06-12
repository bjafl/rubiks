# Megaminx — notasjon, navngivning og grunntrekk

Referansedokument for notasjonen brukt i modellen (`megaminx.py`) og hvordan den forholder seg til community-konvensjon og WCA.

## Referansestilling

Alle navn og retninger i dette dokumentet forutsetter denne orienteringen:

- **U opp**, med spissen på U-pentagonet pekende **fra deg**.
- Da vender en av U-kantene mot deg, og **F er fasaden under den kanten** — den peker mot deg, lett skråstilt, i øvre band.
- Spissen på D peker dermed **mot deg** (bandene er speilvendt forskjøvet).

En megaminx har ikke ett midtbelte som en kube, men **to band forskjøvet 36°** i forhold til hverandre: et øvre band på 5 fasader rundt U og et nedre band på 5 fasader rundt D.

## Fasadenavn

| Navn | Plassering (referansestilling) |
|---|---|
| U | Topp |
| F | Mot deg, øvre band |
| R | Høyre for F, øvre band |
| L | Venstre for F, øvre band |
| BR | Bak til høyre, øvre band |
| BL | Bak til venstre, øvre band |
| dR | Nede til høyre foran, nedre band (berører F og R) |
| dL | Nede til venstre foran, nedre band (berører F og L) |
| B | Rett bak, nedre band |
| dBR | Bak til høyre, nedre band |
| dBL | Bak til venstre, nedre band |
| D | Bunn |

Merk at dR/dL ikke ligger på samme høyde som F — de sitter *nede* foran og deler F sin nedre høyre/venstre kant. Det er forskyvningen mellom bandene som gjør at nedre band trenger egne navn i stedet for et «midtnivå».

**Rekkefølge rundt U**, med klokken sett ovenfra: F → L → BL → BR → R. (Kontraintuitivt for mange: med klokken *ovenfra* går fra F mot venstre, ikke høyre.)

### Motstående fasader

| Fasade | Motstående |
|---|---|
| U | D |
| F | B |
| R | dBL |
| L | dBR |
| BR | dL |
| BL | dR |

Hver øvre-band-fasade er motstående til en nedre-band-fasade «diagonalt bak-ned» på motsatt side. Motstående fasader deler ingen brikker og kommuterer derfor som trekk. Vanlig felle: motstående til DR er BL, ikke L.

## Trekknotasjon

Et fasadetrekk dreier én fasade med tilhørende lag. Hver fasade har orden 5 (fem 72°-steg), så det finnes fire distinkte trekk per fasade:

| Notasjon | Betydning |
|---|---|
| X | 72° **med** klokken |
| X2 | 144° med klokken |
| X2' | 144° **mot** klokken |
| X' | 72° mot klokken |

**Klokkeretning er alltid definert sett utenfra fasaden** — samme regel som på 3×3. X2' og X2 er hverandres inverser; X2' = X·X·X om man vil.

### Hva et trekk gjør

En clockwise dreining av fasade X sykler de 5 hjørnene og 5 kantene rundt X ett hakk. Eksempel **R** (med klokken sett fra høyre):

```
Kanter:  F/R → R/U → BR/R → dBR/R → dR/R → (tilbake til F/R)
Hjørner: dR/F/R → F/U/R → BR/R/U → BR/dBR/R → dBR/dR/R → ...
```

Intuisjonen er den samme som på 3×3: R tar brikkene i F-kolonnen **opp** mot U, U-lagsbrikkene bakover mot BR, og så ned og rundt. R' går motsatt vei (U-laget ned mot F).

Tilsvarende for U: en clockwise U flytter front-brikkene mot **venstre** (F-kanten går til L-posisjonen), som på 3×3.

## WCA scramble-notasjon

WCA definerer overraskende lite for megaminx: kun U, U' og scramble-trekkene **R++, R--, D++, D--** (Pochmann-notasjon). Det finnes ingen offisiell WCA-navngiving av alle 12 fasader — tabellen over er community-konvensjon.

Viktige punkter om scramble-notasjonen:

- **Klokke-konvensjonen er identisk** med fasadetrekk: med klokken sett utenfra langs aksen på den navngitte siden. R++ er med klokken sett fra høyre, D++ med klokken sett nedenfra. Ingen speilvending å passe på.
- **++ / -- betyr alltid 2/5 omdreining (144°)**, aldri 72°. -- tilsvarer ' med dobbel mengde innbakt.
- **R og D er ikke fasadetrekk.** R++ roterer *alt unntatt venstre slice*; D++ alt unntatt topp-slicen. Relativt til faste sentre er R++ ekvivalent med venstre-fasaden dreid 144° mot klokken pluss en helkroppsrotasjon 144° med klokken. Oversetter man R++ naivt til et fasadetrekk er det lett å få fortegnsfeil — retningen «snur» fordi referanserammen byttes, ikke fordi WCA definerer klokken annerledes.
- En offisiell scramble består av sju linjer, hver med ti vekslende R/D-trekk avsluttet med U eller U'.

For å parse WCA-scrambles i en cubie-modell uten sentre kreves derfor rotasjonssporing (eller eksplisitte sentre) i tillegg til selve fasadetrekkene.

## Modellreferanse

I `megaminx/` (pakken splittet i `cube.py`, `model.py`, `moves.py` m.fl.) representeres tilstanden som `(cp, co, ep, eo)` — 20 hjørner og 30 kanter, hver med posisjon og orientering (mod 3 / mod 2). Slots identifiseres ved fasade-tupler i alfabetisk kanonisk form, f.eks. hjørnet `('F', 'U', 'R')` ↔ F/U/R. Et trekk er selv en tilstandstransformasjon, så komposisjon av trekk og anvendelse på en tilstand er samme operasjon (`then`). Orienteringsreferansen per slot er første fasade i kanonisk tuppel; for arbeid med last layer kan referansen med fordel byttes til U-fasaden for LL-slotene, slik at co = 0 betyr «U-merket opp».

### `UL`/`UR` i algoritme-notasjon

Løse-dokumentene bruker `UL` og `UR` som kortform for de øvre-band-fasadene til venstre og høyre:

| Kortform i docs | Modellnavn | Plassering |
|---|---|---|
| `UL` | `BL` | Øvre band, bak-venstre (adjacent til U og L) |
| `UR` | `BR` | Øvre band, bak-høyre (adjacent til U og R) |

I kode og modell brukes alltid `BL`/`BR`. `UL`/`UR` er kun human-lesbar notasjon i metodedokumentene.
