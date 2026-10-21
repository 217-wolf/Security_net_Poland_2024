import geopandas as gpd
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

powiaty = gpd.read_file("Podstawa_grafu/A02_Granice_powiatow.shp", encoding="utf-8")

G = nx.Graph()
for idx, row in powiaty.iterrows():
    G.add_node(idx, nazwa=row.get("JPT_NAZWA_", str(idx)))

for i, geom_i in enumerate(powiaty.geometry):
    for j in range(i + 1, len(powiaty)):
        geom_j = powiaty.geometry.iloc[j]
        if geom_i.touches(geom_j):
            G.add_edge(i, j)

print("Liczba węzłów:", G.number_of_nodes())
print("Liczba krawędzi:", G.number_of_edges())
print("Gęstość grafu:", nx.density(G))


print()
n = G.number_of_nodes()
m = G.number_of_edges()
print("Liczba węzłów:", n)
print("Liczba krawędzi:", m)
print("Maksymalna liczba możliwych krawędzi:", n * (n - 1) // 2)
print("Gęstość grafu:", nx.density(G))
print("Średni stopień węzła:", sum(dict(G.degree()).values()) / n)


plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, seed=31, dim=2)
nx.draw_networkx(G,pos=pos,
    node_size=10,with_labels=False,
    width=0.3,edge_color="blue")

plt.title("Graf sąsiedztwa powiatów Polski")
plt.show()