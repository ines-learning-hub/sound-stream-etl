### VARIABLES ###
CDK=npx aws-cdk-local
STACK_NAME=LambdaS3LocalStack
ENDPOINT=http://localhost:4566
BUCKET_NAME=my-local-bucket
LAMBDA_NAME=SaveToS3Function

### CDK ###
bootstrap:
	cd cdk && $(CDK) bootstrap --app "python3 app.py"

synth:
	cd cdk && $(CDK) synth --app "python3 app.py"

deploy:
	cd cdk && $(CDK) deploy $(STACK_NAME) --require-approval never --app "python3 app.py"

destroy:
	$(CDK) destroy $(STACK_NAME) --force

### LOCALSTACK ###t
start-localstack:
	docker-compose up -d

stop-localstack:
	docker-compose down

### LAMBDA ###
invoke:
	awslocal lambda invoke \
		--function-name $(LAMBDA_NAME) \
		--payload '{ "filename": "archivo.txt", "content": "Desde Makefile!" }' \
		response.json && cat response.json

list-bucket:
	awslocal s3 ls s3://$(BUCKET_NAME)

get-object:
	awslocal s3 cp s3://$(BUCKET_NAME)/archivo.txt -

clean:
	rm -f response.json