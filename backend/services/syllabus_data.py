"""Curated SSC CGL/CHSL topic catalogue. Keys are stable and used by Phase 5 questions."""
import re

OFFICIAL_SOURCES = {
    "CGL": "https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/Notice_of_adv_cgl_2026.pdf",
    "CHSL": "https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/Notice_of_adv_chsle_2026.pdf",
}

# Each subject maps to topic -> subtopics. These are study-friendly breakdowns
# of the subjects/topics described in the SSC 2026 examination notices.
CGL_T1 = {
"General Intelligence and Reasoning": {
"Verbal Reasoning": ["Analogy", "Classification", "Series", "Coding and decoding", "Blood relations", "Direction and distance", "Order and ranking", "Word formation", "Syllogism", "Venn diagrams", "Statement and conclusion", "Problem solving"],
"Non-Verbal Reasoning": ["Figure series", "Embedded figures", "Mirror and water images", "Paper folding and cutting", "Completion of figures", "Spatial visualisation", "Pattern folding"],
"Logical Reasoning": ["Statement and argument", "Statement and assumption", "Course of action", "Decision making", "Critical thinking"],
},
"General Awareness": {
"Current Affairs": ["National events", "International events", "Government schemes", "Appointments and awards", "Sports", "Science and technology updates"],
"History": ["Ancient Indian history", "Medieval Indian history", "Modern Indian history", "Indian freedom movement"],
"Geography": ["Physical geography", "Indian geography", "World geography", "Climate and environment"],
"Polity": ["Constitution", "Fundamental rights and duties", "Parliament", "President and Prime Minister", "Judiciary", "Constitutional bodies"],
"Economy": ["Basic economics", "Indian economy", "Budget and taxation", "Banking and financial institutions"],
"General Science": ["Physics basics", "Chemistry basics", "Biology", "Human body and health", "Everyday science"],
"Static General Knowledge": ["Books and authors", "Art and culture", "Important days", "Countries and capitals", "National parks and organisations"],
},
"Quantitative Aptitude": {
"Number System and Arithmetic": ["Number system", "Simplification", "HCF and LCM", "Decimals and fractions", "Percentage", "Ratio and proportion", "Average", "Partnership"],
"Commercial Mathematics": ["Profit and loss", "Discount", "Simple interest", "Compound interest"],
"Time and Work": ["Work and wages", "Pipes and cisterns", "Efficiency-based problems"],
"Time, Speed and Distance": ["Speed, time and distance", "Trains", "Boats and streams"],
"Algebra": ["Algebraic identities", "Linear equations", "Elementary surds", "Graphs of linear equations"],
"Geometry": ["Lines and angles", "Triangles", "Congruence and similarity", "Circles", "Quadrilaterals and polygons"],
"Mensuration": ["Perimeter and area of 2D figures", "Surface area", "Volume of 3D solids"],
"Trigonometry": ["Trigonometric ratios", "Standard identities", "Complementary angles", "Heights and distances"],
"Data Interpretation": ["Tables", "Bar graphs", "Pie charts", "Histograms", "Frequency polygons"],
},
"English Comprehension": {
"Vocabulary": ["Synonyms", "Antonyms", "One-word substitution", "Idioms and phrases", "Spelling and word usage"],
"Grammar": ["Parts of speech", "Tenses", "Subject-verb agreement", "Articles and determiners", "Prepositions", "Active and passive voice", "Direct and indirect speech", "Sentence correction"],
"Reading and Usage": ["Reading comprehension", "Cloze test", "Fill in the blanks", "Sentence improvement", "Sentence rearrangement", "Error spotting"],
},
}

CGL_T2 = {
"Mathematical Abilities": CGL_T1["Quantitative Aptitude"],
"Reasoning and General Intelligence": CGL_T1["General Intelligence and Reasoning"],
"English Language and Comprehension": CGL_T1["English Comprehension"],
"General Awareness": CGL_T1["General Awareness"],
"Computer Knowledge Test": {
"Computer Fundamentals": ["Computer organisation", "CPU and memory", "Input and output devices", "Hardware and software"],
"Software and Operating Systems": ["Windows basics", "File and folder management", "Operating system concepts", "Office productivity tools"],
"Internet and Networking": ["Internet and web browsers", "Email", "Computer networks", "Cyber security basics"],
"Digital Skills": ["Word processing", "Spreadsheets", "Presentations", "Keyboard shortcuts"],
},
"Data Entry Speed Test (DEST)": {
"Data Entry Practice": ["Typing accuracy", "Typing speed", "Continuous data entry", "Error reduction and time management"],
},
}
CGL_T2_STATS = {
"Statistics": {
"Data Collection and Presentation": ["Collection and classification of data", "Frequency distributions", "Tables and diagrams", "Graphs"],
"Measures of Central Tendency": ["Mean", "Median", "Mode"],
"Measures of Dispersion": ["Range", "Quartile deviation", "Mean deviation", "Standard deviation", "Variance"],
"Moments and Shape": ["Moments", "Skewness", "Kurtosis"],
"Correlation and Regression": ["Scatter diagrams", "Correlation coefficient", "Regression lines"],
"Probability and Sampling": ["Probability theory", "Random variables", "Probability distributions", "Sampling methods"],
"Statistical Inference": ["Estimation", "Hypothesis testing", "Tests of significance", "Analysis of variance"],
"Time Series and Index Numbers": ["Components of time series", "Trend measurement", "Index numbers"],
}
}
CGL_T2_FINANCE = {
"General Studies (Finance and Economics)": {
"Finance and Accounts": ["Basic accounting concepts", "Financial accounting", "Journal and ledger", "Trial balance", "Depreciation", "Bank reconciliation", "Final accounts"],
"Economics and Governance": ["Comptroller and Auditor General of India", "Finance Commission", "Basic economics", "Demand and supply", "Production and cost", "Market forms", "National income", "Indian economy", "Economic reforms", "Money and banking", "Fiscal policy and budget", "Balance of payments", "FRBM Act"],
}
}

CHSL_T1 = {
"English Language": CGL_T1["English Comprehension"],
"General Intelligence": CGL_T1["General Intelligence and Reasoning"],
"Quantitative Aptitude": CGL_T1["Quantitative Aptitude"],
"General Awareness": CGL_T1["General Awareness"],
}
CHSL_T2 = {
"Mathematical Abilities": CGL_T1["Quantitative Aptitude"],
"Reasoning and General Intelligence": CGL_T1["General Intelligence and Reasoning"],
"English Language and Comprehension": CGL_T1["English Comprehension"],
"General Awareness": CGL_T1["General Awareness"],
"Computer Knowledge Test": CGL_T2["Computer Knowledge Test"],
"Skill Test / Typing Test": {
"Typing and Data Entry": ["Typing accuracy", "Typing speed", "English or Hindi typing practice", "Data entry practice", "Time management"],
},
}

# ----------------------------------------------------------------------
# Other SSC exams (added with Phase 5). Topic lists are study-friendly
# summaries of the notice syllabus headings. Always verify the latest notice.
# ----------------------------------------------------------------------
EXAM_NAMES = {
    "CGL": "SSC CGL",
    "CHSL": "SSC CHSL",
    "MTS": "SSC MTS",
    "GD": "SSC GD Constable",
    "CPO": "SSC CPO",
    "JE": "SSC JE",
    "STENO": "SSC Stenographer",
    "SELECTION_POST": "SSC Selection Post",
    "JHT": "SSC JHT",
}

_GENERAL_AWARENESS_SHORT = {
"Current Events": ["National events", "International events", "Sports", "Awards and appointments"],
"India and Neighbouring Countries": ["History", "Culture", "Geography", "Economic scene"],
"General Polity and Constitution": ["Indian Constitution", "Fundamental rights and duties", "Parliament", "Local government"],
"General Science and Scientific Research": ["Physics basics", "Chemistry basics", "Biology", "Everyday science", "Environment"],
}

MTS_S1 = {
"Numerical and Mathematical Ability": {
"Number System": ["Integers and whole numbers", "LCM and HCF", "Decimals and fractions", "BODMAS and simplification"],
"Arithmetic": ["Percentage", "Ratio and proportion", "Average", "Profit, loss and discount", "Simple interest"],
"Time-Based Problems": ["Time and work", "Time, speed and distance"],
"Mensuration": ["Area and perimeter", "Volume and surface area"],
},
"Reasoning Ability and Problem Solving": {
"Series and Analogy": ["Alphanumeric series", "Number series", "Figural series", "Semantic and figural analogy"],
"Coding and Classification": ["Coding and decoding", "Semantic classification", "Figural classification", "Similarities and differences"],
"Logical Reasoning": ["Venn diagrams", "Drawing inferences", "Symbolic operations", "Problem solving"],
"Orientation and Patterns": ["Direction sense", "Space orientation", "Punched hole and pattern folding", "Word building"],
"Calendar, Clock and Age": ["Calendar problems", "Clock problems", "Age problems"],
},
}
MTS_S2 = {
"General Awareness": {
"History and Culture": ["Freedom struggle", "Ancient and medieval India", "Art and culture"],
"Geography": ["Physical geography", "Indian climate", "Resources and agriculture"],
"Civics and Polity": ["Constitution", "Local government", "Rights and duties"],
"General Science": ["Physics", "Chemistry", "Biology", "Everyday science"],
"Current Affairs": ["National events", "International events", "Sports", "Government schemes"],
},
"English Language and Comprehension": {
"Vocabulary": ["Synonyms", "Antonyms", "One-word substitution", "Idioms and phrases"],
"Grammar": ["Parts of speech", "Tenses", "Subject-verb agreement", "Articles and prepositions"],
"Sentence Structure": ["Error spotting", "Fill in the blanks", "Sentence improvement"],
"Reading": ["Reading comprehension", "Cloze test"],
},
}
MTS_HAVALDAR = {
"Physical Tests (Havaldar, CBIC and CBN)": {
"Physical Efficiency Test (PET)": ["Walking test (distance and time as per notice)", "Daily walking and stamina practice"],
"Physical Standard Test (PST)": ["Height and chest standards as per notice", "Document and medical readiness"],
},
}

GD_CBE = {
"General Intelligence and Reasoning": {
"Analogy and Classification": ["Analogies", "Similarities and differences", "Verbal and figure classification"],
"Series and Coding": ["Arithmetical number series", "Non-verbal series", "Coding and decoding"],
"Visual Reasoning": ["Spatial visualisation", "Spatial orientation", "Visual memory", "Discrimination and observation"],
"Logical Reasoning": ["Relationship concepts", "Arithmetical reasoning", "Statement and conclusion", "Syllogistic reasoning"],
},
"General Knowledge and General Awareness": _GENERAL_AWARENESS_SHORT,
"Elementary Mathematics": {
"Number System": ["Computation of whole numbers", "Decimals and fractions", "Relationships between numbers"],
"Arithmetic": ["Percentage", "Ratio and proportion", "Average", "Interest", "Profit and loss", "Discount"],
"Time and Distance": ["Time and distance", "Ratio and time"],
"Mensuration": ["Perimeter and area", "Volume and surface area"],
},
"English or Hindi": {
"Comprehension": ["Reading passages", "Basic comprehension"],
"Grammar": ["Parts of speech", "Tenses", "Sentence correction"],
"Vocabulary": ["Synonyms and antonyms", "Idioms and phrases", "One-word substitution"],
},
}
GD_PHYSICAL = {
"Physical Tests": {
"Physical Efficiency Test (PET)": ["Running test (distance and time as per notice)", "Stamina and speed training"],
"Physical Standard Test (PST)": ["Height and chest standards as per notice", "Document and medical readiness"],
},
}

CPO_P2 = {
"English Language and Comprehension": {
"Error Spotting and Correction": ["Spot the error", "Improvement of sentences", "Spelling and mis-spelt words"],
"Vocabulary": ["Synonyms and antonyms", "Idioms and phrases", "One-word substitution"],
"Sentence Transformation": ["Active and passive voice", "Direct and indirect speech", "Shuffling of sentence parts", "Shuffling of sentences in a passage"],
"Passages": ["Fill in the blanks", "Cloze passage", "Comprehension passage"],
},
}
CPO_PHYSICAL = {
"Physical Tests (PST and PET)": {
"Physical Standard Test (PST)": ["Height, chest and weight standards as per notice", "Document and medical readiness"],
"Physical Endurance Test (PET)": ["100 m race", "800 m race", "Long jump", "High jump", "Shot put"],
},
}

JE_REASONING = {
"General Intelligence and Reasoning": {
"Analogy and Classification": ["Analogies", "Similarities and differences", "Verbal and figure classification"],
"Visual Reasoning": ["Space visualisation", "Visual memory", "Observation and discrimination"],
"Number and Logical Reasoning": ["Arithmetical reasoning", "Number series", "Problem solving", "Analysis and judgement", "Decision making"],
"Abstract Concepts": ["Relationship concepts", "Abstract symbols"],
},
}
JE_GA = {
"General Awareness": {
"Environment and Society": ["Environment and its application to society", "Everyday observations with scientific basis"],
"Current Events": ["National events", "International events"],
"India and Neighbours": ["History", "Culture", "Geography", "Economic scene"],
"Polity and Science": ["General polity", "Scientific research"],
},
}
JE_CIVIL = {
"Civil and Structural Engineering": {
"Building Materials": ["Bricks, cement and sand", "Timber and lime", "Concrete mix and construction materials"],
"Construction Management": ["Planning and scheduling", "PERT and CPM"],
"Estimating, Costing and Valuation": ["Quantity estimation", "Rate analysis", "Valuation"],
"Surveying": ["Levelling", "Theodolite and total station", "Traversing", "Tacheometry"],
"Soil Mechanics": ["Phase relationships", "Permeability and seepage", "Consolidation", "Shear strength"],
"Fluid Mechanics and Hydraulics": ["Pipe flow", "Channel flow", "Hydraulic jump"],
"Hydrology and Irrigation": ["Precipitation", "Unit hydrographs", "Canals", "Dams"],
"Environmental Engineering": ["Water treatment", "Wastewater treatment", "Air pollution", "Solid waste"],
"Transportation Engineering": ["Highway geometry", "Pavement design", "Traffic studies"],
"Engineering Mechanics and Solid Mechanics": ["Force systems and equilibrium", "Stress and strain", "Bending and torsion", "Column buckling"],
"Structural Analysis": ["Determinate and indeterminate structures", "Trusses and frames", "Moment distribution", "Influence lines"],
"Concrete and Steel Structures": ["Limit state design of beams, slabs and columns", "Foundations", "Steel connections", "Tension and compression members"],
},
}
JE_ELECTRICAL = {
"Electrical Engineering": {
"Basic Electrical Engineering": ["Circuit elements", "KCL and KVL", "Network theorems"],
"Magnetic Circuits": ["Flux and reluctance", "Inductance"],
"AC Fundamentals": ["RMS and average values", "Series and parallel AC circuits", "Resonance", "Three-phase circuits"],
"Measurements and Instruments": ["Measuring instruments", "Bridges", "Energy meter", "CT and PT"],
"Electrical Machines": ["Transformers", "DC machines", "Induction motors", "Synchronous machines"],
"Generation, Transmission and Distribution": ["Power stations", "Power factor", "Transmission parameters", "Protection"],
"Estimation and Utilisation": ["Estimation and costing", "Earthing", "Illumination", "Heating and welding", "Traction"],
"Electronics": ["Diodes and rectifiers", "BJT and FET", "Amplifiers and oscillators", "Power electronics basics"],
},
}
JE_MECHANICAL = {
"Mechanical Engineering": {
"Engineering Mechanics and Strength of Materials": ["Free body diagrams", "Friction and centroids", "Stress and strain", "Shear force and bending moment", "Torsion"],
"Theory of Machines": ["Cams and gears", "Belts and chains", "Flywheels and governors", "Balancing", "Brakes and clutches"],
"Machine Design": ["Failure theories", "Keys, shafts and couplings", "Springs", "Bolted and welded joints"],
"Materials Science": ["Phase diagrams", "Heat treatment", "Alloys", "Corrosion and NDT"],
"Thermal Engineering": ["Laws of thermodynamics", "IC engines", "Steam turbines", "Refrigeration and air conditioning", "Heat transfer"],
"Fluid Mechanics and Machinery": ["Pipe flow", "Jets", "Turbines", "Pumps"],
"Production and Industrial Engineering": ["Casting and welding", "Machining and forming", "Work study", "Production planning", "Quality control"],
"Metrology and Advanced Manufacturing": ["Tolerances and fits", "Comparators and CMM", "CNC and CAD/CAM", "Non-traditional machining"],
},
}

STENO_SKILL = {
"Stenography Skill Test": {
"Shorthand Dictation": ["Dictation practice (Grade C and Grade D speeds as per notice)", "Outline speed and accuracy", "Phrases and contractions"],
"Transcription": ["Transcription in English or Hindi on computer", "Accuracy and proofreading", "Time management"],
},
}

SELECTION_POST_SUBJECTS = {
"General Intelligence": {
"Verbal Reasoning": ["Similarities and differences", "Analogy", "Classification", "Number and alphabet series", "Coding and decoding", "Blood relations", "Direction sense", "Ranking and ordering"],
"Non-Verbal Reasoning": ["Visual memory", "Space visualisation", "Figure classification", "Embedded figures", "Mirror image", "Paper folding"],
"Logical Reasoning": ["Venn diagrams", "Syllogism", "Statement-based logic", "Data sufficiency", "Decision making"],
},
"General Awareness": {
"Current Affairs": ["National and international events", "Awards and honours", "Sports", "Persons in news", "Government schemes"],
"Static GK": ["Books and authors", "Important days and dates", "Organisations and headquarters", "Art and culture"],
"History, Geography and Polity": ["Indian history", "Geography", "Polity and constitution"],
"Economy, Science and Environment": ["Indian economy", "General science", "Scientific research", "Environment"],
},
"Quantitative Aptitude": {
"Arithmetic": ["Number system", "Simplification", "Percentage", "Ratio and proportion", "Average", "Profit and loss", "Discount", "Simple and compound interest", "Mixture and alligation", "Problems on ages"],
"Time-Based Problems": ["Time and work", "Time, speed and distance"],
"Algebra and Geometry": ["Basic algebra", "Quadratic equations", "Geometry basics", "Mensuration"],
"Data Interpretation": ["Tables", "Bar graphs", "Pie charts"],
},
"English Language": {
"Grammar": ["Parts of speech", "Tenses", "Active and passive voice", "Sentence structure"],
"Vocabulary": ["Synonyms and antonyms", "One-word substitution", "Idioms and phrases"],
"Reading and Usage": ["Reading comprehension", "Cloze test", "Fill in the blanks", "Error detection", "Sentence improvement", "Para jumbles"],
},
}

JHT_P1 = {
"General Hindi": {
"Hindi Grammar": ["Sandhi", "Samas", "Upsarg and pratyay", "Ling, vachan and karak", "Kriya and kaal", "Vakya shuddhi"],
"Hindi Vocabulary": ["Paryayvachi shabd", "Vilom shabd", "Muhavare and lokoktiyan", "Anek shabdon ke liye ek shabd", "Shabd shuddhi"],
"Hindi Comprehension": ["Apathit gadyansh", "Apathit padyansh"],
},
"General English": {
"Vocabulary": ["Synonyms", "Antonyms", "One-word substitution", "Idioms and phrases", "Spelling and word usage"],
"Grammar": ["Parts of speech", "Tenses", "Subject-verb agreement", "Articles and prepositions", "Voice and narration"],
"Reading and Usage": ["Reading comprehension", "Cloze test", "Fill in the blanks", "Sentence improvement", "Error spotting"],
},
}
JHT_P2 = {
"Translation and Essay (Descriptive)": {
"Hindi to English Translation": ["Passage translation", "Official and administrative terms", "Idioms and phrases"],
"English to Hindi Translation": ["Passage translation", "Official and administrative terms", "Technical terminology"],
},
}

SYLLABUS = []
def _slug(value):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", value.lower())).strip("-")

def add(exam, tier, subjects, note="Check the current SSC notification for post-specific applicability."):
    for subject_order, (subject, topics) in enumerate(subjects.items(), 1):
        for topic_order, (topic, subtopics) in enumerate(topics.items(), 1):
            SYLLABUS.append({
                "key": f"{exam.lower()}-{_slug(tier)}-{_slug(subject)}-{_slug(topic)}",
                "exam_code": exam, "tier": tier, "subject": subject,
                "area": subject.lower().replace(" ", "_"), "subject_note": note,
                "topic": topic, "subtopics": subtopics,
                "sort_order": subject_order * 100 + topic_order,
            })

add("CGL", "Tier 1", CGL_T1)
add("CGL", "Tier 2 Paper I", CGL_T2, "Paper I is compulsory; DEST is qualifying. Verify the current notice for section rules.")
add("CGL", "Tier 2 Paper II", CGL_T2_STATS, "For candidates applying for Junior Statistical Officer (JSO) posts, subject to the current notice.")
add("CGL", "Tier 2 Paper III", CGL_T2_FINANCE, "For candidates applying for the relevant Assistant Audit/Accounts Officer posts, subject to the current notice.")
add("CHSL", "Tier 1", CHSL_T1)
add("CHSL", "Tier 2", CHSL_T2, "Includes computer knowledge and qualifying skill/typing components; post-specific test varies.")

# ---- Other SSC exams ----
add("MTS", "Session 1", MTS_S1, "Session 1 has no negative marking; Session 2 deducts 1 mark per wrong answer (2025 notice). Verify the current notice.")
add("MTS", "Session 2", MTS_S2, "Both sessions are compulsory and held on the same day. Verify the current notice.")
add("MTS", "Havaldar Physical Tests", MTS_HAVALDAR, "Only for Havaldar posts in CBIC and CBN. Check the notice for exact standards.")
add("GD", "Computer Based Examination", GD_CBE)
add("GD", "Physical Tests", GD_PHYSICAL, "PET and PST standards differ by category. Check the notice for exact standards.")
add("CPO", "Paper I", CGL_T1, "Paper I follows the same four-subject style as CGL Tier 1. Verify the current notice.")
add("CPO", "Physical Tests", CPO_PHYSICAL, "PST and PET standards differ by category. Check the notice for exact standards.")
add("CPO", "Paper II", CPO_P2, "Paper II is English Language and Comprehension, taken by candidates who qualify the PET and PST.")
add("JE", "Paper I", {**JE_REASONING, **JE_GA}, "Paper I is the first stage. Part C (engineering subject) uses your branch topics listed in Paper II.")
add("JE", "Paper II Civil", JE_CIVIL, "Choose your own branch. Verify the paper pattern in the current notice.")
add("JE", "Paper II Electrical", JE_ELECTRICAL, "Choose your own branch. Verify the paper pattern in the current notice.")
add("JE", "Paper II Mechanical", JE_MECHANICAL, "Choose your own branch. Verify the paper pattern in the current notice.")
add("STENO", "Written Examination", {
    "General Intelligence and Reasoning": CGL_T1["General Intelligence and Reasoning"],
    "General Awareness": CGL_T1["General Awareness"],
    "English Language and Comprehension": CGL_T1["English Comprehension"],
}, "Computer based test. Verify the current notice.")
add("STENO", "Skill Test", STENO_SKILL, "Qualifying skill test. Dictation speed differs for Grade C and Grade D; check the notice.")
add("SELECTION_POST", "Matriculation Level", SELECTION_POST_SUBJECTS, "Same subjects at every level; questions are basic for Matriculation posts.")
add("SELECTION_POST", "Higher Secondary Level", SELECTION_POST_SUBJECTS, "Same subjects at every level; questions are of moderate difficulty for Higher Secondary posts.")
add("SELECTION_POST", "Graduation Level", SELECTION_POST_SUBJECTS, "Same subjects at every level; questions are of higher difficulty for Graduation posts.")
add("JHT", "Paper I", JHT_P1, "Objective computer based paper in Hindi and English. Verify the current notice.")
add("JHT", "Paper II", JHT_P2, "Descriptive paper. Verify the current notice.")
