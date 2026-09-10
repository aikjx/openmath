@echo off
chcp 65001 >nul
setlocal

REM OpenMath 一键验证：L0 结构校验 -> L2 数值 -> L3 符号 -> 索引 -> 看板
REM 依赖：Python 3.9+（可选 sympy 以启用 L2/L3）

set "PY=python"

echo ============================================================
echo  OpenMath 一键验证
echo ============================================================
echo.

echo [1/5] 环境体检
%PY% -m openmath doctor
if errorlevel 1 goto :fail
echo.

echo [2/5] L0 结构校验
%PY% -m openmath lint
if errorlevel 1 goto :fail
echo.

echo [3/5] L2 数值验证
%PY% -m openmath verify --level L2
echo.

echo [4/5] L3 符号验证
%PY% -m openmath verify --level L3
echo.

echo [5/5] 索引与看板
%PY% -m openmath index
%PY% -m openmath status
echo.

echo ============================================================
echo  完成。
echo  提醒：L2/L3 通过不等于"已证明"，只有 L4 形式化通过才可如此表述。
echo ============================================================
endlocal
exit /b 0

:fail
echo.
echo 验证未通过，请修正上述错误后重试。
echo 禁止通过修改断言或放宽容差来让检查变绿（见 00-宪章/02-诚实红线.md）。
endlocal
exit /b 1
