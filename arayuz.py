import tkinter as tk
from tkinter import messagebox
import simulasyon
import copy
from pathlib import Path

class DepoRobotuArayuzu:
    def __init__(self, root):
        self.root = root
        self.root.title("Depo Robotu Simülatörü")
        self.root.geometry("800x600")
        
        self.izgara = []
        self.baslangic = None
        self.ayarlar = {}
        self.komutlar = []
        self.hatalar = []
        self.durum = None
        self.mevcut_adim = 0
        self.harita_havuzu = []
        self.mevcut_harita = 0
        self.gorev_tamamlandi = False
        self.carpisma_efekti = False
        self.carpisma_efekt_surumu = 0
        self.proje_klasoru = Path(__file__).resolve().parent
        
        self.ust_panel = tk.Frame(self.root)
        self.ust_panel.pack(pady=10)
        
        self.btn_yukle = tk.Button(self.ust_panel, text="Dosyaları Yükle", command=self.dosyalari_yukle)
        self.btn_yukle.grid(row=0, column=0, padx=5)
        
        self.btn_adim = tk.Button(self.ust_panel, text="Adım", command=self.bir_adim_ilerle, state=tk.DISABLED)
        self.btn_adim.grid(row=0, column=1, padx=5)
        
        self.btn_tumunu = tk.Button(self.ust_panel, text="Tümünü Çalıştır", command=self.tumunu_calistir, state=tk.DISABLED)
        self.btn_tumunu.grid(row=0, column=2, padx=5)
        
        self.btn_sifirla = tk.Button(self.ust_panel, text="Sıfırla", command=self.sifirla, state=tk.DISABLED)
        self.btn_sifirla.grid(row=0, column=3, padx=5)
        
        self.orta_panel = tk.Frame(self.root)
        self.orta_panel.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.orta_panel, bg="white", width=500, height=400)
        self.canvas.pack(side=tk.LEFT, padx=20)
        
        self.bilgi_paneli = tk.Frame(self.orta_panel, bg="lightgray", padx=10, pady=10)
        self.bilgi_paneli.pack(side=tk.RIGHT, padx=20, fill=tk.BOTH, expand=True)
        
        self.lbl_batarya = tk.Label(self.bilgi_paneli, text="Batarya: -", bg="lightgray", font=("Arial", 12))
        self.lbl_batarya.pack(anchor="w", pady=5)
        
        self.lbl_yon = tk.Label(self.bilgi_paneli, text="Yön: -", bg="lightgray", font=("Arial", 12))
        self.lbl_yon.pack(anchor="w", pady=5)
        
        self.lbl_yuk = tk.Label(self.bilgi_paneli, text="Yük: Yok", bg="lightgray", font=("Arial", 12))
        self.lbl_yuk.pack(anchor="w", pady=5)
        
        self.lbl_teslim = tk.Label(self.bilgi_paneli, text="Teslim: 0", bg="lightgray", font=("Arial", 12))
        self.lbl_teslim.pack(anchor="w", pady=5)
        
        self.lbl_carpisma = tk.Label(
            self.bilgi_paneli,
            text=f"Çarpışma: 0 / {simulasyon.MAX_CARPISMA}",
            bg="lightgray",
            font=("Arial", 12)
        )
        self.lbl_carpisma.pack(anchor="w", pady=5)
        
        self.lbl_siradaki = tk.Label(self.bilgi_paneli, text="Sıradaki: -", bg="lightgray", font=("Arial", 12))
        self.lbl_siradaki.pack(anchor="w", pady=5)

        self.lbl_harita = tk.Label(self.bilgi_paneli, text="Harita: -", bg="lightgray", font=("Arial", 12))
        self.lbl_harita.pack(anchor="w", pady=5)

        self.lbl_kisayollar = tk.Label(
            self.bilgi_paneli,
            text="Tuşlar: W/↑ ileri | A/← sola | D/→ sağa\nE al | B bırak | C şarj | Space/Enter sıradaki komut",
            bg="lightgray",
            justify=tk.LEFT,
            wraplength=240
        )
        self.lbl_kisayollar.pack(anchor="w", pady=10)
        
        self.alt_panel = tk.Frame(self.root)
        self.alt_panel.pack(pady=10, fill=tk.X, padx=20)
        
        self.lbl_log = tk.Label(self.alt_panel, text="Log: Bekleniyor...", font=("Arial", 10), bg="white", relief="sunken", anchor="w")
        self.lbl_log.pack(fill=tk.X)

        self.root.bind_all("<KeyPress>", self.tus_kontrolu)

    def dosyalari_yukle(self):
        try:
            harita_dosyalari = sorted((self.proje_klasoru / "map_havuzu").glob("*.txt"))
            if not harita_dosyalari:
                raise ValueError("map_havuzu klasöründe .txt haritası bulunamadı.")

            self.harita_havuzu = []
            for dosya_yolu in harita_dosyalari:
                izgara, baslangic = simulasyon.harita_oku(str(dosya_yolu))
                self.harita_havuzu.append({
                    "ad": dosya_yolu.stem,
                    "izgara": izgara,
                    "baslangic": baslangic
                })

            self.ayarlar = simulasyon.ayarlari_oku(str(self.proje_klasoru / "ayarlar.json"))
            self.komutlar, self.hatalar = simulasyon.komutlari_oku(str(self.proje_klasoru / "komutlar.txt"))
            
            self.harita_sec(0)
            self.sifirla()
            
            messagebox.showinfo("Başarılı", "Dosyalar başarıyla yüklendi!")
            self.btn_adim.config(state=tk.NORMAL)
            self.btn_tumunu.config(state=tk.NORMAL)
            self.btn_sifirla.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Hata", f"Yükleme hatası: {str(e)}")

    def harita_sec(self, indeks):
        self.mevcut_harita = indeks
        harita = self.harita_havuzu[indeks]
        self.izgara = copy.deepcopy(harita["izgara"])
        self.baslangic = harita["baslangic"]
        self.orijinal_izgara = copy.deepcopy(self.izgara)
        self.lbl_harita.config(
            text=f"Harita: {harita['ad']} ({indeks + 1}/{len(self.harita_havuzu)})"
        )

    def sonraki_haritayi_yukle(self):
        sonraki_indeks = (self.mevcut_harita + 1) % len(self.harita_havuzu)
        self.harita_sec(sonraki_indeks)
        self.sifirla()
        self.lbl_log.config(text="Log: Yeni görev başladı.")

    def sifirla(self):
        self.izgara = copy.deepcopy(self.orijinal_izgara)
        self.durum = simulasyon.yeni_durum(self.izgara, self.baslangic, self.ayarlar)
        self.mevcut_adim = 0
        self.gorev_tamamlandi = False
        self.carpisma_efekti = False
        self.carpisma_efekt_surumu += 1
        self.haritayi_ciz()
        self.bilgileri_guncelle()
        self.lbl_log.config(text="Log: Sıfırlandı.")
        self.btn_adim.config(state=tk.NORMAL)
        self.btn_tumunu.config(state=tk.NORMAL)

    def haritayi_ciz(self):
        self.canvas.delete("all")
        if not self.izgara: return
        
        satir_sayisi = len(self.izgara)
        sutun_sayisi = len(self.izgara[0])
        
        hucre_w = 500 / sutun_sayisi
        hucre_h = 400 / satir_sayisi
        
        for y in range(satir_sayisi):
            for x in range(sutun_sayisi):
                hucre = self.izgara[y][x]
                x1 = x * hucre_w
                y1 = y * hucre_h
                x2 = x1 + hucre_w
                y2 = y1 + hucre_h
                
                renk = "white"
                if hucre == '#': renk = "gray"
                elif hucre == 'K': renk = "orange"
                elif hucre == 'T': renk = "green"
                elif hucre == 'S': renk = "yellow"
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=renk, outline="black")
                
                if hucre in ['K', 'T', 'S']:
                    self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text=hucre, font=("Arial", 12, "bold"))
                    
        if self.durum:
            rx = self.durum["x"] * hucre_w
            ry = self.durum["y"] * hucre_h
            yon = self.durum["yon"]
            
            cx, cy = rx + hucre_w/2, ry + hucre_h/2
            offset = min(hucre_w, hucre_h) / 3
            
            if yon == "K":
                koordinatlar = [cx, cy-offset, cx-offset, cy+offset, cx+offset, cy+offset]
            elif yon == "G":
                koordinatlar = [cx, cy+offset, cx-offset, cy-offset, cx+offset, cy-offset]
            elif yon == "D":
                koordinatlar = [cx+offset, cy, cx-offset, cy-offset, cx-offset, cy+offset]
            else: 
                koordinatlar = [cx-offset, cy, cx+offset, cy-offset, cx+offset, cy+offset]
                
            self.canvas.create_polygon(koordinatlar, fill="blue", outline="black")

            if self.carpisma_efekti:
                self.canvas.create_rectangle(
                    rx + 2, ry + 2, rx + hucre_w - 2, ry + hucre_h - 2,
                    outline="red", width=5
                )
                self.canvas.create_rectangle(150, 8, 350, 38, fill="red", outline="red")
                self.canvas.create_text(
                    250, 23, text="ÇARPIŞMA!", fill="white",
                    font=("Arial", 14, "bold")
                )
            
    def bilgileri_guncelle(self, olay="", komut_metin=None):
        if not self.durum: return
        
        self.lbl_batarya.config(text=f"Batarya: {self.durum['batarya']} / {self.durum['kapasite']}")
        self.lbl_yon.config(text=f"Yön: {self.durum['yon']}")
        self.lbl_yuk.config(text=f"Yük: {'Var' if self.durum['yuk'] == 1 else 'Yok'}")
        self.lbl_teslim.config(text=f"Teslim: {self.durum['teslim']}")
        self.lbl_carpisma.config(
            text=f"Çarpışma: {self.durum['carpisma']} / {simulasyon.MAX_CARPISMA}"
        )
        
        if self.mevcut_adim < len(self.komutlar):
            k = self.komutlar[self.mevcut_adim]
            siradaki_metin = f"{k[0]} {k[1] if k[1] else ''}".strip()
            self.lbl_siradaki.config(text=f"Sıradaki: {siradaki_metin}")
        else:
            self.lbl_siradaki.config(text="Sıradaki: BİTTİ")
            
        if olay:
            self.lbl_log.config(text=f"{komut_metin} -> ({self.durum['x']}, {self.durum['y']}) {olay}")

    def tus_kontrolu(self, event):
        tus = event.keysym.lower()
        komutlar = {
            "w": ("ILERI", 1),
            "up": ("ILERI", 1),
            "a": ("SOL", None),
            "left": ("SOL", None),
            "d": ("SAG", None),
            "right": ("SAG", None),
            "e": ("AL", None),
            "b": ("BIRAK", None),
            "c": ("SARJ", None)
        }

        if tus in ("space", "return"):
            self.bir_adim_ilerle()
            return "break"

        komut = komutlar.get(tus)
        if (
            komut is None
            or self.durum is None
            or self.durum["batarya_bitti"]
            or self.durum["oyun_bitti"]
            or self.gorev_tamamlandi
        ):
            return

        self.komutu_uygula(komut, f"Tuş {event.keysym}: {komut[0]}")

        return "break"

    def carpisma_efektini_kapat(self, surum):
        if surum == self.carpisma_efekt_surumu:
            self.carpisma_efekti = False
            self.haritayi_ciz()

    def komutu_uygula(self, komut, komut_metin):
        teslim_sayisi = self.durum["teslim"]
        olay = simulasyon.komut_uygula(self.durum, komut, self.izgara)
        if olay == "CARPISMA":
            self.carpisma_efekti = True
            self.carpisma_efekt_surumu += 1
            self.root.after(
                500,
                self.carpisma_efektini_kapat,
                self.carpisma_efekt_surumu
            )
        self.haritayi_ciz()
        self.bilgileri_guncelle(olay, komut_metin)

        if self.durum["teslim"] > teslim_sayisi:
            self.gorev_tamamlandi = True
            self.btn_adim.config(state=tk.DISABLED)
            self.btn_tumunu.config(state=tk.DISABLED)
            self.btn_sifirla.config(state=tk.DISABLED)
            self.lbl_log.config(text="Görev başarılı! Sonraki harita yükleniyor.")
            messagebox.showinfo("Görev Başarılı", "Kutuyu teslim alanına bıraktın!")
            self.sonraki_haritayi_yukle()
        elif self.durum["oyun_bitti"]:
            messagebox.showwarning(
                "Çarpışma Sınırı",
                f"En fazla {simulasyon.MAX_CARPISMA} çarpışma hakkı var. Görev sona erdi."
            )
            self.btn_adim.config(state=tk.DISABLED)
            self.btn_tumunu.config(state=tk.DISABLED)
        elif self.durum["batarya_bitti"]:
            messagebox.showwarning("Uyarı", "Batarya bitti!")
            self.btn_adim.config(state=tk.DISABLED)
            self.btn_tumunu.config(state=tk.DISABLED)
    def bir_adim_ilerle(self):
        if (
            self.mevcut_adim < len(self.komutlar)
            and not self.durum["batarya_bitti"]
            and not self.durum["oyun_bitti"]
            and not self.gorev_tamamlandi
        ):
            komut = self.komutlar[self.mevcut_adim]
            self.mevcut_adim += 1
            komut_metin = f"{komut[0]} {komut[1] if komut[1] is not None else ''}".strip()
            self.komutu_uygula(komut, f"Adım {self.mevcut_adim}: {komut_metin}")
                
    def tumunu_calistir(self):
        baslangic_haritasi = self.mevcut_harita
        while (
            self.mevcut_adim < len(self.komutlar)
            and not self.durum["batarya_bitti"]
            and not self.durum["oyun_bitti"]
            and not self.gorev_tamamlandi
            and self.mevcut_harita == baslangic_haritasi
        ):
            self.bir_adim_ilerle()
            self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = DepoRobotuArayuzu(root)
    root.mainloop()