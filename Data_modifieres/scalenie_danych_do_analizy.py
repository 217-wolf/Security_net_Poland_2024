
import pandas as pd
import html

def wczytaj_csv(plik, nazwa_wartosci):
    df = pd.read_csv(plik, sep=";", dtype=str)

    df.columns = [html.unescape(k).replace("*", "").strip()
        for k in df.columns]

    df = df[["Kod", "Nazwa", "Wartosc"]].copy()

    for kolumna in ["Kod", "Nazwa", "Wartosc"]:
        df[kolumna] = (df[kolumna].fillna("").map(lambda x: html.unescape(x).lstrip("*").strip()))

    df["Kod"] = df["Kod"].str.replace(r"\.0$", "", regex=True)
    df["Wartosc"] = pd.to_numeric(df["Wartosc"], errors="coerce")

    df = df.rename(columns={"Wartosc": nazwa_wartosci})

    return df


ludnosc = wczytaj_csv("Processed_data/ludnosc_t.csv", "ludnosc")
przestepstwa = wczytaj_csv("Processed_data/przestepstwa_t.csv", "przestepstwa")

# Połączenie według kodu TERYT
df = ludnosc.merge(
    przestepstwa[["Kod", "przestepstwa"]],
    on="Kod",
    how="inner",
    validate="one_to_one")

df["przestepstwa_na_1000"] = (
    df["przestepstwa"] / df["ludnosc"] * 1000).where(df["ludnosc"] > 0)

df = df[["Kod", "Nazwa", "ludnosc", "przestepstwa",
     "przestepstwa_na_1000"]]

df.to_csv("powiaty_atrybuty.csv",
    sep=";",
    index=False,
    encoding="utf-8-sig")

print(df.head())
print("Liczba rekordów:", len(df))