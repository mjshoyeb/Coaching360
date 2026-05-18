from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

# ডাটাবেজ এবং সিকিউরিটি মডিউল ইমপোর্ট
from database.queries import (
    get_user_by_email, 
    get_all_students, 
    get_total_counts, 
    enroll_student
)
from core.auth import verify_password

app = FastAPI()

# ১. কনফিগারেশন
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ২. লগইন পেজ (GET)
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")


# ৩. লগইন অ্যাকশন (POST)
@app.post("/login")
async def login_action(request: Request, email: str = Form(...), password: str = Form(...)):
    user = get_user_by_email(email)
    
    if user and verify_password(password, user['password_hash']):
        # ড্যাশবোর্ডের সব তথ্য সংগ্রহ
        all_students = get_all_students()
        counts = get_total_counts()

        return templates.TemplateResponse(
            request=request, 
            name="dashboard_admin.html", 
            context={
                "user_email": email, 
                "role": user['role'], 
                "students": all_students, 
                "student_count": counts["students"],
                "batch_count": counts["batches"],  
                "teacher_count": counts["teachers"]
            }
        )
    
    # ভুল লগইন হলে এরর মেসেজসহ ফেরত পাঠানো
    return templates.TemplateResponse(
        request=request, 
        name="login.html", 
        context={"error": "Invalid Email or Password!"}
    )


# ৪. নতুন স্টুডেন্ট যোগ করা (POST)
@app.post("/add_student")
async def add_student_action(
    request: Request, 
    full_name: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...), 
    phone: str = Form(...)
):
    # ডাটাবেজে স্টুডেন্ট ভর্তি করা
    enroll_student(email, password, full_name, phone)
    
    # নোট: প্রোফেশনাল অ্যাপে এখানে সেশন ব্যবহার করা হয়। 
    # আপাতত আমরা ডাটা লোড করে সরাসরি ড্যাশবোর্ড টেমপ্লেটটি আবার রিটার্ন করছি।
    all_students = get_all_students()
    counts = get_total_counts()
    
    return templates.TemplateResponse(
        request=request, 
        name="dashboard_admin.html", 
        context={
            "user_email": "Admin", 
            "role": "admin", 
            "students": all_students, 
            "student_count": counts["students"],
            "batch_count": counts["batches"],
            "teacher_count": counts["teachers"],
            "success_msg": "Student enrolled successfully!" 
        }
    )


# ৫. সার্ভার রান
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)