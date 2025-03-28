### VARIABLES ###
CDK=npx aws-cdk-local
STACK_NAME=LambdaS3LocalStack
ENDPOINT=http://localhost:4566
BUCKET_NAME=my-audio-bucket
BUCKET_OUTPUT=my-audio-output-bucket
LAMBDA_NAME=SaveToS3Function
API_ID=$(shell awslocal apigateway get-rest-apis | grep '"id"' | head -1 | awk -F'"' '{print $$4}')
LAMBDA_SNS=SNS
STACK_SNS=ETLStack
ETL_STACK=LambdaETLStack

### CDK ###
bootstrap:
	cd cdk && $(CDK) bootstrap --app "python3 app.py"

synth:
	cd cdk && $(CDK) synth --app "python3 app.py"

deploy:
	cd cdk && $(CDK) deploy $(STACK_NAME) --require-approval never --app "python3 app.py"

deploy-etl:
	cd cdk && $(CDK) deploy $(ETL_STACK) --require-approval never --app "python3 app.py
destroy:
	$(CDK) destroy $(STACK_NAME) --force
	
### LOCALSTACK ###

start-localstack:
	docker-compose up -d

stop-localstack:
	docker-compose down

### LAMBDA ###
invoke:
	awslocal lambda invoke \
		--function-name $(LAMBDA_NAME) \
		--payload '{ "audioData": { "oscillator": { "type": "sawtooth", "frequency": 120 }, "gain": 0.3, "filter": { "type": "lowpass", "frequency": 2000 } }, "timestamp": 1679932800000 }' \
		response.json && cat response.json

list-bucket:
	awslocal s3 ls s3://$(BUCKET_NAME)

list-output-bucket:
	awslocal s3 ls s3://$(BUCKET_OUTPUT)

get-object:
	@awslocal s3 ls s3://$(BUCKET_NAME)/ | tail -n 1 | awk '{print $$4}' | xargs -r -I {} awslocal s3 cp s3://$(BUCKET_NAME)/{} -
clean:
	rm -f response.json

### API GATEWAY ###
list-api:
	awslocal apigateway get-rest-apis

generate-config:
	echo '{ "lambdaApiUrl": "http://localhost:4566/restapis/$(API_ID)/prod/_user_request_/items" }' > audio/config.json

invoke-api:
	curl -X POST \
        -H "Content-Type: application/octet-stream" \
        -d '{"audioData": {"oscillator": {"type": "sawtooth", "frequency": 120}, "gain": 0.3, "filter": {"type": "lowpass", "frequency": 2000}}, "timestamp": 1679932800000}' \
		http://localhost:4566/restapis/$(API_ID)/prod/_user_request_/items

test-api:
	echo "Reemplaza <API-ID> en el Makefile para probar la API"
