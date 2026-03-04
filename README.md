# 📋 학생 출석부 시스템

학생이 QR코드를 스캔하여 사진+정보를 제출하면, 교수자가 PDF 출석부를 다운로드하는 Streamlit 웹앱.

- 수업별로 데이터가 분리됩니다
- 데이터는 Google Sheets에 영구 저장됩니다
- 조별 페이지 분리 + 학년순 정렬된 PDF 출석부 생성
- **무료**로 운영 가능합니다

---

## 🚀 설치 가이드 (처음부터 끝까지, 약 20~30분)

---

### 1단계: GitHub 계정 만들기 + 저장소 복사

1. [github.com](https://github.com) 접속 → **Sign up** → 계정 생성 (이미 있으면 로그인)
2. 이 저장소 페이지에서 초록색 **"Use this template"** → **"Create a new repository"** 클릭
3. Repository name에 `attendance-app` 입력
4. **Public** 선택 → **Create repository** 클릭

✅ 내 GitHub에 코드가 복사되었습니다.

---

### 2단계: Google 서비스 계정 만들기 (최초 1회)

#### 2-1. Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com/) 접속 → Google 로그인
2. 상단 프로젝트 선택 → **새 프로젝트** 클릭
3. 프로젝트 이름: `attendance-app` → **만들기**
4. 생성된 프로젝트가 선택되었는지 확인

#### 2-2. API 사용 설정 (2개)

1. 왼쪽 메뉴 **API 및 서비스** → **라이브러리** 클릭
2. `Google Sheets API` 검색 → 클릭 → **사용** 버튼
3. 다시 라이브러리 → `Google Drive API` 검색 → 클릭 → **사용** 버튼

#### 2-3. 서비스 계정 만들기

1. 왼쪽 메뉴 **API 및 서비스** → **사용자 인증 정보** 클릭
2. **+ 사용자 인증 정보 만들기** → **서비스 계정** 선택
3. 서비스 계정 이름: `attendance-bot` → **만들기 및 계속**
4. 역할: **편집자** → **계속** → **완료**

#### 2-4. JSON 키 다운로드

1. 방금 만든 서비스 계정 클릭
2. **키** 탭 → **키 추가** → **새 키 만들기** → **JSON** → **만들기**
3. JSON 파일이 다운로드됩니다 → **메모장으로 열어두세요**

---

### 3단계: Streamlit Cloud 배포

#### 3-1. 배포하기

1. [share.streamlit.io](https://share.streamlit.io) 접속 → **GitHub 계정으로 로그인**
2. **New app** 클릭
3. Repository: `내아이디/attendance-app` 선택
4. Branch: `main` / Main file path: `app.py`
5. **Deploy!** 클릭

#### 3-2. 앱 공개 설정

1. 앱의 **⋮** 메뉴 → **Settings** → **Sharing** 탭
2. **"This app is public and searchable"** 로 변경 → **Save**

#### 3-3. Secrets 설정 (중요!)

1. **Settings** → **Secrets** 탭
2. 아래 내용을 복사하여 붙여넣고, **본인 정보로 수정**:

```toml
admin_password = "원하는관리자비밀번호"
app_url = "https://내앱주소.streamlit.app"
sheet_name = "출석부"
courses = ["수업이름1", "수업이름2", "수업이름3"]

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

> **수정할 부분:**
> - `admin_password` → 관리자 비밀번호
> - `app_url` → 배포된 앱 URL (브라우저 주소창에서 복사)
> - `courses` → 본인 수업 목록 (예: `["경영학원론", "마케팅전략"]`)
> - `[gcp_service_account]` 아래 → 다운로드한 JSON 파일의 값으로 교체
>
> ⚠️ `private_key`는 JSON 파일의 값을 **그대로** 복사하세요 (`\n` 포함)

3. **Save** 클릭

---

### 4단계: Google Sheet 만들기

1. [sheets.google.com](https://sheets.google.com) 접속
2. **새 스프레드시트** 만들기
3. 제목을 **출석부**로 변경
4. 오른쪽 위 **공유** 버튼 클릭
5. JSON 파일의 `client_email` 값을 복사하여 **편집자** 권한으로 추가

> 첫 행에 헤더를 입력하지 않아도 됩니다. 학생이 처음 제출하면 수업별 탭이 자동 생성됩니다.

✅ **완료!** 앱에 접속해서 테스트해 보세요.

---

## 📱 사용법

### 학생
1. 교수자가 보여주는 QR코드를 스마트폰으로 스캔
2. 수업 선택 → 이름, 학번, 학과, 학년, 조 입력 + 사진 업로드
3. 제출 버튼

### 교수자
1. 사이드바 **관리자** → 비밀번호 입력
2. 수업 선택 → 등록 학생 목록 확인
3. **PDF 출석부 생성** → 다운로드 (조별 페이지 분리)
4. **QR코드** 섹션에서 학생 접속용 QR코드 확인/저장

---

## ❓ 문제 해결

| 증상 | 해결 방법 |
|------|-----------|
| 앱에 에러 표시 | Settings → Secrets 설정을 다시 확인 |
| "스프레드시트를 찾을 수 없습니다" | 4단계(Google Sheet 만들기)를 확인 |
| QR코드 접속 불가 | Settings → Sharing → "public" 확인 |
| 데이터가 안 보임 | 관리자 페이지에서 🔄 새로고침 클릭 |
| API 에러 | Google Cloud에서 Sheets API, Drive API 둘 다 사용 설정 확인 |

---

## 로컬 테스트

```bash
pip install -r requirements.txt

# .streamlit/secrets.toml 을 secrets.toml.example 참고하여 생성 후:
streamlit run app.py
```
