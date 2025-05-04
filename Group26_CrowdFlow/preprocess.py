#!/usr/bin/env python3
"""
Video Stabilization + Sharpness & Contrast Enhancement

Dependencies:
    pip install opencv-python vidstab numpy
"""

import cv2
import numpy as np
from vidstab import VidStab
import argparse
import os

def enhance_frame(frame, sharpen_amount=0.5, contrast_alpha=1.2, contrast_beta=0):
    blurred = cv2.GaussianBlur(frame, (0, 0), sigmaX=3)
    sharpened = cv2.addWeighted(frame, 1.0 + sharpen_amount,
                                blurred, -sharpen_amount, 0)
    enhanced = cv2.convertScaleAbs(sharpened,
                                   alpha=contrast_alpha,
                                   beta=contrast_beta)
    return enhanced

def stabilize_and_enhance(input_path, output_path,
                          smoothing_window=30,
                          sharpen_amount=0.6,
                          contrast_alpha=1.3,
                          contrast_beta=10):
    temp_path = '._stabilized_temp.mp4'
    stabilizer = VidStab(kp_method='GFTT')
    stabilizer.stabilize(input_path=input_path,
                         output_path=temp_path,
                         smoothing_window=smoothing_window,
                         border_size=0)

    cap = cv2.VideoCapture(temp_path)
    if not cap.isOpened():
        raise IOError(f"Cannot open stabilized video {temp_path}")
    fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out    = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    print(f"Processing stabilized frames → enhancing → writing to {output_path}...")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        proc = enhance_frame(frame,
                             sharpen_amount=sharpen_amount,
                             contrast_alpha=contrast_alpha,
                             contrast_beta=contrast_beta)
        out.write(proc)

    cap.release()
    out.release()
    os.remove(temp_path)
    print("Done.")

if _name_ == '_main_':
    parser = argparse.ArgumentParser(
        description="Stabilize a video, boost sharpness & contrast.")
    parser.add_argument('input',  help='Path to input video')
    parser.add_argument('output', help='Path to output video')
    parser.add_argument('--smooth', type=int, default=30,
                        help='Stabilization smoothing window (default: 30)')
    parser.add_argument('--sharpen', type=float, default=0.6,
                        help='Sharpening strength (0–1.0)')
    parser.add_argument('--alpha', type=float, default=1.3,
                        help='Contrast gain (>1 increases contrast)')
    parser.add_argument('--beta',  type=float, default=10,
                        help='Brightness offset')
    args = parser.parse_args()

    stabilize_and_enhance(
        args.input,
        args.output,
        smoothing_window=args.smooth,
        sharpen_amount=args.sharpen,
        contrast_alpha=args.alpha,
        contrast_beta=args.beta
    )