@echo off
echo ==============================================
echo  INICIANDO PLATAFORMA DE DETECCION TEMPRANA
echo ==============================================
echo Activando entorno virtual...

call venv\Scripts\activate

echo Ejecutando aplicacion Streamlit...
echo.

streamlit run app.py

echo.
echo La aplicacion ha finalizado.
pause
