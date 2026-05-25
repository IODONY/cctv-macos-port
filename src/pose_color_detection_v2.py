import csv
import os
import sys
import time
from pathlib import Path

import cv2

from walnut_core import WalnutAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_project_path(path_value):
    path = Path(path_value).expanduser()
    resolved = path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    if not str(resolved).startswith(str(PROJECT_ROOT)):
        raise ValueError(f"Path must stay inside project root: {resolved}")
    return str(resolved)


def ensure_log_file(log_path):
    if os.path.exists(log_path):
        return

    with open(log_path, "w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "timestamp",
                "visitor_id",
                "top",
                "bottom",
                "bag",
                "is_long_sleeve",
                "is_long_pants",
                "shoulder-to-hip",
                "brightness_ratio",
            ]
        )


def format_shoulder_to_hip(torso_ratio):
    if torso_ratio in (None, 0):
        return ""
    return f"1:{round(1.0 / torso_ratio, 3)}"


def append_log_rows(log_path, people):
    rows = []
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    for person in people:
        log_record = person.get("log_record")
        if not log_record:
            continue

        profile = log_record["profile"]
        rows.append(
            [
                timestamp,
                log_record["visitor_id"],
                profile["top"],
                profile["bottom"],
                profile["bag"],
                profile["is_long_sleeve"],
                profile["is_long_pants"],
                format_shoulder_to_hip(profile["torso_ratio"]),
                profile["brightness_ratio"],
            ]
        )

    if not rows:
        return

    with open(log_path, "a", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(rows)

    for row in rows:
        print(f"Saved visitor {row[1]} to {log_path}")


def configure_capture(camera_id, frame_width, frame_height):
    if sys.platform == "darwin":
        backend = cv2.CAP_AVFOUNDATION
    elif sys.platform == "win32":
        backend = cv2.CAP_DSHOW
    elif sys.platform.startswith("linux"):
        backend = cv2.CAP_V4L2
    else:
        backend = 0

    cap = cv2.VideoCapture(camera_id, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_id)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def draw_torso_lines(frame, person):
    shoulder_line = person["torso_lines"].get("shoulders")
    hip_line = person["torso_lines"].get("hips")

    if shoulder_line is not None:
        cv2.line(frame, shoulder_line[0], shoulder_line[1], (255, 120, 0), 2)
        cv2.circle(frame, shoulder_line[0], 4, (255, 120, 0), -1)
        cv2.circle(frame, shoulder_line[1], 4, (255, 120, 0), -1)

    if hip_line is not None:
        cv2.line(frame, hip_line[0], hip_line[1], (180, 0, 255), 2)
        cv2.circle(frame, hip_line[0], 4, (180, 0, 255), -1)
        cv2.circle(frame, hip_line[1], 4, (180, 0, 255), -1)


def draw_region_markers(frame, person):
    for region_name in WalnutAnalyzer.REGION_NAMES:
        region = person["regions"].get(region_name)
        if region is None:
            continue

        x, y = region["pos"]
        cv2.circle(frame, (x, y), 5, region["bgr"], -1)
        cv2.circle(frame, (x, y), 6, (255, 255, 255), 1)


def draw_limb_samples(frame, person):
    for sample in person["limb_samples"]:
        start = sample["start"]
        end = sample["end"]
        mid = sample["mid"]
        sample_bgr = sample["bgr"] if sample["bgr"] is not None else (255, 255, 255)
        line_color = (0, 220, 255) if sample["is_skin"] else (0, 255, 80)

        cv2.line(frame, start, end, line_color, 2)
        cv2.circle(frame, start, 3, line_color, -1)
        cv2.circle(frame, end, 3, line_color, -1)
        cv2.circle(frame, mid, 7, sample_bgr, -1)
        cv2.circle(frame, mid, 8, (255, 255, 255), 1)


def draw_bags(frame, bags):
    for bag in bags:
        x1, y1, x2, y2 = bag["box"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 180, 255), 2)


def draw_people(frame, people):
    for person in people:
        x1, y1, x2, y2 = person["box"]
        cv2.rectangle(frame, (x1, y1), (x2, y2), (60, 220, 60), 2)
        cv2.putText(
            frame,
            f"people {person['id']}",
            (x1, max(18, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (60, 220, 60),
            2,
            cv2.LINE_AA,
        )

        draw_torso_lines(frame, person)
        draw_region_markers(frame, person)
        draw_limb_samples(frame, person)
        draw_bags(frame, person["bags"])

    return frame


def format_person_summary(person, vote_frame_window):
    parts = [f"people {person['id']}"]
    if person["final_profile"] is not None:
        for region_name in WalnutAnalyzer.REGION_NAMES:
            parts.append(f"{region_name}: {person['final_profile'][region_name]}")
        parts.append(f"bag: {person['final_profile']['bag']}")
        parts.append(f"is_long_sleeve: {person['final_profile']['is_long_sleeve']}")
        parts.append(f"is_long_pants: {person['final_profile']['is_long_pants']}")
        parts.append(f"torso_ratio: {person['final_profile']['torso_ratio']}")
        parts.append(f"brightness_ratio: {person['final_profile']['brightness_ratio']}")
        if person["skip_reason"] is not None:
            parts.append(f"status: skipped ({person['skip_reason']})")
        else:
            parts.append("status: finalized")
    else:
        for region_name in WalnutAnalyzer.REGION_NAMES:
            region = person["regions"].get(region_name)
            if region is not None:
                parts.append(f"{region_name}: {region['color_name']}")
        parts.append(f"bag: {'yes' if person['bags'] else 'no'}")
        parts.append(f"is_long_sleeve: {person['is_long_sleeve']}")
        parts.append(f"is_long_pants: {person['is_long_pants']}")
        parts.append(f"torso_ratio: {person['torso_ratio']}")
        parts.append(f"brightness_ratio: {person.get('brightness_ratio')}")
        if person["skip_reason"] == "waiting_for_complete_profile":
            parts.append(
                f"status: collecting {person['observed_frames']}/{vote_frame_window} "
                "(waiting for complete profile)"
            )
        else:
            parts.append(f"status: collecting {person['observed_frames']}/{vote_frame_window}")
    return " | ".join(parts)


def print_results(people, analyzer):
    print(
        f"\nPeople: {len(people)} | Device: {analyzer.device} | "
        f"Inference: {analyzer.last_inference_ms:.1f} ms"
    )
    if not people:
        print("No person detected.")
        return

    for person in people:
        print(format_person_summary(person, analyzer.vote_frame_window))


def run_webcam_csv_case(
    camera_id=0,
    log_path="data/visitor_log.csv",
    frame_width=640,
    frame_height=360,
    inference_interval=2,
    print_interval_frames=30,
):
    analyzer = WalnutAnalyzer(
        pose_model_name="yolov8n-pose.pt",
        detect_model_name="yolov8n.pt",
        person_confidence=0.45,
        pose_confidence=0.35,
        accessory_confidence=0.18,
        model_imgsz=640,
        vote_frame_window=75,
        track_max_missing=15,
    )
    log_path = resolve_project_path(log_path)
    ensure_log_file(log_path)

    cap = configure_capture(camera_id, frame_width, frame_height)
    if not cap.isOpened():
        print("Camera is unavailable.")
        return

    frame_index = 0
    last_results = []

    print("\nStarting red-walnut webcam test case.")
    print("The pure analysis engine lives in walnut_core.py.")
    print("This script only handles webcam input, CSV output, terminal logs, and visualization.")
    print("Press q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read a frame from the camera.")
            break

        frame_index += 1

        if frame_index % inference_interval == 0:
            last_results = analyzer.analyze_frame(frame)
            append_log_rows(log_path, last_results)

            if frame_index % print_interval_frames == 0:
                print_results(last_results, analyzer)

        display_frame = draw_people(frame.copy(), last_results)
        cv2.imshow("Red Walnut Webcam Test Case", display_frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("\nProgram terminated.")
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    run_webcam_csv_case()


if __name__ == "__main__":
    main()
