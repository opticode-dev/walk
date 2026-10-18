import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="Campus Walk",
    page_icon="🚶",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .block-container { max-width: 760px; padding-top: 1.2rem; padding-bottom: 3rem; }
    .hero { padding: 1.2rem; border-radius: 18px; background: linear-gradient(135deg, #fff0e8, #fff8d9); margin-bottom: 1rem; }
    .hero h1 { margin: 0; color: #4a2d24; }
    .muted { color: #666; font-size: 0.9rem; }
    .person { border: 1px solid #e8e8e8; border-radius: 14px; padding: 0.9rem; margin-bottom: 0.7rem; }
    div.stButton > button { border-radius: 12px; min-height: 2.7rem; }
</style>
""", unsafe_allow_html=True)

# ---- Demo data -------------------------------------------------------------
# This prototype stores data only in Streamlit's session state.
# It does not share data between different users/devices.
DEMO_PEOPLE = [
    {
        "id": "p1", "name": "みずき", "year": "大学2年生", "role": "学生",
        "bio": "授業前にゆっくり歩きたい派です。音楽やカフェの話が好き。",
        "status": "一緒に歩きたい", "route": "南平駅 → 日野キャンパス",
        "lat": 35.6620, "lon": 139.3950, "minutes": 8,
        "interests": "音楽・カフェ",
    },
    {
        "id": "p2", "name": "りく", "year": "大学3年生", "role": "学生",
        "bio": "通学時間を有効に使いたいです。最近は映画をよく見ます。",
        "status": "会話できたらうれしい", "route": "南平駅 → 日野キャンパス",
        "lat": 35.6632, "lon": 139.3972, "minutes": 12,
        "interests": "映画・ゲーム",
    },
    {
        "id": "p3", "name": "佐藤先生", "year": "教員", "role": "教授",
        "bio": "学生の皆さんと気軽に挨拶できたらと思っています。",
        "status": "今日は一人で歩く", "route": "高幡不動駅 → 日野キャンパス",
        "lat": 35.6598, "lon": 139.3928, "minutes": 15,
        "interests": "研究・散歩",
    },
]

def init_state():
    defaults = {
        "profile": {
            "name": "あなた", "year": "大学2年生", "role": "学生",
            "bio": "音楽を聴くのが好きです。気軽に話しかけてください。",
            "status": "一緒に歩きたい",
            "route": "南平駅 → 日野キャンパス",
            "interests": "音楽・大学生活",
        },
        "online": False,
        "requests_sent": set(),
        "incoming": {},
        "matches": set(),
        "hidden_people": set(),
        "messages": {},
        "selected_chat": None,
        "demo_people": DEMO_PEOPLE.copy(),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_state()

st.markdown("""
<div class="hero">
  <h1>🚶 Campus Walk</h1>
  <p style="margin-bottom:0;color:#60483e">通学時間を、ちょっと楽しい時間に。</p>
</div>
""", unsafe_allow_html=True)

st.info("プロトタイプ / デモ用データです。位置情報はサンプルで、実際のGPS共有や他端末との同期は行いません。")

tabs = st.tabs(["🏠 ホーム", "👤 プロフィール", "💬 チャット", "ℹ️ 使い方"])

# ---- Profile ---------------------------------------------------------------
with tabs[1]:
    st.subheader("プロフィール")
    profile = st.session_state.profile
    with st.form("profile_form"):
        name = st.text_input("表示名", value=profile["name"], max_chars=20)
        role = st.selectbox("区分", ["学生", "教授"], index=0 if profile["role"] == "学生" else 1)
        year_options = ["大学1年生", "大学2年生", "大学3年生", "大学4年生", "大学院生", "教員"]
        year = st.selectbox("学年・所属", year_options, index=year_options.index(profile["year"]) if profile["year"] in year_options else 1)
        bio = st.text_area("自己紹介", value=profile["bio"], max_chars=180, help="本名・電話番号などの個人情報は書かないでください。")
        route = st.text_input("主な通学ルート", value=profile["route"])
        interests = st.text_input("好きなこと", value=profile["interests"])
        status = st.selectbox(
            "今日のステータス",
            ["一緒に歩きたい", "会話できたらうれしい", "今日は一人で歩く"],
            index=["一緒に歩きたい", "会話できたらうれしい", "今日は一人で歩く"].index(profile["status"])
        )
        saved = st.form_submit_button("プロフィールを保存", use_container_width=True)
    if saved:
        st.session_state.profile = {
            "name": name.strip() or "匿名ユーザー",
            "role": role, "year": year, "bio": bio.strip(),
            "route": route.strip(), "interests": interests.strip(), "status": status,
        }
        st.success("プロフィールを保存しました。")
        st.rerun()

# ---- Home/search ------------------------------------------------------------
with tabs[0]:
    st.subheader("近くの通学仲間")
    st.write("同じ方向に歩く人を見つけて、通学時間を一緒に過ごそう。")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🔎 検索を開始する", use_container_width=True):
            st.session_state.online = True
            st.rerun()
    with c2:
        if st.button("オフラインにする", use_container_width=True):
            st.session_state.online = False
            st.rerun()

    if st.session_state.online:
        st.success("オンラインです。デモ用の通学仲間を表示しています。")
        current_route = st.session_state.profile["route"]
        same_route_only = st.checkbox("同じ通学ルートの人を優先する", value=False)
        people = [
            p for p in st.session_state.demo_people
            if p["id"] not in st.session_state.hidden_people
        ]
        if same_route_only:
            people = [p for p in people if p["route"] == current_route]

        if not people:
            st.warning("条件に合う人はいません。条件を変えてみてください。")

        for person in people:
            with st.container(border=True):
                left, right = st.columns([3, 1])
                with left:
                    icon = "🎓" if person["role"] == "学生" else "👩‍🏫"
                    st.markdown(f"### {icon} {person['name']}")
                    st.caption(f"{person['year']} ・ {person['route']}")
                    st.write(f"**ステータス：** {person['status']}")
                    st.write(f"**好きなこと：** {person['interests']}")
                    st.caption(f"デモ上の位置：キャンパスまで約{person['minutes']}分")
                with right:
                    st.metric("距離感", f"約{person['minutes']}分")
                with st.expander("プロフィールを見る"):
                    st.write(person["bio"])
                    st.write(f"**通学ルート：** {person['route']}")
                    st.write(f"**自己紹介：** {person['bio']}")
                if person["id"] in st.session_state.matches:
                    st.success("マッチ成立！チャットを利用できます。")
                elif person["id"] in st.session_state.requests_sent:
                    st.info("マッチ希望を送信済み")
                else:
                    if st.button("🤝 一緒に歩きたい", key=f"request_{person['id']}", use_container_width=True):
                        st.session_state.requests_sent.add(person["id"])
                        # Demo: the person can accept or decline below.
                        st.session_state.incoming[person["id"]] = "pending"
                        st.rerun()

        if st.session_state.requests_sent:
            st.divider()
            st.subheader("送ったマッチ希望（デモ）")
            st.caption("発表デモでは、相手側の操作をここで再現できます。")
            for person_id in list(st.session_state.requests_sent):
                person = next((p for p in st.session_state.demo_people if p["id"] == person_id), None)
                if not person:
                    continue
                status = st.session_state.incoming.get(person_id, "pending")
                st.write(f"**{person['name']}** への希望：{status}")
                a, b = st.columns(2)
                with a:
                    if st.button(f"✅ {person['name']}が承認", key=f"accept_{person_id}", use_container_width=True):
                        st.session_state.matches.add(person_id)
                        st.session_state.incoming[person_id] = "accepted"
                        st.session_state.messages.setdefault(person_id, [
                            {"from": person["name"], "text": "マッチありがとう！大学まで一緒に歩きましょう。"}
                        ])
                        st.success(f"{person['name']}さんとマッチしました！チャットが使えます。")
                        st.rerun()
                with b:
                    if st.button(f"✖️ {person['name']}が辞退", key=f"decline_{person_id}", use_container_width=True):
                        st.session_state.incoming[person_id] = "declined"
                        st.session_state.hidden_people.add(person_id)
                        st.session_state.requests_sent.discard(person_id)
                        st.info("この相手は検索結果から一時的に非表示になりました。")
                        st.rerun()
    else:
        st.warning("検索を開始すると、デモ用の通学仲間が表示されます。")
        st.markdown("**今日の自分のステータス：** " + st.session_state.profile["status"])

# ---- Chat -------------------------------------------------------------------
with tabs[2]:
    st.subheader("マッチした相手とのチャット")
    matched_people = [p for p in st.session_state.demo_people if p["id"] in st.session_state.matches]
    if not matched_people:
        st.info("マッチが成立すると、ここでチャットできます。")
    else:
        names = {p["id"]: p["name"] for p in matched_people}
        selected = st.selectbox(
            "相手を選択",
            options=list(names.keys()),
            format_func=lambda person_id: names[person_id],
            key="chat_select",
        )
        st.session_state.selected_chat = selected
        messages = st.session_state.messages.setdefault(selected, [])
        for msg in messages:
            with st.chat_message("assistant" if msg["from"] != st.session_state.profile["name"] else "user"):
                st.caption(msg["from"])
                st.write(msg["text"])
        new_message = st.chat_input("メッセージを入力")
        if new_message:
            messages.append({"from": st.session_state.profile["name"], "text": new_message})
            st.rerun()
        st.caption("デモ内のチャットです。別の端末の相手には送信されません。")

# ---- Help -------------------------------------------------------------------
with tabs[3]:
    st.subheader("このプロトタイプについて")
    st.markdown("""
**できること**
- プロフィール・自己紹介・通学ルート・ステータスの設定
- 検索を開始して、デモ用の通学仲間を表示
- 相手のプロフィールを確認
- マッチ希望の送信
- デモ上で承認・辞退を操作
- マッチ成立後のチャット画面

**まだ実装していないこと**
- 実際のGPS位置情報の取得・共有
- 複数端末間でのユーザー情報やマッチ状態の共有
- 本当の通知・ログイン
- サーバーに保存するチャット履歴

**安全面の注意**
- 実際の位置情報を公開する場合は、本人の明示的な同意が必要です。
- 正確な現在地を公開せず、駅・エリアなどのおおまかな位置にする設計を検討してください。
- マッチ相手と会う場合は、人目のある場所を選び、無理に会話や合流をしないでください。
- デモでは実名、学籍番号、電話番号などを入力しないでください。
""")
    if st.button("デモ状態をリセット"):
        for key in ["profile", "online", "requests_sent", "incoming", "matches", "hidden_people", "messages", "selected_chat", "demo_people"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

st.divider()
st.caption("激辛ハチワレ ・ ハッカソン用プロトタイプ")
