import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os

FONT_PATH = "NanumGothic.ttf"

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("Nanum", "", FONT_PATH, uni=True)
        self.set_font("Nanum", "", 12)

    def header(self):
        pass

    def chapter_title(self, title):
        self.set_font("Nanum", "", 14)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)

    def add_table(self, data, col_widths=None, align="L", bold_first_col=False):
        epw = self.w - 2 * self.l_margin  # ✅ epw 직접 계산
        if col_widths is None:
            col_widths = [epw / len(data[0])] * len(data[0])
        for i, row in enumerate(data):
            for j, datum in enumerate(row):
                self.set_font("Nanum", "", 12)
                self.cell(col_widths[j], 10, str(datum), border=1, align=align)
            self.ln()

st.title("수행평가 결과 PDF 생성기")

uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("CSV 파일이 업로드되었습니다.")

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for idx, row in df.iterrows():
        pdf.add_page()
        pdf.chapter_title("2학년 1학기 물리학1 수행평가 결과 안내서")

        # 1. 인적사항
        table1 = [[row[0], row[1], row[2], '총점(40점 만점):', row[3]]]
        pdf.add_table(table1, align="R")

        # 2. 실험 평가
        pdf.set_font("Nanum", "", 12)
        pdf.cell(0, 10, "1. 실험 평가: 실험(25점)=실험 활동(10점)+활동지 작성(15점)", ln=True)

        table2 = [["(1) 채점 결과(점수)", row[4]], ["- 17개 항목 중 맞은 항목 개수", row[7]]]
        pdf.add_table(table2)

        table3 = [
            ["(2-1) [3. 실험 결과] 관련 감점 사유", ""],
            ["- 1번 항목", row[25]],
            ["- 2번 항목", row[26]],
            ["- 3번 항목", row[27]],
            ["- 4번 항목", row[28]],
        ]
        pdf.add_table(table3)

        table4 = [
            ["(2-2) [4.결과 정리 및 해석] 관련 감점 사유", ""],
            ["- 5번 항목", row[29]],
            ["- 6번 항목", row[30]],
            ["- 7번 항목", row[31]],
            ["- 8번 항목", row[32]],
            ["- 9번 항목", row[33]],
            ["- 10번 항목", row[34]],
        ]
        pdf.add_table(table4)

        table5 = [
            ["(2-3) [5. 생각해보기] 관련 감점 사유", ""],
            ["- 11번 항목", row[35]],
            ["- 12번 항목", row[36]],
            ["- 13번 항목", row[37]],
            ["- 14번 항목", row[38]],
            ["- 15번 항목", row[39]],
        ]
        pdf.add_table(table5)

        table6 = [
            ["(2-4) [6. 탐구 확인 문제] 관련 감점 사유", ""],
            ["- 16번 항목", row[40]],
            ["- 17번 항목", row[41]],
        ]
        pdf.add_table(table6)

        # 3. 발표 평가
        pdf.set_font("Nanum", "", 12)
        pdf.cell(0, 10, "2. 발표 평가: 창의 융합 활동 발표(15점)=참여도(5점)+충실성(5점)+의사 소통(5점)", ln=True)

        table7 = [["(1) 채점 결과(점수)", row[42]]]
        pdf.add_table(table7)

        table8 = [
            ["(2) 감점 사유", ""],
            ["- 참여도", row[43]],
            ["- 충실성", row[44]],
            ["- 의사 소통", row[45]],
        ]
        pdf.add_table(table8)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        st.download_button(
            label="PDF 다운로드",
            data=open(tmp.name, "rb").read(),
            file_name="수행평가_결과.pdf",
            mime="application/pdf"
        )
        os.unlink(tmp.name)
