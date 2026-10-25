import 0s
import uuid
import boto3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

# We need to add the AWS Access Key, Secret Access Key, region and bucket name to the .env
s3_client = boto3.client(
  "s3",
  aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
  asw_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
  region=os.getenv("AWS_REGION", "us-east-1")
)

BUCKET_NAME = os.getenv("AWS_BUCKET_NAME")
REGION = os.getenv("AWS_REGION", "us-east-1")

def upload_video_to_s3(file_storage):
  """Uploads video and returns a url to the video"""
  filename = secure_filename(file_storage.filename)
  s3_key = f"videos/{uuid.uuid4()}-{filename}"

  s3_client.upload_fileobj(
    file_storage,
    BUCKET_NAME,
    s3_key,
    ExtraArgs={"ContentType": file_storage.content_type}
  )

  video_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{s3_key}"
  return video_url

def delete_video_from_s3(video_url):
  """Deletes the video from the s3 bucket"""
  try:
    parts = video_url.split(".amazonaws.com/")
    if len(parts) > 1:
      s3_key = parts[1]
      s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
  except Exception as e:
    print(f"Error deleting file from s3: {e}")


