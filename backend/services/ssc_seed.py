"""
Starting SSC data for Aspirixa (Phase 2).

IMPORTANT - how trustworthy is this data?
  * Dates, vacancies and notice dates were collected on 3 Nov 2026 from
    education websites that report SSC notices. They are marked
    verification = "secondary".
  * ssc.gov.in itself could not be read from the build environment.
    Phase 3 (automatic sync) will read the official site and upgrade
    records to verification = "official".
  * Anything we could not find is left as None, and the screen shows
    "Not announced yet". Nothing is guessed.
  * The seed will NEVER overwrite a record that has already been
    upgraded to "official".
"""
from datetime import date

from database.models import SSCExam, SSCNotification

VERIFIED_ON = date(2026, 11, 3)
OFFICIAL_SITE = "https://ssc.gov.in/"
APPLY_URL = "https://ssc.gov.in/login"

PATTERN_NOTE = (
    "Standard Tier 1 pattern followed in recent SSC notifications. "
    "It will be re-checked against the 2026 notification PDF when "
    "automatic sync is added."
)
TIER2_PENDING = (
    "Detailed Tier 2 pattern has not been verified yet. It will be added "
    "from the official notification."
)


# ----------------------------------------------------------------------
# Exams
# ----------------------------------------------------------------------
EXAMS = [
    {
        "code": "CGL",
        "name": "SSC CGL",
        "full_name": "Combined Graduate Level Examination",
        "description": (
            "Recruitment to many Group B and Group C posts in central "
            "government ministries, departments and offices. Open to graduates."
        ),
        "qualification": (
            "Bachelor's degree from a recognised university or equivalent. "
            "Some posts need extra qualifications (for example, statistics "
            "posts may need Mathematics or Statistics, and accounts or audit "
            "posts may need CA, CMA, CS, commerce or MBA). Check the post-wise "
            "details in the notification."
        ),
        "age_limit": (
            "Usually 18 to 27 years, but some posts allow up to 30 or 32 years. "
            "The exact range for each post is given in the notification."
        ),
        "age_relaxation": (
            "Standard Government of India relaxation applies "
            "(SC/ST 5 years, OBC 3 years, PwBD 10 years, plus ex-servicemen "
            "and other categories). Check the notification for exact rules."
        ),
        "pattern": [
            {
                "tier": "Tier 1",
                "mode": "Computer Based Examination (CBE)",
                "qualifying": True,
                "sections": [
                    {"subject": "General Intelligence and Reasoning", "questions": 25, "marks": 50},
                    {"subject": "General Awareness", "questions": 25, "marks": 50},
                    {"subject": "Quantitative Aptitude", "questions": 25, "marks": 50},
                    {"subject": "English Comprehension", "questions": 25, "marks": 50},
                ],
                "total_questions": 100,
                "total_marks": 200,
                "duration_minutes": 60,
                "negative_marking": "0.50 mark deducted for each wrong answer",
                "notes": PATTERN_NOTE,
            },
            {
                "tier": "Tier 2",
                "mode": "Computer Based Examination (CBE)",
                "qualifying": False,
                "sections": [],
                "total_questions": None,
                "total_marks": None,
                "duration_minutes": None,
                "negative_marking": None,
                "notes": TIER2_PENDING,
            },
        ],
        "official_url": OFFICIAL_SITE,
        "data_status": "available",
        "sources": [
            {"name": "SSC official website", "url": OFFICIAL_SITE},
        ],
        "last_verified": VERIFIED_ON,
    },
    {
        "code": "CHSL",
        "name": "SSC CHSL",
        "full_name": "Combined Higher Secondary (10+2) Level Examination",
        "description": (
            "Recruitment to Lower Divisional Clerk (LDC), Junior Secretariat "
            "Assistant (JSA) and Data Entry Operator (DEO) posts. "
            "Open to candidates who have passed class 12."
        ),
        "qualification": (
            "12th Standard pass from a recognised board. Some posts need a "
            "specific stream (for example Science with Mathematics for certain "
            "Data Entry Operator posts). Check the notification."
        ),
        "age_limit": "18 to 27 years (age counted as on 1 August 2026 for the 2026 exam).",
        "age_relaxation": (
            "Standard Government of India relaxation applies "
            "(SC/ST 5 years, OBC 3 years, PwBD 10 years, plus ex-servicemen "
            "and other categories). Check the notification for exact rules."
        ),
        "pattern": [
            {
                "tier": "Tier 1",
                "mode": "Computer Based Examination (CBE)",
                "qualifying": True,
                "sections": [
                    {"subject": "General Intelligence", "questions": 25, "marks": 50},
                    {"subject": "English Language", "questions": 25, "marks": 50},
                    {"subject": "Quantitative Aptitude", "questions": 25, "marks": 50},
                    {"subject": "General Awareness", "questions": 25, "marks": 50},
                ],
                "total_questions": 100,
                "total_marks": 200,
                "duration_minutes": 60,
                "negative_marking": "0.50 mark deducted for each wrong answer",
                "notes": PATTERN_NOTE,
            },
            {
                "tier": "Tier 2",
                "mode": "Computer Based Examination (CBE)",
                "qualifying": False,
                "sections": [],
                "total_questions": None,
                "total_marks": None,
                "duration_minutes": None,
                "negative_marking": None,
                "notes": TIER2_PENDING,
            },
        ],
        "official_url": OFFICIAL_SITE,
        "data_status": "available",
        "sources": [
            {"name": "SSC official website", "url": OFFICIAL_SITE},
        ],
        "last_verified": VERIFIED_ON,
    },
]

# Exams whose details are not added yet. They appear in the app with
# "Not announced yet" instead of made-up details.
PENDING_EXAMS = [
    ("MTS", "SSC MTS", "Multi-Tasking (Non-Technical) Staff and Havaldar Examination",
     "Recruitment to Multi-Tasking (Non-Technical) Staff posts and Havaldar in CBIC and CBN."),
    ("GD", "SSC GD Constable", "Constable (General Duty) Examination",
     "Recruitment of Constables (GD) in Central Armed Police Forces, SSF, Rifleman (GD) in Assam Rifles and Sepoy in NCB."),
    ("CPO", "SSC CPO", "Sub-Inspector in Delhi Police and Central Armed Police Forces Examination",
     "Recruitment of Sub-Inspectors in Delhi Police and Central Armed Police Forces."),
    ("JE", "SSC JE", "Junior Engineer Examination",
     "Recruitment of Junior Engineers (Civil, Mechanical, Electrical, and Quantity Surveying and Contracts)."),
    ("STENO", "SSC Stenographer", "Stenographer Grade 'C' and 'D' Examination",
     "Recruitment of Stenographers Grade C and Grade D in central government offices."),
    ("SELECTION_POST", "SSC Selection Post", "Selection Post Examination",
     "Recruitment to selection posts at Matriculation, Higher Secondary and Graduation levels."),
    ("JHT", "SSC JHT", "Junior Hindi Translator Examination",
     "Recruitment of Junior Hindi Translators, Junior Translators, Senior Hindi Translators and related posts."),
]

for _code, _name, _full, _desc in PENDING_EXAMS:
    EXAMS.append({
        "code": _code,
        "name": _name,
        "full_name": _full,
        "description": _desc,
        "qualification": None,
        "age_limit": None,
        "age_relaxation": None,
        "pattern": None,
        "official_url": OFFICIAL_SITE,
        "data_status": "pending",
        "sources": [{"name": "SSC official website", "url": OFFICIAL_SITE}],
        "last_verified": None,
    })


# ----------------------------------------------------------------------
# Notifications
# ----------------------------------------------------------------------
NOTIFICATIONS = [
    {
        "exam_code": "CGL",
        "notification_ref": "CGL-2026",
        "title": "Combined Graduate Level Examination 2026",
        "notification_date": date(2026, 5, 21),
        "apply_start": date(2026, 5, 21),
        "apply_end": date(2026, 6, 25),
        "fee_last_date": date(2026, 6, 26),
        "correction_start": date(2026, 7, 1),
        "correction_end": date(2026, 7, 3),
        "exam_notice_date": date(2026, 9, 12),
        "tier1_start": date(2026, 9, 30),
        "tier1_end": date(2026, 10, 30),
        "tier2_info": "December 2026 (tentative)",
        "vacancies": 10731,
        "vacancy_note": "Tentative. Revised from 12,256 (at notification) to 10,731.",
        "fee_text": None,
        "eligibility_note": "Educational qualification cut-off date: 1 August 2026.",
        "admit_card_info": (
            "Tier 1 admit cards were released in phases from 27 September 2026 "
            "through the candidate login on ssc.gov.in."
        ),
        "result_info": (
            "Tier 1 result and answer key are not announced yet "
            "(some sources expect them in November 2026)."
        ),
        "notice_pdf_url": None,
        "apply_url": APPLY_URL,
        "source_name": "Reports of the SSC notices (Careerpower, updated 2 Nov 2026)",
        "source_url": "https://www.careerpower.in/ssc-cgl.html",
        "sources": [
            {"name": "Careerpower - SSC CGL 2026", "url": "https://www.careerpower.in/ssc-cgl.html"},
            {"name": "Practicemock - SSC CGL notification", "url": "https://www.practicemock.com/blog/ssc-cgl-notification/"},
            {"name": "Testbook - CGL Tier 1 exam date notice", "url": "https://testbook.com/news/ssc-cgl-tier-1-exam-date-2026-out/"},
            {"name": "FreeJobAlert - SSC CGL 2026 application", "url": "https://www.freejobalert.com/articles/ssc-cgl-recruitment-2026-apply-online-for-12256-group-b-group-c-posts-3050273"},
            {"name": "SSC official website", "url": OFFICIAL_SITE},
        ],
        "verification": "secondary",
        "last_verified": VERIFIED_ON,
        "discrepancies": [
            "Vacancies: 12,256 were announced with the notification on 21 May 2026 and later reported as revised to 10,731. The revised number is shown.",
            "Last date to apply: first 22 June 2026, then extended to 25 June 2026 (fee payment until 26 June 2026).",
            "Correction window: 1 to 3 July 2026 after the extension. An earlier plan listed 29 June to 1 July.",
            "Tier 1: the notice of 12 September 2026 gives 30 September to 30 October 2026. Some sites report admit cards only up to 28 October, so the last exam day may be earlier than the window end.",
        ],
    },
    {
        "exam_code": "CHSL",
        "notification_ref": "CHSL-2026",
        "title": "Combined Higher Secondary (10+2) Level Examination 2026",
        "notification_date": date(2026, 9, 7),
        "apply_start": date(2026, 9, 7),
        "apply_end": date(2026, 10, 7),
        "fee_last_date": date(2026, 10, 8),
        "correction_start": date(2026, 10, 14),
        "correction_end": date(2026, 10, 16),
        "exam_notice_date": date(2026, 10, 1),
        "tier1_start": date(2026, 11, 30),
        "tier1_end": date(2026, 12, 31),
        "tier2_info": None,
        "vacancies": 2536,
        "vacancy_note": "Tentative. SSC does not publish state-wise or zone-wise vacancies for CHSL.",
        "fee_text": "Rs. 100 for General category (as reported). Check the notification for exemptions.",
        "eligibility_note": "Age is counted as on 1 August 2026 (18 to 27 years).",
        "admit_card_info": (
            "Not announced yet. The city intimation slip and admit card are "
            "released shortly before the exam on ssc.gov.in."
        ),
        "result_info": "Not announced yet.",
        "notice_pdf_url": None,
        "apply_url": APPLY_URL,
        "source_name": "Reports of the SSC notices (PW, Careerpower, FreeJobAlert)",
        "source_url": "https://www.careerpower.in/ssc-chsl.html",
        "sources": [
            {"name": "PW - SSC CHSL 2026 notification", "url": "https://www.pw.live/ssc/exams/ssc-chsl-2026-notification-out"},
            {"name": "Careerpower - SSC CHSL 2026", "url": "https://www.careerpower.in/ssc-chsl.html"},
            {"name": "FreeJobAlert - CHSL Tier 1 exam date (notice of 1 Oct 2026)", "url": "https://www.freejobalert.com/articles/ssc-chsl-tier-1-exam-date-2026-3075674"},
            {"name": "CollegeBandhu - SSC CHSL 2026", "url": "https://collegebandhu.com/exam/ssc-chsl/"},
            {"name": "SSC official website", "url": OFFICIAL_SITE},
        ],
        "verification": "secondary",
        "last_verified": VERIFIED_ON,
        "discrepancies": [
            "Tier 1 dates (30 November to 31 December 2026) are described as 'proposed' in the SSC notice of 1 October 2026. Each candidate's own exam date is on the admit card.",
            "Tier 2 date is not announced yet.",
        ],
    },
]


# ----------------------------------------------------------------------
# Loader (safe to run many times)
# ----------------------------------------------------------------------
def seed_ssc(db):
    """Adds or updates the starting SSC data. Returns a small summary."""

    summary = {"exams_added": 0, "exams_updated": 0,
               "notifications_added": 0, "notifications_updated": 0,
               "skipped_official": 0}

    for data in EXAMS:
        exam = db.query(SSCExam).filter(SSCExam.code == data["code"]).first()

        if exam is None:
            db.add(SSCExam(**data))
            summary["exams_added"] += 1
        else:
            # Do not downgrade an exam that was already filled in by sync
            if exam.data_status == "available" and data["data_status"] == "pending":
                continue
            for key, value in data.items():
                setattr(exam, key, value)
            summary["exams_updated"] += 1

    db.flush()

    for data in NOTIFICATIONS:
        existing = (
            db.query(SSCNotification)
            .filter(
                SSCNotification.exam_code == data["exam_code"],
                SSCNotification.notification_ref == data["notification_ref"],
            )
            .first()
        )

        if existing is None:
            db.add(SSCNotification(**data))
            summary["notifications_added"] += 1
        elif existing.verification == "official":
            summary["skipped_official"] += 1
        else:
            for key, value in data.items():
                setattr(existing, key, value)
            summary["notifications_updated"] += 1

    db.commit()
    return summary
