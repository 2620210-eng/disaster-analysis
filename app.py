import streamlit as st
import pandas as pd
import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="재난 감지 및 통합 관제 시스템",
    page_icon="🚨",
    layout="wide"
)

# 2. 데이터 저장용 세션 상태(Session State) 초기화
if "data_logs" not in st.session_state:
    st.session_state.data_logs = []

# 상태 판별 함수 (아두이노/Flask와 동일한 로직)
def get_status(dist, vib):
    if vib > 15:
        return "산사태 심각"
    elif 0.5 < dist <= 11.0:
        return "침수 심각"
    elif 11.0 < dist <= 13.0:
        return "수위 경고"
    elif 13.0 < dist <= 15.0:
        return "수위 주의"
    elif dist > 15.0:
        return "안전"
    else:
        return "미감지"

# 3. 상단 헤더 및 기록 삭제 버튼
col_title, col_clear = st.columns([4, 1])

with col_title:
    st.title("🚨 실시간 재난 감지 및 통합 관제 시스템")

with col_clear:
    st.write("") # 여백 맞춤용
    if st.button("🗑️ 전체 기록 삭제", use_container_width=True, type="secondary"):
        st.session_state.data_logs = []
        st.rerun()

st.markdown("---")

# 4. 📟 시리얼 텍스트 데이터 입력 사이드바
st.sidebar.header("📟 시리얼 텍스트 입력")
st.sidebar.write("아두이노 시리얼 모니터 형식의 텍스트를 입력하세요.")
st.sidebar.caption("예시: `12.5,5` (수위,진동)")

# 시리얼 텍스트 입력창
serial_input = st.sidebar.text_input("시리얼 데이터 (수위,진동)", value="12.5,5")

if st.sidebar.button("📥 시리얼 데이터 전송", type="primary", use_container_width=True):
    try:
        # 텍스트 파싱 (콤마 기준 분리)
        parts = serial_input.strip().split(',')
        if len(parts) == 2:
            dist_val = float(parts[0])
            vib_val = int(parts[1])
            
            now_time = datetime.datetime.now().strftime("%H:%M:%S")
            status_result = get_status(dist_val, vib_val)
            
            new_entry = {
                "시각": now_time,
                "수위(cm)": dist_val,
                "진동": vib_val,
                "상태": status_result
            }
            st.session_state.data_logs.append(new_entry)
            
            if len(st.session_state.data_logs) > 100:
                st.session_state.data_logs.pop(0)
                
            st.sidebar.success(f"수신 성공: {serial_input}")
            st.rerun()
        else:
            st.sidebar.error("형식이 올바르지 않습니다. `12.5,5` 형태로 입력해주세요.")
    except ValueError:
        st.sidebar.error("숫자 형식으로 입력해주세요. 예: `10.5,3`")

# 5. 현재 감지 상태 표시 카드
st.subheader("현재 감지 상태")

if len(st.session_state.data_logs) > 0:
    latest = st.session_state.data_logs[-1]
    cur_dist = latest["수위(cm)"]
    cur_vib = latest["진동"]
    cur_status = latest["상태"]

    if "심각" in cur_status:
        st.error(f"🚨 **[경보 발생] {cur_status}**")
    elif "경고" in cur_status or "주의" in cur_status:
        st.warning(f"⚠️ **[주의/경고] {cur_status}**")
    else:
        st.success(f"🟢 **[정상] {cur_status}**")

    col_stat1, col_stat2 = st.columns(2)
    col_stat1.metric("현재 수위 거리", f"{cur_dist:.1f} cm")
    col_stat2.metric("현재 진동 수치", f"{cur_vib}")
else:
    st.info("💡 왼쪽 사이드바에서 시리얼 텍스트(예: `10.5,20`)를 입력하고 [시리얼 데이터 전송] 버튼을 눌러주세요.")

st.markdown("---")

df = pd.DataFrame(st.session_state.data_logs)

# 6. ⚡ 심각 경보 발생 요약
st.subheader("⚡ 심각 경보 발생 요약 (간단 버전)")
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 📋 심각 경보 발생 목록")
    if not df.empty:
        critical_df = df[df["상태"].str.contains("심각", na=False)]
        if not critical_df.empty:
            st.dataframe(
                critical_df[["시각", "상태"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.write("발생한 심각 경보가 없습니다.")
    else:
        st.write("기록된 데이터가 없습니다.")

with col2:
    st.markdown("##### 📊 경보 유형별 발생 횟수")
    if not df.empty:
        flood_cnt = len(df[df["상태"].str.contains("침수", na=False)])
        landslide_cnt = len(df[df["상태"].str.contains("산사태", na=False)])
        
        summary_df = pd.DataFrame({
            "경보 유형": ["침수 심각", "산사태 감지"],
            "발생 횟수": [flood_cnt, landslide_cnt]
        }).set_index("경보 유형")
        
        st.bar_chart(summary_df)
    else:
        st.write("기록된 데이터가 없습니다.")

st.markdown("---")

# 7. 📈 실시간 상세 측정 데이터
st.subheader("📈 실시간 상세 측정 데이터")
col3, col4 = st.columns(2)

with col3:
    st.markdown("##### 실시간 센서 수치 변화")
    if not df.empty:
        st.line_chart(df.set_index("시각")[["수위(cm)", "진동"]])
    else:
        st.write("차트에 표시할 데이터가 없습니다.")

with col4:
    st.markdown("##### 전체 데이터 로그")
    if not df.empty:
        st.dataframe(
            df.iloc[::-1],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("기록된 데이터가 없습니다.")
