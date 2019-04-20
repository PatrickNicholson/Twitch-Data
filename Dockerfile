FROM nickgryg/alpine-pandas
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY data.py /app/data.py
WORKDIR /app
CMD ["python", "data.py"]
