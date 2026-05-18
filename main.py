from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

# 🚀 সব ডাটাবেজ কোয়েরি একসাথে এক লাইনে ইমপোর্ট করা হলো (ওভাররাইড ফিক্স)
from database.queries import (
    get_user_by_email, 
    get_all_students, 
    get_total_counts, 
    enroll_student,
    delete_student_by_id,
    register_user, 
    get_all_teachers,
    get_all_batches,
    create_batch,
    get_all_schedules,
    create_schedule
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
    enroll_student(email, password, full_name, phone)
    
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


# ৫. স্টুডেন্ট লিস্ট পেজ (GET)
@app.get("/students", response_class=HTMLResponse)
async def view_students_page(request: Request):
    all_students = get_all_students()
    return templates.TemplateResponse(
        request=request, 
        name="students_list.html", 
        context={"request": request, "students": all_students}
    )


# স্টুডেন্ট ডিলিট অ্যাকশন (GET)
@app.get("/delete_student/{student_id}")
async def delete_student_action(request: Request, student_id: int):
    delete_student_by_id(student_id)
    return RedirectResponse(url="/students", status_code=303)


# ৬. টিচার লিস্ট পেজ (GET)
@app.get("/teachers", response_class=HTMLResponse)
async def view_teachers_page(request: Request):
    all_teachers = get_all_teachers()
    return templates.TemplateResponse(
        request=request, 
        name="teachers_list.html", 
        context={"request": request, "teachers": all_teachers}
    )


# টিচার অ্যাড অ্যাকশন (POST)
@app.post("/add_teacher")
async def add_teacher_action(request: Request, email: str = Form(...), password: str = Form(...)):
    register_user(email, password, "teacher")
    return RedirectResponse(url="/teachers", status_code=303)

# ৮. ব্যাচ লিস্ট পেজ (GET)
@app.get("/batches", response_class=HTMLResponse)
async def view_batches_page(request: Request):
    """সব ব্যাচ দেখার এবং নতুন ব্যাচ তৈরির পেজ।"""
    all_batches = get_all_batches()
    all_teachers = get_all_teachers() # ফর্মে ড্রপডাউন দেখানোর জন্য টিচারদের লিস্টও লাগবে
    return templates.TemplateResponse(
        request=request, 
        name="batches_list.html", # আমরা পরের ধাপে এই ফাইলটি বানাচ্ছি
        context={"request": request, "batches": all_batches, "teachers": all_teachers}
    )

# ব্যাচ অ্যাড করার অ্যাকশন (POST)
@app.post("/add_batch")
async def add_batch_action(request: Request, batch_name: str = Form(...), teacher_id: int = Form(...)):
    create_batch(batch_name, teacher_id)
    return RedirectResponse(url="/batches", status_code=303)


#
# ৯. শিডিউল লিস্ট পেজ (GET)
@app.get("/schedules", response_class=HTMLResponse)
async def view_schedules_page(request: Request):
    """সব ক্লাসের রুটিন দেখার এবং নতুন শিডিউল তৈরির পেজ।"""
    all_schedules = get_all_schedules()
    all_batches = get_all_batches() # ফর্মে দেখানোর জন্য সব ব্যাচের লিস্টও লাগবে
    return templates.TemplateResponse(
        request=request, 
        name="schedules_list.html", # আমরা পরের ধাপে এই ফাইলটি বানাচ্ছি
        context={"request": request, "schedules": all_schedules, "batches": all_batches}
    )

# শিডিউল অ্যাড করার অ্যাকশন (POST)
@app.post("/add_schedule")
async def add_schedule_action(
    request: Request, 
    batch_id: int = Form(...), 
    class_time: str = Form(...), 
    room_number: str = Form(...)
):
    create_schedule(batch_id, class_time, room_number)
    return RedirectResponse(url="/schedules", status_code=303)

# ১০. ড্যাশবোর্ড লিঙ্ক ফিক্স করার জন্য নতুন রাউট (GET)
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect(request: Request):
    """সাইডবারের ড্যাশবোর্ডে ক্লিক করলে এটি ডাটা লোড করে অ্যাডমিন ড্যাশবোর্ড দেখাবে।"""
    all_students = get_all_students()
    counts = get_total_counts()
    
    return templates.TemplateResponse(
        request=request, 
        name="dashboard_admin.html", 
        context={
            "user_email": "Admin", # সেশন না থাকা পর্যন্ত আমরা ডিফল্ট 'Admin' দেখাচ্ছি
            "role": "admin", 
            "students": all_students, 
            "student_count": counts["students"],
            "batch_count": counts["batches"],  
            "teacher_count": counts["teachers"]
        }
    )

# 🚀 সার্ভার রান
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
