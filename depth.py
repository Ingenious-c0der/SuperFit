import cv2
import sys
import numpy as np
import math 


def ResizeWithAspectRatio(image, width=None, height=None, inter=cv2.INTER_AREA):
    dim = None
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))

    return cv2.resize(image, dim, interpolation=inter)

def getFOV(image):
    # In later functions we will be extracting FOV from camera directly
    FOVx = 59.8396
     
    # Returns height, width of img
    dimensions = image.shape
    height = dimensions[0]
    width = dimensions[1]

    ratio=height/width
    FOVy = 46.664955
    
    print("FOV : FOVx =",FOVx,", FOVy =",FOVy,", W Img =",width,", H Img =",height)
    print()
    return FOVx,FOVy,height,width

def contour(image):
    
    # hsv hue sat values
    lower_skin=np.array([0,30,60])
    upper_skin=np.array([20,150,255])

    # Creates a black and white img by extracting skin regions of image 
    # exclusive only to facial box
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (6,6))
    mask= cv2.inRange(image,lower_skin,upper_skin)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)


    contours,hierarchy=cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)

    largestContourArea = 0
    largestContour = 0
    for cnt in contours:
        contourArea = cv2.contourArea(cnt)
        if( contourArea > largestContourArea):
            largestContour = cnt
            largestContourArea = contourArea

    return largestContour,mask

def depth(image):
    # Gets FOV for calculation of depth
    FOVx,FOVy,height,width= getFOV(image)

    
    # gets largest contour of image and isolates facial region
    largestContour,mask=contour(image)

    
    
    # This finds the bounding rectangle
    # x,y are the co-ordinates of left-top point and w,h are width and height respectively
    x,y,w,h = cv2.boundingRect(largestContour)
    cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
    print("Inner Face Box:","x =",x,", y =",y,", w =",w,", h =",h)
    print()
    Offset = ((y+(h/2))-height/2)
    print(f"Offset Y : {Offset} pixels" )

    # Calculates distance between camera and face
    SweepX=w/width*FOVx
    SweepY=h/height*FOVy
    ThetaX=(180-SweepX)/2
    ThetaY=(180-SweepY)/2

    fh=16.2
    fw=15
    
    #fw=30*math.sin(math.radians(SweepX))/math.sin(math.radians(ThetaX))
    #fh=30*math.sin(math.radians(SweepY))/math.sin(math.radians(ThetaY))
    #print(fw,fh)


    dy=fh*math.sin(math.radians(ThetaY))/math.sin(math.radians(SweepY))
    dx=(fw/2)*(math.cos(math.radians(SweepX/2))/math.sin(math.radians(SweepX/2)))
    #dy=fh*(math.cos(math.radians(SweepY))/math.sin(math.radians(SweepY)))
    # To increase accuracy
    print(f"The X offset : {((x+(w/2))-width/2)}")
    print(f"SweepY : {SweepY}")
    print(f"SweepX : {SweepX}")
    print(f"accuracy of bounding box {abs((SweepY/SweepX)-(fh/fw))}")
    # if dy>100:
    #     distance=(height/2)-(y)
    #     f=(fh/h)*(distance)
    #     d=(dy**2 - f**2)**0.5
    # else:
    #     d=dy
    # print(dy)
    if  abs(Offset)>170:
        print(f"without correction {dy}")
        correction = (y-(height/2))*(fh/(2*h))
        print(correction)
        d=dy-correction
        print(f"dx is {dx}")
    else:
    
        print(f"dx is {dx}")
        d=(dy)



    return d,mask

def main(img_path):
    print()
    # Get user supplied values
    imagePath = img_path
    cascPath = "haarcascade_frontalface_default.xml"

    # Create the haar cascade
    faceCascade = cv2.CascadeClassifier(cascPath)
    eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml') 
    # Read the image
    image = cv2.imread(imagePath)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect faces in the image
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.2,
        minNeighbors=5,
        minSize=(30, 30),
        
    )

    #print("Found {0} faces!".format(len(faces)))
    # Add function so that number of faces does not exceed 1

    # hsv helps isolate only the facial portion of the image to reduce computation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Draw a rectangle around the faces
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x+w, y+h), (0, 255, 0), 2)
        print("Outer Face Box:","x =",x,", y =",y,", w =",w,", h =",h)
        print()
        
        roi_gray=gray[y:y+h, x:x+w] 
        roi_color=image[y:y+h, x:x+w]
        

        image[y:y+h, x:x+w] = hsv[y:y+h, x:x+w]

        # eye detection will help later in ensuring accuracy of facial dimensions

        eyes = eye_cascade.detectMultiScale(roi_gray,scaleFactor=1.2,minSize=(200, 200)) 
        for (ex,ey,ew,eh) in eyes: 
            cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,127,255),2)
            #print("eyes detected")

    d,mask = depth(image)
    
    print("Distance between Camera and Face :",d,"cm")
    
    resize = ResizeWithAspectRatio(mask, height=720)
    resize = ResizeWithAspectRatio(image, height=720)
    cv2.imshow("finalImg", resize)
    cv2.waitKey(0)

img_path = input("image path : ")
main(img_path)
 
    
