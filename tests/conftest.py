# -*- coding: utf-8 -*-
# Конфигурация pytest: добавляем корень проекта в PYTHONPATH для импорта пакета `app`

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)