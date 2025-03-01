# import the necessary packages
import numpy as np
import argparse
import cv2

# Initialize the current frame of the video, along with the list of
# ROI points and whether or not this is input mode
frame = None
roiPts = []
inputMode = False

def selectROI(event, x, y, flags, param):
    # Grab the reference to the current frame, list of ROI
    # points, and whether or not it is ROI selection mode
    global frame, roiPts, inputMode

    # If we are in ROI selection mode, the mouse was clicked,
    # and we do not already have four points, then update the
    # list of ROI points with the (x, y) location of the click
    # and draw the circle
    if inputMode and event == cv2.EVENT_LBUTTONDOWN and len(roiPts) < 4:
        roiPts.append((x, y))
        cv2.circle(frame, (x, y), 4, (0, 255, 0), 2)
        cv2.imshow("frame", frame)

def main():
    # Construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--video", help="path to the (optional) video file")
    args = vars(ap.parse_args())

    # Grab the reference to the current frame, list of ROI
    # points, and whether or not it is ROI selection mode
    global frame, roiPts, inputMode

    # If the video path was not supplied, grab the reference to the camera
    if not args.get("video", False):
        camera = cv2.VideoCapture(0)
    # Otherwise, load the video
    else:
        camera = cv2.VideoCapture(args["video"])

    # Setup the mouse callback
    cv2.namedWindow("frame")
    cv2.setMouseCallback("frame", selectROI)

    # Initialize the termination criteria for CamShift, indicating
    # a maximum of ten iterations or movement by at least one pixel
    # along with the bounding box of the ROI
    termination = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
    roiBox = None

    # Keep looping over the frames
    while True:
        # Grab the current frame
        (grabbed, frame) = camera.read()

        # Check to see if we have reached the end of the video
        if not grabbed:
            break

        # If the ROI has been computed
        if roiBox is not None:
            # Convert the current frame to the HSV color space
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            # Compute the back projection using both Hue and Saturation channels
            backProj = cv2.calcBackProject([hsv], [0, 1], roiHist, [0, 180, 0, 256], 1)

            # Apply CamShift to the back projection, convert the
            # points to a bounding box, and then draw them
            (r, roiBox) = cv2.CamShift(backProj, roiBox, termination)

            # Check if the bounding box is valid
            if r[1][0] < 1 or r[1][1] < 1:  # If width or height is too small
                print("Object lost!")
                roiBox = None  # Reset the ROI
            else:
                # Convert the points to a bounding box and draw them
                pts = np.int0(cv2.boxPoints(r))  # Updated from cv2.cv.BoxPoints
                cv2.polylines(frame, [pts], True, (0, 255, 0), 2)

        # Show the frame
        cv2.imshow("frame", frame)

        # Check if the window is closed
        if cv2.getWindowProperty("frame", cv2.WND_PROP_VISIBLE) < 1:
            break

        # Record if the user presses a key
        key = cv2.waitKey(1) & 0xFF

        # Handle if the 'i' key is pressed, then go into ROI selection mode
        if key == ord("i") and len(roiPts) < 4:
            # Indicate that we are in input mode and clone the frame
            inputMode = True
            orig = frame.copy()

            # Keep looping until 4 reference ROI points have
            # been selected; press any key to exit ROI selection
            # mode once 4 points have been selected
            while len(roiPts) < 4:
                cv2.imshow("frame", frame)
                cv2.waitKey(0)

            # Determine the top-left and bottom-right points
            roiPts = np.array(roiPts)
            s = roiPts.sum(axis=1)
            tl = roiPts[np.argmin(s)]
            br = roiPts[np.argmax(s)]

            # Grab the ROI for the bounding box and convert it
            # to the HSV color space
            roi = orig[tl[1]:br[1], tl[0]:br[0]]
            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # Compute a 2D HSV histogram for the ROI and store the
            # bounding box
            roiHist = cv2.calcHist([roi], [0, 1], None, [16, 16], [0, 180, 0, 256])
            roiHist = cv2.normalize(roiHist, roiHist, 0, 255, cv2.NORM_MINMAX)
            roiBox = (tl[0], tl[1], br[0] - tl[0], br[1] - tl[1])

        # If the 'q' key is pressed, stop the loop
        elif key == ord("q"):
            break

    # Cleanup the camera and close any open windows
    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
    