FROM python:3

WORKDIR /home/app

COPY ./requirements.txt /home/app

RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && \
apt update && \
apt install libgl1-mesa-glx

EXPOSE 12123

CMD ["python", "main.py"]