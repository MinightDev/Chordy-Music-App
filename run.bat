@if (@CodeSection == @Batch) @then

@echo off

setlocal

pip install pytube pygame yt-dlp mutagen

start /B pythonw chordy.py

endlocal
exit

@end
