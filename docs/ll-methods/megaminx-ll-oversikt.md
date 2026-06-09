# Megaminx LL – Metodeoversikt

> Gjelder for Petrus-basert løsning: EO ferdig under F2L → EOLL hoppes over.

---

## Metodelandskapet

| Metode | Alg (u/invers) | CO apps typisk | Total apps | Læringsterskel |
|--------|---------------|----------------|------------|----------------|
| 2 – Ren intuisjon | 2 | 2–4 | 6–12 | Lav alg, høy rom-forståelse |
| **1 – Sune+Niklas+EP** | **3** | **2–4** | **5–8** | **Lav, bygger på 3×3** |
| 3 – +Anti-Sune | 4 | 1–2 | 4–6 | Marginal ekstra |
| 4 – Full OCLL + EP + Niklas | 9 (min) | 1 | 3–5 | Moderat |
| 5 – Full 4LLL | 27 | 1 | 3–4 | Høy |

---

## Metode 1 – Sune + Niklas + EP (3 alg)

```
EP → CP → CO
```

Bruker kun det du kjenner fra 3×3 + én ny EP-alg.
Se `megaminx-ll-metode1-3.md` for fullstendig referanse.

**Alger:**
- EP: `FR++ U-- FR-- U- FR++ U-- FR--`
- CP: Niklas `FR U- FL- U FR- U- FL U`
- CO: Sune `FR U FR- U FR U++ FR-`

---

## Metode 2 – Ren intuisjon (2 alg)

```
EP → CO → CP (intuitivt)
```

Erstatt Niklas med intuitiv commutator-innsetting for CP. Prinsipp:

> Finn hjørne på feil plass → sett det over riktig slot → AUF → trekk tilbake

Eksemel: `(FR- U FR)  AUF  (FR- U- FR)` — bygg selv fra situasjonen.

**Alger:** Sune + EP  
**Tradeoff:** CP tar 3× lengre tid uten fast alg, men null ekstra memorisering.

---

## Metode 3 – +Anti-Sune (4 alg)

Identisk med Metode 1, men legg til Anti-Sune eksplisitt. Halverer CO worst-case fra 5 apps til 2.

```
Anti-Sune: FR- U- FR U- FR- U-- FR
```

Se `megaminx-ll-metode1-3.md`.

---

## Metode 4 – Full OCLL + EP + Niklas (~9 alg)

```
OCLL (1-look) → EPLL → CPLL (Niklas)
```

16 OCLL-algoritmer fra SpeedCubeDB. CO alltid 1 app.  
Se `megaminx-ll-metode4.md` for alle algoritmer.

---

## Metode 5 – Full 4LLL (~27 alg)

```
OCLL (16) + EPLL (5) + CPLL (15) = 36 alg  →  med EOLL-skip: 27 relevante
```

Standard intermediær-metode. Sub-2-min løsere.

---

## Veiledning: hvilken metode?

```
Ny til Megaminx LL
  → Start med Metode 1 (lær EP-algen, bruk Sune og Niklas du kan)

Etter ~20 løsninger
  → Legg til Anti-Sune (Metode 3) — marginal kostnad, merkbar gevinst

Vil raskere uten masse alger?
  → Lær 5 EPLL-alger (Metode 4 delvis: OCLL+fullEPLL+Niklas = 8 alg)

Seriøs speedsolving
  → Full Metode 4 eller 5 (27+ alg)
```

---

## Matematisk bakgrunn

- **CO:** 16 tilfeller (alle jevne orienteringer av 5 hjørner, sum ≡ 0 mod 3, unntatt identitet)
- **EP:** 5 tilfeller (A₅-undergruppe av 5 kanter, jevne permutasjoner)
- **CP:** 4 tilfellstyper (A₅): identitet / 3-sykel (20) / dobbel-transposisjon (15) / 5-sykel (24)

### ⚠️ Megaminx ≠ 3×3 for CP

CP-algoritmer på Megaminx tvister de 3 syklerte hjørnene med **+1 hver** (72°-geometri).  
På 3×3 er CPLL orienterings-bevarende (90°-geometri kansellerer deltaene).  
**Løsning:** CO gjøres alltid sist (metodene 1–4 over respekterer dette).

---

*Algoritmer verifisert via Python Megaminx-simulator + SpeedCubeDB.*
