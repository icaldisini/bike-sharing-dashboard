# Bike Sharing Dashboard 🚲

Dashboard interaktif hasil analisis **Bike Sharing Dataset** (Capital Bikeshare, Washington D.C., 2011–2012) untuk proyek akhir kelas *Belajar Fundamental Analisis Data* Dicoding.

## Struktur Proyek
```
submission
├───dashboard
│   ├───main_data.csv      # data bersih hasil notebook (sumber data dashboard)
│   └───dashboard.py       # aplikasi Streamlit
├───data
│   ├───day.csv            # data penyewaan per hari
│   └───hour.csv           # data penyewaan per jam
├───notebook.ipynb         # proses analisis data lengkap
├───README.md
├───requirements.txt
└───url.txt                # tautan dashboard di Streamlit Cloud
```

## Setup Environment - Anaconda
```
conda create --name main-ds python=3.11
conda activate main-ds
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal
```
cd submission
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

## Run Streamlit App
Dari folder `submission`:
```
streamlit run dashboard/dashboard.py
```
atau masuk ke folder `dashboard` terlebih dahulu:
```
cd dashboard
streamlit run dashboard.py
```
Dashboard akan terbuka di browser pada `http://localhost:8501`.

## Fitur Dashboard
- **Filter** rentang tanggal dan musim di sidebar (tersedia opsi **All Seasons**). Label musim mengikuti kalender: Winter (21 Des–20 Mar), Spring (21 Mar–20 Jun), Summer (21 Jun–22 Sep), Fall (23 Sep–20 Des).
- **Metrik utama:** total penyewaan, rata-rata per hari, porsi pengguna registered & casual.
- **Pola per Jam:** jam puncak penyewaan hari kerja vs libur/akhir pekan (Pertanyaan 1).
- **Cuaca & Musim:** pengaruh kondisi cuaca, musim, dan suhu terhadap penyewaan harian (Pertanyaan 2).
- **Tren & Pengguna:** tren bulanan, pertumbuhan YoY 2012 vs 2011, dan komposisi tipe pengguna (Pertanyaan 3).
- **Clustering:** manual grouping segmen waktu dan binning suhu/tingkat permintaan (analisis lanjutan tanpa machine learning).
