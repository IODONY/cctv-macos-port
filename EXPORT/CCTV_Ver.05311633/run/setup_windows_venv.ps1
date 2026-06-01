$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "Creating virtual environment in $Root\.venv"
py -3.11 -m venv .venv

$Python = Join-Path $Root ".venv\Scripts\python.exe"
& $Python -m pip install --upgrade pip

Write-Host "Installing PyTorch CUDA wheel. If this fails, use the selector at https://pytorch.org/get-started/locally/"
& $Python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126

Write-Host "Installing project requirements"
& $Python -m pip install -r requirements.txt

Write-Host "Checking imports and syntax"
& $Python -m py_compile src\*.py scripts\*.py touchdesigner\*.py run\*.py
& $Python scripts\test_live_topk_units.py

Write-Host "SETUP_OK"

