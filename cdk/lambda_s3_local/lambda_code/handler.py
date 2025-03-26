from s3_uploader import S3Uploader

def main(event, context):
    uploader = S3Uploader()  
    return uploader.handle_request(event) 