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

def yeni_durum(izgara, baslangic, ayarlar):
    return {
        "x": baslangic[0],
        "y": baslangic[1],
        "yon": ayarlar.get("baslangic_yonu", "D"),
        "batarya": ayarlar.get("batarya_kapasitesi", 100),
        "yuk": 0, # 0: Yok, 1: Kutu var
        "teslim": 0,
        "carpisma": 0,
        "toplam_adim": 0,
        "batarya_bitti": False,
        "oyun_bitti": False,
        "ziyaretler": {(baslangic[0], baslangic[1]): 1},
        "kapasite": ayarlar.get("batarya_kapasitesi", 100),
        "adim_maliyeti": ayarlar.get("adim_maliyeti", 2),
        "yuk_carpani": ayarlar.get("yuk_carpani", 2),
        "donus_maliyeti": ayarlar.get("donus_maliyeti", 1),
        "carpisma_cezasi": ayarlar.get("carpisma_cezasi", 5)
    }

def komut_uygula(durum, komut, izgara):
    if durum["batarya_bitti"] or durum["oyun_bitti"]:
        return "BITTI"
        
    tip, deger = komut
    olay = "GECERSIZ"
    
    if tip in ["SAG", "SOL"]:
        durum["toplam_adim"] += 1
        maliyet = durum["donus_maliyeti"]
        if durum["batarya"] < maliyet:
            durum["batarya_bitti"] = True
            return "BATARYA_YOK"
            
        durum["batarya"] -= maliyet
        yonler = ["K", "D", "G", "B"]
        idx = yonler.index(durum["yon"])
        
        if tip == "SAG":
            durum["yon"] = yonler[(idx + 1) % 4]
        else:
            durum["yon"] = yonler[(idx - 1) % 4]
        olay = "DONUS"
        
    elif tip == "ILERI":
        hareket_maliyeti = durum["adim_maliyeti"] * (durum["yuk_carpani"] if durum["yuk"] == 1 else 1)
        
        for _ in range(deger):
            durum["toplam_adim"] += 1
            if durum["batarya"] < hareket_maliyeti:
                durum["batarya_bitti"] = True
                return "BATARYA_YOK"
                
            yeni_x, yeni_y = durum["x"], durum["y"]
            if durum["yon"] == "K": yeni_y -= 1
            elif durum["yon"] == "G": yeni_y += 1
            elif durum["yon"] == "D": yeni_x += 1
            elif durum["yon"] == "B": yeni_x -= 1
            
            if (yeni_y < 0 or yeni_y >= len(izgara) or 
                yeni_x < 0 or yeni_x >= len(izgara[0]) or 
                izgara[yeni_y][yeni_x] == '#'):
                
                durum["carpisma"] = min(durum["carpisma"] + 1, MAX_CARPISMA)
                durum["batarya"] -= durum["carpisma_cezasi"]
                if durum["carpisma"] >= MAX_CARPISMA:
                    durum["oyun_bitti"] = True
                if durum["batarya"] <= 0:
                    durum["batarya"] = 0
                    durum["batarya_bitti"] = True
                olay = "CARPISMA"
                break 
            else:
                durum["batarya"] -= hareket_maliyeti
                durum["x"], durum["y"] = yeni_x, yeni_y
                olay = "HAREKET"

                konum = (durum["x"], durum["y"])
                durum["ziyaretler"][konum] = durum["ziyaretler"].get(konum, 0) + 1

                if durum["batarya"] == 0:
                    durum["batarya_bitti"] = True
                    break
               
    elif tip == "AL":
        durum["toplam_adim"] += 1
        if izgara[durum["y"]][durum["x"]] == 'K' and durum["yuk"] == False:
            durum["yuk"] = True
            izgara[durum["y"]][durum["x"]] = ' '
            olay = "KUTU_ALINDI"
            
    elif tip == "BIRAK":
        durum["toplam_adim"] += 1
        if durum["yuk"] == True:
            durum["yuk"] = False
            if izgara[durum["y"]][durum["x"]] == 'T':
                durum["teslim"] += 1
                olay = "TESLIM_EDILDI"
            else:
                izgara[durum["y"]][durum["x"]] = 'K'
                olay = "KUTU_BIRAKILDI"
                
    elif tip == "SARJ":
        durum["toplam_adim"] += 1
        if izgara[durum["y"]][durum["x"]] == 'S':
            durum["batarya"] = durum["kapasite"]
            olay = "SARJ_OLDU"
            
    return olay

def simulasyonu_calistir(izgara, baslangic, komutlar, ayarlar):
    durum = yeni_durum(izgara, baslangic, ayarlar)
    log = []
    
    for adim_no, komut in enumerate(komutlar, start=1):
        if durum["batarya_bitti"] or durum["oyun_bitti"]:
            break
            
        olay = komut_uygula(durum, komut, izgara)
        
        log.append({
            "adim": adim_no,
            "komut": f"{komut[0]} {komut[1] if komut[1] is not None else ''}".strip(),
            "x": durum["x"],
            "y": durum["y"],
            "yon": durum["yon"],
            "batarya": durum["batarya"],
            "olay": olay
        })
        
    en_cok_ziyaret = (durum["x"], durum["y"])
    en_yuksek = -1
    
    for (x, y), sayi in durum["ziyaretler"].items():
        if sayi > en_yuksek:
            en_yuksek = sayi
            en_cok_ziyaret = (x, y)
        elif sayi == en_yuksek:
            if y < en_cok_ziyaret[1] or (y == en_cok_ziyaret[1] and x < en_cok_ziyaret[0]):
                en_cok_ziyaret = (x, y)
                
    sonuc = {
        "konum": [durum["x"], durum["y"]],
        "yon": durum["yon"],
        "batarya": durum["batarya"],
        "yuk": durum["yuk"],
        "teslim": durum["teslim"],
        "carpisma": durum["carpisma"],
        "toplam_adim": durum["toplam_adim"],
        "batarya_bitti": durum["batarya_bitti"],
        "en_cok_ziyaret_edilen": list(en_cok_ziyaret)
    }
    
    return sonuc, log
