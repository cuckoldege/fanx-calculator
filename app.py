import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="FANX Earnings Calculator v4.1", page_icon="💠", layout="wide")

# ---------- Core math ----------
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

# ---------- UI: Header ----------
st.title("💠 FANX Global Earnings Calculator v4.1 — Gold Edition")
st.caption("Decentralized Attention Economy • A/B Scenario Compare • Presets")

with st.expander("Formüller (Özet)", expanded=False):
    st.markdown("**CCS_i** = ((XP_i · W_a,i · W_r,i) + (TVR_i · AI_s,i)) · Φ_i  
"
                "**Payout_i,USD** = (NEV × s_fan) × (CCS_i / ΣCCS)  
"
                "**Token**: Payout_i,FTX = Payout_i,USD / (FTX/USD)")

st.divider()

# ---------- Section 0: Totals ----------
colA, colB = st.columns([1.1, 1.2], gap="large")
with colA:
    st.subheader("0) Dönemsel Toplamlar")
    g_gross = st.number_input("Brüt Gelir (USD) – G_gross", min_value=0.0, value=123000.0, step=1000.0, format="%.2f")
    cost = st.number_input("Gider (USD) – C", min_value=0.0, value=17000.0, step=1000.0, format="%.2f")
    n_active = st.number_input("Aktif Kullanıcı – N", min_value=1, value=92786, step=1,
                               help="Dönem boyunca en az bir eylem yapan kullanıcı")

    st.markdown("**Dağıtım Oranları (Fan/Creator/DAO/Platform)**")
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    s_fan = col_s1.slider("Fans (%)", 0, 100, 40, 1) / 100.0
    s_creator = col_s2.slider("Creators (%)", 0, 100, 30, 1) / 100.0
    s_dao = col_s3.slider("DAO (%)", 0, 100, 20, 1) / 100.0
    s_platform = col_s4.slider("Platform (%)", 0, 100, 10, 1) / 100.0
    total_share = s_fan + s_creator + s_dao + s_platform
    if abs(total_share - 1.0) > 1e-9:
        st.error("⚠️ Dağıtım oranları toplamı %100 olmalıdır.")

    nev = max(0.0, g_gross - cost)
    fan_pool_usd = nev * s_fan
    st.metric(label="Net Ekosistem Değeri (NEV)", value=f"${nev:,.2f}")
    st.metric(label="Fan Havuzu (USD)", value=f"${fan_pool_usd:,.2f}")

with colB:
    st.subheader("1) TVR Üst Sınır & Token Kur")
    tvr_cap_val = st.number_input("TVR Üst Sınır (Opsiyonel)", min_value=0.0, value=0.0, step=0.1,
                                  help="0 = sınırsız. >0 girerseniz TVR bu değeri geçemez.")
    tvr_cap = None if tvr_cap_val == 0.0 else tvr_cap_val
    fx_ftx_usd = st.number_input("FTX/USD Kur (Opsiyonel – token dönüşümü için)", min_value=0.0, value=0.0, step=0.001)

st.divider()

# ---------- Presets ----------
st.subheader("🔧 1-Click Presets (Ortalama değer setleri)")
preset = st.selectbox("Bir kullanım senaryosu seçin:", [
    "— Elle gireceğim —",
    "Music Launch (MENA)",
    "Sports Highlight (JP/KR)",
    "Influencer Collab (US/EU)"
])

def preset_values(name):
    if name == "Music Launch (MENA)":
        return dict(xp=900, wa=1.08, wr=1.00, tvr=8.0, ai=1.05, phi=1.04)
    if name == "Sports Highlight (JP/KR)":
        return dict(xp=1100, wa=1.12, wr=1.03, tvr=9.2, ai=1.08, phi=1.07)
    if name == "Influencer Collab (US/EU)":
        return dict(xp=1500, wa=1.18, wr=1.05, tvr=10.0, ai=1.12, phi=1.12)
    return None

preset_vals = preset_values(preset)

st.divider()

# ---------- Section 2 & 3: A/B compare ----------
st.subheader("🆚 A/B Senaryo Karşılaştırma (tek tıkla)")

def fan_inputs(label_prefix, defaults=None):
    c1, c2, c3 = st.columns(3)
    if defaults is None:
        defaults = dict(xp=1200.0, wa=1.20, wr=1.05, tvr=9.0, ai=1.10, phi=1.10)
    xp = c1.number_input(f"{label_prefix} XP", min_value=0.0, value=float(defaults['xp']), step=10.0)
    wa = c2.number_input(f"{label_prefix} W_a", min_value=0.1, value=float(defaults['wa']), step=0.05)
    wr = c3.number_input(f"{label_prefix} W_r", min_value=0.1, value=float(defaults['wr']), step=0.05)
    c4, c5, c6 = st.columns(3)
    tvr = c4.number_input(f"{label_prefix} TVR", min_value=0.0, value=float(defaults['tvr']), step=0.1)
    ai = c5.number_input(f"{label_prefix} AI_s", min_value=0.1, value=float(defaults['ai']), step=0.05)
    phi = c6.number_input(f"{label_prefix} Φ", min_value=0.1, value=float(defaults['phi']), step=0.05)
    return dict(xp=xp, wa=wa, wr=wr, tvr=tvr, ai=ai, phi=phi)

colA, colB = st.columns(2, gap="large")
a_defaults = preset_vals or dict(xp=1200, wa=1.20, wr=1.05, tvr=9.0, ai=1.10, phi=1.10)
b_defaults = dict(xp=900, wa=1.05, wr=1.00, tvr=7.5, ai=1.00, phi=1.00)

with colA:
    st.markdown("### **Senaryo A (İyi/aktif fan)**")
    A = fan_inputs("A", a_defaults)

with colB:
    st.markdown("### **Senaryo B (Ortalama fan)**")
    B = fan_inputs("B", b_defaults)

# ---------- ΣCCS mode ----------
st.divider()
st.subheader("ΣCCS (Toplam katkı) modu")

mode = st.radio("Toplamı nasıl belirleyelim?", ["A) Doğrudan ΣCCS gir", "B) Ortalama değerlerle tahmin et"])

if mode.startswith("A"):
    sum_ccs = st.number_input("ΣCCS (toplam katkı)", min_value=1.0, value=150_000_000.0, step=100000.0, format="%.4f")
    ccs_avg = None
else:
    st.markdown("**Ortalama değerlerle tahmin**")
    if preset_vals:
        xp_avg = st.number_input("XP_avg", min_value=0.0, value=float(preset_vals['xp']), step=10.0)
        w_a_avg = st.number_input("W_a,avg", min_value=0.1, value=float(preset_vals['wa']), step=0.05)
        w_r_avg = st.number_input("W_r,avg", min_value=0.1, value=float(preset_vals['wr']), step=0.05)
        tvr_avg = st.number_input("TVR_avg", min_value=0.0, value=float(preset_vals['tvr']), step=0.1)
        ai_s_avg = st.number_input("AI_s,avg", min_value=0.1, value=float(preset_vals['ai']), step=0.05)
        phi_avg = st.number_input("Φ_avg", min_value=0.1, value=float(preset_vals['phi']), step=0.05)
    else:
        xp_avg = st.number_input("XP_avg", min_value=0.0, value=1000.0, step=10.0)
        w_a_avg = st.number_input("W_a,avg", min_value=0.1, value=1.10, step=0.05)
        w_r_avg = st.number_input("W_r,avg", min_value=0.1, value=1.00, step=0.05)
        tvr_avg = st.number_input("TVR_avg", min_value=0.0, value=8.5, step=0.1)
        ai_s_avg = st.number_input("AI_s,avg", min_value=0.1, value=1.05, step=0.05)
        phi_avg = st.number_input("Φ_avg", min_value=0.1, value=1.05, step=0.05)

    sum_ccs, ccs_avg = estimate_sum_ccs_by_avg(n_active, xp_avg, w_a_avg, w_r_avg, tvr_avg, ai_s_avg, phi_avg, tvr_cap=tvr_cap)
    st.metric("Tahmini CCS_avg", f"{ccs_avg:,.4f}")
    st.metric("Tahmini ΣCCS", f"{sum_ccs:,.2f}")

# ---------- Compute outcomes ----------
def compute_results(fan_dict):
    ccs = ccs_single(fan_dict['xp'], fan_dict['wa'], fan_dict['wr'], fan_dict['tvr'], fan_dict['ai'], fan_dict['phi'], tvr_cap=tvr_cap)
    payout = payout_usd(nev, s_fan, ccs, sum_ccs)
    token = tokens_from_usd(payout, fx_ftx_usd) if fx_ftx_usd and fx_ftx_usd > 0 else None
    return ccs, payout, token

ccs_A, payout_A, token_A = compute_results(A)
ccs_B, payout_B, token_B = compute_results(B)

st.divider()
st.subheader("📊 Sonuçlar — A/B Karşılaştırma")

baseline_equal = (nev * s_fan) / n_active

df = pd.DataFrame([
    {"Senaryo": "A (İyi/aktif)", "CCS": ccs_A, "Payout (USD)": payout_A, "Eşit Pay (USD)": baseline_equal},
    {"Senaryo": "B (Ortalama)", "CCS": ccs_B, "Payout (USD)": payout_B, "Eşit Pay (USD)": baseline_equal},
])

st.dataframe(df.style.format({"CCS": "{:,.4f}", "Payout (USD)": "${:,.6f}", "Eşit Pay (USD)": "${:,.6f}"}), use_container_width=True)

st.bar_chart(df.set_index("Senaryo")[["Payout (USD)"]])

# ---------- CSV export ----------
csv_buf = StringIO()
df.to_csv(csv_buf, index=False)
st.download_button("⬇️ Sonuçları CSV olarak indir", data=csv_buf.getvalue(), file_name="fanx_ab_results.csv", mime="text/csv")

st.caption(f"Baseline (eşit pay) = ${(baseline_equal):,.6f} / kullanıcı • NEV = ${nev:,.2f} • Fan Pool = ${fan_pool_usd:,.2f}")
st.write("© FANX v4.1 — A/B Scenario Compare, Presets, CSV export.")
