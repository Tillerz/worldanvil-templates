@echo off

REM this is for Windows

REM example: extract.cmd alana/the-titans_2025-04-17_120213.json
REM example: extract.cmd alana/the-titans_2025-04-17_120213.json -l a -t

python extract.py %1 %2 %3 %4 %5 %6 %7 %8
