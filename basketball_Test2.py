import sys
import cv2 as cv

print(cv.__version__)
cap = cv.VideoCapture('tmp_oos_project/Test/basketball.mp4')

w, h, fps = int(cap.get(3)), int(cap.get(4)), int(cap.get(5))
fourcc = cv.VideoWriter_fourcc(*'DIVX')
out1 = cv.VideoWriter('basketball-mog2.avi', fourcc, fps, (w, h), 0)
out2 = cv.VideoWriter('basketball-mor.avi', fourcc, fps, (w, h), 0)

# BackgroundSubtractorMOG2
fgbg = cv.createBackgroundSubtractorMOG2()
kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE,(10,10))

while(cap.isOpened()):
 # ret: frame capture 결과(boolean)
 # frame: capture한 frame
    ret, frame = cap.read()
    if (ret):
        fgmask1 = fgbg.apply(frame)
        fgmask2 = cv.morphologyEx(fgmask1, cv.MORPH_OPEN, kernel)
        cv.imshow('mog2', fgmask1)
        cv.imshow('mor', fgmask2)
        out1.write(fgmask1)
        out2.write(fgmask2)
        k = cv.waitKey(30) & 0xFF
        if k == ord('q'):
            break
    else:
        break
cap.release()
out1.release()
out2.release()
cv.destroyAllWindows()