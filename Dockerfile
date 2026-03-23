# Use the first one in admin network, the second otherwise
FROM repo.bit.admin.ch:8444/python:3.11-slim
# FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Use the first one in admin network, the second otherwise
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --proxy http://proxy-bvcol.admin.ch:8080 --no-cache-dir -r requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000"]