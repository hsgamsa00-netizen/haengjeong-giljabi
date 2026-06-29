# -*- coding: utf-8 -*-
"""법제처 국가법령정보 OPEN API로 핵심 법령의 시행일·현행성 조회 → law_current.json (L2 시의성 동기화).
OC 키는 .law_oc(gitignore)에서 읽어 공개 코드에 노출하지 않음. 결과(시행일 등)는 키 없는 공공데이터."""
import urllib.request, urllib.parse, json, os
PROJ = os.path.dirname(os.path.abspath(__file__))
OC = open(os.path.join(PROJ, ".law_oc"), encoding="utf-8").read().strip()
CHECK = "2026-06-29"
LAWS = ["건축법", "식품위생법", "국토의 계획 및 이용에 관한 법률", "공공기관의 정보공개에 관한 법률",
        "옥외광고물 등의 관리와 옥외광고산업 진흥에 관한 법률", "민원 처리에 관한 법률", "주민등록법",
        "질서위반행위규제법", "행정심판법", "행정소송법"]
out = {}
for name in LAWS:
    q = urllib.parse.quote(name)
    url = f"http://www.law.go.kr/DRF/lawSearch.do?OC={OC}&target=law&query={q}&type=JSON&display=5"
    try:
        d = json.loads(urllib.request.urlopen(url, timeout=20).read().decode("utf-8"))
        items = d.get("LawSearch", {}).get("law", [])
        items = items if isinstance(items, list) else [items]
        best = next((it for it in items if it.get("법령명한글", "").strip() == name and it.get("현행연혁코드") == "현행"), None)
        if not best and items:
            best = items[0]
        if best:
            out[name] = {"시행일": best.get("시행일자", ""), "공포일": best.get("공포일자", ""),
                         "현행": best.get("현행연혁코드", ""), "확인일": CHECK,
                         "link": f"https://www.law.go.kr/법령/{q}"}
            print(f"  {name}: 시행 {best.get('시행일자')} · {best.get('현행연혁코드')}")
    except Exception as e:
        print(f"  {name}: 오류 {repr(e)[:80]}")
json.dump(out, open(os.path.join(PROJ, "law_current.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"law_current.json {len(out)}건 (법제처 API·{CHECK} 확인)")
