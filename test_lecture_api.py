#!/usr/bin/env python3
"""
Test Lecture Creation via API
Run this script on your server to test lecture creation
"""

import requests
import json

# Configuration - Update these with your server details
SERVER_URL = "http://your-server-ip:8000"  # Replace with your actual server IP
AUTH_TOKEN = "YOUR_JWT_TOKEN_HERE"  # Replace with actual JWT token

def get_auth_headers():
    """Get authorization headers for API requests"""
    return {
        'Authorization': f'Bearer {AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }

def test_lecture_creation():
    """Test creating a lecture via API"""
    print("🎬 Testing Lecture Creation via API")
    print("=" * 40)

    headers = get_auth_headers()

    # Step 1: Get available courses
    print("\n📚 Step 1: Getting available courses...")
    try:
        response = requests.get(f"{SERVER_URL}/api/courses/courses/", headers=headers)
        if response.status_code == 200:
            courses = response.json()
            print(f"✅ Found {len(courses)} courses")
            if courses:
                print(f"First course: {courses[0]['title']} (ID: {courses[0]['id']})")
                course_id = courses[0]['id']
            else:
                print("❌ No courses found. Create a course first.")
                return
        else:
            print(f"❌ Failed to get courses: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return

    # Step 2: Get sections for the course
    print(f"\n📖 Step 2: Getting sections for course {course_id}...")
    try:
        response = requests.get(f"{SERVER_URL}/api/courses/{course_id}/sections/", headers=headers)
        if response.status_code == 200:
            sections = response.json()
            print(f"✅ Found {len(sections)} sections")
            if sections:
                print(f"First section: {sections[0]['title']} (ID: {sections[0]['id']})")
                section_id = sections[0]['id']
            else:
                print("❌ No sections found. Create a section first.")
                return
        else:
            print(f"❌ Failed to get sections: {response.status_code}")
            print(response.text)
            return
    except Exception as e:
        print(f"❌ Error getting sections: {e}")
        return

    # Step 3: Create a lecture
    print(f"\n📝 Step 3: Creating lecture in section {section_id}...")

    lecture_data = {
        "title": "Test Lecture from API",
        "description": "This lecture was created via API test script",
        "order": 1,
        "is_preview": False
    }

    try:
        response = requests.post(
            f"{SERVER_URL}/api/courses/{course_id}/sections/{section_id}/lectures/",
            headers=headers,
            json=lecture_data
        )

        if response.status_code == 201:
            lecture = response.json()
            print("✅ Lecture created successfully!"            print(f"   Title: {lecture['title']}")
            print(f"   ID: {lecture['id']}")
            print(f"   Processing Status: {lecture.get('processing_status', 'N/A')}")

            lecture_id = lecture['id']
            return course_id, section_id, lecture_id

        else:
            print(f"❌ Failed to create lecture: {response.status_code}")
            print("Response:", response.text)
            return None

    except Exception as e:
        print(f"❌ Error creating lecture: {e}")
        return None

def test_lecture_upload(course_id, section_id, lecture_id):
    """Test uploading a video file to the lecture"""
    print(f"\n📤 Step 4: Testing video upload for lecture {lecture_id}...")

    # Create a dummy video file for testing
    import tempfile
    import os

    # Create a simple test video file (this is just for testing file upload)
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
        # Write some dummy content (not a real video)
        temp_file.write(b"dummy video content for testing file upload")
        temp_file_path = temp_file.name

    try:
        # Prepare multipart form data
        files = {
            'original_video': open(temp_file_path, 'rb')
        }

        headers = {
            'Authorization': f'Bearer {AUTH_TOKEN}'
            # Don't set Content-Type for multipart/form-data
        }

        response = requests.patch(
            f"{SERVER_URL}/api/courses/{course_id}/sections/{section_id}/lectures/{lecture_id}/",
            headers=headers,
            files=files
        )

        if response.status_code == 200:
            lecture = response.json()
            print("✅ Video uploaded successfully!")
            print(f"   File: {lecture.get('original_video', 'N/A')}")
            print(f"   Processing Status: {lecture.get('processing_status', 'N/A')}")
        else:
            print(f"❌ Failed to upload video: {response.status_code}")
            print("Response:", response.text)

    except Exception as e:
        print(f"❌ Error uploading video: {e}")

    finally:
        # Clean up temp file
        os.unlink(temp_file_path)

def main():
    print("🚀 Lecture API Test Script")
    print("This script will test lecture creation on your server")
    print("=" * 60)

    # Check configuration
    if SERVER_URL == "http://your-server-ip:8000":
        print("❌ Please update SERVER_URL with your actual server IP")
        return

    if AUTH_TOKEN == "YOUR_JWT_TOKEN_HERE":
        print("❌ Please update AUTH_TOKEN with your actual JWT token")
        print("\nTo get a JWT token:")
        print("1. Login via API: POST /api/users/login/")
        print("2. Copy the 'access' token from response")
        return

    # Run the test
    result = test_lecture_creation()

    if result:
        course_id, section_id, lecture_id = result
        # Optional: Test video upload
        test_lecture_upload(course_id, section_id, lecture_id)

    print("\n" + "=" * 60)
    print("🎯 Test completed!")
    print("If successful, your lecture creation is working.")
    print("If failed, check the error messages above.")

if __name__ == '__main__':
    main()
