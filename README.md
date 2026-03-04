# 📋 학생 출석부 시스템

학생이 QR코드를 스캔하여 사진+정보를 제출하면, 교수자가 PDF 출석부를 다운로드하는 Streamlit 웹앱.

**데이터는 Google Sheets에 영구 저장**되어 서버가 재시작되어도 유지됩니다.

---

## 배포 방법 (Streamlit Cloud, 무료)

### 1단계: Google 서비스 계정 만들기 (최초 1회)

1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 (예: `attendance-app`)
3. **API 및 서비스 → 라이브러리** → `Google Sheets API` 검색 → **사용 설정**
4. **API 및 서비스 → 라이브러리** → `Google Drive API` 검색 → **사용 설정**
5. **API 및 서비스 → 사용자 인증 정보** → **서비스 계정 만들기**
   - 이름: `attendance-bot`
   - 역할: 편집자
6. 만든 서비스 계정 클릭 → **키** 탭 → **키 추가** → **JSON** → 다운로드
7. 다운로드된 JSON 파일 내용을 메모장에 복사해 둡니다

### 2단계: GitHub에 코드 올리기

```bash
cd attendance-app
git init
git add .
git commit -m "initial commit"
# GitHub에서 새 저장소 만든 후:
git remote add origin https://github.com/YOUR_ID/attendance-app.git
git push -u origin main
```

### 3단계: Streamlit Cloud 배포

1. [share.streamlit.io](https://share.streamlit.io) 접속 → GitHub 로그인
2. **New app** → 저장소 선택 → `app.py` 선택 → **Deploy**
3. 배포 후 **Settings → Secrets** 에 아래 내용 입력:

```toml
admin_password = "원하는비밀번호"
app_url = "https://your-app.streamlit.app"
sheet_name = "출석부"

[gcp_service_account]
type = "service_account"
project_id = "여기에-프로젝트ID"
private_key_id = "여기에-키ID"
private_key = "-----BEGIN PRIVATE KEY-----\n여기에-전체키\n-----END PRIVATE KEY-----\n"
client_email = "여기에-서비스계정@이메일"
client_id = "여기에-클라이언트ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "여기에-인증서URL"
```

> ⚠️ `private_key`는 JSON 파일의 값을 **그대로** 복사하세요 (`\n` 포함).

4. **Save** → 앱 자동 재시작 → 완료!

### 4단계: 학생에게 공유

1. 관리자 페이지 로그인
2. "학생 접속 QR코드" 섹션에서 QR코드 확인
3. 강의실에서 화면에 QR코드를 띄우거나, 이미지를 카톡/LMS에 공유

---

## 사용법

### 학생
1. QR코드 스캔 → 브라우저 열림
2. 이름, 학번, 학과, 학년 입력 + 사진 업로드
3. 제출 버튼

### 교수자
1. 사이드바 "관리자" → 비밀번호 입력
2. 등록 학생 목록 확인
3. "PDF 출석부 생성" → PDF 다운로드

---

## 로컬 테스트

```bash
pip install -r requirements.txt

# .streamlit/secrets.toml 을 secrets.toml.example 참고하여 생성 후:
streamlit run app.py
```
