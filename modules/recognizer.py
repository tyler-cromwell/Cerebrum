"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  Copyright (C) 2016 Tyler Cromwell <tyler@csh.rit.edu>

  This file is part of Cerebrum.

  Cerebrum is free software: you can redistribute it and/or modify
  it under Version 2 of the terms of the GNU General Public License
  as published by the Free Software Foundation.

  Cerebrum is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY of FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with Cerebrum.
  If not, see <http://www.gnu.org/licenses/old-licenses/gpl-2.0.html>
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

""" Python libraries """
import configparser
import hashlib
import os

""" External libraries """
import cv2

""" Local modules """
from modules import detector


class Recognizer(detector.Detector):
    def __init__(self, classifier, label, settings):
        super().__init__(classifier, settings)
        config = configparser.ConfigParser()
        config.read(settings)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self._threshold = int(config.get('Recognizer', 'threshold'))
        self._recognizer = cv2.face.createLBPHFaceRecognizer(threshold=self._threshold)
        self._recognizer.load(root_dir +'/data/recognizers/'+ label +'.xml')
        self._label = label
        self._hash = int(hashlib.sha1(label.encode()).hexdigest(), 16) % (10 ** 8)


    def recognize(self, frame):
        labels = []
        faces = self.detect(frame, False)

        for (x, y, w, h) in faces:
            face = preprocess(frame, x, y, w, h)
            predicted_label, confidence = self._recognizer.predict(face)

            if predicted_label == self._hash:
                labels.append(self._label +' ('+ str(round(confidence)) +')')
            else:
                labels.append('Unknown')

        return (labels, faces)


def preprocess(frame, x, y, w, h):
    cropped = frame[y: y+h, x: x+w]
    grayed = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    equalized = cv2.equalizeHist(grayed)
    filtered = cv2.bilateralFilter(equalized, 5, 60, 60)
    return filtered
