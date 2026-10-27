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
