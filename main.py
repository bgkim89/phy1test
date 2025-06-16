import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os

FONT_PATH = "NanumGothic.ttf"  # 프로젝트 폴더에 있는 한글 폰트 파일

class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L')  # 가로 방향
        self.add_font("Nanum", "", FONT_PATH, uni=True)
        self.set_font("Nanum", "", 12)
        self.set_auto_page_break(auto=True, margin=15)

    def chapter_title(self, title):
        self.set_font("Nanum", "", 14)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)

    def add_table(self, data, col_widths=None, aligns=None, merged_rows=None):
        self.set_font("Nanum", "", 9.6)  # 표 글씨 80%

        epw = self.w - 2 * self.l_margin
        num_cols = len(data[0])
        if col_widths is None:
            col_widths = [epw / num_cols] * num_cols
        if aligns is None:
            aligns = ["L"] * num_cols
        if merged_rows is None:
            merged_rows = []

        for row_idx, row in enumerate(data):
            y_start_of_row = self.get_y()
            max_height_for_current_row = 0
            
            # Simulate multi_cell to get required height for the current row
            if row_idx in merged_rows:
                merged_text = str(row[0])
                x_temp, y_temp = self.get_x(), self.get_y()
                lines = self.multi_cell(sum(col_widths), 8, merged_text, border=0, align="L", split_only=True)
                max_height_for_current_row = 8 * len(lines)
                self.set_xy(x_temp, y_temp)
            else:
                for i, cell in enumerate(row):
                    text = str(cell)
                    x_temp, y_temp = self.get_x(), self.get_y()
                    lines = self.multi_cell(col_widths[i], 8, text, border=0, align=aligns[i], split_only=True)
                    max_height_for_current_row = max(max_height_for_current_row, 8 * len(lines))
                    self.set_xy(x_temp, y_temp)

            if y_start_of_row + max_height_for_current_row > self.page_break_trigger:
                self.add_page()
                y_start_of_row = self.get_y() 

            # Now, actually draw the row
            if row_idx in merged_rows:
                merged_text = str(row[0])
                self.multi_cell(sum(col_widths), 8, merged_text, border=1, align="L")
            else:
                x_start_row_drawing = self.get_x()
                current_y_for_row = self.get_y()

                for i, cell in enumerate(row):
                    text = str(cell)
                    self.set_xy(x_start_row_drawing + sum(col_widths[:i]), current_y_for_row)
                    self.multi_cell(col_widths[i], 8, text, border=1, align=aligns[i])
                
                self.set_y(current_y_for_row + max_height_for_current_row)
                self.set_x(self.l_margin)

        self.ln(5)
        self.set_font("Nanum", "", 12)

# Streamlit 앱 시작
st.title("수행평가 결과 PDF 생성기")
uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

if uploaded_file:
    # CSV 파일을 읽을 때 헤더가 없는 경우, header=None을 지정하여 숫자로 된 열 인덱스를 사용하도록 할 수 있습니다.
    # 하지만 기존 코드가 row[0], row[1] 등으로 접근하는 것으로 보아 헤더가 있다고 가정하거나
    # pandas가 자동으로 숫자 인덱스를 부여하는 경우일 수 있습니다.
    # 만약 열 이름(AU, AV, AW)을 사용하고 싶다면 반드시 CSV에 해당 이름의 헤더가 있어야 합니다.
    df = pd.read_csv(uploaded_file) 
    st.success("CSV 파일이 업로드되었습니다.")

    pdf = PDF()

    for idx, row in df.iterrows():
        pdf.add_page()
        pdf.chapter_title("2학년 1학기 물리학1 수행평가 결과 안내서")

        # 1. 인적사항
        table1 = [[row[0], row[1], row[2], '총점(40점 만점):', row[3]]]
        aligns1 = ["C", "C", "C", "R", "L"]
        pdf.add_table(table1, aligns=aligns1)

        # 2. 실험 평가
        pdf.set_font("Nanum", "", 12)
        pdf.cell(0, 10, "1. 실험 평가: 실험(25점)=실험 활동(10점)+활동지 작성(15점)", ln=True)
        pdf.ln(2)

        epw = pdf.w - 2 * pdf.l_margin
        col_widths_2col = [epw * 0.3, epw * 0.7]

        table2 = [["(1) 채점 결과(점수)", row[4]], ["- 17개 항목 중 맞은 항목 개수", row[7]]]
        pdf.add_table(table2, col_widths=col_widths_2col)

        table3 = [
            ["(2-1) [3. 실험 결과] 관련 감점 사유", ""],
            ["- 1번 항목", row[25]],
            ["- 2번 항목", row[26]],
            ["- 3번 항목", row[27]],
            ["- 4번 항목", row[28]],
        ]
        pdf.add_table(table3, col_widths=col_widths_2col, merged_rows=[0])

        table4 = [
            ["(2-2) [4.결과 정리 및 해석] 관련 감점 사유", ""],
            ["- 5번 항목", row[29]],
            ["- 6번 항목", row[30]],
            ["- 7번 항목", row[31]],
            ["- 8번 항목", row[32]],
            ["- 9번 항목", row[33]],
            ["- 10번 항목", row[34]],
        ]
        pdf.add_table(table4, col_widths=col_widths_2col, merged_rows=[0])

        table5 = [
            ["(2-3) [5. 생각해보기] 관련 감점 사유", ""],
            ["- 11번 항목", row[35]],
            ["- 12번 항목", row[36]],
            ["- 13번 항목", row[37]],
            ["- 14번 항목", row[38]],
            ["- 15번 항목", row[39]],
        ]
        pdf.add_table(table5, col_widths=col_widths_2col, merged_rows=[0])

        table6 = [
            ["(2-4) [6. 탐구 확인 문제] 관련 감점 사유", ""],
            ["- 16번 항목", row[40]],
            ["- 17번 항목", row[41]],
        ]
        pdf.add_table(table6, col_widths=col_widths_2col, merged_rows=[0])

        # 3. 발표 평가
        pdf.set_font("Nanum", "", 12)
        pdf.cell(0, 10, "2. 발표 평가: 창의 융합 활동 발표(15점)=참여도(5점)+충실성(5점)+의사 소통(5점)", ln=True)
        pdf.ln(2)

        table7 = [["(1) 채점 결과(점수)", row[42]]]
        pdf.add_table(table7, col_widths=col_widths_2col)

        # 여덟 번째 표 수정: 열 인덱스 사용 (이전 방식 복원)
        # CSV 파일에서 'AU', 'AV', 'AW' 열이 각각 43, 44, 45번째 열(0부터 시작)이라고 가정합니다.
        # 실제 CSV 파일의 열 순서에 맞게 인덱스 (43, 44, 45)를 조정해주세요.
        table8 = [
            ["(2) 감점 사유", ""],
            ["- 참여도", row[43]], # CSV의 AU열 (이전 인덱스 43)
            ["- 충실성", row[44]], # CSV의 AV열 (이전 인덱스 44)
            ["- 의사 소통", row[45]], # CSV의 AW열 (이전 인덱스 45)
        ]
        pdf.add_table(table8, col_widths=col_widths_2col, merged_rows=[0])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name)
        st.download_button(
            label="PDF 다운로드",
            data=open(tmp.name, "rb").read(),
            file_name="수행평가_결과.pdf",
            mime="application/pdf"
        )
        os.unlink(tmp.name)
