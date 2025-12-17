# Payment Gateway Testing Guide

## 🔗 API Endpoints

1. **Create Payment Order**: `POST /api/payments/create/`
2. **Verify Payment**: `POST /api/payments/verify/`

---

## 📋 Step-by-Step Testing

### Step 1: Get JWT Token (Login)

```bash
curl -X POST http://127.0.0.1:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "p@gmail.com",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Save the `access` token for next steps!**

---

### Step 2: Create Payment Order

```bash
curl -X POST http://127.0.0.1:8000/api/payments/create/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "course_id": 1,
    "amount": "999.00",
    "currency": "INR"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Payment order created successfully",
  "data": {
    "order_id": "order_MN1234567890",
    "amount": "999.00",
    "currency": "INR",
    "key": "rzp_test_MGr4dvkOY66fMO",
    "course_id": 1,
    "course_title": "Course Name"
  }
}
```

**Save the `order_id` for Razorpay payment!**

---

### Step 3: Test Payment with Razorpay

1. Go to Razorpay Test Dashboard or use Razorpay Checkout
2. Use the `order_id` and `key` from Step 2
3. **Test Card Details:**
   - Card Number: `4111 1111 1111 1111`
   - CVV: Any 3 digits (e.g., `123`)
   - Expiry: Any future date (e.g., `12/25`)
   - Name: Any name

4. Complete the payment on Razorpay
5. You'll get:
   - `razorpay_payment_id`
   - `razorpay_signature`

---

### Step 4: Verify Payment

```bash
curl -X POST http://127.0.0.1:8000/api/payments/verify/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "razorpay_order_id": "order_MN1234567890",
    "razorpay_payment_id": "pay_MN1234567890",
    "razorpay_signature": "abc123def456..."
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "Payment verified and course enrolled successfully",
  "data": {
    "payment_id": 1,
    "order_id": "order_MN1234567890",
    "status": "completed",
    "course_id": 1,
    "course_title": "Course Name",
    "actions_taken": {
      "enrolled": true,
      "removed_from_cart": true,
      "removed_from_wishlist": true
    }
  }
}
```

---

## 🧪 Quick Test Script

Run this Python script to test:

```bash
python test_payment.py
```

---

## ✅ What to Check

1. **Payment Order Creation:**
   - ✅ Order ID is generated
   - ✅ Payment record created in database
   - ✅ Status is "pending"

2. **Payment Verification:**
   - ✅ Signature verification works
   - ✅ Payment status updated to "completed"
   - ✅ User enrolled in course
   - ✅ Course removed from cart (if exists)
   - ✅ Course removed from wishlist (if exists)

3. **Database Check:**
   ```python
   from payments.models import Payment
   from courses.models import Enrollment
   
   # Check payments
   Payment.objects.all()
   
   # Check enrollments
   Enrollment.objects.all()
   ```

---

## 🔍 Troubleshooting

### Error: "Course not found"
- Make sure course exists in database
- Check course_id is correct

### Error: "You already own this course"
- User is already enrolled
- Check Enrollment model

### Error: "Invalid signature"
- Make sure you're using correct payment_id, order_id, and signature
- Signature must match Razorpay's verification

### Error: "Payment record not found"
- Order ID doesn't exist in database
- Make sure you created payment order first

---

## 📝 Notes

- Use **test mode** Razorpay keys (already configured)
- Test card: `4111 1111 1111 1111`
- All amounts in **paise** (₹1 = 100 paise)
- JWT token expires in 60 minutes

