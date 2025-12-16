# E-Learning Backend API Endpoints

Complete list of all API endpoints with methods, URLs, and descriptions.

## 🔐 Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/users/register/` | Register new user |
| POST | `/api/users/login/` | User login (JWT tokens) |
| POST | `/api/users/logout/` | Logout user |
| POST | `/api/token/refresh/` | Refresh access token |

## 👤 User Profile Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/profile/` | Get current user profile |
| PATCH | `/api/users/profile/` | Update user profile |
| DELETE | `/api/users/profile/` | Delete user account |
| PATCH | `/api/users/profile/image/` | Upload profile image |
| GET | `/api/users/profile/{user_id}/` | Get public profile |
| POST | `/api/users/profile/change-password/` | Change password |
| GET | `/api/users/profile/statistics/` | Get user statistics |

## 📂 Category Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories/` | List all categories |
| POST | `/api/categories/` | Create category (admin) |
| GET | `/api/categories/{id}/` | Get category details |
| PUT | `/api/categories/{id}/` | Update category (admin) |
| DELETE | `/api/categories/{id}/` | Delete category (admin) |

## 📚 Course Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/courses/courses/` | List all courses |
| POST | `/api/courses/courses/` | Create course (instructor) |
| GET | `/api/courses/courses/{id}/` | Get course details |
| PUT | `/api/courses/courses/{id}/` | Update course (instructor) |
| DELETE | `/api/courses/courses/{id}/` | Delete course (instructor) |
| POST | `/api/courses/courses/{id}/enroll/` | Enroll in course |
| POST | `/api/courses/courses/{id}/review/` | Add course review |

## 🎬 Course Content Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/courses/{course_id}/sections/` | Get course sections |
| POST | `/api/courses/{course_id}/sections/` | Create section (instructor) |
| GET | `/api/courses/{course_id}/sections/{section_id}/lectures/` | Get section lectures |
| POST | `/api/courses/{course_id}/sections/{section_id}/lectures/` | Create lecture (instructor) |
| GET | `/api/courses/{course_id}/sections/{section_id}/lectures/{lecture_id}/` | Get lecture details |
| PUT | `/api/courses/{course_id}/sections/{section_id}/lectures/{lecture_id}/` | Update lecture (instructor) |
| DELETE | `/api/courses/{course_id}/sections/{section_id}/lectures/{lecture_id}/` | Delete lecture (instructor) |
| GET | `/api/courses/enrollments/` | Get user enrollments |
| POST | `/api/progress/{progress_id}/update_progress/` | Update video progress |

## 🛒 Shopping Cart Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/shopping/cart/get_cart_summary/` | Get cart summary |
| POST | `/api/shopping/cart/add/` | Add course to cart |
| POST | `/api/shopping/cart/remove/` | Remove from cart |
| POST | `/api/shopping/cart/save_for_later/` | Save item for later |
| POST | `/api/shopping/cart/move_to_cart/` | Move saved item to cart |
| POST | `/api/shopping/cart/apply_coupon/` | Apply discount coupon |
| POST | `/api/shopping/cart/remove_coupon/` | Remove coupon |
| POST | `/api/shopping/cart/clear_cart/` | Clear entire cart |
| GET | `/api/shopping/cart/get_saved_items/` | Get saved items |

## ❤️ Wishlist Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/shopping/wishlist/` | Get user wishlist |
| POST | `/api/shopping/wishlist/add_course/` | Add to wishlist |
| POST | `/api/shopping/wishlist/remove_course/` | Remove from wishlist |
| POST | `/api/shopping/wishlist/move_to_cart/` | Move to cart from wishlist |
| GET | `/api/shopping/course-status/{course_id}/` | Check course status |

## 💳 Payment Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/single/create/` | Create single course payment |
| POST | `/api/payments/single/verify/` | Verify single course payment |
| POST | `/api/payments/multi/create/` | Create multi-course payment |
| POST | `/api/payments/multi/verify/` | Verify multi-course payment |

## ⚙️ Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/core/sliders/` | Get slider images |
| GET | `/api/core/app-versions/` | Get app version info |
| GET | `/health/` | Server health check |

## 🔧 Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/` | Django admin panel |
| Various | `/admin/*` | Admin panel operations |

---

## 📋 Authentication Headers

All protected endpoints require:
```
Authorization: Bearer {access_token}
```

## 📝 Content Types

- **JSON Data**: `Content-Type: application/json`
- **File Upload**: `Content-Type: multipart/form-data`

## 🎯 Response Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **500**: Server Error

## 🔄 Data Flow Examples

### Student Purchase Flow
1. `GET /api/courses/courses/` - Browse courses
2. `POST /api/shopping/cart/add/` - Add to cart
3. `GET /api/shopping/cart/get_cart_summary/` - Review cart
4. `POST /api/payments/single/create/` - Create payment
5. `POST /api/payments/single/verify/` - Verify payment
6. `GET /api/courses/1/sections/` - Access course content

### Instructor Course Creation
1. `POST /api/courses/courses/` - Create course
2. `POST /api/courses/1/sections/` - Add sections
3. `POST /api/courses/1/sections/1/lectures/` - Add lectures
4. `GET /api/users/profile/statistics/` - Check analytics

---

**Complete API reference for your Udemy-like platform! 🚀**

