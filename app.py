import streamlit as st
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="재난 감지 및 통합 관제 시스템", layout="wide")

st.title("🚨 실시간 재난 감지 및 통합 관제 시스템")

# 세션 상태 초기화 (데이터 저장용)
if "logs" not in st.session_state:
    st.session_state.logs = []

# 삭제 버튼
col_title, col_btn = st.columns([4, 1])
with col_btn:
    if st.button("🗑️ 전체 기록 삭제", use_container_width=True):
        st.session_state.logs = []
        st.success("모든 기록이 삭제되었습니다.")

# 최신 상태 표시
st.subheader("현재 감지 상태")
if len(st.session_state.logs) > 0:
    latest = st.session_state.logs[-1]
    dist_val = latest["수위(cm)"]
    vib_val = latest["진동"]
    status_val = latest["상태"]
    
    if "심각" in status_val:
        st.error(f"🚨 경보 발생: {status_val}")
    elif "경고" in status_val or "주의" in status_val:
        st.warning(f"⚠️ 상태: {status_val}")
    else:
        st.success(f"🟢 상태: {status_val}")
        
    st.write(f"**수위(거리):** {dist_val:.1f} cm | **진동 수치:** {vib_val}")
else:
    st.info("데이터 수신 대기 중...")

st.markdown("---")

# 1. 심각 경보 발생 요약
st.subheader("⚡ 심각 경보 발생 요약 (간단 버전)")
df_all = pd.DataFrame(st.session_state.logs)

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 📋 심각 경보 발생 목록")
    if not df_all.empty:
        critical_df = df_all[df_all["상태"].str.contains("심각", na=False)]
        if not critical_df.empty:
            st.dataframe(critical_df[["시각", "상태"]], use_container_width=True)
        else:
            st.write("경보 기록이 없습니다.")
    else:
        st.write("기록된 데이터가 없습니다.")

with col2:
    st.markdown("##### 📊 경보 유형별 발생 횟수")
    if not df_all.empty:
        flood_count = len(df_all[df_all["상태"].str.contains("침수", na=False)])
        landslide_count = len(df_all[df_all["상태"].str.contains("산사태", na=False)])
        summary_data = pd.DataFrame({
            "유형": ["침수 심각", "산사태 감지"],
            "횟수": [flood_count, landslide_count]
        })
        st.bar_chart(summary_data.set_index("유형"))
    else:
        st.write("데이터가 없습니다.")

st.markdown("---")

# 2. 실시간 상세 데이터 및 로그
st.subheader("📈 실시간 상세 측정 데이터")
col3, col4 = st.columns(2)

with col3:
    st.markdown("##### 실시간 센서 수치 변화")
    if not df_all.empty:
        st.line_chart(df_all.set_index("시각")[["수위(cm)", "진동"]])
    else:
        st.write("차트 데이터가 없습니다.")

with col4:
    st.markdown("##### 전체 데이터 로그")
    if not df_all.empty:
        st.dataframe(df_all.iloc[::-1], use_container_width=True)
    else:
        st.write("기록된 데이터가 없습니다.")
