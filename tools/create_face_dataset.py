#!/usr/bin/env python3

#######################################################################
# Copyright (C) 2016 Tyler Cromwell <tyler@csh.rit.edu>
#
# This file is part of Cerebrum.
#
# Cerebrum is free software: you can redistribute it and/or modify
# it under Version 2 of the terms of the GNU General Public License
# as published by the Free Software Foundation.
#
# Cerebrum is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY of FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Cerebrum.
# If not, see <http://www.gnu.org/licenses/old-licenses/gpl-2.0.html>
#######################################################################

import getopt
import os
import sys

import cv2

sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import camera
from modules import configuration
from modules import detection
from modules import imgproc
from modules import misc
from modules import opt
from modules import pathname

CAMERA_DEFAULT = 0


def print_usage():
    """
    Displays program usage information.
    """
    print('Usage:\t./create_face_dataset.py [--classifier=PATH] --label=NAME [--settings=NAME]')
    print('  --help\t\tPrints this text')
    print('  --classifier=PATH\tThe absolute path of a Face Detection classifier (Optional)')
    print('  --label=NAME\t\tThe name of the person\'s face dataset to create')
    print('  --settings=NAME\tThe name of a file located under \'settings/\'')
    print('        See \'settings/\', without \'.txt\' extension')
    exit(0)


def main():
    """
    Main function.
    """
    classifier = None
    label = None
    settings = opt.map_settings()
    key = opt.default_settings()
    window_name = 'Camera {}'.format(CAMERA_DEFAULT)

    try:
        short_opts = ['']
        long_opts = ['help', 'classifier=', 'label=', 'settings=']
        opts, args = getopt.getopt(sys.argv[1:], short_opts, long_opts)
    except getopt.GetoptError as error:
        print('Invalid argument: \"{}\"\n'.format(str(error)))
        print_usage()

    if len(opts) == 0:
        print_usage()

    for o, a in opts:
        if o == '--help':
            print_usage()
        elif o == '--classifier':
            classifier = opt.validate_file(a)
        elif o == '--label':
            label = a
        elif o == '--settings':
            key = a

    if key not in settings.keys():
        print('\n  Settings file \"{}\" not found!\n'.format(key))
        print_usage()

    if not label:
        print('\n  Label not specified!\n')
        print_usage()

    # Setup training set, objects, and window
    config = configuration.Config(settings[key])
    recognizer = config.recognizer()
    width = int(recognizer['width'])
    height = int(recognizer['height'])
    training_path = pathname.get_training_root(label)
    os.makedirs(training_path, exist_ok=True)

    dwidth, dheight = misc.get_display_resolution()
    print('Display resolution: {:d}x{:d}'.format(dwidth, dheight))

    detector = detection.Detector(classifier, config)
    stream = camera.Camera(CAMERA_DEFAULT, config)
    print('Capture Resolution: {:d}x{:d}'.format(stream.get_width(), stream.get_height()))

    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    cv2.moveWindow(window_name, (dwidth - stream.get_width()) // 2, 0)

    p = 0

    if not stream.open():
        print('Failed to open Camera', CAMERA_DEFAULT)
        exit(1)

    while True:
        retval, frame = stream.read()
        faces = detector.detect(frame)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)

        cv2.putText(frame, 'Photos taken: {}'.format(p), (0, 10), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))
        cv2.putText(frame, 'Press \'w\' to take photo', (0, 22), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0))

        cv2.imshow(window_name, frame)
        key = cv2.waitKey(1)

        if key == 27:
            cv2.destroyWindow(window_name)
            cv2.waitKey(1)
            cv2.waitKey(1)
            cv2.waitKey(1)
            cv2.waitKey(1)
            stream.release()
            break
        elif key == ord('w') and len(faces) >= 1:
            retval, frame = stream.read()   # Get frame without drawings
            (x, y, w, h) = faces[0]

            image = imgproc.preprocess(frame, width, height, x, y, w, h)

            if p < 10:
                cv2.imwrite(training_path + label + '.0{}.png'.format(str(p)), image)
            else:
                cv2.imwrite(training_path + label + '.{}.png'.format(str(p)), image)

            p = p + 1

    stream.release()


if __name__ == '__main__':
    """
    Program entry.
    """
    try:
        main()
    except KeyboardInterrupt:
        print()
        exit(0)
