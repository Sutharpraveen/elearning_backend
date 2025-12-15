# Postman API Collection - E-Learning Backend

Complete Postman collection with all API endpoints for your Udemy-like e-learning platform.

## 📁 Files

- `E-Learning_Backend_API_Collection.postman_collection.json` - Main API collection
- `E-Learning_Backend.postman_environment.json` - Environment variables

## 🚀 Quick Setup

### 1. Import Collection & Environment
1. Open Postman
2. Click "Import" button
3. Import both JSON files:
   - `E-Learning_Backend_API_Collection.postman_collection.json`
   - `E-Learning_Backend.postman_environment.json`

### 2. Configure Environment
1. Select "E-Learning Backend Environment" from environment dropdown
2. Update `base_url` if your server is not running on `http://127.0.0.1:8000`
3. Click "Save"

## 📋 API Groups

### 🔐 Authentication
- User Registration
- Login (sets tokens automatically)
- Logout
- Token Refresh

### 👤 User Profile
- Get/Update Profile
- Change Password
- Upload Profile Image
- Profile Statistics
- Public Profile View

### 📂 Categories
- List Categories
- Create/Update/Delete Categories
- Filter Courses by Category

### 📚 Courses
- List/Search Courses
- Create/Update/Delete Courses
- Course Reviews & Ratings
- Course Enrollment

### 🎬 Course Content
- Course Sections & Lectures
- Video Access (HLS Streaming)
- Progress Tracking
- User Enrollments

### 🛒 Shopping Cart
- Add/Remove Items
- Cart Summary & Pricing
- Coupon Application
- Save for Later
- Cart Management

### ❤️ Wishlist
- Add/Remove Courses
- Move to Cart
- Course Status Check

### 💳 Payments
- Single Course Payment
- Multi-Course Payment
- Razorpay Integration
- Payment Verification

### ⚙️ Core Features
- Slider Images
- App Versions
- Health Check

## 🔧 Environment Variables

| Variable | Description | Auto-Set |
|----------|-------------|----------|
| `base_url` | API server URL | Manual |
| `access_token` | JWT access token | Auto (after login) |
| `refresh_token` | JWT refresh token | Auto (after login) |
| `user_id` | Current user ID | Auto (after login) |
| `test_course_id` | Sample course ID | Manual |
| `test_category_id` | Sample category ID | Manual |

## 📝 Usage Examples

### 1. User Registration & Login
```
1. Run "Register User" → Creates account
2. Run "Login User" → Gets tokens (auto-saved)
3. All subsequent requests use Bearer token
```

### 2. Course Management (Instructor)
```
1. Login as instructor
2. "Create Course" → Add new course
3. "Create Section" → Add course sections
4. "Create Lecture" → Add video lectures
```

### 3. Student Course Access
```
1. Login as student
2. "List Courses" → Browse available courses
3. "Add to Cart" → Add course to cart
4. "Create Payment Order" → Generate payment
5. "Verify Payment" → Complete purchase & enrollment
6. "Get Course Sections" → Access course content
```

## 🎯 Key Features Demonstrated

### ✅ Authentication Flow
- JWT tokens with automatic refresh
- Role-based access (Student/Instructor)

### ✅ E-commerce Flow
- Cart → Payment → Enrollment → Content Access
- Wishlist → Cart → Purchase
- Coupon discounts

### ✅ Video Streaming
- HLS adaptive bitrate streaming
- Multiple quality options (1080p, 720p, 480p, 360p)
- Progress tracking

### ✅ Content Management
- Course creation and organization
- Section and lecture management
- File upload handling

## 🔍 Testing Tips

### Authentication
- Always login first to get tokens
- Tokens are automatically saved after login
- Use "Refresh Token" if access token expires

### File Uploads
- Use form-data for file uploads
- Supported: JPG/PNG/GIF for images, MP4 for videos

### IDs in URLs
- Replace `1` with actual IDs from your database
- Example: `/api/courses/courses/1/` → `/api/courses/courses/123/`

### Error Handling
- Check response status codes
- 401 = Authentication required
- 403 = Permission denied
- 404 = Resource not found

## 🚨 Important Notes

### Video Processing
- Videos are processed asynchronously after upload
- Check `processing_status` in lecture responses
- Use management command for manual processing:
  ```bash
  python manage.py process_videos --all
  ```

### Payment Testing
- Use Razorpay test credentials
- Test cards: https://razorpay.com/docs/payments/payment-methods/cards/test-cards/

### File Storage
- Media files are served from `/media/` URL
- Configure `MEDIA_ROOT` and `MEDIA_URL` in Django settings

## 🐛 Troubleshooting

### Common Issues
1. **401 Unauthorized**: Login first to get tokens
2. **403 Forbidden**: Check user permissions (student vs instructor)
3. **404 Not Found**: Verify IDs exist in database
4. **500 Server Error**: Check Django logs

### Debug Steps
1. Check server is running: `python manage.py runserver`
2. Verify database connections
3. Check CORS settings for frontend integration
4. Validate JWT token expiration

## 📞 Support

For API questions:
- Check Django REST Framework documentation
- Review error messages in response
- Check server logs for detailed errors

---

**Happy API Testing! 🎯**