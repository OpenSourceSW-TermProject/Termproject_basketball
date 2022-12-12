## OpenCV에서 동영상 파일의 재생, 흑백처리 및 저장
import numpy as np
import cv2 as cv
import os

# VideoCapture 객체 정의
cap = cv.VideoCapture('tmp_oos_project/Test/basketball.mp4')

# 프레임 너비/높이, 초당 프레임 수 확인
width = cap.get(cv.CAP_PROP_FRAME_WIDTH) # 또는 cap.get(3)
height = cap.get(cv.CAP_PROP_FRAME_HEIGHT) # 또는 cap.get(4)
fps = cap.get(cv.CAP_PROP_FPS) # 또는 cap.get(5)
print('너비: %d, 높이: %d, 초당 프레임 수: %d' %(width, height, fps))

fourcc = cv.VideoWriter_fourcc(*'DIVX') # 코덱 정의
out = cv.VideoWriter('basketball_out.avi', fourcc, fps, (int(width),
int(height))) # VideoWriter 객체 정의
# cap 정상동작 확인
while cap.isOpened():
    ret, frame = cap.read()
    # 프레임이 올바르게 읽히면 ret은 True
    if not ret:
        print("프레임을 수신할 수 없어 종료합니다.")
        break
    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    out.write(frame)
    cv.imshow('basketball_gray', frame)
    if cv.waitKey(30) == ord('q'):
        break
# 작업 완료 후 해제
cap.release()
out.release()
cv.destroyAllWindows()