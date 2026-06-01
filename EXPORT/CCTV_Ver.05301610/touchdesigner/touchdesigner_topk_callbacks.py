# Use this file as a DAT Execute callback on a Table DAT that receives
# /walnut/topk/cam/[cam]/results rows from an OSC In DAT callback.
#
# Expected flat row shape:
# event_id, timestamp, query_id, query_cam_id, k, result_count, gallery_count,
# rank_1, clip_id_1, clip_path_1, score_1, cam_id_1, fallback_1, ...

TOPK_TABLE_PATH = "topk_results_table"
TOPK_HEADER = [
    "event_id",
    "timestamp",
    "query_id",
    "query_cam_id",
    "k",
    "result_count",
    "gallery_count",
    "results...",
]


def _find_table(dat):
    table = dat.parent().op(TOPK_TABLE_PATH)
    if table is None:
        table = op(TOPK_TABLE_PATH)
    return table


def ensureTopKTable(dat):
    table = _find_table(dat)
    if table is None:
        debug(f"Missing Table DAT: {TOPK_TABLE_PATH}")
        return None
    if table.numRows == 0:
        table.appendRow(TOPK_HEADER)
    return table


def appendTopKRow(dat, args):
    table = ensureTopKTable(dat)
    if table is None:
        return
    if len(args) < 7:
        debug(f"TopK payload too short: {args}")
        return
    table.appendRow([str(value) for value in args])


def onReceiveOSC(dat, rowIndex, message, bytes, timeStamp, address, args, peer):
    if not address.startswith("/walnut/topk/cam/") or not address.endswith("/results"):
        return
    appendTopKRow(dat, args)
    return


def onSizeChange(dat):
    if dat.numRows <= 1:
        return

    latest_row = dat.numRows - 1
    try:
        k = int(dat[latest_row, 4].val or 9)
        result_count = int(dat[latest_row, 5].val or 0)
    except Exception:
        k = 9
        result_count = 0

    slot_count = max(1, min(12, k))
    for slot in range(1, slot_count + 1):
        target_movie = op(f"movie_clip_{slot}")
        if target_movie:
            target_movie.par.file = ""

    if result_count <= 0:
        return

    base_col = 7
    fields_per_result = 6
    max_results = min(result_count, slot_count)
    for result_index in range(max_results):
        col = base_col + (result_index * fields_per_result)
        if col + 5 >= dat.numCols:
            break

        try:
            rank = int(dat[latest_row, col].val or (result_index + 1))
        except Exception:
            rank = result_index + 1
        if rank < 1 or rank > slot_count:
            continue

        clip_path = dat[latest_row, col + 2].val.strip().strip('"').strip("'")
        if not clip_path:
            continue

        target_movie = op(f"movie_clip_{rank}")
        if target_movie:
            target_movie.par.file = clip_path
            target_movie.par.reloadpulse.pulse()
    return
