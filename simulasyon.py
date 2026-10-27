import json
import csv
import os

# Bu dosya arayüz (Tkinter) KESİNLİKLE İÇERMEZ.
# Sadece kurallar ve mantık burada yer alır.

MAX_CARPISMA = 3

def harita_oku(dosya_yolu):
    if not os.path.exists(dosya_yolu):
        raise ValueError("Harita dosyası bulunamadı!")
        
    izgara = []
    robot_konumu = None
    
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        satirlar = [s.rstrip("\n\r") for s in f.readlines()]
        
    if not satirlar:
        raise ValueError("Harita dosyası boş!")
        
    uzunluk = len(satirlar[0])
    
    for y, satir in enumerate(satirlar):
        if len(satir) != uzunluk:
            raise ValueError("Harita satır uzunlukları birbirine eşit değil!")
        
        satir_listesi = list(satir)
        for x, hucre in enumerate(satir_listesi):
            if hucre == 'R':
                if robot_konumu is not None:
                    raise ValueError("Haritada birden fazla robot olamaz!")
                robot_konumu = (x, y)
        izgara.append(satir_listesi)
        
    if robot_konumu is None:
        raise ValueError("Haritada robot (R) bulunamadı!")
        
    return izgara, robot_konumu

def ayarlari_oku(dosya_yolu):
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        return json.load(f)

def komutlari_oku(dosya_yolu):
    komutlar = []
    hatalar = []
    
    if not os.path.exists(dosya_yolu):
        return komutlar, hatalar
        
    with open(dosya_yolu, "r", encoding="utf-8") as f:
        for satir_no, satir in enumerate(f, start=1):
            temiz_satir = satir.strip()
            if not temiz_satir:
                continue
                
            parcalar = temiz_satir.split()
            komut = parcalar[0].upper()
            
            if komut in ["SAG", "SOL", "AL", "BIRAK", "SARJ"]:
                if len(parcalar) == 1:
                    komutlar.append((komut, None))
                else:
                    hatalar.append({"satir": satir_no, "icerik": temiz_satir, "neden": "Fazla parametre"})
            elif komut == "ILERI":
                if len(parcalar) == 2 and parcalar[1].isdecimal() and int(parcalar[1]) > 0:
                    komutlar.append((komut, int(parcalar[1])))
                else:
                    hatalar.append({"satir": satir_no, "icerik": temiz_satir, "neden": "Geçersiz ILERI parametresi"})
            else:
                hatalar.append({"satir": satir_no, "icerik": temiz_satir, "neden": "Bilinmeyen komut"})
                
    return komutlar, hatalar
