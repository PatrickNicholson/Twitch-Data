FROM nickgryg/alpine-pandas
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY harvester.py /app/data.py
WORKDIR /app
CMD ["python", "harvester.py"]
