import qrcode
import os

def generate_student_qr(qr_uid: str):
    """
    স্টুডেন্টের ইউনিক আইডি (qr_uid) নিয়ে একটি QR কোড ইমেজ তৈরি করে
    এবং সেটি static/qrcodes/ ফোল্ডারে সেভ করে।
    """
    # ১. QR কোডের কনফিগারেশন সেট করা
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # ২. QR কোডের ভেতরে আমরা স্টুডেন্টের ইউনিক আইডিটি লুকিয়ে রাখব
    qr.add_data(qr_uid)
    qr.make(fit=True)

    # 🎨 ৩. QR কোডের কালার সেট করে ইমেজ তৈরি করা
    img = qr.make_image(fill_color="black", back_color="white")
    
    # ৪. ইমেজটি সেভ করার জন্য ফোল্ডার তৈরি আছে কিনা চেক করা
    output_dir = "static/qrcodes"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # 💾 ৫. ফাইলের নাম হবে স্টুডেন্টের qr_uid অনুযায়ী (যেমন: abc12345.png)
    file_path = f"{output_dir}/{qr_uid}.png"
    img.save(file_path)
    
    print(f"🎯 QR Code generated successfully at: {file_path}")
    return file_path