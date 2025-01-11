# μ-scale: čelna mikrostoritev

Ta repozitorij vsebuje izvorno kodo čelne mikrostoritve, ki je del projekta μ-scale (microscale)
(glavni repozitorij je na voljo [tukaj](https://github.com/RSO-2024-Mikrovrtickarja/micro-scale)).

## 1. Arhitektura in CI/CD
Mikrostoritev je razvita z uporabo ogrodja [Django](https://www.djangoproject.com/) v [Pythonu](https://www.python.org/) 3.12+,
pri čemer za upravljanje odvisnosti in virtualnega Python okolja projekt uporablja orodje [Poetry](https://python-poetry.org/).

Mikrostoritev ob zagonu na vratih `8000` izpostavi:
- uporabniški vmesnik, ki uporabniku omogoča dostop do vseh razvitih funkcionalnosti 
  (registracija, prijava, nalaganje, ogled, prenos, procesiranje fotografij, ...).
- dodatni HTTP API, ki omogoča le dostop do podatkov o zdravju (`/health`).

Ta mikrostoritev interno komunicira neposredno z ostalimi mikrostoritvami (torej gre vse preko te
mikrostoritve, namesto da bi uporabnikov brskalnik poklical storitev sam). 

Ob spremembah na glavni veji (`main`) se v tem GitHub repozitoriju proži CI/CD cevovod, 
ki aplikacijo zapakira v vsebnik Docker in naloži na vsebniški register na oblaku Azure, 
kjer je projekt nameščen. Za več podrobnosti o namestitvi glej glavni repozitorij [tukaj](https://github.com/RSO-2024-Mikrovrtickarja/micro-scale).


## 2. Lokalno nameščanje
Za lokalno nameščanje, razvijanje in testiranje je potrebno namestiti sledeča orodja (navodila so prilagojena razvijanju na operacijskem sistemu Windows):
- [Python](https://www.python.org/) 3.12 ali več,
- [Poetry](https://python-poetry.org/) 1.8 ali več.

Na tej točki poženemo instanco strežnika RabbitMQ (enako instanco moramo uporabiti tudi pri mikrostoritvi shranjevanja fotografij).

Sedaj skopiramo `.env.TEMPLATE` v `.env` in izpolnimo manjkajoče ali spremenimo napačne
nastavitve, kot so naslovi ostalih mikrostoritev in API ključ za dostop do zunanje storitve, ki nam omogoča večanje resolucije fotografij.

Sedaj izvedemo sledeče ukaze:
```bash
$ poetry install --no-root
$ poetry run python main.py
```

S tem bomo zagnali našo mikrostoritev, ki bo izpostavila strežnik HTTP na vratih `8000`.


> Za podrobnejše korake, kar se tiče namestitve v Kubernetes okolje, 
> glej glavni repozitorij [tukaj](https://github.com/RSO-2024-Mikrovrtickarja/micro-scale).   


### 2.1 Konfiguracija
To mikrostoritev se konfigurira preko okoljskih spremenljivk, opisanih spodaj:
```bash
# Naslov (IP ali domena), kjer se nahaja uporabniška mikrostoritev.
USERS_HOST=localhost
# Številka vrat, kjer je dostopna omenjena mikrostoritev.
USERS_PORT=8002

# Naslov (IP ali domena), kjer se nahaja mikrostoritev za hranjenje fotografij.
PHOTO_STORAGE_HOST=localhost
# Številka vrat, kjer je dostopna omenjena mikrostoritev.
PHOTO_STORAGE_PORT=8001

# API ključ, ki omogoča dostop do aplikacijskega vmesnika zunanje storitve "https://picsart.io/".
UPSCALE_API_KEY=myapikey
```
