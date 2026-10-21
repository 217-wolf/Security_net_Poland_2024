from pathlib import Path
import json

import networkx as nx
from networkx.readwrite import json_graph
import pandas as pd
import heapq

SCIEZKA_GRAFU = (Path(__file__).resolve().parent/"Processed_data"/ "graf_powiatow.json")


def wczytaj_graf() -> nx.Graph:
    "Wczytanie grafu z pliku JSON"
    with SCIEZKA_GRAFU.open("r", encoding="utf-8") as plik:
        dane = json.load(plik)
    return json_graph.node_link_graph(dane)


def znajdz_wezel(graf: nx.Graph, nazwa: str):
    """Na podstawie nazwy powiatu zwrócenie identyfikatora"""
    znalezione = [wezel
        for wezel, atrybuty in graf.nodes(data=True)
        if atrybuty.get("nazwa", "").casefold() == nazwa.casefold()]

    if not znalezione:
        raise ValueError(f"Nie znaleziono powiatu: {nazwa}")

    if len(znalezione) > 1:
        raise ValueError(f"Nazwa nie jest jednoznaczna: {nazwa}")
    return znalezione[0]


def najkrotsza_sciezka(graf: nx.Graph, start: str, koniec: str):
    """Wyznacza najkrótszą ścieżkę między powiatami - geograficznie."""
    zrodlo = znajdz_wezel(graf, start)
    cel = znajdz_wezel(graf, koniec)
    sciezka = nx.shortest_path(graf, source=zrodlo, target=cel)
    return [graf.nodes[wezel].get("nazwa", str(wezel)) for wezel in sciezka]



def najkrótsza_sciezka_po_atrybucie(graf, start, koniec, atrybut="przestepstwa"):
    zrodlo = znajdz_wezel(graf, start)
    cel = znajdz_wezel(graf, koniec)

    kolejka = [(0, zrodlo)]
    koszty = {zrodlo: 0}
    poprzednicy = {}

    while kolejka:
        koszt, wezel = heapq.heappop(kolejka)
        if wezel == cel:
            break
        if koszt > koszty[wezel]:
            continue
        for sasiad in graf.neighbors(wezel):
            wartosc = graf.nodes[sasiad].get(atrybut)
            if wartosc is None:
                continue

            nowy_koszt = koszt + float(wartosc)

            if nowy_koszt < koszty.get(sasiad, float("inf")):
                koszty[sasiad] = nowy_koszt
                poprzednicy[sasiad] = wezel
                heapq.heappush(kolejka, (nowy_koszt, sasiad))
    if cel not in koszty:
        raise ValueError("Nie znaleziono ścieżki.")

    sciezka = []
    wezel = cel

    while wezel != zrodlo:
        sciezka.append(wezel)
        wezel = poprzednicy[wezel]

    sciezka.append(zrodlo)
    sciezka.reverse()

    return {"sciezka": [graf.nodes[w]["nazwa"] for w in sciezka],
        "koszt": koszty[cel]}

def analiza_eulerowska(graf: nx.Graph):
    graf_bez_izolatow = graf.subgraph([wezel for wezel in graf if graf.degree(wezel) > 0]).copy()

    if graf_bez_izolatow.number_of_nodes() == 0:
        return {
            "eulerowski": False,
            "sciezka_eulera": None,
            "komunikat": "Graf nie zawiera krawędzi."}

    skladowe = list(nx.connected_components(graf_bez_izolatow))
    najwieksza = max(skladowe, key=len)
    podgraf = graf_bez_izolatow.subgraph(najwieksza).copy()

    eulerowski = nx.is_eulerian(podgraf)
    ma_sciezke = nx.has_eulerian_path(podgraf)

    if ma_sciezke:
        sciezka = list(nx.eulerian_path(podgraf))
        sciezka_wezly = [sciezka[0][0]] if sciezka else []

        for _, cel in sciezka:
            sciezka_wezly.append(cel)

        nazwy = [
            podgraf.nodes[wezel].get("nazwa", str(wezel))
            for wezel in sciezka_wezly
        ]
    else:
        nazwy = None

    return {
        "eulerowski": eulerowski,
        "ma_sciezke_eulera": ma_sciezke,
        "sciezka_eulera": nazwy,
        "liczba_wezlow_podgrafu": podgraf.number_of_nodes(),
        "liczba_krawedzi_podgrafu": podgraf.number_of_edges()}


def oblicz_przepustowosc(p):
    return 100 / (1 + p / 10)

def maksymalny_przeplyw(graf: nx.Graph,start: str,koniec: str):
    """Oblicza maksymalny przepływ z uwzględnieniem mojej arbitralnej przepustowości węzłów."""

    zrodlo = znajdz_wezel(graf, start)
    cel = znajdz_wezel(graf, koniec)

    if zrodlo == cel:
        raise ValueError("Wybierz dwa różne powiaty.")

    graf_przeplywu = nx.DiGraph()

    # Każdy powiat dzielimy na wejście i wyjście.
    for wezel, atrybuty in graf.nodes(data=True):
        p = atrybuty.get("przestepstwa_na_1000")

        if p is None or pd.isna(p) or p < 0:
            raise ValueError(f"Brak poprawnego wskaźnika przestępczości dla: "
                f"{atrybuty.get('nazwa', wezel)}.")

        pojemnosc = oblicz_przepustowosc(float(p))
        graf_przeplywu.add_edge((wezel, "wejscie"),(wezel, "wyjscie"),capacity=pojemnosc)

    # Połączenia między sąsiednimi powiatami działają w obu kierunkach. 
    # (Traktowanie jak skierowanego w oba kierunki ale innymi wartościami)
    maks_pojemnosc = sum(dane["capacity"] for _, _, dane in graf_przeplywu.edges(data=True)) + 1

    for a, b in graf.edges():
        graf_przeplywu.add_edge(
            (a, "wyjscie"), (b, "wejscie"),
            capacity=maks_pojemnosc)
        
        graf_przeplywu.add_edge(
            (b, "wyjscie"), (a, "wejscie"),
            capacity=maks_pojemnosc)

    # Źródło i cel nie ograniczają przepływu własną przepustowością.
    graf_przeplywu[(zrodlo, "wejscie")][(zrodlo, "wyjscie")]["capacity"] = maks_pojemnosc
    graf_przeplywu[(cel, "wejscie")][(cel, "wyjscie")]["capacity"] = maks_pojemnosc

    wartosc, przeplyw = nx.maximum_flow(
        graf_przeplywu,
        (zrodlo, "wejscie"),
        (cel, "wyjscie"),
        capacity="capacity")

    return round(wartosc, 3)


if __name__ == "__main__":
    G = wczytaj_graf()

    print(f"Wczytano {G.number_of_nodes()} węzłów.")
    print(f"Wczytano {G.number_of_edges()} krawędzi.")
    print()
    
    sciezka =najkrótsza_sciezka_po_atrybucie(G, "powiat nowosolski", "powiat wrocławski")
    print(sciezka,len(sciezka))
    print()

    print(analiza_eulerowska(G))
    print()
    
    powiat_a = "powiat wrocławski"
    powiat_b = "powiat oławski"
    print("Maksymalny przepływ między powiatami: ",powiat_a,powiat_b)
    print(maksymalny_przeplyw(G, powiat_a,powiat_b ))
