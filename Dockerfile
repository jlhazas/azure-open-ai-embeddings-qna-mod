FROM python:3.9.10-slim-buster
RUN cat /etc/os-release
RUN apt-get update && apt-get install python-tk python3-tk tk-dev -y
RUN apt-get install unixodbc-dev -y
RUN apt-get install curl -y
RUN apt-get install odbcinst1debian2 -y
COPY ./code/sql_driver.sh /usr/local/src/myscripts/sql_driver.sh
RUN chmod +x /usr/local/src/myscripts/sql_driver.sh
RUN /usr/local/src/myscripts/sql_driver.sh -y
COPY ./code/requirements.txt /usr/local/src/myscripts/requirements.txt
WORKDIR /usr/local/src/myscripts
RUN pip install -r requirements.txt
COPY ./code/ /usr/local/src/myscripts
EXPOSE 80
CMD ["streamlit", "run", "OpenAI_Queries.py", "--server.port", "80", "--server.enableXsrfProtection", "false"]
