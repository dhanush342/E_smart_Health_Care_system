import os
import django
import random
from datetime import datetime, date, time, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Disease.settings')
django.setup()

from django.contrib.auth.models import User, Group
from django.utils import timezone
from doctor.models import DoctorInfo
from appointment.models import AppointmentDetails
from patient.models import Disease1
from chat.models import UserProfile

# Ensure DOCTOR group exists
doctor_group, _ = Group.objects.get_or_create(name='DOCTOR')

SPECIALTIES = [
    {
        "dept": "Cardiology",
        "degrees": ["MBBS, MD (Cardiology)", "MBBS, DM (Cardiology)", "MBBS, DNB (Cardiology)"],
        "diseases": ["Heart Disease", "Chest Pain", "Hypertension", "Arrhythmia", "Heart Attack", "Coronary Artery Disease"]
    },
    {
        "dept": "Neurology",
        "degrees": ["MBBS, DM (Neurology)", "MBBS, MD (Neurology)", "MBBS, DNB (Neurology)"],
        "diseases": ["Migraine", "Stroke", "Epilepsy", "Parkinson Disease", "Brain Tumor", "Neuropathy"]
    },
    {
        "dept": "Pediatrics",
        "degrees": ["MBBS, MD (Pediatrics)", "MBBS, DCH, DNB (Pediatrics)"],
        "diseases": ["Childhood Asthma", "Measles", "Mumps", "Pediatric Fever", "Malnutrition", "Chickenpox"]
    },
    {
        "dept": "Orthopedics",
        "degrees": ["MBBS, MS (Orthopedics)", "MBBS, MCh (Orthopedics)", "MBBS, DNB (Orthopedics)"],
        "diseases": ["Bone Fracture", "Arthritis", "Joint Pain", "Osteoporosis", "Spinal Stenosis", "Ligament Tear"]
    },
    {
        "dept": "Dermatology",
        "degrees": ["MBBS, MD (Dermatology)", "MBBS, DDVL", "MBBS, DNB (Dermatology)"],
        "diseases": ["Acne", "Eczema", "Psoriasis", "Skin Allergy", "Fungal Infection", "Vitiligo"]
    },
    {
        "dept": "Oncology",
        "degrees": ["MBBS, MD, DM (Medical Oncology)", "MBBS, MS, MCh (Surgical Oncology)"],
        "diseases": ["Cancer", "Tumor", "Leukemia", "Lymphoma", "Breast Cancer", "Lung Cancer"]
    },
    {
        "dept": "Gastroenterology",
        "degrees": ["MBBS, DM (Gastroenterology)", "MBBS, DNB (Gastroenterology)"],
        "diseases": ["Gastritis", "Peptic Ulcer", "Liver Cirrhosis", "GERD", "Fatty Liver", "Jaundice"]
    },
    {
        "dept": "Pulmonology",
        "degrees": ["MBBS, MD (Pulmonary Medicine)", "MBBS, DTCD, DNB (Pulmonology)"],
        "diseases": ["Pneumonia", "Asthma", "COPD", "Bronchitis", "Tuberculosis", "Chronic Cough"]
    },
    {
        "dept": "Nephrology",
        "degrees": ["MBBS, DM (Nephrology)", "MBBS, DNB (Nephrology)"],
        "diseases": ["Kidney Stones", "Chronic Kidney Disease", "Renal Failure", "Urinary Infection", "Proteinuria"]
    },
    {
        "dept": "Endocrinology",
        "degrees": ["MBBS, DM (Endocrinology)", "MBBS, MD, DNB (Endocrinology)"],
        "diseases": ["Diabetes Mellitus", "Hypothyroidism", "Hyperthyroidism", "PCOS", "Obesity", "Hormonal Imbalance"]
    },
    {
        "dept": "Gynecology",
        "degrees": ["MBBS, MS (OBG)", "MBBS, DGO, DNB (OBG)"],
        "diseases": ["Pregnancy Care", "PCOS", "Fibroids", "Endometriosis", "Ovarian Cysts", "Infertility"]
    },
    {
        "dept": "Ophthalmology",
        "degrees": ["MBBS, MS (Ophthalmology)", "MBBS, DO, DNB (Ophthalmology)"],
        "diseases": ["Cataract", "Glaucoma", "Myopia", "Diabetic Retinopathy", "Dry Eye", "Conjunctivitis"]
    },
    {
        "dept": "ENT",
        "degrees": ["MBBS, MS (ENT)", "MBBS, DLO, DNB (ENT)"],
        "diseases": ["Sinusitis", "Tonsillitis", "Hearing Loss", "Otitis Media", "Tinnitus", "Deviated Septum"]
    },
    {
        "dept": "Psychiatry",
        "degrees": ["MBBS, MD (Psychiatry)", "MBBS, DPM, DNB (Psychiatry)"],
        "diseases": ["Depression", "Anxiety Disorder", "Bipolar Disorder", "Insomnia", "Panic Attacks", "Schizophrenia"]
    },
    {
        "dept": "General Medicine",
        "degrees": ["MBBS, MD (General Medicine)", "MBBS, DNB (Family Medicine)"],
        "diseases": ["Viral Fever", "Dengue", "Typhoid", "Malaria", "Hypertension", "Fatigue"]
    },
    {
        "dept": "Rheumatology",
        "degrees": ["MBBS, DM (Rheumatology)", "MBBS, MD, DNB (Rheumatology)"],
        "diseases": ["Rheumatoid Arthritis", "Lupus (SLE)", "Gout", "Ankylosing Spondylitis", "Fibromyalgia"]
    },
    {
        "dept": "Urology",
        "degrees": ["MBBS, MCh (Urology)", "MBBS, MS, DNB (Urology)"],
        "diseases": ["Prostate Enlargement", "Bladder Stones", "Urinary Incontinence", "Hematuria", "Erectile Dysfunction"]
    },
    {
        "dept": "Infectious Disease",
        "degrees": ["MBBS, MD (Infectious Diseases)", "MBBS, Fellowship (ID)"],
        "diseases": ["Viral Infection", "Bacterial Infection", "COVID-19", "Hepatitis", "Sepsis", "Cholera"]
    },
    {
        "dept": "Dental Surgery",
        "degrees": ["BDS, MDS (Oral & Maxillofacial)", "BDS, MDS (Orthodontics)"],
        "diseases": ["Tooth Decay", "Periodontitis", "Gingivitis", "Root Canal", "Wisdom Tooth Impaction"]
    },
    {
        "dept": "Radiology",
        "degrees": ["MBBS, MD (Radiodiagnosis)", "MBBS, DMRD, DNB (Radiology)"],
        "diseases": ["Diagnostic Imaging", "MRI Review", "CT Scan Analysis", "Ultrasound Analysis", "X-Ray Screening"]
    }
]

COLLEGES = [
    "All India Institute of Medical Sciences (AIIMS), New Delhi",
    "Madras Medical College (MMC), Chennai",
    "Christian Medical College (CMC), Vellore",
    "Stanley Medical College, Chennai",
    "King George's Medical University, Lucknow",
    "Grant Government Medical College, Mumbai",
    "Bangalore Medical College and Research Institute, Bangalore",
    "JIPMER, Puducherry",
    "Kasturba Medical College, Manipal",
    "Postgraduate Institute of Medical Education (PGIMER), Chandigarh",
    "Osmania Medical College, Hyderabad",
    "Calcutta Medical College, Kolkata",
    "B.J. Medical College, Ahmedabad",
    "Sri Ramachandra Institute of Higher Education, Chennai",
    "Government Medical College, Kozhikode"
]

CITIES_ADDRESSES = [
    "No. 12, Anna Salai, Chennai, Tamil Nadu",
    "No. 45, Mount Road, Guindy, Chennai, Tamil Nadu",
    "No. 18, Ramachandra Nagar, Porur, Chennai, Tamil Nadu",
    "Plot 88, Jubilee Hills, Hyderabad, Telangana",
    "Road No. 10, Banjara Hills, Hyderabad, Telangana",
    "No. 104, 100 Feet Road, Indiranagar, Bangalore, Karnataka",
    "Sector 4, HSR Layout, Bangalore, Karnataka",
    "No. 22, Brigade Road, Bangalore, Karnataka",
    "Dr. DN Road, Fort, Mumbai, Maharashtra",
    "Linking Road, Bandra West, Mumbai, Maharashtra",
    "FC Road, Shivajinagar, Pune, Maharashtra",
    "Koregaon Park, Pune, Maharashtra",
    "Connaught Place, Central Delhi, New Delhi",
    "Ring Road, Lajpat Nagar, New Delhi, New Delhi",
    "Park Street, Central Kolkata, West Bengal",
    "Salt Lake Sector V, Kolkata, West Bengal",
    "MG Road, Ernakulam, Kochi, Kerala",
    "Banjara Hills, Somajiguda, Hyderabad, Telangana",
    "Velachery Main Road, Chennai, Tamil Nadu",
    "Kothrud, Paud Road, Pune, Maharashtra"
]

FIRST_NAMES_MALE = [
    "Aarav", "Aditya", "Ajay", "Alok", "Amit", "Anand", "Anil", "Arjun", "Arun", "Ashok",
    "Bharat", "Bhavesh", "Chetan", "Deepak", "Devendra", "Dinesh", "Ganesh", "Gautam", "Girish", "Harish",
    "Hemant", "Jagdish", "Jayant", "Jitendra", "Kailash", "Kamal", "Karthik", "Kishore", "Krishna", "Kuldeep",
    "Madhav", "Mahesh", "Manish", "Manoj", "Mukesh", "Naresh", "Naveen", "Nikhil", "Nilesh", "Nitin",
    "Pankaj", "Pradeep", "Prakash", "Prashant", "Praveen", "Prem", "Raghav", "Rahul", "Rajesh", "Rakesh",
    "Ramesh", "Ravi", "Rohit", "Sachin", "Sameer", "Sanjay", "Santosh", "Satish", "Shailesh", "Shankar",
    "Sharad", "Subhash", "Sudarshan", "Sujit", "Sunder", "Sunil", "Suresh", "Tarun", "Umesh", "Varun",
    "Vijay", "Vikas", "Vikram", "Vinay", "Vinod", "Vipul", "Virendra", "Vishal", "Vivek", "Yogesh"
]

FIRST_NAMES_FEMALE = [
    "Aadhya", "Aarti", "Aditi", "Alka", "Amrita", "Ananya", "Anita", "Anjali", "Ankita", "Archana",
    "Asha", "Bhavna", "Chitra", "Deepa", "Deepika", "Divya", "Geeta", "Gayatri", "Indira", "Jaya",
    "Jyoti", "Kalyani", "Kamla", "Kavita", "Kiran", "Komal", "Lata", "Madhavi", "Malini", "Mamta",
    "Manju", "Meena", "Meera", "Mona", "Namrata", "Neelam", "Neha", "Nidhi", "Nirmala", "Nisha",
    "Pallavi", "Pooja", "Poonam", "Prabha", "Pratibha", "Preeti", "Priya", "Radha", "Rajni", "Rakhi",
    "Rashmi", "Rekha", "Renu", "Ritu", "Roopa", "Ruchi", "Sadhana", "Sandhya", "Sangeeta", "Sarita",
    "Seema", "Shalini", "Sharda", "Sheetal", "Shikha", "Shilpa", "Shobha", "Shruti", "Sneha", "Sonia",
    "Subhashini", "Sudha", "Sujata", "Sunita", "Sushma", "Swati", "Tanvi", "Usha", "Vandana", "Varsha"
]

LAST_NAMES = [
    "Agarwal", "Bose", "Chakraborty", "Chauhan", "Chopra", "Das", "Deshmukh", "Dey", "Dubey", "Dutta",
    "Gandhi", "Ghosh", "Gupta", "Iyer", "Jadhav", "Jain", "Jha", "Joshi", "Kapoor", "Khan",
    "Khanna", "Kulkarni", "Kumar", "Malhotra", "Mehta", "Mishra", "Mukherjee", "Nair", "Nagineni", "Pandey",
    "Patel", "Patil", "Pillai", "Prasad", "Purohit", "Rao", "Reddy", "Roy", "Sahani", "Sarin",
    "Saxena", "Sen", "Seth", "Shah", "Sharma", "Shetty", "Shukla", "Singh", "Sinha", "Soni",
    "Srivastava", "Subramanian", "Tewari", "Thakur", "Trivedi", "Varma", "Verma", "Vyas", "Yadav"
]

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

TIME_SLOTS = [
    (time(9, 0), time(10, 30)),
    (time(10, 30), time(12, 0)),
    (time(14, 0), time(15, 30)),
    (time(15, 30), time(17, 0)),
    (time(17, 0), time(18, 30)),
    (time(18, 30), time(20, 0))
]

def seed(total_doctors_to_add=105):
    print(f"Starting seed of {total_doctors_to_add} doctors...")
    current_count = DoctorInfo.objects.count()
    print(f"Current doctors in DB: {current_count}")

    created_doctors = 0
    created_appointments = 0
    created_diseases = 0

    base_doc_id_num = 1002
    existing_doc_ids = set(DoctorInfo.objects.values_list('doctorID', flat=True))

    for i in range(1, total_doctors_to_add + 1):
        # Determine unique doc id
        while f"DOC-{base_doc_id_num}" in existing_doc_ids:
            base_doc_id_num += 1
        doctor_id_str = f"DOC-{base_doc_id_num}"
        existing_doc_ids.add(doctor_id_str)

        # Gender & Name
        is_female = (i % 2 == 0)
        gender = "Female" if is_female else "Male"
        first_name = FIRST_NAMES_FEMALE[(i * 7) % len(FIRST_NAMES_FEMALE)] if is_female else FIRST_NAMES_MALE[(i * 7) % len(FIRST_NAMES_MALE)]
        last_name = LAST_NAMES[(i * 11) % len(LAST_NAMES)]

        username = f"dr_{first_name.lower()}_{last_name.lower()}_{base_doc_id_num}"
        email = f"dr.{first_name.lower()}.{last_name.lower()}{base_doc_id_num}@ehealthcare.com"

        # Specialty
        spec_data = SPECIALTIES[i % len(SPECIALTIES)]
        department = spec_data["dept"]
        education_degree = spec_data["degrees"][i % len(spec_data["degrees"])]
        college = COLLEGES[i % len(COLLEGES)]
        address = CITIES_ADDRESSES[i % len(CITIES_ADDRESSES)]
        phone_number = f"+91984{base_doc_id_num:07d}"[-13:] # Ensure length 13 e.g. +919840001002
        if not phone_number.startswith('+91'):
            phone_number = f"+91949{i:06d}"

        grad_year = 2000 + (i % 21) # 2000 to 2020
        education_year = timezone.make_aware(datetime(grad_year, 6, 15, 0, 0))

        # Create User
        user, user_created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'is_active': True
            }
        )
        if user_created:
            user.set_password("doctor123")
            user.save()

        # Add to DOCTOR group
        doctor_group.user_set.add(user)

        # Create UserProfile for chat
        UserProfile.objects.get_or_create(user=user)

        # Create DoctorInfo
        doc_info, doc_created = DoctorInfo.objects.get_or_create(
            user=user,
            defaults={
                'address': address,
                'phone_number': phone_number,
                'department': department,
                'gender': gender,
                'doctorID': doctor_id_str,
                'education_college': college,
                'education_degree': education_degree,
                'education_year': education_year
            }
        )

        if doc_created:
            created_doctors += 1

        # Add 3-4 Appointment Details (Timings & Schedule)
        # Select 2 to 4 days for this doctor
        num_slots = 3 + (i % 2) # 3 or 4 slots
        assigned_days = random.sample(DAYS, k=min(num_slots, len(DAYS)))
        
        # Calculate dates for upcoming appointments
        today = timezone.now().date()
        for slot_idx, day_name in enumerate(assigned_days):
            slot_time_start, slot_time_end = TIME_SLOTS[(i + slot_idx) % len(TIME_SLOTS)]
            
            # Find next occurrence of that weekday
            day_target_index = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(day_name)
            current_day_index = today.weekday()
            days_ahead = (day_target_index - current_day_index) % 7
            if days_ahead == 0:
                days_ahead = 7
            target_date = today + timedelta(days=days_ahead + (7 * (slot_idx % 2)))
            appointment_datetime = timezone.make_aware(datetime.combine(target_date, slot_time_start))

            # Create AppointmentDetails
            appt, appt_created = AppointmentDetails.objects.get_or_create(
                create_by=doc_info,
                appointment_day=day_name,
                appointment_start_time=slot_time_start,
                appointment_end_time=slot_time_end,
                defaults={
                    'appointment_date': appointment_datetime,
                    'appointment_status': 0
                }
            )
            if appt_created:
                created_appointments += 1

        # Link relevant diseases in Disease1
        for d_name in spec_data["diseases"][:3]: # Add top 3 conditions
            d_obj, d_created = Disease1.objects.get_or_create(
                name=d_name,
                doctor=doc_info
            )
            if d_created:
                created_diseases += 1

    final_count = DoctorInfo.objects.count()
    final_appt_count = AppointmentDetails.objects.count()
    print("--------------------------------------------------")
    print(f"SUCCESS: Seed Completed!")
    print(f"Total Doctors in DB: {final_count} (Newly added: {created_doctors})")
    print(f"Total Appointment Timings in DB: {final_appt_count} (Newly added: {created_appointments})")
    print(f"Total Disease Mappings in DB: {Disease1.objects.count()} (Newly added: {created_diseases})")
    print("--------------------------------------------------")

if __name__ == '__main__':
    seed(105)
