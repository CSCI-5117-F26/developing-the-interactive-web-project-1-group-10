import cv2
import os
import uuid
import boto3
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

# We need to add the AWS Access Key, Secret Access Key, region and bucket name to the .env
s3_client = boto3.client(
  "s3",
  aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
  aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
  region_name=os.getenv("AWS_REGION", "us-east-1")
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

def upload_profile_to_s3(file_storage):
  """Uploads profile image and returns a url"""
  filename = secure_filename(file_storage.filename)
  s3_key = f"profiles/{uuid.uuid4()}-{filename}"

  s3_client.upload_fileobj(
    file_storage,
    BUCKET_NAME,
    s3_key,
    ExtraArgs={"ContentType": file_storage.content_type}
  )

  profile_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{s3_key}"
  return profile_url

def delete_profile_from_s3(profile_url):
  """Deletes the profile image from the s3 bucket"""
  try:
    parts = profile_url.split(".amazonaws.com/")
    if len(parts) > 1:
      s3_key = parts[1]
      s3_client.delete_object(Bucket=BUCKET_NAME, Key=s3_key)
  except Exception as e:
    print(f"Error deleting file from s3: {e}")

def extract_and_upload_thumbnail(video_url):
  """Extract a frame and upload to s3 """
  cap = cv2.VideoCapture(video_url)
  success, frame = cap.read()
  cap.release()

  if not success:
    return None

  temp_path = "tmp.jpg"
  cv2.imwrite(temp_path, frame)

  try:
    s3_key = f"thumbnails/{uuid.uuid4()}-thumbnail.jpg"
    with open(temp_path, "rb") as file:
      s3_client.upload_fileobj(
        file,
        BUCKET_NAME,
        s3_key,
        ExtraArgs={"ContentType": "image/jpeg"}
      )

    thumbnail_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{s3_key}"
    return thumbnail_url
  except Exception as e:
    print(f"Error uploading thumbnail: {e}")
    return None
  finally:
    if os.path.exists(temp_path):
      os.remove(temp_path)
