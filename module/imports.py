# module/imports.py
"""
    사용할 라이브러리가 있는 경우 아래 추가
"""
# 표준 라이브러리
import sys
import time
import re
import json
import base64
import itertools
import subprocess
import shutil
import csv
import os
import html
import queue
import threading
import requests
import urllib3
import threading
from datetime import datetime

# 외부 라이브러리
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from dataclasses import dataclass, field
from urllib.parse import quote, urlparse, urljoin
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 내부 모듈