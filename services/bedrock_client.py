import boto3

def init_bedrock_runtime():
    """Initialize AWS Bedrock runtime client"""
    try:
        # Test the credentials by creating client
        client = boto3.client('bedrock-runtime', region_name="us-west-2")
        return client

    except Exception as e:
        print(f"Failed to initialize AWS Bedrock: {e}")
        print("Please refresh your AWS credentials in config.py")
        return None