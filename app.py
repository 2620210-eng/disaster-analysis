import streamlit as st
import pandas as pd
import re

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

# 시스템 안내 펼침상자
with st.expander("📖 시스템 사용 방법 및 개발 목적 (클릭하여 확인)", expanded=False):
    st.markdown("""
    ### 🎯 1. 개발 목적
    * **임계값 기반 비상 제어:** 침수(수위) 및 지진(진동) 재난 발생 시 차단막 작동, 배수 펌프 가동, 경보 발령을 자동 수행하여 골든타임을 확보합니다.
    * **오작동 방지 및 안정성 확보:** 센서 노이즈 필터링(0cm 무시) 및 경보 후 쿨타임 메커니즘을 적용하여 연쇄 오작동을 차단합니다.
    * **데이터 기반 위험 관제:** 하드웨어 시리얼 로그를 실시간 파싱 및 통계 분석하여 위험이 집중되는 시간대를 시각화하고 사전 예방 체계를 구축합니다.

    ---

    ### 🛠️ 2. 시스템 사용 방법
    1. **시리얼 로그 수집:** 아두이노 IDE 시리얼 모니터에서 타임스탬프가 포함된 로그 데이터를 복사합니다.
    2. **데이터 입력:** 아래 텍스트 상자에 복사한 시리얼 로그를 그대로 붙여넣습니다.
    3. **분석 실행:** `📊 로그 파싱 및 위험 시간대 분석` 버튼을 클릭합니다.
    4. **결과 확인:** 
       * **통계 요약:** 평균/최대/최소 수위 및 진동 수치 확인
       * **골든타임 분석:** 침수/지진 감지 횟수 및 최다 위험 발생 시간대 확인
       * **시간대별 경보 수준 그래프:** 시간에 따른 위험 레벨 및 경보 발생 분포 확인
       * **종합 대처 보고서:** 주요 집중 시간대 및 시스템 자동 대처 현황 확인
    """)

st.write("---")
st.write("시리얼 모니터의 데이터를 복사해 붙여넣으면 시간대별 위험 분석 결과를 생성합니다.")

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

# 1. 시리얼 로그 입력 영역
raw_text = st.text_area(
    "센서 시리얼 로그 데이터 입력 (타임스탬프 포함)", 
    height=200, 
    placeholder="예시:\n14:29:03.031 -> [00:01:44 / 104089ms] 12.98,0\n15:58:05.571 -> 10.19,0\n15:58:09.179 -> 9.83,85",
    key="raw_text_input"
)

# 2. 데이터 분석 실행 버튼
if st.button("📊 로그 파싱 및 위험 시간대 분석", type="primary"):
    if not raw_text.strip():
        st.warning("⚠️ 분석할 데이터를 입력해 주세요.")
    else:
        try:
            parsed_data = []
            
            # [수정/강화된 정규식 파서]
            # 14:29:03.031 같은 시간 포맷 추출 패턴
            time_pattern = re.compile(r'(\d{2}:\d{2}:\d{2})')
            # 대괄호 [ ... ] 제거 패턴
            bracket_pattern = re.compile(r'\[.*?\]')
            # 숫자(실수/정수) 2개 연속 추출 패턴 (예: 12.98, 0)
            sensor_pattern = re.compile(r'([-+]?\d*\.?\d+)\s*,\s*([-+]?\d*\.?\d+)')

            for line in raw_text.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                
                # 1. 시간 추출 (줄 전체에서 HH:MM:SS 검색)
                t_match = time_pattern.search(line)
                clean_time = t_match.group(1) if t_match else None

                # 2. 대괄호 [ ... ] 제거
                clean_line = bracket_pattern.sub('', line)

                # 3. 거리, 진동 수치 추출 (마지막 숫자,숫자 형태 감지)
                s_match = sensor_pattern.search(clean_line)
                if s_match:
                    try:
                        dist = float(s_match.group(1))
                        vib = float(s_match.group(2))
                        
                        status_str, status_level = evaluate_status(dist, vib)
                        
                        parsed_data.append({
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
                st.error("❌ 유효한 센서 데이터를 찾지 못했습니다. 올바른 형식인지 확인해 주세요.")
            else:
                st.success(f"✅ 총 {len(df)}개 센서 로그 정상 파싱 완료!")

                # [분석 1] 센서 요약 통계
                st.subheader("📈 통계 요약")
                stats = pd.DataFrame({
                    '수위 거리 (Distance_cm)': [
                        df['Distance_cm'].mean(),
                        df['Distance_cm'].max(),
                        df['Distance_cm'].min(),
                        df['Distance_cm'].std()
                    ],
                    '진동 수치 (Vibration)': [
                        df['Vibration'].mean(),
                        df['Vibration'].max(),
                        df['Vibration'].min(),
                        df['Vibration'].std()
                    ]
                }, index=['평균값', '최댓값', '최솟값', '표준편차'])
                st.dataframe(stats.round(2), use_container_width=True)

                # [분석 2] 위험 조건 카운트 및 집중 시간대 도출
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

                # 주요 위험 집중 시간대 추출 로직 (대용량 데이터 대응)
                most_frequent_time_str = "감지된 위험 없음 (정상 범위)"
                if len(danger_df) > 0:
                    valid_times = danger_df['Time'].dropna()
                    if not valid_times.empty:
                        # HH:MM 단위로 그룹화하여 최고 빈도 시간대 도출
                        hour_mins = valid_times.apply(lambda x: str(x)[:5] if len(str(x)) >= 5 else str(x))
                        top_modes = hour_mins.mode()
                        if not top_modes.empty:
                            most_frequent_time_str = f"약 **{top_modes.iloc[0]}** 부근"
                        else:
                            most_frequent_time_str = f"약 **{hour_mins.iloc[0]}** 부근"
                    
                    st.error(f"🚨 **주요 위험 집중 시간대:** {most_frequent_time_str}에 빈번한 위험이 감지되었습니다.")
                    st.write("📋 **위험 이벤트 로그 목록 (상위 100건):**")
                    st.dataframe(
                        danger_df[['Time', 'Distance_cm', 'Vibration', 'Status']].head(100), 
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("✅ 데이터 수집 기간 내 위험 상태(침수/산사태 심각)가 감지되지 않았습니다. (안전)")

                st.markdown("---")

                # [분석 3] 시간대별 경보 수준 분석
                st.subheader("🚨 시간대별 경보 수준 분석")
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    st.markdown("##### 📊 경보 단계별 감지 횟수")
                    status_counts = df['Status'].value_counts()
                    st.bar_chart(status_counts)

                with chart_col2:
                    st.markdown("##### 📈 시간에 따른 경보 레벨 변화 추이")
                    st.caption("레벨 기준: 0(안전) ➔ 1(수위 주의) ➔ 2(수위 경고) ➔ 3(침수 심각) ➔ 4(산사태 심각)")
                    if 'Time' in df.columns and df['Time'].notna().any():
                        level_chart_df = df.set_index('Time')[['Status_Level']]
                        st.line_chart(level_chart_df)
                    else:
                        st.line_chart(df[['Status_Level']])

                st.markdown("---")

                # [분석 4] 시계열 원본 센서 그래프
                st.subheader("📉 시간에 따른 원본 센서 데이터 추이")
                if 'Time' in df.columns and df['Time'].notna().any():
                    chart_df = df.set_index('Time')[['Distance_cm', 'Vibration']]
                    st.line_chart(chart_df)
                else:
                    st.line_chart(df[['Distance_cm', 'Vibration']])

                st.markdown("---")

                # [분석 5] 📋 종합 관제 요약 및 자동 대처 보고서
                st.subheader("📋 종합 관제 요약 & 시스템 대처 리포트")

                flood_cnt = df['Flood_Danger'].sum()
                quake_cnt = df['Quake_Danger'].sum()
                total_danger_cnt = flood_cnt + quake_cnt

                # 위험 발생 문구 바인딩
                if total_danger_cnt > 0:
                    time_summary_text = most_frequent_time_str
                else:
                    time_summary_text = "위험 상황 미발생 (안전)"

                rep_col1, rep_col2 = st.columns(2)

                with rep_col1:
                    st.markdown("##### 🕒 1. 위험 발생 분석 요약")
                    st.markdown(f"""
                    * **주요 위험 집중 시간대:** {time_summary_text}
                    * **🌊 침수 심각 감지:** **{flood_cnt}회** (수위 0.5cm ~ 11.0cm)
                    * **⛰️ 산사태/지진 감지:** **{quake_cnt}회** (진동 수치 15 초과)
                    * **총 위험 이벤트:** 총 **{total_danger_cnt}회** 발생
                    """)

                with rep_col2:
                    st.markdown("##### 🛡️ 2. 하드웨어 자동 대처 현황")
                    
                    barrier_status = "🚨 **[작동 완료]** 차단막 하강 (진입 통제)" if total_danger_cnt > 0 else "🟢 **[대기 중]** 통행 가능"
                    pump_status = "🚨 **[가동 완료]** 배수 펌프 비상 동작" if flood_cnt > 0 else "🟢 **[대기 중]** 수위 안정"
                    alarm_status = "🚨 **[경보 발령]** 현장 사이렌 & LED 켜짐" if total_danger_cnt > 0 else "🟢 **[정상]** 평시 관제 상태"

                    st.markdown(f"""
                    * **🚧 진입 차단막 (서보 모터):** {barrier_status}
                    * **🌊 비상 배수 펌프 (모터 릴레이):** {pump_status}
                    * **🔔 현장 경보 장치:** {alarm_status}
                    """)

        except Exception as e:
            st.error(f"❌ 데이터 분석 중 오류 발생: {e}")
