import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

SCIEZKA = Path("Graf_reprezentacja")

PLIK_SASIEDZTWA = SCIEZKA / "macierz_sasiedztwa.csv"
PLIK_INCYDENCJI = SCIEZKA / "macierz_incydencji.csv"

df_sasiedztwa = pd.read_csv(PLIK_SASIEDZTWA,index_col=0)

graf_sasiedztwa = nx.from_pandas_adjacency(df_sasiedztwa)

pozycje_sasiedztwa = nx.spring_layout(graf_sasiedztwa,seed=42)

plt.figure(figsize=(14, 10))
nx.draw(
    graf_sasiedztwa,
    pos=pozycje_sasiedztwa,
    with_labels=False,
    node_size=10,
    edge_color="green",
    width=0.5)

plt.title("Graf odtworzony z macierzy sąsiedztwa")
plt.axis("off")
plt.show()
print("Graf z macierzy sąsiedztwa:")
print("Wierzchołki:", graf_sasiedztwa.number_of_nodes())
print("Krawędzie:", graf_sasiedztwa.number_of_edges())

# macierz incydencji
df_incydencji = pd.read_csv(PLIK_INCYDENCJI, index_col=0)

graf_incydencji = nx.Graph()

graf_incydencji.add_nodes_from(df_incydencji.index)

for nazwa_krawedzi in df_incydencji.columns:
    incydentne = df_incydencji.index[df_incydencji[nazwa_krawedzi].to_numpy() != 0].tolist()

    if len(incydentne) == 1:
        graf_incydencji.add_edge(
            incydentne[0],
            incydentne[0])

    elif len(incydentne) == 2:
        graf_incydencji.add_edge(incydentne[0],incydentne[1])

    elif len(incydentne) > 2:
        pass

pozycje_incydencji = nx.spring_layout(graf_incydencji,seed=42)

plt.figure(figsize=(14, 10))
nx.draw(
    graf_incydencji,
    pos=pozycje_incydencji,
    with_labels=False,
    node_size=10,
    edge_color="green",
    width=0.5)

plt.title("Graf odtworzony z macierzy incydencji")
plt.axis("off")
plt.show()

print("Graf z macierzy incydencji:")
print("Wierzchołki:", graf_incydencji.number_of_nodes())
print("Krawędzie:", graf_incydencji.number_of_edges())

# Porównanie grafów i miar

print("Grafy są izomorficzne:",nx.is_isomorphic(graf_sasiedztwa, graf_incydencji))
print("Liczba wierzchołków jest zgodna:",graf_sasiedztwa.number_of_nodes()== graf_incydencji.number_of_nodes())

print("Liczba krawędzi jest zgodna:", graf_sasiedztwa.number_of_edges()== graf_incydencji.number_of_edges())

def oblicz_miary(graf, nazwa="Graf"):
    print(nazwa)

    # Rozkład stopni wierzchołków
    stopnie = dict(graf.degree())
    rozklad_stopni = pd.Series(list(stopnie.values())).value_counts().sort_index()

    print("\nRozkład stopni wierzchołków:")
    print(rozklad_stopni.to_string())
    
    plt.figure(figsize=(10, 6))
    rozklad_stopni.sort_index().plot(kind="bar")
    plt.title(f"Rozkład stopni wierzchołków - {nazwa}")
    plt.xlabel("Stopień wierzchołka")
    plt.ylabel("Liczba wierzchołków")
    plt.tight_layout()
    plt.show()

    # Gęstość grafu
    gestosc = nx.density(graf)
    print(f"\nGęstość grafu: {gestosc}")

    # Średnica grafu
    if graf.number_of_nodes() == 0:
        print("Średnica grafu: brak wierzchołków")
    elif nx.is_connected(graf):
        print("Średnica grafu:", nx.diameter(graf))
    else:
        skladowe = list(nx.connected_components(graf))
        najwieksza_skladowa = graf.subgraph(max(skladowe, key=len)).copy()

        print("Graf jest niespójny.")
        print("Średnica największej składowej spójnej:",nx.diameter(najwieksza_skladowa))

oblicz_miary(graf_sasiedztwa, "Graf z macierzy sąsiedztwa")
oblicz_miary(graf_incydencji, "Graf z macierzy incydencji")