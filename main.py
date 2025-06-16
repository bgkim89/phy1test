import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os

# --- 폰트 설정 ---
# 프로젝트 폴더에 NanumGothic.ttf 파일이 있어야 합니다.
FONT_PATH = "NanumGothic.ttf" 

# --- PDF 클래스 정의 ---
class PDF(FPDF):
    def __init__(self):
        super().__init__(orientation='L')  # 가로 방향 설정
        # 폰트 추가 및 설정 (유니코드 지원)
        self.add_font("Nanum", "", FONT_PATH, uni=True)
        self.set_font("Nanum", "", 12)
        # 자동 페이지 나누기 활성화 및 여백 설정
        self.set_auto_page_break(auto=True, margin=15)

    def chapter_title(self, title):
        """챕터 제목을 PDF에 추가합니다."""
        self.set_font("Nanum", "", 14)
        self.cell(0, 10, title, ln=True, align="C")
        self.ln(5)

    def add_table(self, data, col_widths=None, aligns=None, merged_rows=None):
        """
        데이터를 기반으로 표를 PDF에 추가합니다.
        각 행이 페이지 경계를 넘어가지 않도록 자동 페이지 나누기를 처리합니다.
        """
        self.set_font("Nanum", "", 9.6)  # 표 내부 글씨 크기 (원래 크기의 80%)

        epw = self.w - 2 * self.l_margin  # 유효 페이지 폭 (여백 제외)
        num_cols = len(data[0])

        # 컬럼 폭이 지정되지 않았으면 균등하게 분배
        if col_widths is None:
            col_widths = [epw / num_cols] * num_cols
        # 정렬 방식이 지정되지 않았으면 모두 왼쪽 정렬
        if aligns is None:
            aligns = ["L"] * num_cols
        # 병합된 행 정보가 없으면 빈 리스트로 초기화
        if merged_rows is None:
            merged_rows = []

        for row_idx, row in enumerate(data):
            y_start_of_row = self.get_y() # 현재 Y 좌표 저장
            max_height_for_current_row = 0
            
            # --- 현재 행이 다음 페이지로 넘어갈지 미리 계산 (페이지 나누기 방지) ---
            if row_idx in merged_rows:
                # 병합된 행의 경우, 첫 번째 셀의 텍스트를 전체 폭으로 처리
                merged_text = str(row[0])
                x_temp, y_temp = self.get_x(), self.get_y() # 현재 위치 임시 저장
                # multi_cell의 split_only=True를 사용하여 내용이 차지할 높이만 계산
                lines = self.multi_cell(sum(col_widths), 8, merged_text, border=0, align="L", split_only=True)
                max_height_for_current_row = 8 * len(lines)
                self.set_xy(x_temp, y_temp) # 계산 후 원래 위치로 복원
            else:
                # 일반 행의 경우, 각 셀의 텍스트가 차지할 최대 높이 계산
                for i, cell in enumerate(row):
                    text = str(cell)
                    x_temp, y_temp = self.get_x(), self.get_y() # 현재 위치 임시 저장
                    lines = self.multi_cell(col_widths[i], 8, text, border=0, align=aligns[i], split_only=True)
                    max_height_for_current_row = max(max_height_for_current_row, 8 * len(lines))
                    self.set_xy(x_temp, y_temp) # 계산 후 원래 위치로 복원

            # --- 페이지 넘김 판단 및 새 페이지 추가 ---
            # 현재 Y 좌표 + 현재 행의 최대 높이가 페이지 자동 분할 지점(하단 여백)을 초과하면
            if y_start_of_row + max_height_for_current_row > self.page_break_trigger:
                self.add_page() # 새 페이지 추가
                y_start_of_row = self.get_y() # 새 페이지의 시작 Y 좌표로 업데이트

            # --- 실제 행 그리기 ---
            if row_idx in merged_rows:
                merged_text = str(row[0])
                # 전체 폭에 걸쳐 병합된 셀 그리기
                self.multi_cell(sum(col_widths), 8, merged_text, border=1, align="L")
            else:
                x_start_row_drawing = self.get_x() # 행의 시작 X 좌표 저장
                current_y_for_row = self.get_y() # 행의 시작 Y 좌표 저장

                for i, cell in enumerate(row):
                    text = str(cell)
                    # 각 셀의 위치 설정 후 내용 그리기
                    self.set_xy(x_start_row_drawing + sum(col_widths[:i]), current_y_for_row)
                    self.multi_cell(col_widths[i], 8, text, border=1, align=aligns[i])
                
                # 모든 셀을 그린 후, 행의 최대 높이만큼 Y 좌표를 이동하고 X 좌표를 왼쪽 여백으로 재설정
                self.set_y(current_y_for_row + max_height_for_current_row)
                self.set_x(self.l_margin)

        self.ln(5) # 표 아래 공백 추가
        self.set_font("Nanum", "", 12)  # 표 외부 글씨 크기 원래대로 복원

---

# Streamlit 앱 시작

```python
st.title("수행평가 결과 PDF 생성기")
uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])

if uploaded_file:
    # CSV 파일 읽기
    # pandas는 기본적으로 첫 행을 헤더로 간주합니다.
    # 만약 CSV에 헤더가 없다면, `header=None` 옵션을 추가하여 숫자로 열에 접근해야 합니다.
    df = pd.read_csv(uploaded_file) 
    st.success("CSV 파일이 업로드되었습니다.")

    pdf = PDF()

    # CSV 파일의 각 행(학생별 데이터)에 대해 PDF 페이지 생성
    for idx, row in df.iterrows():
        pdf.add_page() # 새로운 페이지 추가
        pdf.chapter_title("2학년 1학기 물리학1 수행평가 결과 안내서")

        # 1. 인적사항
        table1 = [[row[0], row[1], row[2], '총점(40점 만점):', row[3]]]
        aligns1 = ["C", "C", "C", "R", "L"]
        pdf.add_table(table1, aligns=aligns1)

        # 2. 실험 평가 섹션 제목
        pdf.set_font("Nanum", "", 12)
        pdf.cell(0, 10, "1. 실험 평가: 실험(25점)=실험 활동(10점)+활동지 작성(15점)", ln=True)
        pdf.ln(2)

        # 공통 컬럼 폭 설정 (두 열짜리 표의 경우: 1열 30%, 2열 70%)
        epw = pdf.w - 2 * pdf.l_margin
        col_widths_2col = [epw * 0.3, epw * 0.7]

        # 2. 실험 평가 - (1) 채점 결과
        table2 = [["(1) 채점 결과(점수)", row[4]], ["- 17개 항목 중 맞은 항목 개수", row[7]]]
        pdf.add_table(table2, col_widths=col_widths_2col)

        # 2. 실험 평가 - (2-1) [3. 실험 결과] 관련 감점 사유
        table3 = [
            ["(2-1) [3. 실험 결과] 관련 감점 사유", ""],
            ["- 1번 항목", row[25]],
            ["- 2번 항목", row[26]],
            ["- 3번 항목", row[27]],
            ["- 4번 항목", row[28]],
        ]
        pdf.add_table(table3, col_widths=col_widths_2col, merged_rows=[0])

        # 2. 실험 평가 - (2-2) [4.결과 정리 및 해석] 관련 감점 사유
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

        # 2. 실험 평가 - (2-3) [5. 생각해보기] 관련 감점 사유
        table5 = [
            ["(2-3) [5. 생각해보기] 관련 감점 사유", ""],
            ["- 11번 항목", row[35]],
            ["- 12번 항목", row[36]],
            ["- 13번 항목", row[37]],
            ["- 14번 항목", row[38]],
            ["- 15번 항목", row[39]],
        ]
        pdf.add_table(table5, col_widths=col_widths_2col, merged_rows=[0])

        # 2. 실험 평가 - (2-4) [6. 탐구 확인 문제] 관련 감점 사유 (여섯 번째 표)
        table6 = [
            ["(2-4) [6. 탐구 확인 문제] 관련 감점 사유", ""],
            ["- 16번 항목", row[40]],
            ["- 17번 항목", row[41]],
        ]
        pdf.add_table(table6, col_widths=col_widths_2col, merged_rows=[0])

        # 3. 발표 평가 섹션 제목
        pdf.set_font("Nanum", "", 12)
        pdf.cell(0, 10, "2. 발표 평가: 창의 융합 활동 발표(15점)=참여도(5점)+충실성(5점)+의사 소통(5점)", ln=True)
        pdf.ln(2)

        # 3. 발표 평가 - (1) 채점 결과 (일곱 번째 표)
        table7 = [["(1) 채점 결과(점수)", row[42]]]
        pdf.add_table(table7, col_widths=col_widths_2col)

        # 3. 발표 평가 - (2) 감점 사유 (여덟 번째 표 - 요청에 따라 수정)
        # AU, AV, AW 열이 각각 인덱스 43, 44, 45에 해당한다고 가정합니다.
        # CSV 파일의 실제 열 순서에 따라 이 인덱스들을 조정해야 할 수 있습니다.
        table8 = [
            ["(2) 감점 사유", ""],
            ["- 참여도", row[43]],   # CSV의 AU열 데이터 (인덱스 43으로 추정)
            ["- 충실성", row[44]],   # CSV의 AV열 데이터 (인덱스 44로 추정)
            ["- 의사 소통", row[45]], # CSV의 AW열 데이터 (인덱스 45로 추정)
        ]
        pdf.add_table(table8, col_widths=col_widths_2col, merged_rows=[0])

    # --- PDF 저장 및 다운로드 ---
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        pdf.output(tmp.name) # PDF 파일 생성
        st.download_button(
            label="PDF 다운로드",
            data=open(tmp.name, "rb").read(),
            file_name="수행평가_결과.pdf",
            mime="application/pdf"
        )
        os.unlink(tmp.name) # 임시 파일 삭제
