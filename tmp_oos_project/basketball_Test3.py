import numpy as np
import cv2 as cv
import Ball
import time, pymysql, os
try:
    log = open('log.txt',"w")
except:
    print( "Could not open log file.")
#cap = cv.VideoCapture(0) # 웹캠일 경우
cap = cv.VideoCapture('tmp_oos_project/Test/Basketball5.mp4') # 144, 180, 108, 216
#cap = cv.VideoCapture('Test/hyunho1.mp4') # 252, 293
cap.set(3,1280) # Width
cap.set(4,720) # Height
cap.set(5,30) # FPS

# cap 속성 정보 출력
for i in range(19):
    print( i, cap.get(i))

H, W = 720, 1280
X1, X2, Y1, Y2 = 600, 680, 0, 300
line_up = int(8*H/23) # 252 270
print(line_up)
line_down = int(8*H/18) # 265 307a
print(line_down)
up_limit = int(6*H/20) # 252-(265-252)
print(up_limit)
down_limit = int(8*H/19) # 293+(293-252)
print(down_limit)

line_down_color = (255,0,0) # 빨강
line_up_color = (0,0,255) # 파랑
pts_L1, pts_L2, pts_L3, pts_L4 = None, None, None, None

def calc_linepos(y, yh, x=620, xw=690) :
    global line_up, line_down, up_limit, down_limit
    global pts_L1, pts_L2, pts_L3, pts_L4, W, X1, X2, Y1, Y2, areaTH
    X1 = x - (xw-x); X2 = x + (xw-x); Y2 = yh + (yh-y)
    print('area', (yh-y) * (xw-x), ', X1', X1, ', X2', X2, ' Y2', Y2)
    # Entry / exit lines
    print( "Red line y:", str(y))
    print( "Blue line y:", str(yh))
    line_down = yh; line_up = y
    pt1 = [0, line_down];
    pt2 = [W, line_down];
    pts_L1 = np.array([pt1,pt2], np.int32)
    pts_L1 = pts_L1.reshape((-1,1,2))
    pt3 = [0, line_up];
    pt4 = [W, line_up];
    pts_L2 = np.array([pt3,pt4], np.int32)
    pts_L2 = pts_L2.reshape((-1,1,2))
    up_limit = y - (yh-y); down_limit = yh + (yh-y)
    pt5 = [0, up_limit];
    pt6 = [W, up_limit];
    pts_L3 = np.array([pt5,pt6], np.int32)
    pts_L3 = pts_L3.reshape((-1,1,2))
    pt7 = [0, down_limit];
    pt8 = [W, down_limit];
    pts_L4 = np.array([pt7,pt8], np.int32)
    pts_L4 = pts_L4.reshape((-1,1,2))

calc_linepos(line_up, line_down)

# 배경제거
fgbg = cv.createBackgroundSubtractorMOG2(detectShadows = True)
# Structuring elements for morphogic filters
kernelOp = np.ones((5,5),np.uint8) ### (3,3)
kernelOp2 = np.ones((5,5),np.uint8)
kernelCl = np.ones((13,13),np.uint8) ### (18,18)
# Variables
col, width, row, height = -1,-1,-1,-1
frame, frame2 = None, None
inputmode, rectangle, trackWindow, roi_hist = False, False, None, None
font = cv.FONT_HERSHEY_SIMPLEX
balls = []
max_b_age = 5
pid = 1
cur, conn = None, None
cnt_up, cnt_down = 0, 0
user = 'lee'

def onMouse(event,x,y,flags,param):
    global frame, frame2, col, width, row, height 
    global inputmode, rectangle, roi_hist, trackWindow 
    #global line_up, line_down, up_limit, down_limit
    if inputmode:
    # 좌 클릭시
        if event == cv.EVENT_LBUTTONDOWN: rectangle = True
        col, row = x,y
    # 좌 클릭하는 도중 움직일 때
    elif event == cv.EVENT_MOUSEMOVE:
        if rectangle:
            frame = frame2.copy() 
            cv.rectangle(frame,(col,row),(x,y),(0,255,0),2) 
            cv.imshow('frame', frame)
    # 좌 클릭 뗐을때
    elif event == cv.EVENT_LBUTTONUP:
        inputmode = False
        rectangle = False 
        cv.rectangle(frame,(col,row),(x,y),(0,255,0),2) 
        height, width = abs(row-y), abs(col-x) 
        trackWindow = (col,row,width,height)
        roi = frame[row:row+height,col:col+width] 
        line_up = row; line_down = row+height

        calc_linepos(row, row+height, col, col+height)
        # HSV 색공간으로 변환
        # roi = cv.cvtColor(roi,cv.COLOR_BGR2HSV)
        # HSV 색공간으로 변경한 히스토그램 계산
        # roi_hist = cv.calcHist([roi],[0],None,[180],[0,180])
        # 계산된 히스토그램 노말라이즈
        cv.normalize(roi_hist,roi_hist,0,255,cv.NORM_MINMAX)
    return
# dic={'02이태현':'Taehyun', '51윤현호':'hyeonho', '59이수정':'suejeong'}
fourcc = cv.VideoWriter_fourcc(*'DIVX') # 코덱 정의
out = cv.VideoWriter(user + '_out.avi', fourcc, 24, (int(1280),int(720))) # VideoWriter 객체 정의

while(cap.isOpened()):
    # Read an image from the video source
    ret, frame = cap.read()

    ## 201101 추가
    cv.namedWindow('frame')
    cv.setMouseCallback('frame',onMouse,param=(frame,frame2))

    for i in balls:
        i.age_one() # age every ball one frame

    # 전처리 
    # Apply background subtraction
    # http://blog.daum.net/geoscience/1316 OpenCV-Python으로 영상 배경 제거
    fgmask = fgbg.apply(frame)

    # Binary to remove shadows (color gris)
    try:
        ## 이미지 임계값 처리 https://bit.ly/3lwIotM
        ret,imBin = cv.threshold(fgmask,200,255,cv.THRESH_BINARY) # 모폴로지 연산(경계값 처리) Opening
        mask = cv.morphologyEx(imBin, cv.MORPH_OPEN, kernelOp) # Closing
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernelCl) 
    except:
        print('EOF')
        print( 'UP:',cnt_up)
        print ('DOWN:',cnt_down) 
        break

    # CONTORNOS
    # RETR_EXTERNAL returns only extreme outer flags. All child contours are left behind. 
    contours0, hierarchy = cv.findContours(mask,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE) 
    for cnt in contours0:
        area = cv.contourArea(cnt) 
        if area > 200:
            # TRACKING
            # It remains to add conditions for multi-ball, screen outputs and inputs. # 무게중심 구하기 https://bit.ly/3nuhB37
            M = cv.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            x,y,w,h = cv.boundingRect(cnt)

            new = True
            if cy in range(up_limit,down_limit):
                print(cy,"디버깅중 1")
                for i in balls:
                    print(i,"디버깅중")
                    if abs(x-i.getX()) <= w and abs(y-i.getY()) <= h:
                        # The object is already near what was detected before. new = False
                        i.updateCoords(cx,cy)
                        if False and i.going_UP(line_down,line_up) == True :
                            pass
                        elif i.going_DOWN(line_down,line_up) == True and (cx > X1 and cx < X2) :
                            cnt_down += 1;
                            print("드버그중")
                            print("ID: %2d"%(i.getId()),'crossed going down at',time.strftime("%c")," area %4d"%(area), ' cx ', str(cx), ' cy ', str(cy)) 
                            log.write("ID: " + str(i.getId()) + ' crossed going down at ' + time.strftime("%c") + ' area ' + str(area) + '\n')                            
                        break

                    if i.getState() == '1':
                        if i.getDir() == 'down' and i.getY() > down_limit:
                            i.setDone()
                        elif i.getDir() == 'up' and i.getY() < up_limit:
                            i.setDone() 
                    if i.timedOut():
                        # balls 리스트에서 꺼냄 
                        index = balls.index(i)
                        balls.pop(index)
                        del i # 메모리 해제
                if new == True and (cx > 550 and cx < 750 and cy < 320) :
                    p = Ball.MyBall(pid,cx,cy,max_b_age)
                    balls.append(p)
                    pid += 1

            if cx > X1 and cx < X2 and cy < Y2 :
                cv.circle(frame,(cx,cy), 5, (0,0,255), -1)
                img = cv.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                cv.drawContours(frame, cnt, -1, (0,255,0), 3)
        
    # END for cnt in contours0
    # DRAWING TRAJECTORS 
    
    for i in balls:
        ''' if
        # if
        # 궤적 추가 코드/ 주석처리 len(i.getTracks()) >= 2:
        # pts = np.array(i.getTracks(), np.int32)
        # pts = pts.reshape((-1,1,2))
        # frame = cv.polylines(frame,[pts],False,i.getRGB())
        # i.getId() == 9:
        # print(str(i.getX()), ',', str(i.getY()))
        # '''
        cv.putText(frame, str(i.getId()),(i.getX(),i.getY()),font,0.3, i.getRGB(),1,cv.LINE_AA)

    # IMAGANES
    str_down = 'SCORE: '+ str(cnt_down)
    str_player = 'PLAYER: '+ user
    frame = cv.polylines(frame,[pts_L1],False,line_down_color,thickness=2) 
    frame = cv.polylines(frame,[pts_L2],False,line_up_color,thickness=2) 
    frame = cv.polylines(frame,[pts_L3],False,(255,255,255),thickness=1) 
    frame = cv.polylines(frame,[pts_L4],False,(255,255,255),thickness=1)


    cv.putText(frame, str_down ,(480,40),font,1,(255,255,255),6,cv.LINE_AA) 
    cv.putText(frame, str_down ,(480,40),font,1,(255,0,0),2,cv.LINE_AA)
    cv.putText(frame, str_player ,(680,40),font,1,(255,255,255),6,cv.LINE_AA) 
    cv.putText(frame, str_player ,(680,40),font,1,(255,0,0),2,cv.LINE_AA)

    out.write(frame) 
    cv.imshow('frame',frame) 
    # cv.imshow('Mask',mask)

    #ESC눌러종료
    k = cv.waitKey(30) & 0xff 
    if k==27:
        break
    # i를 눌러서 영상을 멈춰서 roi 설정 
    if k == ord('i'):
        print("농구링 영역을 선택하고 아무키나 누르세요.") 
        inputmode = True
        frame2 = frame.copy()

    while inputmode: 
        cv.imshow('frame',frame) 
        cv.waitKey(0) 
        print(trackWindow)

    if k == ord('s'): ### start
        user=input("학번 뒤 두 자리와 이름을 입력하세요. 예)99홍길동 : ") 
        cnt_down=0

    # END while(cap.isOpened())

# CLEANING 
log.flush()
log.close() 
cap.release() 
out.release() 
cv.destroyAllWindows()
