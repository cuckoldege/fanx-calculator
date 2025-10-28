
import streamlit as st

st.set_page_config(page_title="FANX Earnings Calculator v4.0", page_icon="💠", layout="wide")

def ccs_single(xp, w_a, w_r, tvr, ai_s, phi, tvr_cap=None):
    if tvr_cap is not None and tvr_cap > 0:
        tvr = min(tvr, tvr_cap)
    return ((xp * w_a * w_r) + (tvr * ai_s)) * phi

def payout_usd(nev_usd, fan_pool_share, ccs_i, sum_ccs):
    if sum_ccs <= 0:
        return 0.0
    return (nev_usd * fan_pool_share) * (ccs_i / sum_ccs)

def tokens_from_usd(payout_usd_value, fx_ftx_usd):
    if fx_ftx_usd <= 0:
        return None
    return payout_usd_value / fx_ftx_usd

def estimate_sum_ccs_by_avg(n_active, xp_avg, w_a_avg, w_r_avg, tvr_avg, ai_s_avg, phi_avg, tvr_cap=None):
    ccs_avg = ccs_single(xp_avg, w_a_avg, w_r_avg, tvr_avg, ai_s_avg, phi_avg, tvr_cap)
    return ccs_avg * n_active, ccs_avg

st.title("💠 FANX Global Earnings Calculator v4.0")
st.caption("Every second counts, every action pays.")

with st.expander("Formüller (Özet)", expanded=False):
    st.markdown("**1) CCS:**  CCS_i = ((XP_i · W_a,i · W_r,i) + (TVR_i · AI_s,i)) · Φ_i")
    st.markdown("**2) 1 Fan (USD):**  Payout_i = (G_gross - C) × s_fan × (CCS_i / ΣCCS)")
    st.markdown("**3) Token:**  Payout_i,FTX = Payout_i,USD / (FTX/USD)")

st.divider()

colA, colB = st.columns([1.1, 1.2], gap="large")

with colA:
    st.subheader("0) Dönemsel Toplamlar")
    g_gross = st.number_input("Brüt Gelir (USD) – G_gross", min_value=0.0, value=123000.0, step=1000.0, format="%.2f")
    cost = st.number_input("Gider (USD) – C", min_value=0.0, value=17000.0, step=1000.0, format="%.2f")
    n_active = st.number_input("Aktif Kullanıcı – N", min_value=1, value=92786, step=1)

    st.markdown("**Dağıtım Oranları (Fan/Creator/DAO/Platform)**")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    s_fan = col_s1.slider("Fans (%)", min_value=0, max_value=100, value=40, step=1) / 100.0
    s_creator = col_s2.slider("Creators (%)", min_value=0, max_value=100, value=30, step=1) / 100.0
    s_dao = col_s3.slider("DAO (%)", min_value=0, max_value=100, value=20, step=1) / 100.0
    s_platform = col_s4.slider("Platform (%)", min_value=0, max_value=100, value=10, step=1) / 100.0

    total_share = s_fan + s_creator + s_dao + s_platform
    if abs(total_share - 1.0) > 1e-9:
        st.error("⚠️ Dağıtım oranları toplamı %100 olmalıdır.")
    nev = max(0.0, g_gross - cost)
    fan_pool_usd = nev * s_fan

    st.metric(label="Net Ekosistem Değeri (NEV)", value=f"${nev:,.2f}")
    st.metric(label="Fan Havuzu (USD)", value=f"${fan_pool_usd:,.2f}")

with colB:
    st.subheader("1) TVR Üst Sınır & Token Kur")
    tvr_cap_val = st.number_input("TVR Üst Sınır (Opsiyonel)", min_value=0.0, value=0.0, step=0.1, help="0 = sınırsız. >0 girerseniz TVR bu değeri geçemez.")
    tvr_cap = None if tvr_cap_val == 0.0 else tvr_cap_val
    fx_ftx_usd = st.number_input("FTX/USD Kur (Opsiyonel – token dönüşümü için)", min_value=0.0, value=0.0, step=0.001)

st.divider()

col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("2) 1 Fan Girdileri")
    xp_i = st.number_input("XP_i (fanın dönem XP toplamı)", min_value=0.0, value=1200.0, step=10.0)
    w_a_i = st.number_input("W_a,i (Aktiflik katsayısı)", min_value=0.1, value=1.20, step=0.05)
    w_r_i = st.number_input("W_r,i (Reputation katsayısı)", min_value=0.1, value=1.05, step=0.05)
    tvr_i = st.number_input("TVR_i (Zaman değeri)", min_value=0.0, value=9.0, step=0.1)
    ai_s_i = st.number_input("AI_s,i (AI kalite katsayısı)", min_value=0.1, value=1.10, step=0.05)
    phi_i = st.number_input("Φ_i (Ağ etkisi katsayısı)", min_value=0.1, value=1.10, step=0.05)

    ccs_i = ccs_single(xp_i, w_a_i, w_r_i, tvr_i, ai_s_i, phi_i, tvr_cap=tvr_cap)
    st.metric("CCS_i (Bileşik katkı skoru)", f"{ccs_i:,.4f}")

with col2:
    st.subheader("3) Toplam ΣCCS")
    mode = st.radio("Toplamı nasıl belirleyelim?", ["A) Doğrudan ΣCCS gir", "B) Ortalama değerlerle tahmin et"])

    if mode.startswith("A"):
        sum_ccs = st.number_input("ΣCCS (toplam katkı)", min_value=1.0, value=150_000_000.0, step=100000.0, format="%.4f")
        ccs_avg = None
    else:
        st.markdown("**Ortalama değerlerle tahmin**")
        xp_avg = st.number_input("XP_avg", min_value=0.0, value=1000.0, step=10.0)
        w_a_avg = st.number_input("W_a,avg", min_value=0.1, value=1.10, step=0.05)
        w_r_avg = st.number_input("W_r,avg", min_value=0.1, value=1.00, step=0.05)
        tvr_avg = st.number_input("TVR_avg", min_value=0.0, value=8.5, step=0.1)
        ai_s_avg = st.number_input("AI_s,avg", min_value=0.1, value=1.05, step=0.05)
        phi_avg = st.number_input("Φ_avg", min_value=0.1, value=1.05, step=0.05)
        sum_ccs, ccs_avg = estimate_sum_ccs_by_avg(n_active, xp_avg, w_a_avg, w_r_avg, tvr_avg, ai_s_avg, phi_avg, tvr_cap=tvr_cap)
        st.metric("Tahmini CCS_avg", f"{ccs_avg:,.4f}")
        st.metric("Tahmini ΣCCS", f"{sum_ccs:,.2f}")

st.divider()

st.subheader("4) 1 Fan Kazanç Sonuçları")
payout_i_usd = payout_usd(nev, s_fan, ccs_i, sum_ccs)
st.metric(label="Payout_i (USD)", value=f"${payout_i_usd:,.6f}")
if fx_ftx_usd > 0:
    payout_i_ftx = tokens_from_usd(payout_i_usd, fx_ftx_usd)
    st.metric(label="Payout_i (FTX)", value=f"{payout_i_ftx:,.6f} FTX")

avg_usd_equal = fan_pool_usd / n_active
st.caption(f"🔎 Karşılaştırma • Eşit pay olsaydı: ${avg_usd_equal:,.6f} / kullanıcı")

st.info("Hesaplama, NEV ve ΣCCS ile orantılıdır. N büyürken NEV sabitse kişi başına pay düşer; NEV N ile orantılı büyürse kişi başına ortalama sabit kalır.")

st.divider()
st.write("© FANX v4.0 – Decentralized Attention Economy.")
