import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

from algorytmy_grafowe import oblicz_przepustowosc


# Setup
SCIEZKA = Path("Processed_data/powiaty_atrybuty.csv")
KATALOG = Path("Wyniki_grafu_dwudzielnego")
KATALOG.mkdir(parents=True, exist_ok=True)

MIN_POWIATOW = 10

GRANICE_LUDNOSCI = [0,35_000, 70_000, 105_000, 200_000, float("inf")]
KATEGORIE_LUDNOSCI = [
    "do 35 tys.",
    "35-70 tys.",
    "70-105 tys.",
    "105-200 tys.",
    "powyżej 200 tys."
]
KOLORY_LUDNOSCI = [ "#89c776", "#60f13c", "#08e713", "#0DAD3D", "#04802D"]


GRANICE_BEZPIECZENSTWA = [0,    22,     30,     38,     46,     100]
KATEGORIE_BEZPIECZENSTWA = [
    "< 22",
    "22-30",
    "30-38",
    "38-46",
    "46+"
]
KOLORY_BEZPIECZENSTWA = ["#b90038", "#ff3c00", "#ffe600","#52ec5f", "#0bbd64"]


# Wczytanie danych ================================================================================================================
dane = pd.read_csv(SCIEZKA, sep=";", encoding="utf-8-sig")
dane.columns = dane.columns.str.strip()

dane["przepustowosc"] = dane["przestepstwa_na_1000"].apply(oblicz_przepustowosc)


# Klasyfikacja ludności
dane["kategoria_ludnosci"] = pd.cut(dane["ludnosc"],
    bins=GRANICE_LUDNOSCI,
    labels=KATEGORIE_LUDNOSCI,
    include_lowest=True)


# Klasyfikacja bezpieczeństwa
dane["kategoria_bezpieczenstwa"] = pd.cut(dane["przepustowosc"],
    bins=GRANICE_BEZPIECZENSTWA,
    labels=KATEGORIE_BEZPIECZENSTWA,
    include_lowest=True)

# infromacje o grafie dwudzielnym
print("Liczebność ")
print(dane["kategoria_ludnosci"].value_counts().reindex(KATEGORIE_LUDNOSCI, fill_value=0))

print("\n\nLiczebność dla bezpieczeństwa")
print(dane["kategoria_bezpieczenstwa"].value_counts().reindex(KATEGORIE_BEZPIECZENSTWA, fill_value=0))
zaleznosci = pd.crosstab(
    dane["kategoria_ludnosci"],
    dane["kategoria_bezpieczenstwa"]
).reindex(
    index=KATEGORIE_LUDNOSCI,
    columns=KATEGORIE_BEZPIECZENSTWA,
    fill_value=0)
print('\n'*2)
print(zaleznosci)
print("\n"*2)
# Budowa grafu dwudzielnego
graf = nx.Graph(nazwa="Graf dwudzielny kategorii ludności i bezpieczeństwa")

# Wierzchołki kategorii ludności
for i, kategoria in enumerate(KATEGORIE_LUDNOSCI):
    graf.add_node(
        f"ludnosc:{kategoria}",
        nazwa=kategoria,
        typ="ludnosc",
        bipartite=0,
        kolor=KOLORY_LUDNOSCI[i],
        liczba_powiatow=int((dane["kategoria_ludnosci"] == kategoria).sum()))

# Wierzchołki kategorii bezpieczeństwa
for i, kategoria in enumerate(KATEGORIE_BEZPIECZENSTWA):
    graf.add_node(
        f"bezpieczenstwo:{kategoria}",
        nazwa=kategoria,
        typ="bezpieczenstwo",
        bipartite=1,
        kolor=KOLORY_BEZPIECZENSTWA[i],
        liczba_powiatow=int((dane["kategoria_bezpieczenstwa"] == kategoria).sum()))
# Krawędzie między kategoriami
for ludnosc in KATEGORIE_LUDNOSCI:
    for bezpieczenstwo in KATEGORIE_BEZPIECZENSTWA:
        liczba = int(zaleznosci.loc[ludnosc, bezpieczenstwo])

        if liczba >= MIN_POWIATOW:
            graf.add_edge(
                f"ludnosc:{ludnosc}",
                f"bezpieczenstwo:{bezpieczenstwo}",
                weight=liczba,
                liczba_powiatow=liczba
            )

# Wizualizacja grafu dwudzielnego
pozycje = {}

# Kategorie ludności po lewej
for i, kategoria in enumerate(KATEGORIE_LUDNOSCI):
    pozycje[f"ludnosc:{kategoria}"] = (0, -i)

# Kategorie bezpieczeństwa po prawej
for i, kategoria in enumerate(KATEGORIE_BEZPIECZENSTWA):
    pozycje[f"bezpieczenstwo:{kategoria}"] = (4, -i * (len(KATEGORIE_LUDNOSCI) - 1) / (len(KATEGORIE_BEZPIECZENSTWA) - 1))

fig, ax = plt.subplots(figsize=(16, 10))

nx.draw_networkx_edges(
    graf,
    pozycje,
    width=[1 + graf[u][v]["weight"] / 5 for u, v in graf.edges],
    edge_color="#001AFF",
    alpha=0.5,
    ax=ax)

for kategorie, kolory in [(KATEGORIE_LUDNOSCI, KOLORY_LUDNOSCI),(KATEGORIE_BEZPIECZENSTWA, KOLORY_BEZPIECZENSTWA)]:
    prefiks = "ludnosc" if kategorie == KATEGORIE_LUDNOSCI else "bezpieczenstwo"
    wezly = [f"{prefiks}:{k}" for k in kategorie]

    nx.draw_networkx_nodes(
        graf,
        pozycje,
        nodelist=wezly,
        node_color=kolory,
        node_size=2500,
        edgecolors="#333333",
        linewidths=1.5,
        ax=ax)

etykiety = {n: graf.nodes[n]["nazwa"] for n in graf.nodes}

nx.draw_networkx_labels(
    graf,
    pozycje,
    labels=etykiety,
    font_size=9,
    font_weight="bold",
    ax=ax
)

# Liczba powiatów na krawędziach
for u, v, a in graf.edges(data=True):
    x1, y1 = pozycje[u]
    x2, y2 = pozycje[v]

    ax.text(
        x1 + (x2 - x1) * 0.15,
    y1 + (y2 - y1) * 0.15,
        str(a["weight"]),
        fontsize=10,
        fontweight="bold",
        ha="center",
        va="center",
        bbox=dict(facecolor="white", edgecolor="#999999", alpha=0.95, boxstyle="round,pad=0.3"))

ax.set_title("Graf dwudzielny: kategorie ludności i bezpieczeństwa", fontsize=14)
ax.axis("off")
plt.tight_layout()
plt.savefig(KATALOG / "graf_dwudzielny.png", dpi=300, bbox_inches="tight")


# PROJEKCJE ===================================================================================================================================
lewa = [f"ludnosc:{k}" for k in KATEGORIE_LUDNOSCI]
prawa = [f"bezpieczenstwo:{k}" for k in KATEGORIE_BEZPIECZENSTWA]

projekcja_ludnosci = nx.bipartite.weighted_projected_graph(graf, lewa)
projekcja_bezpieczenstwa = nx.bipartite.weighted_projected_graph(graf, prawa)


# Funkcja wizualizacji projekcji
def wizualizuj_projekcje(projekcja, kategorie, prefiks, kolory, tytul, nazwa_pliku):
    wezly = [f"{prefiks}:{k}" for k in kategorie]
    pozycje = nx.circular_layout(projekcja, scale=2)
    fig, ax = plt.subplots(figsize=(12, 9))
    nx.draw_networkx_edges(
        projekcja,
        pozycje,
        width=[
            1.5 + projekcja[u][v]["weight"] * 2
            for u, v in projekcja.edges
        ],
        edge_color="#A50097",
        alpha=0.65,
        ax=ax)

    wezly = [f"{prefiks}:{k}" for k in kategorie]

    nx.draw_networkx_nodes(
        projekcja,
        pozycje,
        nodelist=wezly,
        node_color=kolory,
        node_size=2500,
        edgecolors="#333333",
        linewidths=1.5,
        ax=ax)

    etykiety = {n: graf.nodes[n]["nazwa"] for n in projekcja.nodes}

    nx.draw_networkx_labels(
        projekcja,
        pozycje,
        labels=etykiety,
        font_size=9,
        font_weight="bold",
        ax=ax)

    for u, v, a in projekcja.edges(data=True):
        x1, y1 = pozycje[u]
        x2, y2 = pozycje[v]

        ax.text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            str(a["weight"]),
            fontsize=10,
            fontweight="bold",
            ha="center",
            va="center",
            bbox=dict(facecolor="white", edgecolor="#999999", alpha=0.95, boxstyle="round,pad=0.3"))

    ax.set_title(tytul, fontsize=14)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(KATALOG / nazwa_pliku, dpi=300, bbox_inches="tight")


# Projekcja kategorii ludności
wizualizuj_projekcje(
    projekcja_ludnosci,
    KATEGORIE_LUDNOSCI,
    "ludnosc",
    KOLORY_LUDNOSCI,
    "Projekcja kategorii ludności",
    "projekcja_ludnosci.png")

# Projekcja kategorii bezpieczeństwa
wizualizuj_projekcje(
    projekcja_bezpieczenstwa,
    KATEGORIE_BEZPIECZENSTWA,
    "bezpieczenstwo",
    KOLORY_BEZPIECZENSTWA,
    "Projekcja kategorii bezpieczeństwa",
    "projekcja_bezpieczenstwa.png")
print("Wyniki zapisano w:", KATALOG.resolve(),"\n")