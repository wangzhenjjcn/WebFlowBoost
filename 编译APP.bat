set "SCRIPT_DIR=%~dp0"
pip install --upgrade pip  -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install  -r requirements.txt  -i https://pypi.tuna.tsinghua.edu.cn/simple
pip install pyinstaller  -i https://pypi.tuna.tsinghua.edu.cn/simple
PyInstaller -y -F -w -n WebFlowBoost  %SCRIPT_DIR%\src\app.py 
@pause
 