# me - this DAT
#
# Use this file as the callbacks DAT for an OSC In DAT in TouchDesigner.
# It stores one row per unique /walnut/log/cam/[cam]/visit event and ignores repeats.
# It also stores Type C lookup history rows from /walnut/type_c/cam/[cam]/history.

LOG_TABLE_PATH = "visitor_log_table"
TYPE_C_HISTORY_TABLE_PATH = "type_c_history_table"
VISIT_PREFIX = "/walnut/log/cam/"
VISIT_SUFFIX = "/visit"
TYPE_C_HISTORY_PREFIX = "/walnut/type_c/cam/"
TYPE_C_HISTORY_SUFFIX = "/history"
EVENT_CACHE_KEY = "seen_visit_event_keys"
TYPE_C_EVENT_CACHE_KEY = "seen_type_c_history_keys"
HEADER = [
    "event_id",
    "timestamp",
    "visitor_id",
    "cam_id",
    "top",
    "bottom",
    "bag",
    "is_long_sleeve",
    "is_long_pants",
    "shoulder-to-hip",
    "brightness_ratio",
    "snapshot_path",
]
TYPE_C_HISTORY_HEADER = [
    "event_id",
    "timestamp",
    "matched_id",
    "cam_id",
    "clip_count",
    "clip_paths...",
]


def _find_log_table(dat):
    table = dat.parent().op(LOG_TABLE_PATH)
    if table is None:
        table = op(LOG_TABLE_PATH)
    return table


def _find_type_c_history_table(dat):
    table = dat.parent().op(TYPE_C_HISTORY_TABLE_PATH)
    if table is None:
        table = op(TYPE_C_HISTORY_TABLE_PATH)
    return table


def _ensure_log_table(dat):
    table = _find_log_table(dat)
    if table is None:
        debug(f"Missing Table DAT: {LOG_TABLE_PATH}")
        return None

    if table.numRows == 0:
        table.appendRow(HEADER)
    return table


def _ensure_type_c_history_table(dat):
    table = _find_type_c_history_table(dat)
    if table is None:
        debug(f"Missing Table DAT: {TYPE_C_HISTORY_TABLE_PATH}")
        return None

    if table.numRows == 0:
        table.appendRow(TYPE_C_HISTORY_HEADER)
    return table


def _get_seen_event_ids(dat, table):
    seen_keys = dat.fetch(EVENT_CACHE_KEY, None)
    if seen_keys is not None:
        return seen_keys

    seen_keys = set()
    if table.numRows > 1:
        for row_index in range(1, table.numRows):
            seen_keys.add(_make_event_key_from_row(table, row_index))

    dat.store(EVENT_CACHE_KEY, seen_keys)
    return seen_keys


def _is_visit_address(address):
    return address.startswith(VISIT_PREFIX) and address.endswith(VISIT_SUFFIX)


def _is_type_c_history_address(address):
    return address.startswith(TYPE_C_HISTORY_PREFIX) and address.endswith(TYPE_C_HISTORY_SUFFIX)


def _append_visit_row(table, args):
    row = [str(value) for value in args[: len(HEADER)]]
    table.appendRow(row)


def _make_event_key(args):
    return f"{args[0]}|{args[1]}|{args[3]}"


def _make_event_key_from_row(table, row_index):
    return f"{table[row_index, 0].val}|{table[row_index, 1].val}|{table[row_index, 3].val}"


def onReceiveOSC(dat, rowIndex, message, bytes, timeStamp, address, args, peer):
    if _is_type_c_history_address(address):
        _handle_type_c_history(dat, args)
        return

    if not _is_visit_address(address):
        return

    table = _ensure_log_table(dat)
    if table is None:
        return

    if len(args) < len(HEADER):
        debug(f"OSC visit payload too short: {args}")
        return

    event_key = _make_event_key(args)
    seen_ids = _get_seen_event_ids(dat, table)
    if event_key in seen_ids:
        return

    _append_visit_row(table, args)
    seen_ids.add(event_key)
    return


def _handle_type_c_history(dat, args):
    table = _ensure_type_c_history_table(dat)
    if table is None:
        return

    if len(args) < 5:
        debug(f"OSC Type C history payload too short: {args}")
        return

    event_key = f"{args[0]}|{args[1]}|{args[3]}"
    seen_keys = dat.fetch(TYPE_C_EVENT_CACHE_KEY, None)
    if seen_keys is None:
        seen_keys = set()
        if table.numRows > 1:
            for row_index in range(1, table.numRows):
                seen_keys.add(f"{table[row_index, 0].val}|{table[row_index, 1].val}|{table[row_index, 3].val}")
        dat.store(TYPE_C_EVENT_CACHE_KEY, seen_keys)

    if event_key in seen_keys:
        return

    table.appendRow([str(value) for value in args])
    seen_keys.add(event_key)
    return
