"""Streamlit Alpha MVP dashboard.
run: PYTHONPATH=. streamlit run sepa/ui/dashboard_alpha.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import streamlit as st


st.set_page_config(page_title="SEPA Alpha Dashboard", layout="wide")
st.title("SEPA Alpha Dashboard (MVP)")

with st.sidebar:
    st.subheader("Pipeline")
    if st.button("Run Live Cycle"):
        r = subprocess.run(["python3", "-m", "sepa.pipeline.run_live_cycle"], capture_output=True, text=True)
        st.code((r.stdout or "") + (r.stderr or ""))


col1, col2 = st.columns(2)

with col1:
    if st.button("1) Generate Sample Data"):
        r = subprocess.run(["python3", "sepa/pipeline/generate_sample_data.py"], capture_output=True, text=True)
        st.code((r.stdout or "") + (r.stderr or ""))

with col2:
    if st.button("2) Run Pipeline"):
        r = subprocess.run(["python3", "sepa/pipeline/run_mvp.py"], capture_output=True, text=True)
        st.code((r.stdout or "") + (r.stderr or ""))

signals_root = Path(".omx/artifacts/daily-signals")
latest = sorted(signals_root.glob("*/alpha-passed.json"))

st.divider()
if latest:
    p = latest[-1]
    data = json.loads(p.read_text(encoding="utf-8"))
    st.success(f"Latest Alpha: {p}")

    if data:
        summary = [
            {"symbol": x["symbol"], "score": x["score"], "rs_percentile": x["rs_percentile"]}
            for x in data
        ]
        st.subheader("Top Candidates")
        st.dataframe(summary, use_container_width=True)

        st.subheader("Check Matrix")
        for row in data:
            with st.expander(f"{row['symbol']} | score={row['score']}"):
                st.json(row["checks"])
    else:
        st.warning("alpha-passed.json is empty")

    st.download_button(
        "Download alpha-passed.json",
        data=json.dumps(data, ensure_ascii=False, indent=2),
        file_name="alpha-passed.json",
    )
else:
    st.info("No alpha-passed.json found yet.")
