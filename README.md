# Little Lemon Backend Capstone (final)

`final/` 폴더는 아래 3개 구현을 통합한 최종 Django 프로젝트입니다.

- `Django/` : 기본 웹 페이지(홈, 메뉴, 상세)
- `full/` : 예약 기능 + JS 기반 실시간 슬롯/중복 방지
- `api/` : DRF + Djoser 인증 API

---

## 1) 프로젝트 구조

```text
final/
├── manage.py
├── littlelemon/        # Django project (settings, urls, wsgi, asgi)
├── restaurant/         # 웹 페이지 + 예약 기능
├── LittleLemonAPI/     # DRF API
├── templates/          # 공통 템플릿
├── static/             # 정적 파일(css, img)
└── migrations/         # (루트 migrations 폴더)

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

