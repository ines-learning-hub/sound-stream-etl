from s3_uploader import S3Uploader

def main(event, context):
    uploader = S3Uploader()  
    response = uploader.handle_request(event) 

    response["headers"] = {
        "Access-Control-Allow-Origin" : "*",
        "Access-Control-Allow-Methods" : "OPTIONS, POST",
        "Access-Control-Allow-Headers" : "Content-Type"
    }

    return response