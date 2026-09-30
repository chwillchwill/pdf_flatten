@echo off
rem Build dist\PDFFlattener.exe with PyInstaller. Run from a Windows checkout.
rem   build.bat         build
rem   build.bat clean   remove the build venv, build output and caches
setlocal
pushd "%~dp0"

if /i "%~1"=="clean" (
    for %%d in (.venv-win build dist __pycache__ tests\__pycache__ .pytest_cache) do (
        if exist %%d rmdir /s /q %%d
    )
    if exist *.spec del /q *.spec
    echo Cleaned.
    popd
    exit /b 0
)

if not exist .venv-win\Scripts\python.exe (
    py -3 -m venv .venv-win || goto :error
)
.venv-win\Scripts\python -m pip install --quiet --upgrade pip || goto :error
.venv-win\Scripts\python -m pip install --quiet -r requirements.txt -r requirements-build.txt || goto :error

.venv-win\Scripts\pyinstaller --noconfirm --clean --onefile --windowed ^
    --name PDFFlattener pdf_flattener.py || goto :error

echo.
echo Built %CD%\dist\PDFFlattener.exe
popd
exit /b 0

:error
echo Build failed.
popd
exit /b 1
