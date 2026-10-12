import streamlit as st
import pandas as pd
import io

st.title("🚨 재난 대응 센서 데이터 분석기")
st.write("아두이노 시리얼 모니터에서 복사한 텍스트를 아래에 붙여넣어 주세요.")

raw_text = st.text_area("센서 데이터 입력 (거리,진동)", height=200, placeholder="예시:\n13.5,0\n12.1,50\n10.2,3")

if st.button("📊 데이터 분석하기"):
    if not raw_text.strip():
        st.warning("⚠️ 데이터를 붙여넣은 후 버튼을 눌러주세요!")
    else:
        try:
            df = pd.read_csv(io.StringIO(raw_text.strip()), header=None, names=['Distance_cm', 'Vibration'])
            df['Distance_cm'] = pd.to_numeric(df['Distance_cm'], errors='coerce')
            df['Vibration'] = pd.to_numeric(df['Vibration'], errors='coerce')
            df = df.dropna()

            st.success(f"✅ 총 {len(df)}개의 데이터 분석 완료!")
            st.subheader("📈 통계 요약")
            
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
            }, index=['평균값 (Mean)', '최댓값 (Max)', '최솟값 (Min)', '표준편차 (Std)'])

            st.dataframe(stats.round(2), use_container_width=True)

            st.subheader("📉 센서 데이터 변화 그래프")
            st.line_chart(df[['Distance_cm', 'Vibration']])

        except Exception as e:
            st.error("❌ 데이터 형식이 올바르지 않습니다. '거리,진동' 형태인지 확인해 주세요.")
