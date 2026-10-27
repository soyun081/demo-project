import streamlit.components.v1 as components
import streamlit as st
import pandas as pd
import json
import math
import requests
from pathlib import Path
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="출석관리",
    page_icon="📘",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "attendance_data"
DATA_DIR.mkdir(exist_ok=True)

CSV_FILE = DATA_DIR / "attendance.csv"
ADMINS_FILE = DATA_DIR / "admins.json"
SETTINGS_FILE = DATA_DIR / "settings.json"

COLUMNS = [
    "날짜", "이름", "출결상태", "결석사유", "지각사유",
    "등록시간", "건물 이름", "GPS정확도(m)", "지도링크",
    "위도", "경도"
]

ABSENCE_REASONS = [
    "질병", "병원 진료", "가정 사정", "경조사",
    "학교 승인 활동", "교통 문제", "기타"
]

LATE_REASONS = [
    "교통 문제", "늦잠", "병원 진료", "가정 사정",
    "학교 승인 활동", "기타"
]

MAX_GPS_ACCURACY = 300
BUILDING_SEARCH_RADIUS = 300

# -----------------------------
# 화면 디자인
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: #f3f7fd;
    color: #1f2937;
    font-family: "Malgun Gothic", sans-serif;
}
.block-container {
    max-width: 1150px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}
h1 {
    color: #164e9b !important;
    font-size: 2.1rem !important;
    font-weight: 800 !important;
}
h2 {
    color: #1d4e89 !important;
    font-size: 1.55rem !important;
    font-weight: 750 !important;
}
h3 {
    color: #245b96 !important;
    font-size: 1.2rem !important;
    font-weight: 700 !important;
}
p, label, .stMarkdown {
    color: #263449;
    line-height: 1.65;
}
[data-testid="stCaptionContainer"] p {
    color: #64748b !important;
    font-size: 0.9rem;
}
section[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #dbe5f1;
}
section[data-testid="stSidebar"] * {
    color: #1f2937 !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #164e9b !important;
}
.stTextInput input,
.stDateInput input,
.stNumberInput input,
.stTextArea textarea {
    background: #ffffff !important;
    color: #172033 !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 9px !important;
    min-height: 42px;
}
.stSelectbox div[data-baseweb="select"] > div,
.stMultiSelect div[data-baseweb="select"] > div {
    background: #ffffff !important;
    color: #172033 !important;
    border-radius: 9px !important;
    border-color: #cbd5e1 !important;
}
.stSelectbox [data-baseweb="select"] *,
.stMultiSelect [data-baseweb="select"] * {
    color: #172033 !important;
}
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button,
div[data-testid="stFormSubmitButton"] button,
.stLinkButton > a {
    background: #ffffff !important;
    color: #111827 !important;
    border: 1px solid #b8c7da !important;
    border-radius: 10px !important;
    min-height: 43px;
    padding: 0.55rem 1rem !important;
    font-weight: 700 !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
}
.stButton > button:hover,
.stDownloadButton > button:hover,
.stFormSubmitButton > button:hover,
div[data-testid="stFormSubmitButton"] button:hover,
.stLinkButton > a:hover {
    background: #eef5ff !important;
    color: #111827 !important;
    border-color: #4c8fe8 !important;
}
.stButton > button:disabled,
.stDownloadButton > button:disabled {
    background: #f1f5f9 !important;
    color: #94a3b8 !important;
    border-color: #e2e8f0 !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid #dbe5f1;
}
.stTabs [data-baseweb="tab"] {
    background: #ffffff;
    border-radius: 8px 8px 0 0;
    padding: 10px 16px;
}
.stTabs [data-baseweb="tab"] p {
    color: #334155 !important;
    font-weight: 650 !important;
}
.stTabs [aria-selected="true"] {
    background: #e6f0ff !important;
    border-bottom: 3px solid #2878d0 !important;
}
div[data-testid="stAlert"] {
    border-radius: 10px;
    border: 1px solid #d8e3f0;
}
div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #dbe5f1;
    border-radius: 13px;
    padding: 16px;
    box-shadow: 0 2px 5px rgba(15, 23, 42, 0.04);
}
div[data-testid="stMetricLabel"] {
    color: #526176 !important;
}
div[data-testid="stMetricValue"] {
    color: #164e9b !important;
    font-weight: 800 !important;
}
div[data-testid="stDataFrame"],
div[data-testid="stTable"] {
    background: #ffffff;
    border: 1px solid #dbe5f1;
    border-radius: 10px;
    overflow: hidden;
}
hr {
    border-color: #dbe5f1 !important;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
}
@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.8rem 2rem;
    }
    h1 {
        font-size: 1.65rem !important;
    }
    h2 {
        font-size: 1.3rem !important;
    }
    .stButton > button,
    .stDownloadButton > button,
    .stLinkButton > a {
        width: 100%;
    }
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 데이터 관리
# -----------------------------
def load_data():
    if not CSV_FILE.exists():
        return pd.DataFrame(columns=COLUMNS)

    try:
        data = pd.read_csv(CSV_FILE, dtype={"이름": str})
    except Exception:
        return pd.DataFrame(columns=COLUMNS)

    # 이전 버전 CSV와 호환되도록 누락된 열 추가
    for col in COLUMNS:
        if col not in data.columns:
            data[col] = ""

    return data[COLUMNS].fillna("")


def save_data(data):
    data = data.copy()

    for col in COLUMNS:
        if col not in data.columns:
            data[col] = ""

    data[COLUMNS].to_csv(
        CSV_FILE,
        index=False,
        encoding="utf-8-sig"
    )


def load_json(path, default):
    if not path.exists():
        return default

    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_settings():
    today = date.today().isoformat()

    return load_json(SETTINGS_FILE, {
        "start_date": today,
        "end_date": today,
        "period_name": "출석 기간"
    })


# -----------------------------
# 지도 및 GPS
# -----------------------------
def make_map_link(lat, lon):
    query = urlencode({
        "api": "1",
        "query": f"{lat},{lon}"
    })
    return f"https://www.google.com/maps/search/?{query}"


def haversine_m(lat1, lon1, lat2, lon2):
    """GPS 두 좌표 사이의 직선거리를 미터 단위로 계산합니다."""
    radius = 6371000

    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (
        math.sin(dp / 2) ** 2
        + math.cos(p1)
        * math.cos(p2)
        * math.sin(dl / 2) ** 2
    )

    a = max(0, min(1, a))

    return radius * 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )


def find_nearest_building(lat, lon):
    """
    OpenStreetMap에서 GPS 위치 기준 300m 이내 건물을 찾고
    가장 가까운 건물 정보를 반환합니다.

    API 키는 필요하지 않지만 인터넷과 검색 서버가 필요합니다.
    """
    query = f"""
    [out:json][timeout:20];
    (
      nwr(around:{BUILDING_SEARCH_RADIUS},{lat},{lon})["building"];
    );
    out center tags;
    """

    endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]

    elements = []

    for endpoint in endpoints:
        try:
            response = requests.post(
                endpoint,
                data={"data": query},
                headers={
                    "User-Agent": "AttendanceApp/1.0"
                },
                timeout=25
            )
            response.raise_for_status()
            elements = response.json().get("elements", [])
            break
        except Exception:
            continue

    if not elements:
        return None

    candidates = []

    for element in elements:
        tags = element.get("tags", {})

        if "lat" in element and "lon" in element:
            building_lat = element["lat"]
            building_lon = element["lon"]
        elif "center" in element:
            building_lat = element["center"].get("lat")
            building_lon = element["center"].get("lon")
        else:
            continue

        if building_lat is None or building_lon is None:
            continue

        building_lat = float(building_lat)
        building_lon = float(building_lon)

        distance = haversine_m(
            lat, lon, building_lat, building_lon
        )

        # 검색 결과도 다시 거리 검사
        if distance > BUILDING_SEARCH_RADIUS:
            continue

        name = str(tags.get("name", "")).strip()

        if not name:
            street = str(tags.get("addr:street", "")).strip()
            number = str(tags.get("addr:housenumber", "")).strip()
            address = f"{street} {number}".strip()

            if address:
                name = address
            else:
                building_type = str(tags.get("building", "")).strip()

                if building_type and building_type != "yes":
                    name = f"이름 미등록 건물 ({building_type})"
                else:
                    name = "이름 미등록 건물"

        candidates.append({
            "name": name,
            "distance": distance,
            "lat": building_lat,
            "lon": building_lon
        })

    if not candidates:
        return None

    return min(candidates, key=lambda item: item["distance"])


# -----------------------------
# 세션 및 로그인
# -----------------------------
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "location_result" not in st.session_state:
    st.session_state.location_result = None

# -----------------------------
# 같은 브라우저에서 다른 이름 로그인 제한
# -----------------------------
from streamlit_cookies_manager import EncryptedCookieManager

cookies = EncryptedCookieManager(
    prefix="attendance_app/",
    password="attendance-device-lock-2026-change-this-secret"
)

if not cookies.ready():
    st.stop()   

<script>
    const KEY = "attendance_user_name";
    const savedName = localStorage.getItem(KEY);

    window.addEventListener("message", function(event) {
        if (event.data && event.data.type === "attendance_login") {
            const name = event.data.name;

            if (savedName && savedName !== name) {
                window.parent.postMessage({
                    type: "attendance_login_blocked"
                }, "*");
            } else {
                localStorage.setItem(KEY, name);
            }
        }
    });
    </script>
    """,
    height=0,
)

df = load_data()
admins = load_json(ADMINS_FILE, [])
settings = load_settings()

if not isinstance(admins, list):
    admins = []

st.title("📘 출석관리 시스템")
st.caption("GPS 위치 기록 · 가까운 건물 검색 · 관리자 지도 확인")

with st.sidebar:
    st.header("메뉴")

    if not st.session_state.user_name:
        st.subheader("로그인")
        login_name = st.text_input("이름", key="login_name")

if st.button("로그인", use_container_width=True):
    name = login_name.strip()
    saved_name = cookies.get("attendance_user_name", "")

    if not name:
        st.error("이름을 입력해 주세요.")

    elif saved_name and saved_name != name:
        st.error(
            f"이 기기는 이미 '{saved_name}' 이름으로 등록되어 있습니다. "
            "다른 이름으로 로그인할 수 없습니다."
        )

    else:
        cookies["attendance_user_name"] = name
        cookies.save()

        st.session_state.user_name = name
        st.rerun()

    else:
        st.write(f"로그인: **{st.session_state.user_name}**")

        if st.button("로그아웃", use_container_width=True):
            st.session_state.user_name = ""
            st.session_state.location_result = None
            st.rerun()

    st.divider()

    if not admins:
        page = st.radio(
            "페이지",
            ["출석관리", "내 출결 기록", "최초 관리자 임명"],
            key="page_no_admin"
        )
    elif st.session_state.user_name in admins:
        page = st.radio(
            "페이지",
            ["출석관리", "내 출결 기록", "관리자 페이지"],
            key="page_admin"
        )
    else:
        page = st.radio(
            "페이지",
            ["출석관리", "내 출결 기록"],
            key="page_student"
        )

if not st.session_state.user_name:
    st.info("왼쪽 메뉴에서 이름을 입력하고 로그인해 주세요.")
    st.stop()

user_name = st.session_state.user_name
is_admin = user_name in admins

# -----------------------------
# 최초 관리자 임명
# -----------------------------
if page == "최초 관리자 임명":
    st.header("최초 관리자 임명")

    if admins:
        st.warning("이미 관리자가 지정되어 있습니다.")
    else:
        st.warning(
            "이름만으로 로그인하므로 다른 사람의 이름을 입력하면 "
            "본인 확인 없이 로그인할 수 있습니다."
        )

        admin_name = st.text_input("관리자로 지정할 이름")

        if st.button("최초 관리자 지정"):
            admin_name = admin_name.strip()

            if not admin_name:
                st.error("이름을 입력해 주세요.")
            else:
                save_json(ADMINS_FILE, [admin_name])
                st.success(f"{admin_name} 님을 관리자로 지정했습니다.")
                st.rerun()


# -----------------------------
# 출석 등록
# -----------------------------
elif page == "출석관리":
    st.header("출석 등록")

    settings = load_settings()

    start_date = date.fromisoformat(settings["start_date"])
    end_date = date.fromisoformat(settings["end_date"])
    registration_end = end_date + timedelta(days=7)
    today = date.today()

    st.write(f"**출석 기간:** {settings.get('period_name', '출석 기간')}")
    st.write(f"{start_date} ~ {end_date}")
    st.caption(
        f"등록 가능 기간: {start_date} ~ {registration_end} "
        "(종료일 이후 7일까지)"
    )

    if today < start_date or today > registration_end:
        st.error("현재는 출석 등록 기간이 아닙니다.")
    else:
        df = load_data()

        already_registered = (
            (df["날짜"].astype(str) == today.isoformat())
            & (df["이름"].astype(str) == user_name)
        ).any()

        if already_registered:
            st.warning("오늘은 이미 출석 기록이 등록되어 있습니다.")
        else:
            st.info(
                "브라우저의 위치 권한을 허용해 주세요. "
                "GPS 정확도가 300m보다 나쁘면 등록할 수 없습니다."
            )

            try:
                from streamlit_geolocation import streamlit_geolocation
                location = streamlit_geolocation()
            except ImportError:
                location = None
                st.error(
                    "위치 기능 패키지가 설치되어 있지 않습니다. "
                    "터미널에서 다음 명령어를 실행해 주세요: "
                    "python -m pip install streamlit-geolocation"
                )

            if isinstance(location, dict):
                lat_value = location.get("latitude")
                lon_value = location.get("longitude")
                accuracy_value = location.get("accuracy")

                if (
                    lat_value is not None
                    and lon_value is not None
                    and accuracy_value is not None
                ):
                    try:
                        lat_value = float(lat_value)
                        lon_value = float(lon_value)
                        accuracy_value = float(accuracy_value)

                        if (
                            math.isfinite(lat_value)
                            and math.isfinite(lon_value)
                            and math.isfinite(accuracy_value)
                            and -90 <= lat_value <= 90
                            and -180 <= lon_value <= 180
                            and accuracy_value >= 0
                        ):
                            st.session_state.location_result = {
                                "lat": lat_value,
                                "lon": lon_value,
                                "accuracy": accuracy_value
                            }
                    except (TypeError, ValueError):
                        pass

            loc = st.session_state.location_result

            if loc:
                lat = loc["lat"]
                lon = loc["lon"]
                accuracy = loc["accuracy"]

                st.success("GPS 위치를 받았습니다.")
                st.write(f"위도: `{lat:.6f}`")
                st.write(f"경도: `{lon:.6f}`")
                st.write(f"GPS 정확도: 약 **{accuracy:.0f}m**")

                st.link_button(
                    "Google 지도에서 현재 위치 확인",
                    make_map_link(lat, lon)
                )

                if accuracy > MAX_GPS_ACCURACY:
                    st.error(
                        "GPS 정확도가 300m를 초과합니다. "
                        "창가나 실외에서 위치를 다시 확인해 주세요."
                    )

                    if st.button("GPS 다시 확인"):
                        st.session_state.location_result = None
                        st.rerun()

                else:
                    st.success("GPS 정확도 기준을 통과했습니다.")

                    # 장소 검색은 등록 버튼을 누르기 전 미리 실행하지 않습니다.
                    with st.form("attendance_form"):
                        status = st.selectbox(
                            "출결 상태",
                            ["출석", "결석", "지각"]
                        )

                        absence_reason = ""
                        late_reason = ""
                        detail = ""

                        if status == "결석":
                            absence_reason = st.selectbox(
                                "결석 사유",
                                ABSENCE_REASONS
                            )

                            if absence_reason == "기타":
                                detail = st.text_input("결석 사유 상세 입력")

                        elif status == "지각":
                            late_reason = st.selectbox(
                                "지각 사유",
                                LATE_REASONS
                            )

                            if late_reason == "기타":
                                detail = st.text_input("지각 사유 상세 입력")

                        submitted = st.form_submit_button("출석 기록 등록")

                    if submitted:
                        # 등록 직전 중복 확인
                        df = load_data()

                        duplicate = (
                            (df["날짜"].astype(str) == today.isoformat())
                            & (df["이름"].astype(str) == user_name)
                        ).any()

                        if duplicate:
                            st.error("오늘 기록이 이미 존재합니다.")
                        elif accuracy > MAX_GPS_ACCURACY:
                            st.error("GPS 정확도가 기준을 초과했습니다.")
                        else:
                            with st.spinner(
                                "300m 이내의 가장 가까운 건물을 검색하고 있습니다..."
                            ):
                                nearby_building = find_nearest_building(
                                    lat, lon
                                )

                            if nearby_building is None:
                                st.error(
                                    "300m 이내의 건물 정보를 찾지 못했습니다. "
                                    "인터넷 연결을 확인하고 다시 시도해 주세요. "
                                    "지도 데이터에 건물이 등록되어 있지 않을 수도 있습니다."
                                )
                            else:
                                if (
                                    status == "결석"
                                    and absence_reason == "기타"
                                ):
                                    absence_reason = (
                                        f"기타: {detail.strip()}"
                                        if detail.strip() else "기타"
                                    )

                                if (
                                    status == "지각"
                                    and late_reason == "기타"
                                ):
                                    late_reason = (
                                        f"기타: {detail.strip()}"
                                        if detail.strip() else "기타"
                                    )

                                record = {
                                    "날짜": today.isoformat(),
                                    "이름": user_name,
                                    "출결상태": status,
                                    "결석사유": absence_reason,
                                    "지각사유": late_reason,
                                    "등록시간": datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                    "건물 이름": nearby_building["name"],
                                    "GPS정확도(m)": round(accuracy, 1),
                                    "지도링크": make_map_link(lat, lon),
                                    "위도": lat,
                                    "경도": lon
                                }

                                df = pd.concat(
                                    [df, pd.DataFrame([record])],
                                    ignore_index=True
                                )
                                save_data(df)

                                st.session_state.location_result = None

                                st.success(
                                    f"출석 기록을 등록했습니다. "
                                    f"가장 가까운 건물: {nearby_building['name']} "
                                    f"(건물 중심까지 약 "
                                    f"{nearby_building['distance']:.0f}m)"
                                )
                                st.rerun()
            else:
                st.warning(
                    "GPS 정보를 아직 받지 못했습니다. "
                    "위치 권한을 허용하고 잠시 기다려 주세요."
                )

                if st.button("위치 다시 확인"):
                    st.session_state.location_result = None
                    st.rerun()


# -----------------------------
# 내 출결 기록
# -----------------------------
elif page == "내 출결 기록":
    st.header("내 출결 기록")

    df = load_data()
    mine = df[df["이름"].astype(str) == user_name].copy()

    if mine.empty:
        st.info("등록된 출결 기록이 없습니다.")
    else:
        mine = mine.sort_values("날짜", ascending=False)
        st.dataframe(
            mine,
            use_container_width=True,
            hide_index=True
        )

        csv_bytes = mine.to_csv(
            index=False,
            encoding="utf-8-sig"
        ).encode("utf-8-sig")

        st.download_button(
            "내 출결 기록 CSV 다운로드",
            data=csv_bytes,
            file_name=f"{user_name}_출결기록.csv",
            mime="text/csv"
        )

        st.subheader("등록 위치 지도")

        for index, record in mine.iterrows():
            map_url = str(record.get("지도링크", "")).strip()

            if map_url.startswith("https://"):
                st.write(
                    f"**{record['날짜']}** · {record['출결상태']} · "
                    f"{record.get('건물 이름', '')}"
                )
                st.link_button(
                    f"{record['날짜']} 지도 열기",
                    map_url,
                    key=f"student_map_{index}"
                )


# -----------------------------
# 관리자 페이지
# -----------------------------
elif page == "관리자 페이지":
    if not is_admin:
        st.error("관리자만 접근할 수 있습니다.")
        st.stop()

    st.header("관리자 페이지")

    tab1, tab2, tab3 = st.tabs([
        "출결 조회 및 수정",
        "출석 기간 설정",
        "관리자 관리"
    ])

    # -------------------------
    # 출결 조회 및 수정
    # -------------------------
    with tab1:
        df = load_data()

        selected_date = st.date_input(
            "조회할 날짜",
            value=date.today()
        )

        day_df = df[
            df["날짜"].astype(str) == selected_date.isoformat()
        ].copy()

        total = len(day_df)
        present_count = (day_df["출결상태"] == "출석").sum()
        absent_count = (day_df["출결상태"] == "결석").sum()
        late_count = (day_df["출결상태"] == "지각").sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("전체 등록", total)
        c2.metric("출석", int(present_count))
        c3.metric("결석", int(absent_count))
        c4.metric("지각", int(late_count))

        if day_df.empty:
            st.info("선택한 날짜의 출결 기록이 없습니다.")
        else:
            st.dataframe(
                day_df,
                use_container_width=True,
                hide_index=True
            )

            # 관리자 지도: 저장된 GPS 좌표 표시
            st.subheader("📍 출석 등록 위치 지도")

            map_df = day_df.copy()
            map_df["위도"] = pd.to_numeric(
                map_df["위도"], errors="coerce"
            )
            map_df["경도"] = pd.to_numeric(
                map_df["경도"], errors="coerce"
            )

            map_df = map_df.dropna(subset=["위도", "경도"])

            if not map_df.empty:
                map_points = map_df.rename(columns={
                    "위도": "latitude",
                    "경도": "longitude"
                })

                st.map(
                    map_points,
                    latitude="latitude",
                    longitude="longitude",
                    size=100
                )

                st.caption(
                    "각 점은 출석 등록 당시 저장된 GPS 위치입니다. "
                    "GPS 오차가 있을 수 있습니다."
                )

                for idx, location_row in map_df.iterrows():
                    st.write(
                        f"**{location_row['이름']}** · "
                        f"{location_row['건물 이름']} · "
                        f"정확도 약 {location_row['GPS정확도(m)']}m"
                    )

                    map_url = str(
                        location_row.get("지도링크", "")
                    ).strip()

                    if map_url.startswith("https://"):
                        st.link_button(
                            f"{location_row['이름']} 등록 위치를 Google 지도에서 보기",
                            map_url,
                            key=f"admin_map_{idx}"
                        )
            else:
                st.info(
                    "지도에 표시할 좌표가 없습니다. "
                    "기존 기록에는 위도·경도가 저장되어 있지 않을 수 있습니다."
                )

            st.divider()
            st.subheader("출결 기록 수정")

            names = day_df["이름"].astype(str).tolist()
            selected_name = st.selectbox(
                "수정할 이름",
                names
            )

            row_matches = day_df[
                day_df["이름"].astype(str) == selected_name
            ]

            if not row_matches.empty:
                selected_row = row_matches.iloc[-1]
                current_status = str(selected_row["출결상태"])
                status_options = ["출석", "결석", "지각"]

                status_index = (
                    status_options.index(current_status)
                    if current_status in status_options
                    else 0
                )

                def reason_index(value, options):
                    value = str(value)

                    if value in options:
                        return options.index(value)

                    if value.startswith("기타"):
                        return options.index("기타")

                    return 0

                with st.form("admin_edit_form"):
                    new_status = st.selectbox(
                        "출결 상태 수정",
                        status_options,
                        index=status_index
                    )

                    new_absence = st.selectbox(
                        "결석 사유",
                        ABSENCE_REASONS,
                        index=reason_index(
                            selected_row["결석사유"],
                            ABSENCE_REASONS
                        )
                    )

                    new_late = st.selectbox(
                        "지각 사유",
                        LATE_REASONS,
                        index=reason_index(
                            selected_row["지각사유"],
                            LATE_REASONS
                        )
                    )

                    save_edit = st.form_submit_button("수정 저장")

                if save_edit:
                    mask = (
                        (df["날짜"].astype(str) == selected_date.isoformat())
                        & (df["이름"].astype(str) == selected_name)
                    )

                    indexes = df.index[mask].tolist()

                    if indexes:
                        idx = indexes[-1]

                        df.at[idx, "출결상태"] = new_status
                        df.at[idx, "결석사유"] = (
                            new_absence if new_status == "결석" else ""
                        )
                        df.at[idx, "지각사유"] = (
                            new_late if new_status == "지각" else ""
                        )

                        save_data(df)
                        st.success("출결 기록을 수정했습니다.")
                        st.rerun()

        # CSV 다운로드
        st.divider()
        st.subheader("출결 데이터 다운로드")

        all_csv = df.to_csv(
            index=False,
            encoding="utf-8-sig"
        ).encode("utf-8-sig")

        st.download_button(
            "전체 출결 CSV 다운로드",
            data=all_csv,
            file_name="전체_출결기록.csv",
            mime="text/csv"
        )

        month_value = st.date_input(
            "다운로드할 월 선택",
            value=date.today(),
            key="download_month"
        )

        month_key = month_value.strftime("%Y-%m")
        month_df = df[
            df["날짜"].astype(str).str.startswith(month_key)
        ].copy()

        st.download_button(
            "선택 월 CSV 다운로드",
            data=month_df.to_csv(
                index=False,
                encoding="utf-8-sig"
            ).encode("utf-8-sig"),
            file_name=f"{month_key}_출결기록.csv",
            mime="text/csv"
        )

    # -------------------------
    # 출석 기간 설정
    # -------------------------
    with tab2:
        st.subheader("출석 등록 기간 설정")
        settings = load_settings()

        try:
            old_start = date.fromisoformat(settings["start_date"])
        except Exception:
            old_start = date.today()

        try:
            old_end = date.fromisoformat(settings["end_date"])
        except Exception:
            old_end = date.today()

        with st.form("period_form"):
            period_name = st.text_input(
                "기간 이름",
                value=settings.get("period_name", "출석 기간")
            )

            new_start = st.date_input(
                "출석 시작일",
                value=old_start
            )

            new_end = st.date_input(
                "출석 종료일",
                value=old_end
            )

            save_period = st.form_submit_button("기간 설정 저장")

        if save_period:
            if new_end < new_start:
                st.error("종료일은 시작일보다 빠를 수 없습니다.")
            else:
                settings = {
                    "start_date": new_start.isoformat(),
                    "end_date": new_end.isoformat(),
                    "period_name": period_name.strip() or "출석 기간"
                }

                save_json(SETTINGS_FILE, settings)

                st.success(
                    "출석 기간을 저장했습니다. 종료일 이후 7일까지 등록할 수 있습니다."
                )
                st.rerun()

    # -------------------------
    # 관리자 관리
    # -------------------------
    with tab3:
        st.subheader("관리자 임명")
        current_admins = load_json(ADMINS_FILE, [])

        with st.form("add_admin_form"):
            new_admin = st.text_input("관리자로 지정할 이름")
            add_admin = st.form_submit_button("관리자 임명")

        if add_admin:
            new_admin = new_admin.strip()

            if not new_admin:
                st.error("이름을 입력해 주세요.")
            elif new_admin in current_admins:
                st.warning("이미 관리자입니다.")
            else:
                current_admins.append(new_admin)
                save_json(ADMINS_FILE, current_admins)
                st.success(f"{new_admin} 님을 관리자로 임명했습니다.")
                st.rerun()

        st.divider()
        st.subheader("관리자 목록")

        if current_admins:
            st.write(", ".join(current_admins))
        else:
            st.info("등록된 관리자가 없습니다.")

        removable_admins = [
            name for name in current_admins
            if name != user_name
        ]

        if removable_admins:
            remove_name = st.selectbox(
                "해제할 관리자 (본인 제외)",
                removable_admins
            )

            if st.button("선택한 관리자 해제"):
                current_admins = [
                    name for name in current_admins
                    if name != remove_name
                ]

                save_json(ADMINS_FILE, current_admins)
                st.success(
                    f"{remove_name} 님의 관리자 권한을 해제했습니다."
                )
                st.rerun()
        else:
            st.caption("해제할 다른 관리자가 없습니다.")


# -----------------------------
# 안내
# -----------------------------
st.divider()
st.caption(
    "안내: 이름만으로 로그인하므로 본인 확인 기능은 없습니다. "
    "GPS 정확도는 기기와 주변 환경에 따라 달라집니다. "
    "건물 이름은 OpenStreetMap 데이터에 등록된 정보에 따라 달라질 수 있습니다. "
    "GPS 위치는 실제 출석을 완벽하게 증명하지 않습니다."
)
