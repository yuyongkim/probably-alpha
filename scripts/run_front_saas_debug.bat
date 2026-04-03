@echo on
cd /d C:\Users\USER\Desktop\Company_Credit

where py
where python

py -V
python -V

py -m sepa.pipeline.run_after_close

py -m uvicorn sepa.api.app:app --host 127.0.0.1 --port 8000
pause
