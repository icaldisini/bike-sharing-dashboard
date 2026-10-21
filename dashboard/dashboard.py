import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns
import streamlit as st

# ======================== Konfigurasi ========================
st.set_page_config(page_title="Bike Sharing Dashboard", page_icon="🚲", layout="wide")
sns.set_theme(style="whitegrid")
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold"})

HIGHLIGHT = "#1f6fb4"
SECOND = "#f28e2b"
NEUTRAL = "#c8ccd2"
LOW = "#d1495b"

# Label musim mengikuti kalender (hasil koreksi di notebook): 1=Winter, 2=Spring, 3=Summer, 4=Fall
SEASON_ORDER = ["Winter", "Spring", "Summer", "Fall"]
SEASON_RANGE_TEXT = "Winter: 21 Des–20 Mar · Spring: 21 Mar–20 Jun · Summer: 21 Jun–22 Sep · Fall: 23 Sep–20 Des"

# Teks pertanyaan bisnis (identik dengan yang ada di notebook)
Q1 = "Pada jam berapa puncak rata-rata penyewaan sepeda per jam terjadi pada **hari kerja** dibandingkan **hari libur/akhir pekan** selama periode Januari 2011 – Desember 2012, dan berapa rata-rata jumlah sepeda yang disewa pada jam puncak tersebut, sebagai dasar penjadwalan redistribusi armada dan perawatan sepeda?"
Q2 = "Berapa persen penurunan rata-rata penyewaan sepeda harian saat kondisi cuaca **hujan/salju ringan** dibandingkan cuaca **cerah**, serta musim apa yang memiliki rata-rata penyewaan harian tertinggi dan terendah selama periode 2011 – 2012, sebagai dasar perencanaan kapasitas armada dan program promosi musiman?"
Q3 = "Berapa tingkat pertumbuhan total penyewaan sepeda tahun 2012 dibandingkan tahun 2011 (*Year-over-Year*) untuk setiap bulan, dan berapa kontribusi pengguna **casual** vs **registered** terhadap total penyewaan di masing-masing tahun, sebagai dasar strategi konversi pengguna casual menjadi member terdaftar?"
WEATHER_ORDER = ["Cerah/Berawan", "Berkabut/Mendung", "Hujan/Salju Ringan", "Hujan Lebat/Badai"]
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
SEGMENT_ORDER = ["Dini Hari (00-05)", "Pagi Sibuk (06-09)", "Siang (10-15)", "Sore Sibuk (16-19)", "Malam (20-23)"]
TEMP_LABELS = ["Dingin (<10°C)", "Sejuk (10-20°C)", "Hangat (20-30°C)", "Panas (>30°C)"]


# ======================== Helper functions ========================
@st.cache_data
def load_data():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main_data.csv")
    df = pd.read_csv(path, parse_dates=["date"])
    df["season"] = pd.Categorical(df["season"], categories=SEASON_ORDER, ordered=True)
    df["weather"] = pd.Categorical(df["weather"], categories=WEATHER_ORDER, ordered=True)
    df["day_weather"] = pd.Categorical(df["day_weather"], categories=WEATHER_ORDER, ordered=True)
    df["month"] = pd.Categorical(df["month"], categories=MONTH_ORDER, ordered=True)
    df["time_segment"] = pd.Categorical(df["time_segment"], categories=SEGMENT_ORDER, ordered=True)
    return df


def create_daily_df(df):
    """Agregasi data per jam menjadi data per hari."""
    daily = df.groupby("date").agg(
        season=("season", "first"),
        year=("year", "first"),
        month=("month", "first"),
        workingday=("workingday", "first"),
        weather=("day_weather", "first"),
        temp_c=("temp_c", "mean"),
        casual=("casual", "sum"),
        registered=("registered", "sum"),
        total_rentals=("total_rentals", "sum"),
    ).reset_index()
    daily["weather"] = pd.Categorical(daily["weather"], categories=WEATHER_ORDER, ordered=True)
    daily["season"] = pd.Categorical(daily["season"], categories=SEASON_ORDER, ordered=True)
    daily["temp_group"] = pd.cut(daily["temp_c"], bins=[0, 10, 20, 30, 42], labels=TEMP_LABELS)
    return daily


def create_hourly_pattern_df(df):
    return df.groupby(["hour", "workingday"])["total_rentals"].mean().unstack()


def create_weather_df(daily):
    return daily.groupby("weather", observed=True)["total_rentals"].mean()


def create_season_df(daily):
    return daily.groupby("season", observed=True)["total_rentals"].mean().sort_values(ascending=False)


def create_monthly_df(df):
    monthly = df.groupby(["year", "month"], observed=True)["total_rentals"].sum().unstack(0)
    return monthly


def create_segment_df(df):
    return df.groupby(["time_segment", "workingday"], observed=True)["total_rentals"].mean().unstack()


def bar_labels(ax, bars, fmt="{:,.0f}", offset_ratio=0.01):
    ymax = ax.get_ylim()[1]
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + ymax * offset_ratio,
                fmt.format(bar.get_height()), ha="center", va="bottom", fontsize=10)


# ======================== Load data ========================
all_df = load_data()
min_date, max_date = all_df["date"].min().date(), all_df["date"].max().date()

# ======================== Sidebar ========================
with st.sidebar:
    st.title("🚲 Bike Sharing")
    st.caption("Capital Bikeshare, Washington D.C. (2011–2012)")
    date_range = st.date_input("Rentang waktu", value=[min_date, max_date],
                               min_value=min_date, max_value=max_date)
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0] if isinstance(date_range, (list, tuple)) else date_range

    selected_seasons = st.multiselect(
        "Musim", ["All Seasons"] + SEASON_ORDER, default=["All Seasons"],
        help="Pilih 'All Seasons' untuk menampilkan semua musim, atau hapus lalu pilih musim tertentu.")
    st.caption(SEASON_RANGE_TEXT)
    st.markdown("---")
    st.caption("Dibuat oleh Faishal Muflih Irfanu Tsaqib · Proyek Analisis Data Dicoding")

# "All Seasons" (atau pilihan kosong) berarti semua musim ditampilkan
if "All Seasons" in selected_seasons or not selected_seasons:
    seasons = SEASON_ORDER
else:
    seasons = selected_seasons
season_label = "All Seasons" if set(seasons) == set(SEASON_ORDER) else ", ".join(seasons)

main_df = all_df[(all_df["date"].dt.date >= start_date) & (all_df["date"].dt.date <= end_date)
                 & (all_df["season"].isin(seasons))]

if main_df.empty:
    st.warning("Tidak ada data untuk filter yang dipilih. Silakan ubah rentang waktu atau musim.")
    st.stop()

daily_df = create_daily_df(main_df)

# ======================== Header & metrics ========================
st.title("🚲 Bike Sharing Dashboard")
st.markdown(f"Periode **{start_date:%d %b %Y} – {end_date:%d %b %Y}** · Musim: **{season_label}**")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Penyewaan", f"{main_df['total_rentals'].sum():,}")
col2.metric("Rata-rata per Hari", f"{daily_df['total_rentals'].mean():,.0f}")
col3.metric("Pengguna Registered", f"{main_df['registered'].sum() / main_df['total_rentals'].sum():.1%}")
col4.metric("Pengguna Casual", f"{main_df['casual'].sum() / main_df['total_rentals'].sum():.1%}")

tab1, tab2, tab3, tab4 = st.tabs(["⏰ Pola per Jam", "🌦️ Cuaca & Musim", "📈 Tren & Pengguna", "🧩 Clustering"])

# ======================== Tab 1: Pertanyaan 1 ========================
with tab1:
    st.subheader("Pertanyaan 1")
    st.markdown(Q1)
    hourly = create_hourly_pattern_df(main_df)
    fig, ax = plt.subplots(figsize=(12, 5))
    colors = {"Hari Kerja": HIGHLIGHT, "Libur/Akhir Pekan": SECOND}
    for col in hourly.columns:
        s = hourly[col].dropna()
        ax.plot(s.index, s.values, marker="o", linewidth=2.5, color=colors.get(col, NEUTRAL), label=col)
        peak = s.idxmax()
        ax.annotate(f"{peak:02d}.00\n{s[peak]:.0f} sepeda", (peak, s[peak]), textcoords="offset points",
                    xytext=(0, 10), ha="center", fontsize=10, fontweight="bold", color=colors.get(col, NEUTRAL))
    ax.set_xlabel("Jam")
    ax.set_ylabel("Rata-rata penyewaan per jam")
    ax.set_xticks(range(24))
    ax.set_xticklabels([f"{h:02d}" for h in range(24)])
    ax.set_ylim(0, hourly.max().max() * 1.2)
    ax.legend(title="Tipe hari", frameon=False)
    st.pyplot(fig)

    cols = st.columns(len(hourly.columns))
    for c, col in zip(cols, hourly.columns):
        s = hourly[col].dropna()
        c.metric(f"Jam puncak – {col}", f"{s.idxmax():02d}.00", f"±{s.max():.0f} sepeda/jam", delta_color="off")

    with st.expander("💡 Insight"):
        st.markdown(
            "- **Hari kerja** memiliki dua puncak (jam berangkat ±08.00 dan pulang kerja ±17.00) yang didorong pengguna *registered*.\n"
            "- **Libur/akhir pekan** memuncak di siang hari (±12.00–15.00) karena penggunaan rekreasi.\n"
            "- Redistribusi armada sebaiknya selesai sebelum 07.00 & 16.00 pada hari kerja; perawatan dilakukan pukul 00.00–05.00."
        )

# ======================== Tab 2: Pertanyaan 2 ========================
with tab2:
    st.subheader("Pertanyaan 2")
    st.markdown(Q2)
    weather = create_weather_df(daily_df)
    season = create_season_df(daily_df)

    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(7, 5))
        bars = ax.bar(weather.index.astype(str), weather.values,
                      color=[HIGHLIGHT if v == weather.max() else NEUTRAL for v in weather.values])
        ax.set_ylim(0, weather.max() * 1.2)
        base = weather.get("Cerah/Berawan")
        for bar, (cat, val) in zip(bars, weather.items()):
            label = f"{val:,.0f}"
            if base and cat != "Cerah/Berawan":
                label += f"\n({(val / base - 1) * 100:+.1f}%)"
            ax.text(bar.get_x() + bar.get_width() / 2, val + weather.max() * 0.01, label, ha="center", va="bottom", fontsize=10)
        ax.set_title("Rata-rata penyewaan harian per kondisi cuaca")
        ax.set_xlabel("Kondisi cuaca")
        ax.set_ylabel("Rata-rata penyewaan per hari")
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
        st.pyplot(fig)
    with col2:
        fig, ax = plt.subplots(figsize=(7, 5))
        colors = [HIGHLIGHT if v == season.max() else (LOW if v == season.min() and len(season) > 1 else NEUTRAL)
                  for v in season.values]
        bars = ax.bar(season.index.astype(str), season.values, color=colors)
        ax.set_ylim(0, season.max() * 1.2)
        bar_labels(ax, bars)
        ax.set_title("Rata-rata penyewaan harian per musim")
        ax.set_xlabel("Musim")
        ax.set_ylabel("Rata-rata penyewaan per hari")
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
        st.pyplot(fig)

    fig, ax = plt.subplots(figsize=(12, 4.5))
    palette = {"Winter": "#9aa5b1", "Spring": "#7fb069", "Summer": SECOND, "Fall": HIGHLIGHT}
    sns.scatterplot(data=daily_df, x="temp_c", y="total_rentals", hue="season", palette=palette,
                    hue_order=[s for s in SEASON_ORDER if s in seasons], alpha=0.75, ax=ax)
    ax.set_title(f"Suhu vs penyewaan harian (r = {daily_df['temp_c'].corr(daily_df['total_rentals']):.2f})")
    ax.set_xlabel("Suhu (°C)")
    ax.set_ylabel("Total penyewaan per hari")
    ax.set_ylim(0, None)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax.legend(title="Musim", frameon=False, loc="lower right")
    st.pyplot(fig)

    with st.expander("💡 Insight"):
        st.markdown(
            "- Pada periode penuh 2011–2012, hujan/salju ringan menurunkan rata-rata penyewaan harian **±63%** dibanding cuaca cerah.\n"
            "- Musim **Summer** tertinggi (±5.644/hari) dan **Winter** terendah (±2.604/hari).\n"
            "- Suhu adalah pendorong utama (r ≈ 0,63); penyewaan ideal pada suhu 20–30 °C."
        )

# ======================== Tab 3: Pertanyaan 3 ========================
with tab3:
    st.subheader("Pertanyaan 3")
    st.markdown(Q3)
    monthly = create_monthly_df(main_df)
    fig, ax = plt.subplots(figsize=(12, 5))
    year_colors = {2011: NEUTRAL, 2012: HIGHLIGHT}
    for yr in monthly.columns:
        s = monthly[yr].dropna()
        ax.plot(s.index.astype(str), s.values, marker="o", linewidth=2.5, color=year_colors.get(yr, SECOND), label=str(yr))
    ax.set_title("Total penyewaan per bulan")
    ax.set_xlabel("Bulan")
    ax.set_ylabel("Total penyewaan")
    ax.set_ylim(0, monthly.max().max() * 1.15)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    ax.legend(title="Tahun", frameon=False)
    st.pyplot(fig)

    col1, col2 = st.columns(2)
    with col1:
        if {2011, 2012}.issubset(monthly.columns):
            growth = ((monthly[2012] / monthly[2011] - 1) * 100).dropna()
            fig, ax = plt.subplots(figsize=(7, 4.5))
            bars = ax.bar(growth.index.astype(str), growth.values,
                          color=[HIGHLIGHT if v == growth.max() else NEUTRAL for v in growth.values])
            ax.set_ylim(0, max(growth.max() * 1.2, 1))
            bar_labels(ax, bars, fmt="{:.0f}%")
            ax.set_title("Pertumbuhan YoY per bulan (2012 vs 2011)")
            ax.set_xlabel("Bulan")
            ax.set_ylabel("Pertumbuhan (%)")
            st.pyplot(fig)
        else:
            st.info("Pilih rentang waktu yang mencakup 2011 dan 2012 untuk melihat pertumbuhan YoY.")
    with col2:
        users = main_df.groupby("year")[["registered", "casual"]].sum()
        fig, ax = plt.subplots(figsize=(7, 4.5))
        years = users.index.astype(str)
        ax.bar(years, users["registered"], color=HIGHLIGHT, label="Registered")
        ax.bar(years, users["casual"], bottom=users["registered"], color=SECOND, label="Casual")
        for i, yr in enumerate(users.index):
            total = users.loc[yr].sum()
            ax.text(i, users.loc[yr, "registered"] / 2, f"{users.loc[yr, 'registered'] / total:.1%}",
                    ha="center", color="white", fontweight="bold")
            ax.text(i, users.loc[yr, "registered"] + users.loc[yr, "casual"] / 2,
                    f"{users.loc[yr, 'casual'] / total:.1%}", ha="center", fontweight="bold")
        ax.set_title("Komposisi tipe pengguna per tahun")
        ax.set_xlabel("Tahun")
        ax.set_ylabel("Total penyewaan")
        ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
        ax.legend(frameon=False)
        st.pyplot(fig)

    with st.expander("💡 Insight"):
        st.markdown(
            "- Total penyewaan tumbuh **±64,9%** (1,24 juta → 2,05 juta) dan setiap bulan 2012 lebih tinggi dari 2011.\n"
            "- Pengguna **registered** menyumbang ±80% penyewaan — target utama program loyalitas.\n"
            "- Pengguna **casual** lebih aktif saat libur, peluang untuk program konversi menjadi member."
        )

# ======================== Tab 4: Analisis lanjutan ========================
with tab4:
    st.subheader("Clustering tanpa machine learning: Manual Grouping & Binning")
    segment = create_segment_df(main_df)
    fig, ax = plt.subplots(figsize=(12, 4.5))
    segment.plot(kind="bar", ax=ax, color=[HIGHLIGHT, SECOND][: len(segment.columns)], width=0.75, rot=0)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", fontsize=9)
    ax.set_title("Rata-rata penyewaan per jam berdasarkan segmen waktu (manual grouping)")
    ax.set_xlabel("Segmen waktu")
    ax.set_ylabel("Rata-rata penyewaan per jam")
    ax.legend(title="Tipe hari", frameon=False)
    st.pyplot(fig)

    col1, col2 = st.columns(2)
    with col1:
        temp = daily_df.groupby("temp_group", observed=True)["total_rentals"].mean()
        fig, ax = plt.subplots(figsize=(7, 4.5))
        bars = ax.bar(temp.index.astype(str), temp.values,
                      color=[HIGHLIGHT if v == temp.max() else NEUTRAL for v in temp.values])
        ax.set_ylim(0, temp.max() * 1.2)
        bar_labels(ax, bars)
        ax.set_title("Rata-rata penyewaan harian per kategori suhu (binning)")
        ax.set_xlabel("Kategori suhu")
        ax.set_ylabel("Rata-rata penyewaan per hari")
        ax.tick_params(axis="x", labelsize=9)
        st.pyplot(fig)
    with col2:
        demand_labels = ["Rendah", "Sedang", "Tinggi", "Sangat Tinggi"]
        daily_df["demand_level"] = pd.cut(daily_df["total_rentals"], bins=[0, 2500, 4500, 6500, 10000],
                                          labels=demand_labels, include_lowest=True)
        ct = pd.crosstab(daily_df["season"], daily_df["demand_level"]).reindex(columns=demand_labels, fill_value=0)
        fig, ax = plt.subplots(figsize=(7, 4.5))
        sns.heatmap(ct, annot=True, fmt="d", cmap="Blues", cbar_kws={"label": "Jumlah hari"}, ax=ax)
        ax.set_title("Jumlah hari per tingkat permintaan & musim (binning)")
        ax.set_xlabel("Tingkat permintaan harian")
        ax.set_ylabel("Musim")
        st.pyplot(fig)

    st.caption("Tingkat permintaan harian: Rendah < 2.500 · Sedang 2.500–4.500 · Tinggi 4.500–6.500 · Sangat Tinggi > 6.500 sepeda/hari")

st.caption("Sumber data: Bike Sharing Dataset (Fanaee-T & Gama, 2013) · Copyright © 2026 Faishal Muflih Irfanu Tsaqib")
