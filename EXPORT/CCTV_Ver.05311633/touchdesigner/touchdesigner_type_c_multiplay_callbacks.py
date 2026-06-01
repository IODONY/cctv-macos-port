import re

def onSizeChange(dat):
    # 헤더 제외하고 새 데이터(행)가 들어왔을 때만 작동
    if dat.numRows <= 1:
        return
        
    latest_row = dat.numRows - 1
    
    try:
        clip_count = int(dat[latest_row, 4].val or 0)
    except:
        clip_count = 0
        
    if clip_count == 0:
        return

    # 1번부터 9번 무비 클립 노드들 우선 리셋 (allowCooking 삭제)
    for i in range(1, 10):
        target_movie = op(f"movie_clip_{i}")
        if target_movie:
            target_movie.par.file = ""

    # 5번 열부터 가로로 쭉 읽으며 경로 파싱
    for col_idx in range(5, dat.numCols):
        cell_val = dat[latest_row, col_idx].val
        if not cell_val:
            continue
            
        clean_path = cell_val.strip().strip('"').strip("'")
        if not clean_path:
            continue
            
        # 파일 경로 이름에서 cam_1, cam_2 등 가메라 번호 자동 추출
        cam_match = re.search(r'cam_(\d+)', clean_path, re.IGNORECASE)
        if cam_match:
            cam_num = int(cam_match.group(1))
            
            # 해당 번호에 딱 맞는 movie_clip_1~9 노드에 강제 주입
            if 1 <= cam_num <= 9:
                target_movie = op(f"movie_clip_{cam_num}")
                if target_movie:
                    target_movie.par.file = clean_path
                    target_movie.par.reloadpulse.pulse() # 영상 강제 새로고침
                    
    return