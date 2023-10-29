import re
import os
import cv2
import srt
import math
import argparse
import datetime
import pytesseract
import pytesseract
import numpy as np
from tqdm import tqdm
from autocorrect import Speller

def jaccard_similarity(x, y):
    try:
        intersection_cardinality = len(set.intersection(set(x), set(y)))
        union_cardinality = len(set.union(set(x), set(y)))
        return intersection_cardinality / float(union_cardinality)
    except ZeroDivisionError:
        return 0

def filter_text(text_in):
    text_out = text_in
    text_out = spell(text_out)
    text_out = re.sub(r'[\s\r\n#!\'_*=123456789]', '', text_out)
    text_out = text_out.encode("ascii", "ignore").decode()
    return text_out

def realistic_filter(text_in):
    text_out = text_in
    text_out = re.sub(r'[_=*#¢123456789]', '', text_out)
    return text_out

# Create the argument parser
parser = argparse.ArgumentParser(description="Description of your script")
parser.add_argument("video_filename", type=str, help="Path to the video file")
args = parser.parse_args()

# Use args.video_filename to get the video file name
video_filename = args.video_filename

# Extract the video file directory
video_directory = os.path.dirname(video_filename)

# Extract the base name of the video file (without extension)
video_name_base = os.path.splitext(os.path.basename(video_filename))[0]

# Create the full path of the SRT file by adding the ".srt" extension
srt_filename = os.path.join(video_directory, video_name_base + ".srt")

# Check if the SRT file already exists
if os.path.exists(srt_filename):
    valid_responses = re.compile(r'^(o(ui)?|y(es)?)$', re.IGNORECASE)

    # The file exists, ask the user if they want to overwrite it
    user_choice = input(f"The file {srt_filename} already exists. Do you want to overwrite it? (Y/n): ")

    if not valid_responses.match(user_choice):
        # The user chose not to overwrite it, exit the script
        print("Operation canceled. No file was created.")
        exit(0)

# Create the SRT file
text_sub = open(srt_filename, "w")

spell = Speller(only_replacements=True)
startTime = 0.0
sub_change_trigger = False
last_ret = ""
subNumber = 0  # Initialize subNumber

pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

vidcap = cv2.VideoCapture(video_filename)

fps = vidcap.get(cv2.CAP_PROP_FPS)
total_frame_count = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))

print(f"Processing {total_frame_count} frames at {fps}fps")

parsed = []

# Use tqdm to create a progress bar
for c in tqdm(range(total_frame_count), desc="Processing frames"):
    success, image = vidcap.read()
    if not success:
        break

    # Add your code for processing frames here
    img_width = image.shape[1]
    img_height = image.shape[0]

    cropped_image = image[int(1 / 1.2 * img_height):img_height, int(1 / 5 * img_width):int(2 / 2.3 * img_width)]

    gray_img_copy = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    gray_img_copy[gray_img_copy < 252] = 0

    # Convert the grayscale image to 3 channels (BGR)
    gray_img_copy_bgr = cv2.cvtColor(gray_img_copy, cv2.COLOR_GRAY2BGR)

    # Stack the original image and the grayscale image vertically
    stacked_image = np.vstack((cropped_image, gray_img_copy_bgr))

    cv2.imshow("Current frame", stacked_image)

    cv2.waitKey(1)
    
    ret = pytesseract.image_to_string(gray_img_copy, lang="fra", config="--psm 6 --oem 1")

    if sub_change_trigger:
        sentences = [filter_text(ret), filter_text(last_ret)]
        sim = jaccard_similarity(sentences[0], sentences[1])

        if sim <= 0.7:
            sub_change_trigger = False
            endTime = list(math.modf(c / fps + 2))
            unmodifiedEnd = c / fps + 2
            endTime[0] = int(endTime[0] * 1000000)
            endTime[1] = int(endTime[1])

            if unmodifiedEnd - unmodifiedStart > 0.5:
                print("Stopped at", c / fps, "Seconds in")
                subtitle = srt.Subtitle(
                    index=subNumber,
                    start=datetime.timedelta(seconds=startTime[1], microseconds=startTime[0]),
                    end=datetime.timedelta(seconds=endTime[1], microseconds=endTime[0]),
                    content=realistic_filter(last_ret),
                    proprietary="",
                )
                parsed.append(subtitle)

                # Write the subtitle to the SRT file
                text_sub.write(srt.compose([subtitle]))
                text_sub.write("\n")

            else:
                print("Sub thrown out because it did not last long enough (" + str(unmodifiedEnd - unmodifiedStart) + ") seconds")

    if ret != "":
        sentences = [filter_text(ret), filter_text(last_ret)]
        sim = jaccard_similarity(sentences[0], sentences[1])

        if sim <= 0.7:
            subNumber += 1
            print("Started at", c / fps, "Seconds in")
            startTime = list(math.modf(c / fps + 2))
            unmodifiedStart = c / fps + 2
            startTime[0] = int(startTime[0] * 1000000)
            startTime[1] = int(startTime[1])
            print(startTime)
            sub_change_trigger = True
            print(realistic_filter(ret))

    last_ret = ret

# Release the video capture when done
vidcap.release()

# Close the SRT file
text_sub.close()
