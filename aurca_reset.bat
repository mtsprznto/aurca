@echo off
echo [INFO] Devolviendo la GPU a su estado normal...
nvidia-smi -rgc
echo [DONE] Frecuencias liberadas.
pause