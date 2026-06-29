# -*- coding: utf-8 -*-
"""화성 행정 길잡이 — 빌드타임 디제스트 생성기.
워크플로 수집 실데이터(처리기한·과태료·복지) + 화성 감사 샘플을 정제해 data.js(window.DATA)로 인코딩.
= 'L1 빌드타임 디제스트' 레이어의 실체. 앱(index.html)은 런타임 LLM 없이 이 데이터를 검색·규칙·계산만 한다."""
import json, os, re

PROJ = r"C:\AuditApp\haengjeong-giljabi"
WF = r"C:\Users\KOOJIN~1\AppData\Local\Temp\claude\C--Users-koojinkyu-OneDrive-------------------------\679beb71-6c52-492c-9642-909f6b49cf08\tasks\wl8sbsiqp.output"
AUD = r"C:\Users\koojinkyu\OneDrive\바탕 화면\클로드\이관\260619_화성시_이관\_haengjeong_audit_sample.json"

wf = json.load(open(WF, encoding="utf-8"))["result"]
welfare = wf["welfare"]["programs"]
handling = wf["handling"]
fine = wf["fine"]
audit = json.load(open(AUD, encoding="utf-8"))


def parse_won(s):
    m = re.search(r"([\d,]+)\s*원", s or "")
    if m:
        return int(m.group(1).replace(",", ""))
    m = re.search(r"(\d+)\s*만", s or "")
    if m:
        return int(m.group(1)) * 10000
    return 0


for e in fine["examples"]:
    e["base"] = parse_won(e.get("base_amount", ""))

# 복지 16종 최신성 검증(welfare-verify 워크플로·2026) 반영 — 출처·기준연도 부착 + 변경분 보정
try:
    ver = json.load(open(os.path.join(PROJ, "_welfare_verify.json"), encoding="utf-8"))
except Exception:
    ver = []
CORR = {
 "기초연금": {"income": "65세+·단독 소득인정액 월 247만원 이하(2026·소득 하위 약 70%)", "benefit": "월 최대 349,700원(2026·단독), 소득·부부 여부 따라 차등"},
 "에너지바우처": {"benefit": "세대원수별 냉·난방비 지원(2026: 1인 약 29.5만~4인 70.1만원), 소득산정 미반영"},
 "한부모가족 아동양육비": {"income": "기준 중위소득 65% 이하(2026 확대)"},
 "아이돌봄서비스": {"income": "기준 중위소득 250% 이하 4구간 차등(2026 확대)"},
 "장애인연금": {"income": "단독 소득인정액 월 140만원 이하(2026)", "benefit": "기초급여 월 최대 349,700원 + 부가급여(합산 최대 약 43.97만원·2026)"},
 "문화누리카드": {"benefit": "1인 연간 15만원(2026) 문화·여행·체육 이용"},
}
for p in welfare:
    for v in ver:
        if v["name"][:4] and v["name"][:4] in p["name"]:
            p["source"] = v.get("source", "")
            p["base_year"] = v.get("base_year", "")
            break
    for key, corr in CORR.items():
        if key in p["name"]:
            p.update(corr)

# 처리기한: 즉시처리/원칙 항목(days<=0) 제외, 범위(max) 부여 — P0-3 단일판정 방지
MAXMAP = {"건축허가": 40, "건축신고": 20, "개발행위허가(국토계획법)": 30, "정보공개청구": 20, "옥외광고물 허가": 20}
deadlines = []
for d in handling["deadlines"]:
    if d["days"] <= 0:
        continue
    deadlines.append({"type": d["type"], "min": d["days"], "max": MAXMAP.get(d["type"], d["days"]),
                      "basis": d["basis"], "note": d["note"]})

# 법령 출처(국가법령정보센터 deep link) — 처리기한·과태료
LAWURL = {
 "건축법": "https://www.law.go.kr/법령/건축법",
 "식품위생법": "https://www.law.go.kr/법령/식품위생법",
 "국토": "https://www.law.go.kr/법령/국토의계획및이용에관한법률",
 "정보공개": "https://www.law.go.kr/법령/공공기관의정보공개에관한법률",
 "옥외광고": "https://www.law.go.kr/법령/옥외광고물등의관리와옥외광고산업진흥에관한법률",
 "민원": "https://www.law.go.kr/법령/민원처리에관한법률",
 "주민등록": "https://www.law.go.kr/법령/주민등록법",
}
def law_url(basis):
    for k, u in LAWURL.items():
        if k in basis:
            return u
    return ""
for d in deadlines:
    d["source"] = law_url(d["basis"])
for r in handling["remedies"]:
    r["source"] = law_url(r.get("basis", ""))
fine["source"] = "https://www.law.go.kr/법령/질서위반행위규제법"

chips = [
 {"label": "65세 이상 어르신", "tags": ["노인"]},
 {"label": "청년(19~34세)", "tags": ["청년"]},
 {"label": "대학생", "tags": ["대학생", "교육"]},
 {"label": "영유아 키우는 중(0~7세)", "tags": ["영유아", "육아"]},
 {"label": "초등 자녀 돌봄(~12세)", "tags": ["돌봄", "육아"]},
 {"label": "한부모·조손 가정", "tags": ["한부모", "조손"]},
 {"label": "장애가 있음", "tags": ["장애", "중증장애"]},
 {"label": "저소득·수급·차상위", "tags": ["저소득", "차상위", "수급자"]},
 {"label": "위기상황(실직·질병·재난)", "tags": ["위기", "실직", "재난", "긴급"]},
 {"label": "무주택·월세 거주", "tags": ["월세", "주거", "임차", "무주택"]},
 {"label": "맞벌이", "tags": ["맞벌이"]},
 {"label": "구직 중", "tags": ["구직", "일자리"]},
 {"label": "경기·화성 거주", "tags": ["화성", "경기"]},
]
fchips = [
 {"label": "긴급·불가피한 상황이었음", "kind": "dispute"},
 {"label": "억울하다·위반 아님", "kind": "dispute"},
 {"label": "기초생활수급자", "tag": "수급"},
 {"label": "한부모 가정", "tag": "한부모"},
 {"label": "심한 장애가 있음", "tag": "장애"},
 {"label": "미성년자", "tag": "미성년"},
 {"label": "바로 납부할 의향 있음", "tag": "자진"},
]
# 시민 분야 그리드(큼직 선택) — count는 데이터에서 자동 산출, route는 엔진
bunya = [
 {"key": "welfare", "label": "복지·지원금", "icon": "gift", "route": "welfare", "on": 1, "desc": "놓친 복지·지원금 찾기"},
 {"key": "fine", "label": "세금·과태료", "icon": "scale", "route": "fine", "on": 1, "desc": "과태료 감경·이의 안내"},
 {"key": "delay", "label": "민원·처리지연", "icon": "clock", "route": "delay", "on": 1, "desc": "처리기한 점검"},
 {"key": "license", "label": "인허가·창업", "icon": "stamp", "route": "delay", "on": 1, "desc": "인허가 처리 점검"},
 {"key": "edu", "label": "보육·교육", "icon": "school", "route": "welfare", "pre": ["영유아", "육아", "교육"], "on": 1, "desc": "육아·교육 지원"},
 {"key": "house", "label": "주거·임대", "icon": "home", "route": "welfare", "pre": ["월세", "주거", "임차"], "on": 1, "desc": "주거 지원·월세"},
 {"key": "traffic", "label": "교통·주차", "icon": "car", "route": None, "on": 0},
 {"key": "env", "label": "환경·생활불편", "icon": "leaf", "route": None, "on": 0},
 {"key": "safe", "label": "안전", "icon": "shield", "route": None, "on": 0},
]

DATA = {
 "기준일": "2026-06-29",
 "기준설명": "2026년 기준 검증 반영(일부 제도) · 최종 자격·금액은 신청기관 심사로 확정",
 "welfare": welfare, "chips": chips,
 "handling": {"deadlines": deadlines, "remedies": handling["remedies"]},
 "fine": fine, "fchips": fchips,
 "bunya": bunya, "audit": audit,
}
out = "window.DATA=" + json.dumps(DATA, ensure_ascii=False) + ";\n"
open(os.path.join(PROJ, "data.js"), "w", encoding="utf-8").write(out)
print(f"data.js {len(out)} bytes · 복지 {len(welfare)} · 처리기한 {len(deadlines)} · 과태료예시 {len(fine['examples'])} · 감사 {len(audit)} · 분야 {len(bunya)}")
