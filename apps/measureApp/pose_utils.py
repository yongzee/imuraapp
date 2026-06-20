import math
import cv2
import mediapipe as mp
import numpy as np


# === Utility Functions ===
def load_image_safely(image_input):
    """Safely loads an image whether it's a file path string or a Django upload stream."""
    if isinstance(image_input, str):
        # If it's a file path string
        image = cv2.imread(image_input)
    else:
        # If it's an uploaded file stream (InMemoryUploadedFile, TemporaryUploadedFile)
        try:
            image_input.seek(0)  # Reset stream pointer to the beginning
            file_bytes = np.frombuffer(image_input.read(), np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        except Exception as e:
            raise ValueError(f"Failed to read file stream: {e}")

    if image is None:
        raise ValueError(
            f"Could not load image from input: {type(image_input)}. Check if file is corrupt or path is invalid."
        )

    return image


def pixel_distance(p1, p2, width, height):
    x1, y1 = int(p1.x * width), int(p1.y * height)
    x2, y2 = int(p2.x * width), int(p2.y * height)
    return math.hypot(x2 - x1, y2 - y1)


def convert_cm_to_in(cm):
    return cm * 0.3937


def cm_inch(distance_px, pixels_per_cm):
    cm = distance_px / pixels_per_cm if pixels_per_cm > 0 else 0
    return cm, convert_cm_to_in(cm)


def ellipse_circumference(a, b):
    return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))


def process_pose_images(front_image_input, side_image_input, user_height_cm):
    mp_pose = mp.solutions.pose

    # === FRONT VIEW PROCESSING ===
    # Use the safe helper instead of cv2.imread
    front_image = load_image_safely(front_image_input)
    front_height, front_width = front_image.shape[:2]

    front_pose = mp_pose.Pose(
        static_image_mode=True, model_complexity=2, min_detection_confidence=0.7
    )
    front_rgb = cv2.cvtColor(front_image, cv2.COLOR_BGR2RGB)
    front_results = front_pose.process(front_rgb)

    front_measurements = {}
    pixels_per_cm_front = 1

    if front_results.pose_landmarks:
        lm = front_results.pose_landmarks.landmark
        nose = lm[mp_pose.PoseLandmark.NOSE]
        l_shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
        r_shoulder = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        l_hip = lm[mp_pose.PoseLandmark.LEFT_HIP]
        r_hip = lm[mp_pose.PoseLandmark.RIGHT_HIP]
        l_ankle = lm[mp_pose.PoseLandmark.LEFT_ANKLE]

        body_height_px = abs((l_ankle.y - nose.y) * front_height)
        pixels_per_cm_front = (
            body_height_px / user_height_cm if body_height_px > 0 else 1
        )

        shoulder_px = pixel_distance(
            l_shoulder, r_shoulder, front_width, front_height
        )
        chest_px = shoulder_px
        waist_px = pixel_distance(l_hip, r_hip, front_width, front_height)
        hip_px = waist_px

        front_measurements = {
            "Height": (user_height_cm, convert_cm_to_in(user_height_cm)),
            "Shoulder Width": cm_inch(shoulder_px, pixels_per_cm_front),
            "Chest Width": cm_inch(chest_px, pixels_per_cm_front),
            "Waist Width": cm_inch(waist_px, pixels_per_cm_front),
            "Hip Width": cm_inch(hip_px, pixels_per_cm_front),
            "Arm Circumference": cm_inch(
                shoulder_px * 0.25, pixels_per_cm_front
            ),
        }

    # === SIDE VIEW PROCESSING ===
    # Use the safe helper instead of cv2.imread
    side_image = load_image_safely(side_image_input)
    side_height, side_width = side_image.shape[:2]

    side_pose = mp_pose.Pose(
        static_image_mode=True, model_complexity=2, min_detection_confidence=0.7
    )
    side_rgb = cv2.cvtColor(side_image, cv2.COLOR_BGR2RGB)
    side_results = side_pose.process(side_rgb)

    side_measurements = {}

    if side_results.pose_landmarks:
        lm = side_results.pose_landmarks.landmark
        shoulder = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
        hip = lm[mp_pose.PoseLandmark.LEFT_HIP]
        knee = lm[mp_pose.PoseLandmark.LEFT_KNEE]
        ankle = lm[mp_pose.PoseLandmark.LEFT_ANKLE]
        elbow = lm[mp_pose.PoseLandmark.LEFT_ELBOW]
        wrist = lm[mp_pose.PoseLandmark.LEFT_WRIST]
        nose = lm[mp_pose.PoseLandmark.NOSE]

        body_height_px = abs((ankle.y - nose.y) * side_height)
        pixels_per_cm_side = (
            body_height_px / user_height_cm if body_height_px > 0 else 1
        )

        arm_px = pixel_distance(
            shoulder, elbow, side_width, side_height
        ) + pixel_distance(elbow, wrist, side_width, side_height)
        inseam_px = pixel_distance(hip, ankle, side_width, side_height)
        thigh_px = pixel_distance(hip, knee, side_width, side_height)
        hip_depth_px = abs(shoulder.x - hip.x) * side_width

        side_measurements = {
            "Arm Length": cm_inch(arm_px, pixels_per_cm_side),
            "Inseam": cm_inch(inseam_px, pixels_per_cm_side),
            "Thigh Length": cm_inch(thigh_px, pixels_per_cm_side),
        }

        if front_results.pose_landmarks:
            l_hip_f = front_results.pose_landmarks.landmark[
                mp_pose.PoseLandmark.LEFT_HIP
            ]
            r_hip_f = front_results.pose_landmarks.landmark[
                mp_pose.PoseLandmark.RIGHT_HIP
            ]
            hip_px_f = pixel_distance(
                l_hip_f, r_hip_f, front_width, front_height
            )
            hip_width_cm = (
                hip_px_f / pixels_per_cm_front if pixels_per_cm_front > 0 else 0
            )
            hip_depth_cm = (
                hip_depth_px / pixels_per_cm_side if pixels_per_cm_side > 0 else 0
            )
            a = hip_width_cm / 2
            b = hip_depth_cm / 2
            hip_circum_cm = ellipse_circumference(a, b)
            side_measurements["Hip Circumference"] = (
                hip_circum_cm,
                convert_cm_to_in(hip_circum_cm),
            )

    combined_measurements = {**front_measurements, **side_measurements}
    return combined_measurements