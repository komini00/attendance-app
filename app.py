import streamlit as st
import os
import io
import base64
import tempfile
from datetime import datetime
from pathlib import Path
from PIL import Image
import qrcode
import gspread
from google.oauth2.service_account import Credentials
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
)
from itertools import groupby
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── 설정 ───────────────────────────────────────────────
PHOTO_SIZE = (300, 400)  # 3:4 비율
ADMIN_PASSWORD = st.secrets.get("admin_password", "admin1234")
SHEET_NAME = st.secrets.get("sheet_name", "출석부")

COURSES = [
    "우정과관계의글로벌비지니스",
    "생성형AI실무",
    "항공서비스의이해",
    "전공진로탐색",
    "취창업세미나",
]

# ─── 한글 폰트 등록 ──────────────────────────────────────
FONT_PATHS = [
    "C:/Windows/Fonts/malgun.ttf",
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    str(Path(__file__).parent / "fonts" / "NanumGothic.ttf"),
    "/System/Library/Fonts/AppleGothic.ttf",
]
FONT_NAME = "KoreanFont"
_font_registered = False
for fp in FONT_PATHS:
    if os.path.exists(fp):
        pdfmetrics.registerFont(TTFont(FONT_NAME, fp))
        _font_registered = True
        break
if not _font_registered:
    FONT_NAME = "Helvetica"


# ─── Google Sheets 연결 ──────────────────────────────────
@st.cache_resource
def get_spreadsheet():
    """Google Sheets 스프레드시트 객체를 반환합니다."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    try:
        spreadsheet = client.open(SHEET_NAME)
    except gspread.SpreadsheetNotFound:
        st.error(
            f"⚠️ '{SHEET_NAME}' 스프레드시트를 찾을 수 없습니다.\n\n"
            "**설정 방법:**\n\n"
            "1. Google Sheets에서 새 스프레드시트 생성\n"
            f"2. 이름을 **{SHEET_NAME}**(으)로 변경\n"
            f"3. 공유 버튼 → 아래 이메일을 **편집자**로 추가\n\n"
            f"`{creds_dict.get('client_email', '확인필요')}`"
        )
        st.stop()

    return spreadsheet


HEADERS = ["이름", "학번", "학과", "학년", "조", "사진(base64)", "제출일시"]


def get_course_sheet(course: str):
    """수업별 워크시트를 반환합니다. 없으면 자동 생성."""
    spreadsheet = get_spreadsheet()
    try:
        sheet = spreadsheet.worksheet(course)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=course, rows=1000, cols=7)
        sheet.append_row(HEADERS)
    return sheet


# ─── 데이터 관리 (Google Sheets) ─────────────────────────
def load_students(course: str) -> list[dict]:
    sheet = get_course_sheet(course)
    rows = sheet.get_all_records()
    students = []
    for r in rows:
        students.append({
            "name": str(r.get("이름", "")),
            "student_id": str(r.get("학번", "")),
            "department": str(r.get("학과", "")),
            "year": int(r.get("학년", 1)),
            "group": int(r.get("조", 0)) if r.get("조") else 0,
            "photo_b64": str(r.get("사진(base64)", "")),
            "submitted_at": str(r.get("제출일시", "")),
        })
    students.sort(key=lambda s: s["student_id"])
    return students


def add_student(course: str, name: str, student_id: str, department: str, year: int, group: int, photo_bytes: bytes):
    # 사진 리사이즈 → base64
    img = Image.open(io.BytesIO(photo_bytes))
    img = img.convert("RGB")
    img.thumbnail(PHOTO_SIZE, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    photo_b64 = base64.b64encode(buf.getvalue()).decode()

    sheet = get_course_sheet(course)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 중복 학번 → 해당 행 업데이트
    cell = sheet.find(student_id, in_column=2)
    if cell:
        sheet.update_cell(cell.row, 1, name)
        sheet.update_cell(cell.row, 3, department)
        sheet.update_cell(cell.row, 4, year)
        sheet.update_cell(cell.row, 5, group)
        sheet.update_cell(cell.row, 6, photo_b64)
        sheet.update_cell(cell.row, 7, now)
        return "updated"
    else:
        sheet.append_row([name, student_id, department, year, group, photo_b64, now])
        return "created"


def delete_student(course: str, student_id: str):
    sheet = get_course_sheet(course)
    cell = sheet.find(student_id, in_column=2)
    if cell:
        sheet.delete_rows(cell.row)


def clear_course(course: str):
    sheet = get_course_sheet(course)
    sheet.clear()
    sheet.append_row(HEADERS)


def b64_to_photo_bytes(b64_str: str) -> bytes | None:
    if not b64_str:
        return None
    try:
        return base64.b64decode(b64_str)
    except Exception:
        return None


# ─── PDF 생성 ────────────────────────────────────────────
def generate_pdf(students: list[dict], title: str = "출석부") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "KorTitle", parent=styles["Title"],
        fontName=FONT_NAME, fontSize=18, leading=24,
    )
    cell_style = ParagraphStyle(
        "KorCell", parent=styles["Normal"],
        fontName=FONT_NAME, fontSize=10, leading=14, alignment=1,
    )
    header_style = ParagraphStyle(
        "KorHeader", parent=styles["Normal"],
        fontName=FONT_NAME, fontSize=10, leading=14,
        alignment=1, textColor=colors.white,
    )
    group_title_style = ParagraphStyle(
        "KorGroupTitle", parent=styles["Heading2"],
        fontName=FONT_NAME, fontSize=14, leading=20,
    )

    elements = [Paragraph(title, title_style), Spacer(1, 0.5 * cm)]

    headers = [
        Paragraph("번호", header_style),
        Paragraph("사진", header_style),
        Paragraph("학번", header_style),
        Paragraph("이름", header_style),
        Paragraph("학과", header_style),
        Paragraph("학년", header_style),
    ]

    photo_w, photo_h = 2.5 * cm, 3.3 * cm
    row_height = 3.6 * cm
    col_widths = [1.0 * cm, 2.8 * cm, 2.8 * cm, 2.2 * cm, 4.0 * cm, 1.5 * cm]

    usable_height = A4[1] - 3 * cm - 2 * cm
    rows_per_page = max(int(usable_height / row_height) - 1, 6)

    # 임시 디렉토리에 사진 저장 (ReportLab이 파일 경로 필요)
    tmp_dir = tempfile.mkdtemp()

    # 조별 그룹화 → 조 내에서 학년순 정렬
    sorted_students = sorted(students, key=lambda s: (s.get("group", 0), s.get("year", 1)))
    grouped = groupby(sorted_students, key=lambda s: s.get("group", 0))

    first_group = True
    for group_num, group_students_iter in grouped:
        group_students = list(group_students_iter)

        if not first_group:
            elements.append(PageBreak())
        first_group = False

        group_label = f"{group_num}조" if group_num else "미배정"
        elements.append(Paragraph(f"{group_label} ({len(group_students)}명)", group_title_style))
        elements.append(Spacer(1, 0.3 * cm))

        # 조 인원이 한 페이지 초과 시 분할
        for page_start in range(0, len(group_students), rows_per_page):
            if page_start > 0:
                elements.append(Spacer(1, 0.3 * cm))

            page_students = group_students[page_start:page_start + rows_per_page]
            data = [headers]

            for idx, s in enumerate(page_students, start=page_start + 1):
                photo_data = b64_to_photo_bytes(s.get("photo_b64", ""))
                if photo_data:
                    tmp_path = os.path.join(tmp_dir, f"{s['student_id']}.jpg")
                    with open(tmp_path, "wb") as f:
                        f.write(photo_data)
                    img = RLImage(tmp_path, width=photo_w, height=photo_h)
                else:
                    img = Paragraph("사진 없음", cell_style)

                data.append([
                    Paragraph(str(idx), cell_style),
                    img,
                    Paragraph(s["student_id"], cell_style),
                    Paragraph(s["name"], cell_style),
                    Paragraph(s["department"], cell_style),
                    Paragraph(str(s["year"]), cell_style),
                ])

            table = Table(data, colWidths=col_widths,
                          rowHeights=[1 * cm] + [row_height] * len(page_students))
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                *[("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F8F9FA"))
                  for i in range(2, len(data), 2)],
            ]))
            elements.append(table)

    doc.build(elements)
    return buf.getvalue()


# ─── QR코드 생성 ─────────────────────────────────────────
def make_qr_image(url: str) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ─── Streamlit UI ────────────────────────────────────────
st.set_page_config(page_title="출석부 시스템", page_icon="📋", layout="centered")

page = st.sidebar.radio("메뉴", ["📝 정보 입력", "🔒 관리자"])

# ── 학생 정보 입력 페이지 ──
if page == "📝 정보 입력":
    st.title("📋 학생 정보 입력")
    st.write("아래 양식을 작성하고 사진을 업로드해 주세요.")

    with st.form("student_form", clear_on_submit=True):
        course = st.selectbox("수업 선택 *", COURSES)

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("이름 *", placeholder="홍길동")
            student_id = st.text_input("학번 *", placeholder="20250001")
            department = st.text_input("학과 *", placeholder="컴퓨터공학과")
        with col2:
            year = st.selectbox("학년 *", [1, 2, 3, 4])
            group = st.selectbox("조 *", list(range(1, 21)), format_func=lambda x: f"{x}조")

        photo = st.file_uploader(
            "증명사진 업로드 *",
            type=["jpg", "jpeg", "png"],
            help="JPG 또는 PNG 파일 (증명사진 권장)"
        )
        st.caption("📷 스마트폰: 카메라로 촬영하거나 갤러리에서 선택하세요.")

        submitted = st.form_submit_button("✅ 제출", use_container_width=True)

        if submitted:
            if not name or not student_id or not department or not photo:
                st.error("모든 항목을 입력해 주세요.")
            else:
                with st.spinner("제출 중..."):
                    result = add_student(course, name, student_id, department, year, group, photo.read())
                if result == "updated":
                    st.warning(f"학번 {student_id}의 기존 정보를 업데이트했습니다.")
                else:
                    st.success(f"✅ {name}님의 정보가 제출되었습니다!")

# ── 관리자 페이지 ──
elif page == "🔒 관리자":
    st.title("🔒 관리자 페이지")

    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False

    if not st.session_state.admin_auth:
        pw = st.text_input("관리자 비밀번호", type="password")
        if st.button("로그인"):
            if pw == ADMIN_PASSWORD:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    else:
        # ── 수업 선택 ──
        selected_course = st.selectbox("수업 선택", COURSES)

        # ── QR코드 / 링크 공유 ──
        with st.expander("📱 학생 접속 QR코드", expanded=False):
            app_url = st.text_input(
                "앱 URL",
                value=st.secrets.get("app_url", ""),
                placeholder="https://your-app.streamlit.app",
                help="Streamlit Cloud 배포 후 생성된 URL을 입력하세요",
            )
            if app_url:
                qr_bytes = make_qr_image(app_url)
                col_qr, col_info = st.columns([1, 1])
                with col_qr:
                    st.image(qr_bytes, width=250, caption="학생에게 이 QR코드를 보여주세요")
                with col_info:
                    st.code(app_url, language=None)
                    st.download_button("QR코드 이미지 저장", qr_bytes, "qrcode.png", "image/png")

        st.divider()

        # ── 학생 목록 ──
        with st.spinner("데이터 불러오는 중..."):
            students = load_students(selected_course)
        st.write(f"**[{selected_course}] 등록된 학생: {len(students)}명**")

        if st.button("🔄 새로고침"):
            st.cache_resource.clear()
            st.rerun()

        if not students:
            st.info("아직 등록된 학생이 없습니다.")
        else:
            # PDF 다운로드
            col_a, col_b = st.columns([2, 1])
            with col_a:
                pdf_title = st.text_input("출석부 제목", value=f"2026학년도 1학기 {selected_course} 출석부")
            with col_b:
                st.write("")
                st.write("")
                if st.button("📄 PDF 출석부 생성", use_container_width=True):
                    with st.spinner("PDF 생성 중..."):
                        pdf_data = generate_pdf(students, pdf_title)
                    st.session_state.pdf_data = pdf_data

            if "pdf_data" in st.session_state:
                st.download_button(
                    "⬇️ PDF 다운로드",
                    data=st.session_state.pdf_data,
                    file_name=f"출석부_{selected_course}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            st.divider()

            # 학생 목록 표시
            for s in students:
                with st.container():
                    cols = st.columns([1, 1.5, 1.5, 1.5, 1.5, 1, 0.5])
                    with cols[0]:
                        photo_data = b64_to_photo_bytes(s.get("photo_b64", ""))
                        if photo_data:
                            st.image(photo_data, width=60)
                        else:
                            st.write("🖼️")
                    with cols[1]:
                        st.write(f"**{s['name']}**")
                    with cols[2]:
                        st.write(s["student_id"])
                    with cols[3]:
                        st.write(s["department"])
                    with cols[4]:
                        st.write(f"{s['year']}학년")
                    with cols[5]:
                        st.write(f"{s['group']}조" if s.get("group") else "-")
                    with cols[6]:
                        if st.button("🗑️", key=f"del_{s['student_id']}"):
                            delete_student(selected_course, s["student_id"])
                            st.cache_resource.clear()
                            st.rerun()
                    st.divider()

            # 전체 초기화
            with st.expander("⚠️ 위험 영역"):
                if st.button(f"'{selected_course}' 데이터 초기화", type="secondary"):
                    clear_course(selected_course)
                    st.cache_resource.clear()
                    st.session_state.pop("pdf_data", None)
                    st.rerun()

        # 로그아웃
        st.sidebar.button("로그아웃", on_click=lambda: st.session_state.update(admin_auth=False))
