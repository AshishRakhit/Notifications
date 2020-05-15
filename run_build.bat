@echo off
REM get path to conda executable
if [%CONDA%] == [] set CONDA=%CONDA_BAT%
if [%CONDA%] == [] for /f %%a in ('where conda') do set CONDA=%%a
if [%CONDA%] == [] echo Could not locate conda. 1>&2
if [%CONDA%] == [] goto end

REM Read conda environment name from environment.yml into a variable
for /f "tokens=1-2 eol=# delims=: " %%a in (environment.yml) do if /i "%%a" == "name" set CONDA_EnvName=%%b
set PYTHONIOENCODING=

REM Activate the conda environment
CALL %CONDA% activate %CONDA_EnvName%
if ERRORLEVEL 1 goto end

python setup.py check_version

:end