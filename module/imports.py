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

# 외부 라이브러리
import requests
import urllib3
from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass, field
from urllib.parse import quote, urlparse, urljoin
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 내부 모듈
from module.headers_module import get_headers, get_data, get_proxy, HTTPSession
from module.console_module import ConsolePrinter, col, colors, banner
from extract.ext_form import form_ext
from extract.ext_form_test import form_ext2

#테스트 모듈
from extract.report_test import report_test