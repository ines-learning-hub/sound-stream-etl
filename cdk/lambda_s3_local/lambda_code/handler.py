from s3_uploader import S3Uploader
import os
def main(event, context):
    uploader = S3Uploader(os.environ["BUCKET_NAME"], os.environ.get("LOCALSTACK_ENDPOINT"))  
    response= uploader.handle_request(event) 
    uploader.notify_glue(response['file_name'], os.environ["TOPIC_ARN"])

    del response["file_name"]
    response["headers"] = {
        "Access-Control-Allow-Origin" : "*",
        "Access-Control-Allow-Methods" : "OPTIONS, POST",
        "Access-Control-Allow-Headers" : "Content-Type"
    }

    return response