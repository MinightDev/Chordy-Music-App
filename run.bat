@if (@CodeSection == @Batch) @then

@echo off

setlocal

pip install pytube pygame yt-dlp pypresence mutagen ttkthemes

start /B pythonw chordy.py

endlocal
exit

@end
