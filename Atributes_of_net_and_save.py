"""Poligon: przypisanie danych z CSV do węzłów grafu powiatów. Skrypt nie zapisuje żadnych plików."""

from pathlib import Path
import json
import re
import unicodedata

import geopandas as gpd
import networkx as nx
import pandas as pd
from networkx.readwrite import json_graph

KATALOG_PROJEKTU = Path(__file__).resolve().parent
SCIEZKA_GRANIC = KATALOG_PROJEKTU / "Podstawa_grafu" / "A02_Granice_powiatow.shp"
SCIEZKA_ATRYBUTOW = KATALOG_PROJEKTU / "Processed_data" / "powiaty_atrybuty.csv"
SCIEZKA_GRAFU_JSON = KATALOG_PROJEKTU / "Graf_reprezentacja" / "graf_powiatow.json"


KOLUMNA_KODU_SHP = None
KOLUMNA_NAZWY_SHP = "JPT_NAZWA_"


def kod_terc_z_shp(wartosc: object) -> str:
    if pd.isna(wartosc):
        return ""
    kod = str(wartosc).strip()
    kod = re.sub(r"\.0$", "", kod)
    return kod.zfill(4) if kod.isdigit() else kod

def kod_terc_z_csv(wartosc: object) -> str:
    if pd.isna(wartosc):
        return ""
    kod = re.sub(r"\.0$", "", str(wartosc).strip())
    return str(int(kod) // 1000).zfill(4) if kod.isdigit() else kod

def normalizuj_nazwe(wartosc: object) -> str:
    """Normalizacja wyłącznie do dopasowania po nazwie."""
    tekst = unicodedata.normalize("NFKD", str(wartosc))
    tekst = "".join(znak for znak in tekst if not unicodedata.combining(znak))
    return re.sub(r"\s+", " ", tekst.lower()).strip()

def znajdz_kolumne_kodu(powiaty: gpd.GeoDataFrame) -> str | None:
    if KOLUMNA_KODU_SHP:
        if KOLUMNA_KODU_SHP not in powiaty.columns:
            raise KeyError(f"Brak kolumny {KOLUMNA_KODU_SHP!r} w pliku SHP.")
        return KOLUMNA_KODU_SHP
    kandydaci = ("JPT_KOD_JE", "KOD", "kod", "TERYT", "teryt")
    return next((kolumna for kolumna in kandydaci if kolumna in powiaty.columns), None)

def zbuduj_graf_z_atrybutami() -> nx.Graph:
    powiaty = gpd.read_file(SCIEZKA_GRANIC, encoding="utf-8")
    dane = pd.read_csv(SCIEZKA_ATRYBUTOW, sep=";", encoding="utf-8-sig", dtype={"Kod": str})

    wymagane_csv = {"Kod", "Nazwa"}
    brakujace = wymagane_csv - set(dane.columns)

    if brakujace:
        raise KeyError(f"CSV nie zawiera wymaganych kolumn: {sorted(brakujace)}")

    if KOLUMNA_NAZWY_SHP not in powiaty.columns:
        raise KeyError(f"SHP nie zawiera kolumny nazw: {KOLUMNA_NAZWY_SHP!r}")

    kolumna_kodu = znajdz_kolumne_kodu(powiaty)
    # SHP: 0201; CSV: 0201000 
    # Do łączenia wykorzystujemy wspólną, 4-cyfrową postać
    dane["_kod"] = dane["Kod"].map(kod_terc_z_csv)
    if dane["_kod"].duplicated().any():
        duplikaty = dane.loc[dane["_kod"].duplicated(keep=False), "Kod"].tolist()
        raise ValueError(f"Powtórzone kody w CSV: {duplikaty}")

    dane["_nazwa"] = dane["Nazwa"].map(normalizuj_nazwe)
    atrybuty_po_kodzie = (
    dane.set_index("_kod")
    .drop(columns="_nazwa")
    .to_dict("index"))

    unikalne_nazwy = ~dane["_nazwa"].duplicated(keep=False)

    atrybuty_po_nazwie = (
        dane.loc[unikalne_nazwy]
        .set_index("_nazwa")
        .drop(columns="_kod")
        .to_dict("index"))

    graf = nx.Graph()
    bez_dopasowania = []
    dopasowane_kody = set()

    for indeks, rekord in powiaty.iterrows():
        nazwa = rekord[KOLUMNA_NAZWY_SHP]
        atrybuty = None
        sposob = None

        if kolumna_kodu:
            kod = kod_terc_z_shp(rekord[kolumna_kodu])
            atrybuty = atrybuty_po_kodzie.get(kod)
            if atrybuty is not None:
                dopasowane_kody.add(kod)
                sposob = "kod"

        if atrybuty is None:
            atrybuty = atrybuty_po_nazwie.get(normalizuj_nazwe(nazwa))
            if atrybuty is not None:
                sposob = "nazwa"
                dopasowane_kody.add(kod_terc_z_csv(atrybuty["Kod"]))

        graf.add_node(indeks, nazwa=nazwa, dopasowanie_atrybutow=sposob or "brak")
        if atrybuty is None:
            bez_dopasowania.append(nazwa)
        else:
            graf.nodes[indeks].update(atrybuty)

    for pozycja_i, (indeks_i, geometria_i) in enumerate(powiaty.geometry.items()):
        for pozycja_j in range(pozycja_i + 1, len(powiaty)):
            indeks_j = powiaty.index[pozycja_j]
            if geometria_i.touches(powiaty.geometry.iloc[pozycja_j]):
                graf.add_edge(indeks_i, indeks_j)

    brakujace_w_csv = sorted(set(atrybuty_po_kodzie) - dopasowane_kody)
    print(f"Węzły grafu: {graf.number_of_nodes()}")
    print(f"Krawędzie grafu: {graf.number_of_edges()}")
    print(f"Kolumna kodu w SHP: {kolumna_kodu or 'nie znaleziona — użyto nazw'}")
    print(f"Węzły bez dopasowanych atrybutów: {len(bez_dopasowania)}")
    print(bez_dopasowania[:20])
    print(f"Rekordy CSV niewykorzystane przez graf: {len(brakujace_w_csv)}")
    print(brakujace_w_csv[:20])
    return graf


def zapisz_graf_do_json(graf: nx.Graph, sciezka: Path = SCIEZKA_GRAFU_JSON) -> None:
    """Zapisuje graf do pliku JSON."""
    dane_json = json_graph.node_link_data(graf)
    dane_json["metadata"] = {
        "opis": "Graf sąsiedztwa powiatów Polski z atrybutami",
        "liczba_wezlow": graf.number_of_nodes(),
        "liczba_krawedzi": graf.number_of_edges(),}

    sciezka.parent.mkdir(parents=True, exist_ok=True)
    with sciezka.open("w", encoding="utf-8") as plik:
        json.dump(dane_json, plik, ensure_ascii=False, indent=2)
    print(f"Graf zapisano do: {sciezka}")



if __name__ == "__main__":
    G = zbuduj_graf_z_atrybutami()
    zapisz_graf_do_json(G)
    pierwszy_wezel = next(iter(G.nodes))
    print("\nPrzykładowy węzeł z atrybutami:")
    print(G.nodes[pierwszy_wezel])
