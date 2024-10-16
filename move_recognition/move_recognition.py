import cv2
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import pygame

KEYPOINT_THRESHOLD = 0.5

# 音声再生の初期化
def make_sound():
    pygame.mixer.init()
    sound = pygame.mixer.Sound('materials/se_sab01.wav')  # 'cute_sound.wav' を可愛い音のファイルに置き換えてください
    sound.play()

def play_sound(keypoints_list, scores_list, frame):
    # 0:nose, 1:left eye, 2:right eye, 3:left ear, 4:right ear, 5:left shoulder, 6:right shoulder, 7:left elbow, 8:right elbow, 9:left wrist, 10:right wrist,
    # 11:left hip, 12:right hip, 13:left knee, 14:right knee, 15:left ankle, 16:right ankle


    right_shoulder_position = keypoints_list[0][6] # 0番目の人物の鼻の位置（0番目のキーポイント）
    right_elbow_position = keypoints_list[0][8]  # 0番目の人物の右肘の位置（8番目のキーポイント）

    right_shoulder_score = scores_list[0][6]  # 0番目の人物の右肩のスコア（6番目のスコア）
    right_elbow_score = scores_list[0][8]  # 0番目の人物の右肘のスコア（8番目のスコア）

    # 右肩より右に右肘があるかどうかを判定    
    if right_shoulder_position[1] > right_elbow_position[1] :
        if right_shoulder_score > KEYPOINT_THRESHOLD and right_elbow_score > KEYPOINT_THRESHOLD:
            make_sound()  # 可愛い音を鳴らす


def main():
    # Tensorflow Hubを利用してモデルダウンロード
    model = hub.load('https://www.kaggle.com/models/google/movenet/TensorFlow2/multipose-lightning/1')
    movenet = model.signatures['serving_default']
    
    # カメラ設定
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    while(True):
        ret, frame = cap.read()
        if not ret:
            break

        # 推論実行
        keypoints_list, scores_list, bbox_list = run_inference(movenet, frame)

        if keypoints_list:
            #nose_position = keypoints_list[0][0]  # 0番目の人物の鼻の位置（0番目のキーポイント）
            play_sound(keypoints_list, scores_list, frame)  # 音声再生

        # 画像レンダリング
        result_image = render(frame, keypoints_list, scores_list, bbox_list)

        cv2.namedWindow("image", cv2.WINDOW_FULLSCREEN)
        cv2.imshow('image', result_image)
        key = cv2.waitKey(1) & 0xFF
        # Q押下で終了
        if key == ord('q'):
            break
    
    cap.release()

def run_inference(model, image):
    # 画像の前処理
    input_image = cv2.resize(image, dsize=(256, 256))
    input_image = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
    input_image = np.expand_dims(input_image, 0)
    input_image = tf.cast(input_image, dtype=tf.int32)

    # 推論実行・結果取得
    outputs = model(input_image)
    keypoints = np.squeeze(outputs['output_0'].numpy())

    image_height, image_width = image.shape[:2]
    keypoints_list, scores_list, bbox_list = [], [], []

    # 検出した人物ごとにキーポイントのフォーマット処理
    for kp in keypoints:
        keypoints = []
        scores = []
        for index in range(17):
            kp_x = int(image_width * kp[index*3+1])
            kp_y = int(image_height * kp[index*3+0])
            score = kp[index*3+2]
            keypoints.append([kp_x, kp_y])
            scores.append(score)
        bbox_ymin = int(image_height * kp[51])
        bbox_xmin = int(image_width * kp[52])
        bbox_ymax = int(image_height * kp[53])
        bbox_xmax = int(image_width * kp[54])
        bbox_score = kp[55]

        keypoints_list.append(keypoints)
        scores_list.append(scores)
        bbox_list.append([bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax, bbox_score])

    return keypoints_list, scores_list, bbox_list

def render(image, keypoints_list, scores_list, bbox_list):
    render = image.copy()
    for i, (keypoints, scores, bbox) in enumerate(zip(keypoints_list, scores_list, bbox_list)):
        if bbox[4] < 0.2:
            continue

        cv2.rectangle(render, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0,255,0), 2)

        # 0:nose, 1:left eye, 2:right eye, 3:left ear, 4:right ear, 5:left shoulder, 6:right shoulder, 7:left elbow, 8:right elbow, 9:left wrist, 10:right wrist,
        # 11:left hip, 12:right hip, 13:left knee, 14:right knee, 15:left ankle, 16:right ankle
        # 接続するキーポイントの組
        kp_links = [
            (0,1),(0,2),(1,3),(2,4),(0,5),(0,6),(5,6),(5,7),(7,9),(6,8),
            (8,10),(11,12),(5,11),(11,13),(13,15),(6,12),(12,14),(14,16)
        ]
        for kp_idx_1, kp_idx_2 in kp_links:
            kp_1 = keypoints[kp_idx_1]
            kp_2 = keypoints[kp_idx_2]
            score_1 = scores[kp_idx_1]
            score_2 = scores[kp_idx_2]
            if score_1 > KEYPOINT_THRESHOLD and score_2 > KEYPOINT_THRESHOLD:
                cv2.line(render, tuple(kp_1), tuple(kp_2), (0,0,255), 2)

        for idx, (keypoint, score) in enumerate(zip(keypoints, scores)):
            if score > KEYPOINT_THRESHOLD:
                cv2.circle(render, tuple(keypoint), 4, (0,0,255), -1)

    return render

def check_and_play_sound(nose_position, frame):
    frame_height, frame_width = frame.shape[:2]
    
    # 右上のエリアを定義（画面の右上1/4を基準にします）
    right_upper_area_x = frame_width // 2  # 画面の横半分より右
    right_upper_area_y = frame_height // 2  # 画面の縦半分より上
    
    # 鼻の位置（nose_position）が右上にあるかどうかを判定
    if nose_position[0] > right_upper_area_x and nose_position[1] < right_upper_area_y:
        make_sound()  # 可愛い音を鳴らす

if __name__ == '__main__':
    main()
