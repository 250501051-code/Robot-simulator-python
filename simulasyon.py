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