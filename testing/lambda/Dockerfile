FROM amazon/aws-lambda-python:3.9

WORKDIR ${LAMBDA_TASK_ROOT}

COPY app.py requirements.txt ${LAMBDA_TASK_ROOT}

RUN python3.9 -m pip install -r ./requirements.txt

CMD ["app.lambda_handler"]

