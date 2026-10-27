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
         