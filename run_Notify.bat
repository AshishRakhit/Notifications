@echo off
echo. > output_notify.log
echo. > output_notify.err

REM To create the environment, use `conda env create -f environment.yml`

REM get path to conda executable
if [%CONDA%] == [] set CONDA=%CONDA_BAT%
if [%CONDA%] == [] for /f %%a in ('where conda') do set CONDA=%%a
if [%CONDA%] == [] echo Could not locate conda. >> output_notify.log 2>> output_notify.err
if [%CONDA%] == [] goto end

REM Read conda environment name from environment.yml into a variable
for /f "tokens=1-2 eol=# delims=: " %%a in (environment.yml) do if /i "%%a" == "name" set CONDA_EnvName=%%b

REM Activate the conda environment
CALL %CONDA% activate %CONDA_EnvName%
if ERRORLEVEL 1 goto conda_env_error

python notify.py >> output_notify.log 2>> output_notify.err

goto end

:conda_env_error
echo An error occurred while activating the conda environment. >> output_notify.log 2>> output_notify.err
exit 1

:end
