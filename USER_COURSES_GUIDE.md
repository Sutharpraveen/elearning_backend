# User Enrolled Courses - API Guide

## 📚 User ke Enrolled Courses Kaise Aayenge

### API Endpoint:
```
GET /api/courses/enrollments/
```

### Headers Required:
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

---

## 🔧 Step-by-Step:

### Step 1: Login (Get JWT Token)
```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "p@gmail.com", "password": "test123"}'
```

**Response:**
```json
{
  "tokens": {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
}
```

### Step 2: Get Enrolled Courses
```bash
curl -X GET http://127.0.0.1:8000/api/courses/enrollments/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
[
  {
    "id": 1,
    "course": {
      "id": 1,
      "title": "Flutter Development",
      "description": "...",
      "original_price": "2999.00",
      "discounted_price": "1999.00",
      "thumbnail": "http://127.0.0.1:8000/media/...",
      "instructor": {...},
      "category": {...}
    },
    "user": {
      "id": 1,
      "email": "p@gmail.com",
      "username": "praveen"
    },
    "enrolled_at": "2025-12-06T18:09:37.038154Z",
    "completed": false,
    "completed_at": null,
    "last_accessed": null,
    "progress_percentage": 0
  }
]
```

---

## 📋 Response Fields:

- **id**: Enrollment ID
- **course**: Complete course details
  - title, description, price, thumbnail
  - instructor details
  - category details
- **user**: User details
- **enrolled_at**: Enrollment date
- **completed**: Course completion status
- **completed_at**: Completion date (if completed)
- **last_accessed**: Last access time
- **progress_percentage**: Course progress (0-100%)

---

## ✅ What Was Fixed:

**Bug Found:** 
- `EnrollmentViewSet` में `student` field use हो रहा था
- But model में field name `user` है

**Fix Applied:**
```python
# Before (❌ Error):
return Enrollment.objects.filter(student=self.request.user)

# After (✅ Fixed):
return Enrollment.objects.filter(user=self.request.user)
```

---

## 🧪 Test Script:

```bash
python -c "
import requests
import json

# Login
login = requests.post('http://127.0.0.1:8000/api/users/login/', 
    json={'email': 'p@gmail.com', 'password': 'test123'})
token = login.json()['tokens']['access']

# Get enrollments
enrollments = requests.get('http://127.0.0.1:8000/api/courses/enrollments/',
    headers={'Authorization': f'Bearer {token}'})

print(json.dumps(enrollments.json(), indent=2))
"
```

---

## 📱 Frontend Integration Example:

```javascript
// React/Next.js Example
async function getUserCourses() {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://127.0.0.1:8000/api/courses/enrollments/', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  const courses = await response.json();
  return courses;
}
```

---

## 🎯 Summary:

✅ **API Working:** `/api/courses/enrollments/`  
✅ **Authentication:** JWT Token required  
✅ **Response:** Complete course details with enrollment info  
✅ **Bug Fixed:** EnrollmentViewSet now uses correct field name

**User ke enrolled courses ab properly aa rahe hain!**










