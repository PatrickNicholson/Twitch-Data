FROM nickgryg/alpine-pandas
COPY requirements.txt /
RUN pip install -r /requirements.txt
COPY harvester.py /harvester.py
WORKDIR /
CMD ["python", "harvester.py"]
