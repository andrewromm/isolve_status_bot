FROM rockstat/band-base-py
LABEL maintainer="Andrey Romm <andrew.romm@gmail.com>"

WORKDIR /usr/src/services

ENV HOST=0.0.0.0
ENV PORT=8080
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE ${PORT}
COPY . .

CMD [ "python", "-m", "isolve_status_bot"]
