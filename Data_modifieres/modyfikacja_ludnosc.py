import pandas as pd

df = pd.read_csv("ludnosc_t.csv", sep=";", encoding="utf-8-sig")

# df = df.drop(columns=["Rok"])

# df = df.groupby("Kod", as_index=False).agg({
#     "Nazwa": "first",
#     "Wartosc": "sum"
# })

# df = df.drop(columns=["Zakres terytorialny"], errors="ignore")

# Usunięcie danych: Polski i województw
df = df[~df["Nazwa"].str.isupper()]

df.to_csv("ludnosc_t.csv", sep=";", index=False, encoding="utf-8-sig")

print("Zapisano plik ludnosc_t.csv")