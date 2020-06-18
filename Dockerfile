FROM python:3.8

WORKDIR /toad_sp_data

COPY ./ .

RUN pip install --no-cache-dir -r requirements.txt
CMD [ "./run.sh" ]
