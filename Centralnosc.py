import networkx as nx
import json
from networkx.readwrite import node_link_graph
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from algorytmy_grafowe import oblicz_przepustowosc


# Setup
with open("Graf_reprezentacja/graf_powiatow.json", "r", encoding="utf-8") as plik:
    graf = node_link_graph(json.load(plik), edges="edges")
graf = nx.Graph(graf)
graf.remove_edges_from(nx.selfloop_edges(graf))

def nazwa(wezel):
    """zwrócenie nazwy węzła sieci"""
    return graf.nodes[wezel].get("Nazwa", graf.nodes[wezel].get("nazwa", str(wezel)))

PROG_NIEBEZPIECZENSTWA = 33
PROG_BEZPIECZENSTWA = 40


# Częśc wykonawcza
print("Sprawdzenie komunikacji grafu sieci bezpiecznych i sieci przestępczych")

wskaznik_p = {wezel: float(atrybuty["przestepstwa_na_1000"]) for wezel, atrybuty in graf.nodes(data=True)}
przepustowosci = {wezel: oblicz_przepustowosc(wskaznik) for wezel, wskaznik in wskaznik_p.items()}

# Podział na kategorie
wezly_przestepcze = {wezel for wezel, przepustowosc in przepustowosci.items()
    if przepustowosc < PROG_NIEBEZPIECZENSTWA}
    
wezly_bezpieczne = {wezel for wezel, przepustowosc in przepustowosci.items()
    if przepustowosc > PROG_BEZPIECZENSTWA}

wezly_posrednie = (set(graf.nodes) - wezly_przestepcze - wezly_bezpieczne)

# Log podziału
print("\nPodział kategorii bezpieczeństwa")
print(f"Próg niebezpieczeństwa: < {PROG_NIEBEZPIECZENSTWA}")
print(f"Próg bezpieczeństwa: > {PROG_BEZPIECZENSTWA}")
print("Węzły przestępcze:", len(wezly_przestepcze))
print("Węzły zwyczajne:", len(wezly_posrednie))
print("Węzły bezpieczne:", len(wezly_bezpieczne))

def miary_sieci(g):
    """Obsługa wszystkich miar"""
    if g.number_of_nodes() == 0:
        pass

    centralnosci = {
        "Stopień": nx.degree_centrality(g),
        "Pośredniość": nx.betweenness_centrality(g),
        "Bliskość": nx.closeness_centrality(g),
        "Wektor własny": nx.eigenvector_centrality(g, max_iter=1000),
        "PageRank": nx.pagerank(g)}

    skladowe = list(nx.connected_components(g))
    najwieksza = g.subgraph(max(skladowe, key=len)).copy()

    if najwieksza.number_of_nodes() >= 2:
        wierzcholkowa = nx.node_connectivity(najwieksza)
        krawedziowa = nx.edge_connectivity(najwieksza)
    else:
        wierzcholkowa = 0
        krawedziowa = 0

    kliki = list(nx.find_cliques(g))
    najwieksza_klika = max(kliki, key=len, default=[])

    return {"wezly": g.number_of_nodes(), "krawedzie": g.number_of_edges(),
            "skladowe": len(skladowe), "najwieksza": najwieksza.number_of_nodes(),
            "wierzcholkowa": wierzcholkowa, "krawedziowa": krawedziowa,
            "centralnosci": centralnosci, "liczba_klik": len(kliki),
            "rząd_kliki": len(najwieksza_klika), "klika": najwieksza_klika, "kliki": kliki}

def parametry_polaczen(g, wezly_docelowe):
    skladowe = list(nx.connected_components(g))
    liczebnosc_docelowych = [len(skladowa & wezly_docelowe) for skladowa in skladowe]
    najwieksza = max(liczebnosc_docelowych, default=0)
    return {"liczba_skladowych": len(skladowe),"najwieksza_skladowa_docelowa": najwieksza,
            "udzial_w_najwiekszej_skladowej": (najwieksza / len(wezly_docelowe) if wezly_docelowe else 0)}

def porownaj_miary(po):
    print("\nParametry sieci")
    print(f"Liczba wierzchołków: {po['wezly']}")
    print(f"Liczba krawędzi: {po['krawedzie']}")
    print(f"Liczba składowych: {po['skladowe']}")
    print(f"Największa składowa: {po['najwieksza']}")
    print(f"Spójność wierzchołkowa: {po['wierzcholkowa']}")
    print(f"Spójność krawędziowa: {po['krawedziowa']}")

    print("\nCentralności - Top 10")
    for miara, dane in po["centralnosci"].items():
        print(f"\n{miara}")
        top10 = sorted(dane.items(), key=lambda x: x[1], reverse=True)[:10]
        for wezel, wartosc in top10:
            print(f"{nazwa(wezel)}: {wartosc:.6f}")

    print("\nKliki")
    print(f"Liczba klik maksymalnych: {po['liczba_klik']}")
    print(f"Rząd największej kliki: {po['rząd_kliki']}")
    print("Największa klika:")
    for wezel in po["klika"]:
        print(" ", nazwa(wezel))

def wizualizuj_usuwanie(g_przed, g_po,pozycje, tytul,plik):
    kolory = {"bezpieczne": "#00a769","przestępcze": "#ff0000","posrednie": "#323FFD"}
    fig, osie = plt.subplots(1, 2, figsize=(18, 9))

    for os, graf_do_narysowania, podtytul in ((osie[0], g_przed, "Przed usunięciem"),(osie[1], g_po, "Po usunięciu")):
        kolory_wezlow = []
        for wezel in graf_do_narysowania.nodes:
            if wezel in wezly_bezpieczne:
                kolory_wezlow.append(kolory["bezpieczne"])
            elif wezel in wezly_przestepcze:
                kolory_wezlow.append(kolory["przestępcze"])
            else:
                kolory_wezlow.append(kolory["posrednie"])

        nx.draw_networkx_edges(graf_do_narysowania, pozycje, ax=os, width=0.5, alpha=0.3)

        nx.draw_networkx_nodes(graf_do_narysowania, pozycje, ax=os, node_size=20, node_color=kolory_wezlow)
    
        os.set_title(f"{podtytul}\nWęzły: {graf_do_narysowania.number_of_nodes()}    Krawędzie: {graf_do_narysowania.number_of_edges()}")
        os.set_axis_off()
    
    fig.suptitle(tytul, fontsize=10)
    
    fig.legend(handles=[
            Patch(color=kolory["bezpieczne"], label="Bezpieczne"),
            Patch(color=kolory["przestępcze"], label="Przestępcze"),
            Patch(color=kolory["posrednie"], label="Pośrednie")],loc="lower center",ncol=3)
    
    fig.savefig(plik, dpi=200, bbox_inches="tight")
    plt.show()
    plt.close(fig)

pozycje_grafu = nx.spring_layout(graf, seed=30)
katalog_grafik = Path("Graf_reprezentacja")
katalog_grafik.mkdir(parents=True, exist_ok=True)

scenariusze = [("\nUsunięcie bezpiecznych węzłów",wezly_bezpieczne,wezly_przestepcze,"Usunięcie_bezpiecznych.png"),
("\nUsunięcie niebezpiecznych węzłów",wezly_przestepcze,wezly_bezpieczne,"Usunięcie_niebezpiecznych.png")]

for tytul, wezly_usuwane, wezly_docelowe, plik in scenariusze:
    print(tytul)
    graf_po_edycji = graf.copy()
    graf_po_edycji.remove_nodes_from(wezly_usuwane)
    miary_po_edycji = miary_sieci(graf_po_edycji)
    porownaj_miary(miary_po_edycji)
    polaczenia = parametry_polaczen(graf_po_edycji,wezly_docelowe)

    print("\nPołączenia węzłów docelowych")
    print("Liczba składowych całej pozostałej sieci:",polaczenia["liczba_skladowych"])
    print("Węzły docelowe w największej składowej:",polaczenia["najwieksza_skladowa_docelowa"])
    print(f"Udział węzłów docelowych w największej składowej:{polaczenia['udzial_w_najwiekszej_skladowej']:.1%}")

    wizualizuj_usuwanie(graf,graf_po_edycji,pozycje_grafu,
        (f"{tytul}\nProgi: niebezpieczne < {PROG_NIEBEZPIECZENSTWA}\nbezpieczne > {PROG_BEZPIECZENSTWA}"),katalog_grafik / plik)

# analiza wycinka
PROG_NIEBEZPIECZENSTWA = 33
PROG_BEZPIECZENSTWA = 35

if PROG_BEZPIECZENSTWA < PROG_NIEBEZPIECZENSTWA:
    PROG_NIEBEZPIECZENSTWA, PROG_BEZPIECZENSTWA = PROG_BEZPIECZENSTWA, PROG_NIEBEZPIECZENSTWA

if PROG_NIEBEZPIECZENSTWA <= 0:
    PROG_NIEBEZPIECZENSTWA = 10
if PROG_BEZPIECZENSTWA <= 0:
    PROG_BEZPIECZENSTWA = 10

print(f"Próg niebezpieczeństwa: {PROG_NIEBEZPIECZENSTWA}")
print(f"Próg bezpieczeństwa: {PROG_BEZPIECZENSTWA}")

wezly_przestepcze = {wezel for wezel, wskaznik in przepustowosci.items()
    if wskaznik < PROG_NIEBEZPIECZENSTWA}

wezly_bezpieczne = {wezel for wezel, wskaznik in przepustowosci.items()
    if wskaznik > PROG_BEZPIECZENSTWA}

wezly_posrednie = set(graf.nodes) - wezly_przestepcze - wezly_bezpieczne

def wizualizuj_onecat_graf(g, tytul, kolor, plik):
    plt.figure(figsize=(10, 10))
    pozycje = nx.spring_layout(g, seed=30)

    nx.draw_networkx_edges(g, pozycje, width=0.7, alpha=0.4)
    nx.draw_networkx_nodes(g, pozycje, node_size=35, node_color=kolor)

    plt.title(f"{tytul}\nWęzły: {g.number_of_nodes()} | Krawędzie: {g.number_of_edges()}")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(katalog_grafik / plik, dpi=200, bbox_inches="tight")
    plt.show()
    plt.close()

graf_bezpieczne = graf.subgraph(wezly_bezpieczne).copy()
graf_niebezpieczne = graf.subgraph(wezly_przestepcze).copy()

print("\nWizualizacja jednej kategorii powiatów")

wizualizuj_onecat_graf(graf_bezpieczne, "Graf powiatów bezpiecznych", "#00a769", "Graf_bezpieczne.png")
wizualizuj_onecat_graf(graf_niebezpieczne, "Graf powiatów przestępczych", "#ff0000", "Graf_przestępczych.png")