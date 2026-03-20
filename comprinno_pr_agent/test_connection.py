#!/usr/bin/env python3
"""Quick test script to verify AWS Bedrock connection"""
import os
import sys
import boto3

# Load .env
with open('.env') as f:
    for line in f:
        if line.strip() and not line.startswith('#') and '=' in line:
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

print("🔍 Testing AWS Bedrock Connection")
print("=" * 50)

# Check credentials
print(f"✓ AWS Region: {os.getenv('AWS_REGION')}")
print(f"✓ Access Key: {os.getenv('AWS_ACCESS_KEY_ID')[:10]}...")
print(f"✓ Model: {os.getenv('BEDROCK_MODEL')}")

# Test AWS connection
try:
    print("\n📡 Testing AWS STS (credentials)...")
    sts = boto3.client('sts', region_name=os.getenv('AWS_REGION'))
    identity = sts.get_caller_identity()
    print(f"✅ Connected as Account: {identity['Account']}")
except Exception as e:
    print(f"❌ AWS credentials failed: {e}")
    sys.exit(1)

# Test Bedrock access
try:
    print("\n🤖 Testing AWS Bedrock access...")
    bedrock = boto3.client('bedrock', region_name=os.getenv('AWS_REGION'))
    models = bedrock.list_foundation_models()
    print(f"✅ Bedrock accessible - {len(models.get('modelSummaries', []))} models available")
except Exception as e:
    print(f"❌ Bedrock access failed: {e}")
    print("\n💡 Note: Make sure Bedrock is enabled in ap-south-1 region")
    sys.exit(1)

# Test Bedrock Runtime
try:
    print("\n🚀 Testing Bedrock Runtime (Nova model)...")
    bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION'))
    
    response = bedrock_runtime.converse(
        modelId=os.getenv('BEDROCK_MODEL'),
        messages=[{"role": "user", "content": [{"text": "Say 'Hello' in one word"}]}],
        inferenceConfig={"temperature": 0.3, "maxTokens": 10}
    )
    
    result = response['output']['message']['content'][0]['text']
    print(f"✅ Nova model working! Response: '{result}'")
    
except Exception as e:
    print(f"❌ Bedrock Runtime failed: {e}")
    print("\n💡 Possible issues:")
    print("   - Model not available in ap-south-1")
    print("   - Need to request model access in AWS Console")
    sys.exit(1)

print("\n" + "=" * 50)
print("✨ All tests passed! Ready to analyze code.")
