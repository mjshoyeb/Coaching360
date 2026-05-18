from database.db_handler import get_db_connection
from core.auth import hash_password

def register_user(email: str, password: str, role: str):
    """নতুন ইউজার তৈরি করে ডেটাবেজে সেভ করে।"""
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        # পাসওয়ার্ডটি সেভ করার আগে হ্যাশ করে নেওয়া হচ্ছে
        hashed_pass = hash_password(password)
        
        query = "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)"
        values = (email, hashed_pass, role)
        
        try:
            cursor.execute(query, values)
            conn.commit() # ডেটাবেজে পরিবর্তন সেভ করা
            print(f"User {email} registered successfully!")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            cursor.close()
            conn.close()


import uuid # QR কোডের জন্য ইউনিক আইডি জেনারেট করতে
from core.qr_generator import generate_student_qr # QR কোড জেনারেট করার ফাংশন ইমপোর্ট করা হচ্ছে

def enroll_student(email: str, password: str, full_name: str, phone: str):
    conn = get_db_connection()
    if not conn: return

    cursor = conn.cursor()
    try:
        # ১. ট্রানজেকশন শুরু
        conn.start_transaction()

        # ২. ইউজার টেবিলে অ্যাকাউন্ট তৈরি
        hashed_pass = hash_password(password)
        user_query = "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'student')"
        cursor.execute(user_query, (email, hashed_pass))
        
        # সদ্য তৈরি হওয়া ইউজারের ID নেওয়া
        user_id = cursor.lastrowid

        # ৩. স্টুডেন্ট টেবিলে ডাটা ইনসার্ট (QR এর জন্য একটি র‍্যান্ডম কি তৈরি করা হচ্ছে)
        qr_uid = str(uuid.uuid4())[:8] # জাস্ট ৮ অক্ষরের ইউনিক আইডি
        student_query = """
            INSERT INTO students (user_id, full_name, phone, qr_code_uid) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(student_query, (user_id, full_name, phone, qr_uid))

        # ৪. ডাটাবেজে সবকিছু ঠিক থাকলে সেভ করো (Commit)
        conn.commit()
        print(f"✅ Success: Student {full_name} enrolled and account created!")

        # 🚀 ৫. ডাটাবেজে সেভ হওয়ার পর আসল QR Code ইমেজটি জেনারেট করা হচ্ছে
        generate_student_qr(qr_uid)

    except Exception as e:
        # কোনো ভুল হলে আগের সব কাজ বাতিল করো (Rollback)
        conn.rollback()
        print(f"❌ Error during enrollment: {e}")
    finally:
        cursor.close()
        conn.close()

def check_schedule_conflict(room_no: str, day: str, start_time: str, end_time: str, teacher_id: int) -> bool:
    """
    একই সময়ে একই রুমে বা একই টিচারের অন্য ক্লাস আছে কিনা চেক করে।
    যদি কনফ্লিক্ট থাকে তবে True রিটার্ন করে।
    """
    conn = get_db_connection()
    if not conn: return True

    cursor = conn.cursor()
    # লজিক: এমন কোনো ক্লাস আছে কি যার সময় আমাদের ইনপুট সময়ের সাথে ওভারল্যাপ করে?
    query = """
        SELECT id FROM schedules 
        WHERE day_of_week = %s 
        AND (
            (room_no = %s AND (%s < end_time AND %s > start_time)) 
            OR 
            (batch_id IN (SELECT id FROM batches WHERE teacher_id = %s) AND (%s < end_time AND %s > start_time))
        )
    """
    # নোট: (%s < end_time AND %s > start_time) হলো ওভারল্যাপ চেক করার ম্যাথমেটিক্যাল লজিক
    values = (day, room_no, start_time, end_time, teacher_id, start_time, end_time)
    
    cursor.execute(query, values)
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return result is not None # রেজাল্ট থাকলে কনফ্লিক্ট আছে (True)

def add_schedule(batch_id: int, room_no: str, day: str, start: str, end: str):
    """
    নতুন শিডিউল যোগ করার আগে কনফ্লিক্ট চেক করে এবং ডাটাবেজে সেভ করে।
    """
    # ১. প্রথমে এই ব্যাচের টিচার কে তা খুঁজে বের করি (কনফ্লিক্ট চেকের জন্য)
    conn = get_db_connection()
    if not conn: return
    
    cursor = conn.cursor()
    try:
        # ব্যাচ টেবিল থেকে টিচার আইডি নেওয়া
        cursor.execute("SELECT teacher_id FROM batches WHERE id = %s", (batch_id,))
        teacher_result = cursor.fetchone()
        
        if not teacher_result:
            print("❌ Error: Batch not found!")
            return
        
        teacher_id = teacher_result[0]

        # ২. কনফ্লিক্ট চেক করা (আমরা আগেই এই ফাংশনটি লিখেছি)
        if check_schedule_conflict(room_no, day, start, end, teacher_id):
            print(f"⚠️ Conflict! Room {room_no} or Teacher is already busy on {day} from {start} to {end}.")
        else:
            # ৩. কোনো কনফ্লিক্ট নেই, এখন ডাটা সেভ করো
            insert_query = """
                INSERT INTO schedules (batch_id, room_no, day_of_week, start_time, end_time) 
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (batch_id, room_no, day, start, end))
            conn.commit()
            print(f"✅ Success: Class scheduled for Batch {batch_id} in Room {room_no} on {day}.")

    except Exception as e:
        print(f"❌ Database Error: {e}")
    finally:
        cursor.close()
        conn.close()

# ইউজারকে ইমেইল দিয়ে ডেটাবেজ থেকে খুঁজে বের করে রিটার্ন করে
def get_user_by_email(email: str):
    conn = get_db_connection()
    if not conn: return None
    
    cursor = conn.cursor(dictionary=True) 
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    
    cursor.close()
    conn.close()
    return user

# সব স্টুডেন্টের ডেটা নিয়ে আসে (এডমিন প্যানেলে দেখানোর জন্য)
def get_all_students():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        return students # এটি একটি লিস্ট রিটার্ন করবে
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

# ড্যাশবোর্ডে মোট স্টুডেন্ট, ব্যাচ এবং টিচারের সংখ্যা দেখানোর জন্য একটি ফাংশন
def get_total_counts():
    """ডাটাবেজ থেকে স্টুডেন্ট, ব্যাচ এবং টিচারের মোট সংখ্যা গুনে আনে।"""
    conn = get_db_connection()
    counts = {"students": 0, "batches": 0, "teachers": 0}
    
    if conn:
        cursor = conn.cursor()
        # স্টুডেন্ট সংখ্যা
        cursor.execute("SELECT COUNT(*) FROM students")
        counts["students"] = cursor.fetchone()[0]
        
        # ব্যাচ সংখ্যা
        cursor.execute("SELECT COUNT(*) FROM batches")
        counts["batches"] = cursor.fetchone()[0]
        
        # টিচার সংখ্যা (যাদের রোল 'teacher')
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
        counts["teachers"] = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
    return counts