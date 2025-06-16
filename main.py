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
        self.set_auto_page_break(auto=True, margin=15) # Keep auto page break, but we'll add manual checks

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

        # Calculate max height of the table to estimate if it fits (optional, more for full table fit)
        # However, for row-by-row control, we check each row.

        for row_idx, row in enumerate(data):
            y_start_of_row = self.get_y()
            max_height_for_current_row = 0
            
            # Simulate multi_cell to get required height for the current row
            # This is crucial for pre-checking page breaks
            if row_idx in merged_rows:
                merged_text = str(row[0])
                # Temporarily save current position
                x_temp, y_temp = self.get_x(), self.get_y()
                # Use split_only to calculate height without drawing
                lines = self.multi_cell(sum(col_widths), 8, merged_text, border=0, align="L", split_only=True)
                max_height_for_current_row = 8 * len(lines)
                # Restore position
                self.set_xy(x_temp, y_temp)
            else:
                for i, cell in enumerate(row):
                    text = str(cell)
                    # Temporarily save current position
                    x_temp, y_temp = self.get_x(), self.get_y()
                    # Use split_only to calculate height without drawing
                    lines = self.multi_cell(col_widths[i], 8, text, border=0, align=aligns[i], split_only=True)
                    max_height_for_current_row = max(max_height_for_current_row, 8 * len(lines))
                    # Restore position
                    self.set_xy(x_temp, y_temp)

            # Check if the current row will fit on the page
            # self.b_margin is the bottom margin, so self.page_break_trigger is y position where break occurs.
            # We want to check if the row's end will exceed the page break trigger.
            if y_start_of_row + max_height_for_current_row > self.page_break_trigger:
                # If it doesn't fit, add a new page before drawing this row
                self.add_page()
                # If you have headers for your tables, you might want to redraw them here
                # For this specific issue (splitting within the table), adding a page is enough.
                y_start_of_row = self.get_y() # Reset y_start_of_row for the new page

            # Now, actually draw the row
            if row_idx in merged_rows:
                merged_text = str(row[0])
                self.multi_cell(sum(col_widths), 8, merged_text, border=1, align="L")
            else:
                x_start_row_drawing = self.get_x() # Store X for resetting after drawing cells
                current_y_for_row = self.get_y() # Store Y for setting after drawing cells

                for i, cell in enumerate(row):
                    text = str(cell)
                    # Set position for current cell
                    self.set_xy(x_start_row_drawing + sum(col_widths[:i]), current_y_for_row)
                    # Draw cell content. If content is too long for cell, multi_cell will handle line breaks within the cell.
                    self.multi_cell(col_widths[i], 8, text, border=1, align=aligns[i])
                
                # After drawing all cells in the row, move Y down by the max height of any cell in that row
                # and reset X to the left margin for the next row.
                self.set_y(current_y_for_row + max_height_for_current_row)
                self.set_x(self.l_margin) # Reset X to left margin for the next row

        self.ln(5)
        self.set_font("Nanum", "", 12)  # 표 외 글씨는 원래 크기로 복원

# Streamlit 앱 시작
st.title("수행평가 결과 PDF 생성기")
uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("CSV 파일이 업로드되었습니다.")

    pdf = PDF()

    for idx, row in df.iterrows():
        pdf.add_page() # Start each student's report on a new page
        pdf.chapter_title("2학년 1학기 물리학1 수행평가 결과 안내서")

        # 1. 인적사항
        table1 = [[row[0], row[1], row[2], '총점(40점 만점):', row[3]]]
        aligns1 = ["C", "C", "C", "R", "L"]
        pdf.add_table(table1, aligns=aligns1)

        # 2. 실험 평가
        pdf.set_font("Nanum", "", 12)
        pdf.cell(0, 10, "1. 실험 평가: 실험(25점)=실험 활동(10점)+활동지 작성(15점)", ln=True)
        pdf.ln(2)

        # 공통 컬럼 폭 설정 (두 열짜리 표의 경우: 1열 30%, 2열 70%)
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

        # --- Tables 6, 7, 8: Problematic tables handled by the improved add_table ---
        # The key improvement is within the add_table method itself,
        # which now performs a pre-check before drawing each row.

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

        table8 = [
            ["(2) 감점 사유", ""],
            ["- 참여도", row[43]],
            ["- 충실성", row[44]],
            ["- -의사 소통", row[45]],
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
