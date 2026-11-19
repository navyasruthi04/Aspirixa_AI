from database.connection import SessionLocal
from database.init_db import init_database
import services.question_review as qr

explanations = {
    13: "10% of 350 = (10/100) x 350 = 35.",
    14: "Discount = 15% of 800 = Rs 120. Selling price = 800 - 120 = Rs 680.",
    15: "Assume the original price is Rs 100. After a 20% increase it becomes Rs 120. A 20% decrease on 120 is Rs 24, leaving Rs 96. Net change is a 4% decrease.",
    16: "The sequence increases by 5 each time. The next number is 20 + 5 = 25.",
    17: "The differences are 3, 5, 7. The next difference is 9, so 17 + 9 = 26.",
    18: "The terms are factorials: 1!, 2!, 3!, 4!, 5!. The next is 6! = 720.",
    19: "'They' is plural, so the correct present continuous form is 'They are playing football.'",
    20: "'Since' is used with a specific starting point in time, such as 2019.",
    21: "'If I were you' is the standard subjunctive form used for an imaginary or hypothetical situation.",
    22: "The Vice President of India serves as the ex-officio Chairman of the Rajya Sabha.",
    23: "The minimum constitutional age for election to the Lok Sabha is 25 years.",
    24: "Article 352 of the Indian Constitution deals with the proclamation of a National Emergency.",
    26: "Loss = Cost price - Selling price = 500 - 450 = Rs 50.",
    28: "Selling price is 120% of cost price. Cost price = 720 x 100/120 = Rs 600.",
    30: "Assume cost price is Rs 100. Marked price = Rs 140. After a 10% discount, selling price = Rs 126. Profit = 26%.",
    31: "If A completes the whole work in 10 days, the one-day work is 1/10.",
    32: "Each person completes 1/6 of the work per day. Together they complete 1/6 + 1/6 = 1/3 per day, so they take 3 days.",
    33: "Combined daily work = 1/12 + 1/24 = 3/24 = 1/8. They complete the work in 8 days.",
    34: "Total work = 10 x 12 = 120 man-days. For 15 men, days = 120/15 = 8.",
    35: "B's daily work = 1/12 - 1/20 = 2/60 = 1/30. Therefore B alone takes 30 days.",
    36: "Together A and B complete 1/20 + 1/30 = 1/12 per day. In 6 days they complete half the work. B completes the remaining half in 15 days. Total time = 6 + 15 = 21 days.",
    38: "Each letter moves one position forward in the alphabet: D becomes E, O becomes P and G becomes H. DOG becomes EPH.",
    40: "Each letter moves one position forward: F-G, R-S, I-J, D-E, A-B, Y-Z. FRIDAY becomes GSJEBZ.",
    42: "The shifts are +1, +2 and +3. C becomes D, A becomes C and T becomes W. CAT becomes DCW.",
    43: "Riya's mother's brother is her maternal uncle. His son is Riya's cousin.",
    44: "A is explicitly stated to be the father of B. Since C is B's brother, A is also C's father.",
    45: "The only daughter of Ravi's mother is Ravi's sister. The girl's mother is therefore Ravi's sister, making the girl Ravi's niece.",
    46: "A is B's sister and C is their mother. D is C's father, so D is A's grandfather. A is D's granddaughter.",
    47: "The only daughter of the woman's father is the woman herself. Therefore, she is the man's mother.",
    48: "Y is W's mother, and X is Y's father. Therefore X is W's maternal grandfather.",
    50: "Modern means relating to the present or recent times. It is the opposite of ancient.",
    52: "Stingy means unwilling to give or spend. It is the opposite of generous.",
    54: "A blessing in disguise is something that initially appears unfortunate but eventually results in something good.",
    55: "The Ganga is commonly identified as the longest river in India.",
    56: "The Thar Desert is located mainly in Rajasthan, in northwestern India.",
    57: "Gujarat has the longest coastline among Indian states.",
    58: "The Tropic of Cancer passes through Tripura, Gujarat and Jharkhand, but not Odisha.",
    59: "The Kosi River is known as the Sorrow of Bihar because of its frequent floods and course changes.",
    60: "Chilika Lake is a large brackish-water lagoon located in Odisha.",
    62: "The chemical symbol for sodium is Na, derived from its Latin name natrium.",
    64: "The newton (N) is the SI unit of force. One newton equals one kilogram metre per second squared.",
    66: "Bromine is a non-metal that exists as a liquid at ordinary room temperature.",
    67: "Mahatma Gandhi is popularly known as the Father of the Nation in India.",
    68: "India became independent from British rule on 15 August 1947.",
    69: "The Quit India Movement was launched by Mahatma Gandhi in August 1942.",
    70: "Chandragupta Maurya founded the Maurya Empire in ancient India.",
    71: "The Battle of Plassey was fought in 1757 between the forces of Siraj-ud-Daulah and the East India Company.",
    72: "Lord Mountbatten was the first Governor-General of independent India."
}

init_database()
db = SessionLocal()

try:
    questions = qr.list_questions(db, status="draft")
    by_id = {q.id: q for q in questions}

    missing_ids = sorted(set(explanations) - set(by_id))
    if missing_ids:
        raise RuntimeError(f"These expected draft question IDs were not found: {missing_ids}")

    for question_id, explanation in explanations.items():
        fields = {"explanation": explanation}

        if question_id == 55:
            fields["question"] = "Which is the longest river in India?"
            fields["correct_answer"] = "C"

        qr.edit_question(db, question_id, **fields)
        print(f"Question {question_id}: explanation updated")

    print("\nAll 48 explanations updated.")
    print("All questions remain DRAFT and must still pass batch review.")

finally:
    db.close()
