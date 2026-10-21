import pandas as pd

df = pd.read_csv("przestepstwa_t.csv",sep=";",encoding="utf-8-sig")
# df = df.drop(columns=["Okresy","Przestępstwa","Rodzaje przestępstw","Rok","Jednostka miary","Atrybut"],
#     errors="ignore")

nazwa = df["Nazwa"].astype(str).str.replace("*", "", regex=False).str.strip()
df = df[(nazwa != "POLSKA") & (~nazwa.str.isupper())]

df.to_csv("przestepstwa_t.csv",sep=";",index=False,encoding="utf-8-sig")

print(df.head())
print("Liczba powiatów:", len(df))