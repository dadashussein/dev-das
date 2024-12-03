FROM python:alpine
WORKDIR /myapp
ADD . .
RUN pip install -r requirements.txt
EXPOSE 80
CMD ["python", "app.py"]
