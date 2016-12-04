#!/usr/bin/env python
import sys
import rospy
import cv2
import numpy as np
from geometry_msgs.msg import Point
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from scipy.spatial import distance

class cup:
    def __init__(self):
        self.containsTreasure = False
        self.originalPoint = 0
        self.currentPoint = 0

class image_converter:
    def __init__(self):
        self.bridge = CvBridge()
        self.image_sub = rospy.Subscriber("/usb_cam/image_raw",Image,self.callback)
        self.cups = []
        self.cupCenters = [[0,0],[0,0],[0,0]]
        self.flag = False
        self.minRadius = 30
        for i in range(0,3):
            self.cups.append(cup())
            print self.cups[i].containsTreasure

    def callback(self,data):
        try:
            imgOriginal = self.bridge.imgmsg_to_cv2(data,"bgr8")
        except CvBridgeError as e:
            print("==[CAMERA MANAGER]==",e)

        blurred = cv2.GaussianBlur(imgOriginal,(11,11),0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        lower = np.array([0,100,100])
        upper = np.array([50,255,255])
        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.erode(mask, None, iterations=7)
        mask = cv2.dilate(mask, None, iterations=7)
        output = cv2.bitwise_and(imgOriginal, imgOriginal, mask = mask)
        outputGrayscale = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
        contours = cv2.findContours(outputGrayscale,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)[0]

        radius = [0,0,0]
        x = [[0,0],[0,0],[0,0]]
        y = [[0,0],[0,0],[0,0]]
        if len(contours) > 2:
            contours = sorted(contours, key = cv2.contourArea, reverse = True)[:10]
            for i in range(0,3):
                ((x[i],y[i]),radius[i]) = cv2.minEnclosingCircle(contours[i])
            # this will ensure that it is the 3 separate cups that are being identified
            # may have to change the radius threshold when testing on baxter
            if radius[0] > self.minRadius and radius[1] > self.minRadius and radius[2] > self.minRadius:
                for i in range(0,3):
                    M = cv2.moments(contours[i])
                    self.cupCenters[i] = (int(M["m10"]/M["m00"]),int(M["m01"]/M["m00"]))
                    cv2.circle(imgOriginal,(int(x[i]),int(y[i])),int(radius[i]),(0,255,0),2)
                    cv2.circle(imgOriginal,self.cupCenters[i],5,(0,0,255),-1)
                if self.flag is False:
                    for i in range(0,3):
                        self.cups[i].originalPoint = self.cupCenters[i]
                        self.cups[i].currentPoint = self.cupCenters[i]
                    self.flag = True
                else:
                    for i in range(0,3):
                        print "BEFORE"
                        print "Cup 1 Current Location:",self.cups[0].currentPoint
                        print "Cup 2 Current Location:",self.cups[1].currentPoint
                        print "Cup 3 Current Location:",self.cups[2].currentPoint
                        print "cupCenter1:",self.cupCenters[0]
                        print "cupCenter2:",self.cupCenters[1]
                        print "cupCenter3:",self.cupCenters[2]
                        self.cups[i].currentPoint = self.cupCenters[closestPoint(self.cups[i].currentPoint,self.cupCenters)]
                        print "AFTER"
                        print "Cup 1 Current Location:",self.cups[0].currentPoint
                        print "Cup 2 Current Location:",self.cups[1].currentPoint
                        print "Cup 3 Current Location:",self.cups[2].currentPoint
        else:
            self.flag = False

        flipped = cv2.flip(imgOriginal, 1)
        output = cv2.flip(output, 1)
        cv2.imshow("Image",flipped)
        cv2.imshow("MyImage",output)
        cv2.waitKey(3)

def closestPoint(currentPoint,cupCenters):
    minimumDist = distance.euclidean(currentPoint,cupCenters[0])
    mindex = 0
    for i in range(1,3):
        dist = distance.euclidean(currentPoint,cupCenters[i])
        if dist < minimumDist:
            minimumDist = dist
            mindex = i
    print "MINDEX:",mindex
    return mindex

def main(args):
    rospy.init_node('image_converter', anonymous=True)
    ic = image_converter()

    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main(sys.argv)