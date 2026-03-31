from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from translations import t
from utils import distance_option_caption, format_date_ru, sport_line_emoji


def add_nav_rows(lang: str, with_back: bool = True) -> list[list[InlineKeyboardButton]]:
    row: list[InlineKeyboardButton] = []
    if with_back:
        row.append(
            InlineKeyboardButton(
                text=t(lang, "nav_back"), callback_data="add:nav:back"
            )
        )
    row.append(
        InlineKeyboardButton(
            text=t(lang, "nav_cancel"), callback_data="add:nav:cancel_prompt"
        )
    )
    return [row]


def nav_only_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=add_nav_rows(lang, True))


def edit_flow_dist_nav_rows(lang: str) -> list[list[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                text=t(lang, "nav_back"), callback_data="edit:nav:dist"
            ),
            InlineKeyboardButton(
                text=t(lang, "nav_cancel"), callback_data="edit:cancel"
            ),
        ]
    ]


def cancel_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "cancel_break_yes"), callback_data="add:cancel:yes"
                ),
                InlineKeyboardButton(
                    text=t(lang, "cancel_break_no"), callback_data="add:cancel:no"
                ),
            ],
        ]
    )


def sport_type_keyboard(flow: str, lang: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(lang, "sport_swimming"),
                callback_data=f"{flow}:sport:swimming",
            ),
            InlineKeyboardButton(
                text=t(lang, "sport_running"),
                callback_data=f"{flow}:sport:running",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "sport_cycling"),
                callback_data=f"{flow}:sport:cycling",
            ),
            InlineKeyboardButton(
                text=t(lang, "sport_triathlon"),
                callback_data=f"{flow}:sport:triathlon",
            ),
        ],
        [
            InlineKeyboardButton(
                text=t(lang, "sport_other"), callback_data=f"{flow}:sport:other"
            )
        ],
        *add_nav_rows(lang, False),
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def yes_no_keyboard(prefix: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "yes"), callback_data=f"{prefix}:yes"
                ),
                InlineKeyboardButton(
                    text=t(lang, "no"), callback_data=f"{prefix}:no"
                ),
            ],
            *add_nav_rows(lang, True),
        ]
    )


def skip_url_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "skip"), callback_data="add:url:skip"
                )
            ],
            *add_nav_rows(lang, True),
        ]
    )


def skip_notes_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "skip"), callback_data="add:notes:skip"
                )
            ],
            *add_nav_rows(lang, True),
        ]
    )


def preview_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "save"), callback_data="add:save"
                ),
                InlineKeyboardButton(
                    text=t(lang, "edit"), callback_data="add:edit:menu"
                ),
            ],
            *add_nav_rows(lang, True),
        ]
    )


def edit_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "field_sport"), callback_data="add:edit:sport"
                ),
                InlineKeyboardButton(
                    text=t(lang, "field_name"), callback_data="add:edit:name"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "field_date"), callback_data="add:edit:dates"
                ),
                InlineKeyboardButton(
                    text=t(lang, "field_location"), callback_data="add:edit:loc"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "field_distance"), callback_data="add:edit:dist"
                ),
                InlineKeyboardButton(
                    text=t(lang, "field_url"), callback_data="add:edit:url"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "field_participants_btn"),
                    callback_data="add:edit:extras",
                ),
                InlineKeyboardButton(
                    text=t(lang, "field_notes"), callback_data="add:edit:notes"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "edit_back_preview"),
                    callback_data="add:edit:back",
                )
            ],
            *add_nav_rows(lang, True),
        ]
    )


def date_confirm_past_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "date_past_ok"),
                    callback_data="add:dateconfirm:yes",
                ),
                InlineKeyboardButton(
                    text=t(lang, "date_past_redo"),
                    callback_data="add:dateconfirm:redo",
                ),
            ],
            *add_nav_rows(lang, True),
        ]
    )


def date_year_doubt_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "year_ok_yes"), callback_data="add:yearok:yes"
                ),
                InlineKeyboardButton(
                    text=t(lang, "year_ok_no"), callback_data="add:yearok:no"
                ),
            ],
            *add_nav_rows(lang, True),
        ]
    )


def date_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "date_confirm_yes"),
                    callback_data="add:dateconfirm:yes",
                ),
                InlineKeyboardButton(
                    text=t(lang, "date_confirm_redo"),
                    callback_data="add:dateconfirm:redo",
                ),
            ],
            *add_nav_rows(lang, True),
        ]
    )


def extras_manage_reply_keyboard(names: list[str], lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for i, n in enumerate(names):
        label = f"{i + 1}. {(n or '')[:26]} ❌"
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"add:exrm:{i}")]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(lang, "extra_add_participant"), callback_data="add:exadd"
            )
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(lang, "edit_back_preview"), callback_data="add:exback"
            )
        ]
    )
    rows.extend(add_nav_rows(lang, True))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def extras_remove_confirm_keyboard(idx: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "yes"), callback_data=f"add:exdel:{idx}"
                ),
                InlineKeyboardButton(text=t(lang, "no"), callback_data="add:excn"),
            ],
            *add_nav_rows(lang, True),
        ]
    )


def keep_field_keyboard(field: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "next_keep"),
                    callback_data=f"add:keep:{field}",
                )
            ],
            *add_nav_rows(lang, True),
        ]
    )


def multi_duration_keyboard(lang: str) -> InlineKeyboardMarkup:
    nums = [
        InlineKeyboardButton(text=str(n), callback_data=f"add:multidur:{n}")
        for n in range(2, 8)
    ]
    rows = [nums[:4], nums[4:]]
    rows.append(
        [
            InlineKeyboardButton(
                text=t(lang, "multi_enter_end_date"),
                callback_data="add:multidur:custom",
            )
        ]
    )
    rows.extend(add_nav_rows(lang, True))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def duration_range_confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "duration_confirm_yes"),
                    callback_data="add:durconf:yes",
                ),
                InlineKeyboardButton(
                    text=t(lang, "duration_confirm_edit"),
                    callback_data="add:durconf:edit",
                ),
            ],
            *add_nav_rows(lang, True),
        ]
    )


def distance_pick_keyboard(
    flow: str,
    options: list[str],
    lang: str,
    *,
    show_done: bool,
    add_navigation: bool = True,
    edit_navigation: bool = False,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i, opt in enumerate(options):
        row.append(
            InlineKeyboardButton(
                text=distance_option_caption(opt, lang),
                callback_data=f"{flow}:dist:pick:{i}",
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    if show_done:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "done_check"),
                    callback_data=f"{flow}:dist:done",
                )
            ]
        )

    if edit_navigation:
        rows.extend(edit_flow_dist_nav_rows(lang))
    elif add_navigation:
        rows.extend(add_nav_rows(lang, True))
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "join_cancel"), callback_data="join:cancel"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def distance_custom_keyboard(
    flow: str,
    lang: str,
    *,
    add_navigation: bool = True,
    edit_navigation: bool = False,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=t(lang, "done_check"), callback_data=f"{flow}:dist:done"
            )
        ]
    ]
    if edit_navigation:
        rows.extend(edit_flow_dist_nav_rows(lang))
    elif add_navigation:
        rows.extend(add_nav_rows(lang, True))
    else:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t(lang, "join_cancel"), callback_data="join:cancel"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def distance_more_done_keyboard(flow: str, lang: str) -> InlineKeyboardMarkup:
    return distance_custom_keyboard(
        flow, lang, add_navigation=(flow == "add")
    )


def extra_participants_more_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "extra_add_more_btn"),
                    callback_data="add:extra:more",
                ),
                InlineKeyboardButton(
                    text=t(lang, "done_plain"), callback_data="add:extra:done"
                ),
            ],
            *add_nav_rows(lang, True),
        ]
    )


def list_filters_keyboard(period: str, sport: str | None, lang: str) -> InlineKeyboardMarkup:
    sp = sport or "all"
    period_keys = {
        "weekend": "list_period_weekend",
        "month": "list_period_month",
        "3months": "list_period_3months",
        "all": "list_period_all",
    }

    def plab(k: str) -> str:
        base = t(lang, period_keys.get(k, "list_period_all"))
        return f"✓ {base}" if period == k else base

    period_row = [
        InlineKeyboardButton(
            text=plab("weekend"), callback_data=f"list:u:weekend:{sp}"
        ),
        InlineKeyboardButton(text=plab("month"), callback_data=f"list:u:month:{sp}"),
        InlineKeyboardButton(
            text=plab("3months"), callback_data=f"list:u:3months:{sp}"
        ),
        InlineKeyboardButton(text=plab("all"), callback_data=f"list:u:all:{sp}"),
    ]

    def slab(key: str, emoji: str) -> str:
        sel = sp == key
        return f"✓{emoji}" if sel else emoji

    all_types_lbl = (
        t(lang, "list_all_types_sel") if sp == "all" else t(lang, "list_all_types")
    )

    sport_row = [
        InlineKeyboardButton(
            text=slab("swimming", "🏊"), callback_data=f"list:u:{period}:swimming"
        ),
        InlineKeyboardButton(
            text=slab("running", "🏃"), callback_data=f"list:u:{period}:running"
        ),
        InlineKeyboardButton(
            text=slab("cycling", "🚴"), callback_data=f"list:u:{period}:cycling"
        ),
        InlineKeyboardButton(
            text=slab("triathlon", "🔱"), callback_data=f"list:u:{period}:triathlon"
        ),
        InlineKeyboardButton(
            text=slab("other", "🏅"), callback_data=f"list:u:{period}:other"
        ),
        InlineKeyboardButton(
            text=all_types_lbl, callback_data=f"list:u:{period}:all"
        ),
    ]

    return InlineKeyboardMarkup(inline_keyboard=[period_row, sport_row])


def join_events_keyboard(
    events: list[dict],
    lang: str,
    *,
    registered_event_ids: frozenset[str] | None = None,
) -> InlineKeyboardMarkup:
    reg = registered_event_ids or frozenset()
    rows: list[list[InlineKeyboardButton]] = []
    dash = t(lang, "dash")
    for e in events:
        eid = str(e["id"])
        emo = sport_line_emoji(str(e.get("sport_type", "")))
        title = str(e.get("name", t(lang, "event_default")))[:22]
        ds = format_date_ru(e["date_start"]) if e.get("date_start") else dash
        suffix = " ✅" if eid in reg else ""
        label = f"{emo} {title} — {ds}{suffix}"[:64]
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"join:pick:{eid}")]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text=t(lang, "join_cancel"), callback_data="join:cancel"
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def upcoming_events_pick_keyboard(
    events: list[dict],
    prefix: str,
    lang: str,
    *,
    extra_rows: list[list[InlineKeyboardButton]] | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    dash = t(lang, "dash")
    for e in events:
        eid = str(e["id"])
        emo = sport_line_emoji(str(e.get("sport_type", "")))
        title = str(e.get("name", t(lang, "event_default")))[:22]
        ds = format_date_ru(e["date_start"]) if e.get("date_start") else dash
        label = f"{emo} {title} — {ds}"[:64]
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"{prefix}:pick:{eid}")]
        )
    if extra_rows:
        rows.extend(extra_rows)
    rows.append(
        [
            InlineKeyboardButton(
                text=t(lang, "join_cancel_x"),
                callback_data=f"{prefix}:cancel",
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_field_menu_keyboard(event_id: str, lang: str) -> InlineKeyboardMarkup:
    e = event_id
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "field_name"), callback_data=f"edit:field:{e}:name"
                ),
                InlineKeyboardButton(
                    text=t(lang, "field_date"), callback_data=f"edit:field:{e}:date"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "field_location"),
                    callback_data=f"edit:field:{e}:location",
                ),
                InlineKeyboardButton(
                    text=t(lang, "field_sport"),
                    callback_data=f"edit:field:{e}:sport",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "field_distance"),
                    callback_data=f"edit:field:{e}:dist",
                ),
                InlineKeyboardButton(
                    text=t(lang, "field_url"), callback_data=f"edit:field:{e}:url"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "field_notes"),
                    callback_data=f"edit:field:{e}:notes",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "edit_back_list"), callback_data="edit:back:list"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "nav_cancel"), callback_data="edit:cancel"
                )
            ],
        ]
    )


def edit_sport_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "sport_swimming"),
                    callback_data="edit:sport:pick:swimming",
                ),
                InlineKeyboardButton(
                    text=t(lang, "sport_running"),
                    callback_data="edit:sport:pick:running",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "sport_cycling"),
                    callback_data="edit:sport:pick:cycling",
                ),
                InlineKeyboardButton(
                    text=t(lang, "sport_triathlon"),
                    callback_data="edit:sport:pick:triathlon",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "sport_other"),
                    callback_data="edit:sport:pick:other",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "nav_back"), callback_data="edit:nav:field"
                ),
                InlineKeyboardButton(
                    text=t(lang, "nav_cancel"), callback_data="edit:cancel"
                ),
            ],
        ]
    )


def edit_dist_after_sport_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "yes"), callback_data="edit:distreset:yes"
                ),
                InlineKeyboardButton(
                    text=t(lang, "edit_dist_keep"),
                    callback_data="edit:distreset:no",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "nav_cancel"), callback_data="edit:cancel"
                )
            ],
        ]
    )


def delete_confirm_keyboard(event_id: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "delete_yes"), callback_data=f"del:yes:{event_id}"
                ),
                InlineKeyboardButton(
                    text=t(lang, "delete_no"), callback_data="del:no"
                ),
            ],
        ]
    )


def stats_choice_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "stats_mine"), callback_data="stats:mine"
                ),
                InlineKeyboardButton(
                    text=t(lang, "stats_team"), callback_data="stats:community"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "nav_cancel"), callback_data="stats:cancel"
                )
            ],
        ]
    )


def result_preview_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "save"), callback_data="res:save"
                ),
                InlineKeyboardButton(
                    text=t(lang, "result_redo"), callback_data="res:redo"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "nav_cancel"), callback_data="res:cancel"
                )
            ],
        ]
    )


def result_skip_place_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t(lang, "skip"), callback_data="res:place:skip"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t(lang, "nav_cancel"), callback_data="res:cancel"
                )
            ],
        ]
    )


def add_group_pick_keyboard(groups: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for g in groups:
        raw_title = str(g.get("name") or "").strip()
        tid = g.get("telegram_chat_id", "")
        title = raw_title or t(lang, "group_chat_fallback", id=tid)
        gid = str(g.get("id") or "")
        if not gid:
            continue
        rows.append(
            [
                InlineKeyboardButton(
                    text=title[:64],
                    callback_data=f"add:grp:{gid}",
                ),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)
