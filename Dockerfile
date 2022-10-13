FROM mcr.microsoft.com/azure-cli
WORKDIR /app
RUN pip3 install pygsheets && pip3 install python-dateutil
COPY . .
