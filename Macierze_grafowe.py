import json
import networkx as nx
import pandas as pd
import numpy as np
from pathlib import Path
from networkx.readwrite import json_graph

# Ścieżki
SCIEZKA_GRAFU_JSON = Path("Graf_reprezentacja/graf_powiatow.json")
SCIEZKA_WYNIKOW = Path("Graf_reprezentacja")

def generuj_macierze(sciezka_json, sciezka_wynikow):
    # Wczytanie grafu
    with sciezka_json.open("r", encoding="utf-8") as plik:
        graf = json_graph.node_link_graph(json.load(plik))

    wezly = list(graf.nodes())
    lacza = list(graf.edges())

    nazwy_powiatow = [graf.nodes[v].get("Nazwa", str(v)) for v in wezly]

    nazwy_krawedzi = [f"{graf.nodes[u].get('Nazwa', u)} -> "
        f"{graf.nodes[v].get('Nazwa', v)}"
        for u, v in lacza]

    # Macierz sąsiedztwa
    macierz_sasiedztwa = nx.to_numpy_array(
        graf, nodelist=wezly, weight=None, dtype=int)

    # Macierz incydencji
    indeksy_wezlow = {v: i for i, v in enumerate(wezly)}
    macierz_incydencji = np.zeros(
        (len(wezly), len(lacza)), dtype=int)

    for j, (u, v) in enumerate(lacza):
        macierz_incydencji[indeksy_wezlow[u], j] = 2 if u == v else 1
        if u != v:
            macierz_incydencji[indeksy_wezlow[v], j] = 1

    # Utworzenie tabel z etykietami
    macierze = {
        "macierz_sasiedztwa.csv": pd.DataFrame(
            macierz_sasiedztwa,
            index=nazwy_powiatow,
            columns=nazwy_powiatow),

        "macierz_incydencji.csv": pd.DataFrame(
            macierz_incydencji,
            index=nazwy_powiatow,
            columns=nazwy_krawedzi)}

    # Zapis wyników
    sciezka_wynikow.mkdir(parents=True, exist_ok=True)

    for nazwa_pliku, macierz in macierze.items():
        macierz.to_csv(sciezka_wynikow / nazwa_pliku,
            encoding="utf-8-sig")
        print(f"Zapisano: {nazwa_pliku} \n \t Wymiary: {macierz.shape}\n")

    print(f"Liczba wierzchołków: {graf.number_of_nodes()}")
    print(f"Liczba krawędzi: {graf.number_of_edges()}")
    print(f"Macierze zapisano w: {sciezka_wynikow}")

generuj_macierze(SCIEZKA_GRAFU_JSON, SCIEZKA_WYNIKOW)