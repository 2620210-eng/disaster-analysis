import streamlit as st
import pandas as pd
import re
from datetime import datetime, timedelta

# 대시보드 기본 설정
st.set_page_config(
    page_title="재난 관제 데이터 분석기",
    page_icon="🚨",
    layout="wide"
)

# 사이드바 관제 센터
st.sidebar.title("🛡️ 재난 관제 시스템")
st.sidebar.success("● 시스템 상태: 가동 중")
st.sidebar.info("연결 장치: 초음파 센서, 진동 센서, 모터 릴레이, 서보 차단막")

# 삭제 버튼 콜백 함수
def clear_text():
    st.session_state["raw_text_input"] = ""

# 헤더 영역 및 삭제 버튼 배치
col_header, col_reset = st.columns([4, 1])

with col_header:
    st.title("🚨 스마트 재난 대응 센서 & 시간대별 위험 분석기")

with col_reset:
    st.write("") 
    st.write("")
    st.button("🗑️ 전체 입력/기록 삭제", type="secondary", use_container_width=True, on_click=clear_text)

# 상태 판별 및 레벨 부여 함수
def evaluate_status(dist, vib):
    if vib > 15.0:
        return "산사태 심각", 4
    elif 0.5 < dist <= 11.0:
        return "침수 심각", 3
    elif 11.0 < dist <= 13.0:
        return "수위 경고", 2
    elif 13.0 < dist <= 15.0:
        return "수위 주의", 1
    elif dist > 15.0:
        return "안전", 0
    else:
        return "미감지", 0

# 1. 수집 조건 및 입력 영역
st.subheader("⚙️ 센서 데이터 수집 설정")
col_time1, col_time2 = st.columns(2)

with col_time1:
    start_time_input = st.time_input("측정 시작 시각 (타임스탬프 누락 시 보정용)", value=datetime.strptime("14:00:00", "%H:%M:%S").time())

with col_time2:
    sample_interval = st.number_input("센서 측정 간격 (초)", min_value=0.1, value=1.0, step=0.5)

raw_text = st.text_area(
    "센서 시리얼 로그 데이터 입력", 
    height=200, 
    placeholder="예시:\n12.98,0\n10.19,0\n9.83,85",
    key="raw_text_input"
)

# 2. 데이터 분석 실행 버튼
if st.button("📊 로그 파싱 및 위험 시간대 분석", type="primary"):
    if not raw_text.strip():
        st.warning("⚠️ 분석할 데이터를 입력해 주세요.")
    else:
        try:
            parsed_data = []
            time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2})')
            bracket_pattern = re.compile(r'\[.*?\]')
            sensor_pattern = re.compile(r'([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)')

            # 시작 기준 시간 생성
            base_datetime = datetime.combine(datetime.today(), start_time_input)

            for idx, line in enumerate(raw_text.strip().splitlines(), start=0):
                line = line.strip()
                if not line:
                    continue
                
                clean_time = None

                # 로그 자체에 시간 텍스트가 존재하는지 검사
                if '->' in line:
                    before_arrow = line.split('->')[0]
                    t_match = time_pattern.search(before_arrow)
                    if t_match:
                        clean_time = t_match.group(1)

                if not clean_time:
                    no_brackets = bracket_pattern.sub('', line)
                    t_match = time_pattern.search(no_brackets)
                    if t_match:
                        clean_time = t_match.group(1)

                # 로그에 시간이 없는 경우: 시작 시간 + (줄번호 * 측정간격) 자동 생성
                if not clean_time:
                    calculated_time = base_datetime + timedelta(seconds=idx * sample_interval)
                    clean_time = calculated_time.strftime("%H:%M:%S")

                # 센서 수치 파싱
                clean_line = bracket_pattern.sub('', line)
                s_match = sensor_pattern.search(clean_line)
                
                if s_match:
                    try:
                        dist = float(s_match.group(1))
                        vib = float(s_match.group(2))
                        status_str, status_level = evaluate_status(dist, vib)
                        
                        parsed_data.append({
                            'Seq': idx + 1,
                            'Time': clean_time,
                            'Distance_cm': dist,
                            'Vibration': vib,
                            'Status': status_str,
                            'Status_Level': status_level
                        })
                    except ValueError:
                        continue
            
            df = pd.DataFrame(parsed_data)

            if len(df) == 0:
                st.error("❌ 유효한 센서 데이터를 찾지 못했습니다.")
            else:
                st.success(f"✅ 총 {len(df)}개 센서 로그 정상 파싱 완료!")

                # 통계 요약
                st.subheader("📈 통계 요약")
                stats = pd.DataFrame({
                    '수위 거리 (Distance_cm)': [df['Distance_cm'].mean(), df['Distance_cm'].max(), df['Distance_cm'].min(), df['Distance_cm'].std()],
                    '진동 수치 (Vibration)': [df['Vibration'].mean(), df['Vibration'].max(), df['Vibration'].min(), df['Vibration'].std()]
                }, index=['평균값', '최댓값', '최솟값', '표준편차'])
                st.dataframe(stats.round(2), use_container_width=True)

                # 위험 분석
                df['Flood_Danger'] = df['Status'] == "침수 심각"
                df['Quake_Danger'] = df['Status'] == "산사태 심각"
                df['Is_Danger'] = df['Status_Level'] >= 3

                danger_df = df[df['Is_Danger']]

                st.subheader("⚠️ 위험 상황 및 골든타임 분석")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("침수 심각 감지 횟수", f"{df['Flood_Danger'].sum()}회")
                with col2:
                    st.metric("지진/산사태 감지 횟수", f"{df['Quake_Danger'].sum()}회")

                if len(danger_df) > 0:
                    hour_mins = danger_df['Time'].apply(lambda x: str(x)[:5])
                    top_mode = hour_mins.mode().iloc[0]
                    
                    st.error(f"🚨 **주요 위험 집중 시간대:** 약 **{top_mode}** 부근에 위험이 집중되었습니다.")
                    st.write("📋 **위험 이벤트 로그 목록 (상위 100건):**")
                    st.dataframe(
                        danger_df[['Seq', 'Time', 'Distance_cm', 'Vibration', 'Status']].head(100), 
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("✅ 감지된 위험 상태가 없습니다. (안전)")

                st.markdown("---")

                # 경보 레벨 변화 추이
                st.subheader("🚨 시간대별 경보 레벨 추이")
                level_chart_df = df.set_index('Time')[['Status_Level']]
                st.line_chart(level_chart_df)

                # 원본 센서 그래프
                st.subheader("📉 시간에 따른 원본 센서 데이터 추이")
                chart_df = df.set_index('Time')[['Distance_cm', 'Vibration']]
                st.line_chart(chart_df)

        except Exception as e:
            st.error(f"❌ 데이터 분석 중 오류 발생: {e}")
