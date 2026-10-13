import streamlit as st
import pandas as pd
import io
import re

st.title("🚨 재난 대응 센서 & 시간대별 위험 분석기")
st.write("시리얼 모니터의 타임스탬프가 포함된 텍스트를 붙여넣으시면, 위험이 집중되는 시간대를 분석해 드립니다.")

# 1. 텍스트 입력창
raw_text = st.text_area(
    "센서 데이터 입력 (타임스탬프 포함)", 
    height=200, 
    placeholder="예시:\n15:58:03.807 -> 14.82,9\n15:58:05.571 -> 10.19,0\n15:58:09.179 -> 9.83,85"
)

# 2. 분석 버튼
if st.button("📊 시각 및 위험 시간대 분석하기"):
    if not raw_text.strip():
        st.warning("⚠️ 데이터를 붙여넣은 후 버튼을 눌러주세요!")
    else:
        try:
            parsed_data = []
            
            # 한 줄씩 읽어서 시간, 거리, 진동 분리
            for line in raw_text.strip().splitlines():
                line = line.strip()
                if not line:
                    continue
                
                time_str = None
                data_str = line
                
                # '->'로 시간과 센서 값 구분
                if '->' in line:
                    parts = line.split('->')
                    time_str = parts[0].strip()
                    data_str = parts[1].strip()
                
                # 센서 값 (거리, 진동) 분리
                sensor_parts = data_str.split(',')
                if len(sensor_parts) == 2:
                    try:
                        dist = float(sensor_parts[0].strip())
                        vib = float(sensor_parts[1].strip())
                        
                        # 시간 텍스트 추출 (예: 15:58:03)
                        time_match = re.search(r'(\d{2}:\d{2}:\d{2})', time_str) if time_str else None
                        clean_time = time_match.group(1) if time_match else None
                        
                        parsed_data.append({
                            'Time': clean_time,
                            'Distance_cm': dist,
                            'Vibration': vib
                        })
                    except ValueError:
                        continue
            
            df = pd.DataFrame(parsed_data)

            if len(df) == 0:
                st.error("❌ 유효한 데이터를 찾지 못했습니다. 형식을 확인해 주세요!")
            else:
                st.success(f"✅ 총 {len(df)}개의 센서 기록 파싱 완료!")

                # ----------------------------------------------------
                # [분석 1] 기본 통계 요약
                # ----------------------------------------------------
                st.subheader("📈 기본 센서 통계")
                stats = pd.DataFrame({
                    '거리 센서 (Distance_cm)': [
                        df['Distance_cm'].mean(),
                        df['Distance_cm'].max(),
                        df['Distance_cm'].min(),
                        df['Distance_cm'].std()
                    ],
                    '진동 센서 (Vibration)': [
                        df['Vibration'].mean(),
                        df['Vibration'].max(),
                        df['Vibration'].min(),
                        df['Vibration'].std()
                    ]
                }, index=['평균값', '최댓값', '최솟값', '표준편차'])
                st.dataframe(stats.round(2), use_container_width=True)

                # ----------------------------------------------------
                # [분석 2] 위험 조건 판단 (침수 심각 11cm 이하 OR 진동 50 초과)
                # ----------------------------------------------------
                df['Flood_Danger'] = df['Distance_cm'] <= 11.0
                df['Quake_Danger'] = df['Vibration'] > 50.0
                df['Is_Danger'] = df['Flood_Danger'] | df['Quake_Danger']

                danger_df = df[df['Is_Danger']]

                st.subheader("⚠️ 위험 시간대 분석 결과")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("총 침수 심각 발생 횟수", f"{df['Flood_Danger'].sum()}회")
                with col2:
                    st.metric("총 지진 진동 발생 횟수", f"{df['Quake_Danger'].sum()}회")

                # 시간 데이터가 유효한 경우 집중 위험 시간대 계산
                if 'Time' in df.columns and df['Time'].notna().any():
                    if len(danger_df) > 0 and danger_df['Time'].notna().any():
                        # 시:분 기준으로 가장 위험이 많이 발생한 시간대 추출
                        danger_df['Hour_Min'] = danger_df['Time'].apply(lambda x: str(x)[:5] if pd.notna(x) else None)
                        most_frequent_time = danger_df['Hour_Min'].mode()
                        
                        if not most_frequent_time.empty:
                            st.error(f"🚨 **주요 위험 집중 시간대:** 약 **{most_frequent_time.iloc[0]}** 부근에 위험 상황이 제일 자주 발생했습니다!")
                        
                        st.write("📋 **위험 감지 기록 목록:**")
                        st.dataframe(danger_df[['Time', 'Distance_cm', 'Vibration']], use_container_width=True)
                    else:
                        st.info("✅ 데이터 수집 기간 중 위험 기준을 초과한 기록이 없습니다. (안전 상태)")
                else:
                    st.info("💡 타임스탬프(시간 정보)가 없어도 거리/진동 분석은 정상 수행됩니다.")

                # ----------------------------------------------------
                # [분석 3] 시간에 따른 거리 및 진동 추이 그래프
                # ----------------------------------------------------
                st.subheader("📉 시간에 따른 센서 변화 그래프")
                if 'Time' in df.columns and df['Time'].notna().any():
                    chart_df = df.set_index('Time')[['Distance_cm', 'Vibration']]
                    st.line_chart(chart_df)
                else:
                    st.line_chart(df[['Distance_cm', 'Vibration']])

        except Exception as e:
            st.error(f"❌ 데이터 처리 중 오류 발생: {e}")
