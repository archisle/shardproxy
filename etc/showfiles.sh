#! /bin/sh


find . \
    -name '.git' -prune -o \
    -name 'dist' -prune -o \
    -name 'build' -prune -o \
    -name 'htmlcov' -prune -o \
    -name '*.egg-info' -prune -o \
    -name '__pycache__' -prune -o \
    -name '.pytype' -prune -o \
    -name '.*_cache' -prune -o \
    -name '.coverage' -prune -o \
    -name '.venv' -prune -o \
    -name 'data' -prune -o \
    -name '*.log' -prune -o \
    -name '*.pid' -prune -o \
    -name '*.orig' -prune -o \
    -name '*.rej' -prune -o \
    -name 'tmp' -prune -o \
    -name '*.swp' -prune -o \
    -print

