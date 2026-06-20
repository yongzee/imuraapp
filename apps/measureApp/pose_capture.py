import cv2
import mediapipe as mp
import math
import os

# Utility functions
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

def process_camera(front_img_path, side_img_path, height_cm, save_annotated=True):
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose(static_image_mode=True, model_complexity=2)

    front_img = cv2.imread(front_img_path)
    side_img = cv2.imread(side_img_path)

    front_height, front_width = front_img.shape[:2]
    side_height, side_width = side_img.shape[:2]

    front_result = pose.process(cv2.cvtColor(front_img, cv2.COLOR_BGR2RGB))
    side_result = pose.process(cv2.cvtColor(side_img, cv2.COLOR_BGR2RGB))

    if not front_result.pose_landmarks or not side_result.pose_landmarks:
        print("Could not detect pose landmarks.")
        return {}

    if save_annotated:
        annotated_front = front_img.copy()
        annotated_side = side_img.copy()

        mp_drawing.draw_landmarks(annotated_front, front_result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        mp_drawing.draw_landmarks(annotated_side, side_result.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        front_out_path = os.path.splitext(front_img_path)[0] + "_landmarks.jpg"
        side_out_path = os.path.splitext(side_img_path)[0] + "_landmarks.jpg"

        cv2.imwrite(front_out_path, annotated_front)
        cv2.imwrite(side_out_path, annotated_side)
    else:
        front_out_path = ""
        side_out_path = ""

    lm_f = front_result.pose_landmarks.landmark
    lm_s = side_result.pose_landmarks.landmark

    pixel_height = pixel_distance(lm_f[mp_pose.PoseLandmark.NOSE], lm_f[mp_pose.PoseLandmark.LEFT_ANKLE], front_width, front_height)
    pixels_per_cm_front = pixel_height / height_cm if height_cm > 0 else 1

    shoulder_px = pixel_distance(lm_f[mp_pose.PoseLandmark.LEFT_SHOULDER], lm_f[mp_pose.PoseLandmark.RIGHT_SHOULDER], front_width, front_height)
    chest_px = shoulder_px
    waist_px = pixel_distance(lm_f[mp_pose.PoseLandmark.LEFT_HIP], lm_f[mp_pose.PoseLandmark.RIGHT_HIP], front_width, front_height)
    hip_px = waist_px

    arm_circ_px = shoulder_px * 0.25

    height_cm_final = height_cm
    shoulder_width = cm_inch(shoulder_px, pixels_per_cm_front)
    chest_width = cm_inch(chest_px, pixels_per_cm_front)
    waist_width = cm_inch(waist_px, pixels_per_cm_front)
    hip_width = cm_inch(hip_px, pixels_per_cm_front)
    arm_circ = cm_inch(arm_circ_px, pixels_per_cm_front)

    body_height_side_px = abs((lm_s[mp_pose.PoseLandmark.LEFT_ANKLE].y - lm_s[mp_pose.PoseLandmark.NOSE].y) * side_height)
    pixels_per_cm_side = body_height_side_px / height_cm if height_cm > 0 else 1

    arm_px = pixel_distance(lm_s[mp_pose.PoseLandmark.LEFT_SHOULDER], lm_s[mp_pose.PoseLandmark.LEFT_ELBOW], side_width, side_height) + \
              pixel_distance(lm_s[mp_pose.PoseLandmark.LEFT_ELBOW], lm_s[mp_pose.PoseLandmark.LEFT_WRIST], side_width, side_height)

    inseam_px = pixel_distance(lm_s[mp_pose.PoseLandmark.LEFT_HIP], lm_s[mp_pose.PoseLandmark.LEFT_ANKLE], side_width, side_height)
    thigh_px = pixel_distance(lm_s[mp_pose.PoseLandmark.LEFT_HIP], lm_s[mp_pose.PoseLandmark.LEFT_KNEE], side_width, side_height)

    hip_depth_px = abs(lm_s[mp_pose.PoseLandmark.LEFT_SHOULDER].x - lm_s[mp_pose.PoseLandmark.LEFT_HIP].x) * side_width
    hip_depth_cm = hip_depth_px / pixels_per_cm_side
    hip_width_cm = hip_px / pixels_per_cm_front
    a = hip_width_cm / 2
    b = hip_depth_cm / 2
    hip_circum_cm = ellipse_circumference(a, b)

    measurements = {
        "Height": (height_cm_final, convert_cm_to_in(height_cm_final)),
        "Shoulder Width": shoulder_width,
        "Chest Width": chest_width,
        "Waist Width": waist_width,
        "Hip Width": hip_width,
        "Arm Circumference": arm_circ,
        "Arm Length": cm_inch(arm_px, pixels_per_cm_side),
        "Inseam": cm_inch(inseam_px, pixels_per_cm_side),
        "Thigh Length": cm_inch(thigh_px, pixels_per_cm_side),
        "Hip Circumference": (hip_circum_cm, convert_cm_to_in(hip_circum_cm)),
        "annotated_front": front_out_path,
        "annotated_side": side_out_path,
    }

    return measurements
