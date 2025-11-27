# checklist_app_a_layout.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(layout="wide", page_title="始業前チェックリスト (Aレイアウト)")

# --------------------------
# スマホ対応の簡易CSS（ボタンを小さく、表の横スクロール許可）
# --------------------------
st.markdown("""
<style>
/* container padding */
.block-container {
  padding-top: 8px;
  padding-bottom: 8px;
}

/* テーブルの横スクロール領域 */
.scroll-wrap {
  overflow-x: auto;
}

/* Streamlit ボタンを小さくする（全体に効く） */
button[data-baseweb="button"] {
  padding: 6px 8px !important;
  font-size: 15px !important;
  min-width: 44px !important;
  height: 40px !important;
}

/* ボタン内テキストを中央に */
button[data-baseweb="button"] > span {
  display: inline-block;
  width: 100%;
}

/* タブの横スクロール（もしタブを使う場合） */
[data-baseweb="tab-list"] {
  overflow-x: auto !important;
  white-space: nowrap !important;
}

/* 小さい画面の微調整 */
@media (max-width: 600px) {
  button[data-baseweb="button"] {
    padding: 4px 6px !important;
    font-size: 14px !important;
    min-width: 36px !important;
    height: 36px !important;
  }
  .stMarkdown p, .stMarkdown div {
    font-size: 0.95rem;
  }
}
</style>
""", unsafe_allow_html=True)

# ==========================
# パスワード
# ==========================
PASSWORD = "2226"

def check_password():
    st.title("🔐 チェックリスト アクセス認証")
    pwd = st.text_input("パスワードを入力してください", type="password", key="login_pwd")
    if st.button("ログイン", key="login_btn"):
        if pwd == PASSWORD:
            st.session_state["auth"] = True
            st.success("認証成功！")
        else:
            st.error("パスワードが違います")
    return st.session_state.get("auth", False)

# ==========================
# ボタンの状態切替（即時反映）
# ==========================
def toggle_state(state_key):
    """state_key を '','〇','×' の順で切り替える"""
    now = st.session_state.get(state_key, "")
    if now == "":
        st.session_state[state_key] = "〇"
    elif now == "〇":
        st.session_state[state_key] = "×"
    else:
        st.session_state[state_key] = ""

# ==========================
# メインアプリ（Aレイアウト：1画面に全部並べる）
# ==========================
def main_app():
    machines = [f"{i}号機" for i in range(1, 11)]
    sections = {
        "作業台": ["シャーペン", "消しゴム", "不要物"],
        "成形機": ["真鍮棒", "EJロッド", "フライパン", "不要物"]
    }

    HISTORY_FILE = "checklist_history.csv"

    # 履歴読み込み（なければ空）
    if os.path.exists(HISTORY_FILE):
        try:
            history_df = pd.read_csv(HISTORY_FILE)
        except pd.errors.EmptyDataError:
            history_df = pd.DataFrame()
    else:
        history_df = pd.DataFrame()

    st.header("📋 始業前チェックリスト（Aレイアウト）")

    # 担当者ID
    staff_id = st.text_input("担当者IDを入力してください", key="staff_id")
    if staff_id == "":
        st.warning("担当者IDを入力してください")

    st.markdown("---")

    # ---------- 表形式で表示（横スクロール可能） ----------
    st.markdown('<div class="scroll-wrap">', unsafe_allow_html=True)

    # ヘッダー行（項目 + 各号機）
    header_cols = st.columns(len(machines) + 1)
    header_cols[0].markdown("**項目**")
    for i, m in enumerate(machines):
        header_cols[i + 1].markdown(f"**{m}**")

    # 各セクション（作業台 / 成形機）
    # コメント（不要物）はセクションごとに1つのコメント欄にする（画面を小さく保つため）
    section_comments = {}
    for section, items in sections.items():
        st.subheader(f"【{section}】")
        for item in items:
            # 1行に (項目 + 10台) を表示
            row_cols = st.columns(len(machines) + 1)
            row_cols[0].markdown(item)
            # 各号機ごとのボタン
            for idx, m in enumerate(machines):
                # state key のユニーク化（section, item, machine を含める）
                state_key = f"state__{section}__{item}__{m}"
                if state_key not in st.session_state:
                    st.session_state[state_key] = ""  # 初期は空

                # ラベルは session_state の値（空はスペースでボタン幅を確保）
                label = st.session_state[state_key] if st.session_state[state_key] else " "

                # ボタンのキー（確実にユニーク）
                btn_key = f"btn__{section}__{item}__{m}"

                # ボタン。押すと toggle_state をコール（即反映）
                row_cols[idx + 1].button(
                    label,
                    key=btn_key,
                    on_click=toggle_state,
                    args=(state_key,),
                    use_container_width=True,
                    help="タッチで〇→×→空白"
                )

            # 不要物はセクション単位でコメント（折りたたみ）
            if item == "不要物":
                comment_key = f"comment__{section}__{item}"
                with st.expander(f"{section} - 不要物 コメント"):
                    section_comments[section] = st.text_input("コメントを入力（このセクション共通）", key=comment_key)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ---------- 登録ボタン（当日上書き） ----------
    if st.button("登録", key="register_btn"):
        if staff_id == "":
            st.error("担当者IDを入力してください")
        else:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            today = datetime.now().strftime("%Y-%m-%d")

            # 同日の履歴は削除して上書きする動作
            if not history_df.empty and "日時" in history_df.columns:
                history_df = history_df[~history_df["日時"].str.startswith(today)]

            # 新規行を作る（各 section/item/machine の状態を展開）
            rows = []
            for section, items in sections.items():
                for item in items:
                    for m in machines:
                        state_key = f"state__{section}__{item}__{m}"
                        state_val = st.session_state.get(state_key, "")
                        row = {
                            "日時": timestamp,
                            "担当者ID": staff_id,
                            "セクション": section,
                            "項目": item,
                            "号機": m,
                            "状態": state_val,
                            "コメント": section_comments.get(section, "")
                        }
                        rows.append(row)

            new_df = pd.DataFrame(rows)
            history_df = pd.concat([history_df, new_df], ignore_index=True)
            history_df.to_csv(HISTORY_FILE, index=False)
            st.success("登録しました！（同日のデータを上書きしました）")

    # ---------- 履歴表示 / ダウンロード ----------
    if not history_df.empty:
        st.subheader("履歴一覧")
        st.dataframe(history_df, use_container_width=True)
        csv = history_df.to_csv(index=False).encode("utf-8")
        st.download_button("CSVダウンロード", csv, "checklist_history.csv", key="download_csv")

    # ---------- 履歴全削除 ----------
    if st.button("履歴を全削除", key="clear_history"):
        if os.path.exists(HISTORY_FILE):
            os.remove(HISTORY_FILE)
        history_df = pd.DataFrame()
        st.warning("履歴ファイルを削除しました（ローカル）")

# ==========================
# アプリ起動
# ==========================
if check_password():
    main_app()
