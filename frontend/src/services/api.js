// ============================================================
// API LAYER. The ONLY file that talks to the backend.
// Today it returns mock data. To connect FastAPI later:
//   1) set USE_MOCK = false
//   2) fill in the request(...) lines marked "FASTAPI" below
// ============================================================
import { student, dashboardStats, achievements, leaderboard } from '../data/studentData.js';
import { exams, topExplanation, shapSample, algorithms } from '../data/examData.js';
import { diagnosticQuestions, adaptivePool, diagnosticResult } from '../data/questionData.js';
import { schedule, planSummary, whyPlan, planFlow } from '../data/studyPlanData.js';
import { analytics } from '../data/performanceData.js';
import { resources, resourceCategories } from '../data/resourceData.js';
import { pyqs } from '../data/pyqData.js';
import { doubts } from '../data/communityData.js';
import { difficultyFor } from '../utils/helpers.js';

export const BASE_URL = 'http://127.0.0.1:8000';
const USE_MOCK = true;
const USE_BACKEND_RECOMMENDATION = true;
const USE_BACKEND_DIAGNOSTIC = true;
const USE_BACKEND_STUDY_PLAN = true;
const USE_BACKEND_QUIZ = true; 

const wait = (ms = 500) => new Promise((r) => setTimeout(r, ms));
const clone = (o) => JSON.parse(JSON.stringify(o));
const strip = ({ answer, explanation, ...rest }) => rest;

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res.json();
}

// In-memory mock state (resets on page refresh)
let profileState = clone(student);
let planState = clone(schedule);
let doubtState = clone(doubts);

// ---------- Student profile ----------
export async function getStudentProfile() {
  return request('/api/profile');
}

export async function updateStudentProfile(changes) {
  return request('/api/profile', {
    method: 'PUT',
    body: JSON.stringify(changes),
  });
}

// ---------- Dashboard (combined view) ----------
export async function getDashboard() {
  if (!USE_MOCK) return request('/api/dashboard'); // FASTAPI: GET /api/dashboard
  await wait(600);
  const top = exams[0];
  return {
    student: clone(profileState),
    stats: clone(dashboardStats),
    recommendation: { ...clone(top), suitability: 87, factors: top.base, explanation: topExplanation },
    today: clone(planState),
    achievements: clone(achievements),
  };
}

// ---------- Module 1: exam recommendation (Eligibility Rules + XGBoost + TOPSIS + SHAP) ----------
const clamp = (v) => Math.max(35, Math.min(98, Math.round(v)));
const levelDelta = { Beginner: -10, Intermediate: 0, Advanced: 6 };

export async function getExamRecommendations(profile) {
  if (USE_BACKEND_RECOMMENDATION) {
    const backendResult = await request('/recommendation', {
      method: 'POST',
      body: JSON.stringify({
        qualification: profile.qualification,
        preparation_level: profile.level || profile.preparation_level,
        study_hours: Number(profile.dailyHours || profile.study_hours),
        subject_preferences:
          profile.subjects?.join(', ') ||
          profile.subject_preferences ||
          null,
      }),
    });

    // Convert FastAPI response into the structure
    // already expected by ExamRecommendation.jsx
    const eligibility = backendResult.recommendations.map((exam) => ({
      id: Number(exam.exam_id),
      name: exam.exam_name,
      status: 'eligible',
      note: `${exam.domain} exam • ${exam.difficulty} difficulty`,
      factors: {
        qualification: 100,
        subject: 100,
        time: Math.round(exam.suitability_score * 100),
        level: Math.round(exam.suitability_score * 100),
      },
      suitability: Math.round(exam.suitability_score * 100),
    }));

    const ranked = backendResult.recommendations.map((exam) => ({
      id: Number(exam.exam_id),
      name: exam.exam_name,
      factors: {
        qualification: 100,
        subject: 100,
        time: Math.round(exam.suitability_score * 100),
        level: Math.round(exam.suitability_score * 100),
      },
      suitability: Math.round(exam.suitability_score * 100),
      explanation: exam.explanation,
      topsisScore: exam.topsis_score,
      domain: exam.domain,
      difficulty: exam.difficulty,
      subjects: exam.subjects,
    }));

    const top = ranked[0] || null;

    return {
      eligibility,
      ranked,
      top,

      // Backend SHAP explanation is currently text/features,
      // so provide it in the format your existing chart expects.
      shap: ranked.length
        ? [
            { label: 'Qualification', value: 0.30 },
            { label: 'Preparation Level', value: 0.25 },
            { label: 'Study Time', value: 0.20 },
            { label: 'Exam Domain', value: 0.15 },
            { label: 'Difficulty', value: 0.10 },
          ]
        : [],

      algorithms: [
        {
          name: 'Eligibility Rules',
          role: 'Filters examinations based on qualification requirements.',
        },
        {
          name: 'XGBoost',
          role: 'Predicts examination suitability from student and exam features.',
        },
        {
          name: 'TOPSIS',
          role: 'Ranks eligible examinations using multiple criteria.',
        },
        {
          name: 'SHAP',
          role: 'Explains the factors contributing to the suitability prediction.',
        },
      ],
    };
  }

  // ---------------- MOCK VERSION ----------------

  await wait(1400);

  const graduate = !['12th Pass', 'Diploma'].includes(profile.qualification);

  const rows = exams.map((e) => {
    const f = {
      qualification:
        graduate || !e.graduateOnly
          ? e.base.qualification
          : clamp(e.base.qualification - 30),
      subject: clamp(
        e.base.subject + (profile.subjects.length - 3) * 4
      ),
      time: clamp(
        e.base.time + (profile.dailyHours - 3) * 5
      ),
      level: clamp(
        e.base.level + (levelDelta[profile.level] ?? 0)
      ),
    };

    let status = e.status;

    if (
      (e.graduateOnly && !graduate) ||
      Number(profile.age) > e.maxAge
    ) {
      status = 'not-eligible';
    }

    const suitability = Math.round(
      (f.qualification + f.subject + f.time + f.level) / 4
    );

    return {
      ...clone(e),
      factors: f,
      suitability,
      status,
    };
  });

  const ranked = rows
    .filter((r) => r.status === 'eligible')
    .sort((a, b) => b.suitability - a.suitability);

  return {
    eligibility: rows,
    ranked,
    top: ranked[0] || null,
    shap: clone(shapSample),
    algorithms: clone(algorithms),
  };
}
// ---------- Module 2: diagnostic assessment (Bayesian Knowledge Tracing) ----------
export async function getDiagnosticQuestions() {
  if (USE_BACKEND_DIAGNOSTIC) {
    const result = await request('/diagnostic/questions');

    // Backend returns:
    // { total_questions: 12, questions: [...] }
    // Diagnostic.jsx expects only the questions array.
    return result.questions.map((q) => ({
      id: q.question_id,
      subject: q.subject,
      topic: q.topic,
      difficulty: q.difficulty,
      text: q.question,
      options: [
        q.options.A,
        q.options.B,
        q.options.C,
        q.options.D,
      ],
    }));
  }

  await wait(500);
  return diagnosticQuestions.map(strip);
}

export async function submitDiagnosticAnswer({ questionId, selected }) {
  return {
    saved: true,
    questionId,
    selected,
  };
}

export async function getDiagnosticResult(answers) {
  if (USE_BACKEND_DIAGNOSTIC) {
    const formattedAnswers = Object.entries(answers).map(
      ([questionId, selected]) => ({
        question_id: Number(questionId),
        answer: selected,
      })
    );

    const result = await request('/diagnostic/submit', {
      method: 'POST',
      body: JSON.stringify({
        answers: formattedAnswers,
      }),
    });

    /*
      Backend already calculates weak_topics.
      If it returns none, derive weak topics from topic_analysis
      using the same threshold used by the Diagnostic page.
    */

    let weakTopics = result.weak_topics || [];

    if (!weakTopics.length && Array.isArray(result.topic_analysis)) {
      weakTopics = result.topic_analysis
        .map((topic) => {
          const value = Number(
            topic.mastery_percentage ??
            topic.mastery ??
            topic.score_percentage ??
            topic.percentage ??
            0
          );

          return {
            name:
              topic.topic ||
              topic.topic_name ||
              topic.name ||
              '',
            value:
              value <= 1 && value > 0
                ? value * 100
                : value,
          };
        })
        .filter((topic) => topic.name && topic.value < 55)
        .map((topic) => topic.name);
    }

    // Save weak topics for the Study Plan
    localStorage.setItem(
      'aspirixa_weak_topics',
      JSON.stringify(weakTopics)
    );

    // Save the complete diagnostic response
    localStorage.setItem(
      'aspirixa_diagnostic_result',
      JSON.stringify(result)
    );

    console.log('Diagnostic weak topics:', weakTopics);

    return result;
  }

  // Keep your existing mock implementation below this point.
}



// ---------- Module 3: study plan ----------
export async function getStudyPlan() {
  if (USE_BACKEND_STUDY_PLAN) {
    const profile = await getStudentProfile();

    let weakTopics = [];

    try {
      weakTopics = JSON.parse(
        localStorage.getItem('aspirixa_weak_topics') || '[]'
      );
    } catch {
      weakTopics = [];
    }

    // Fallback to profile data if diagnostic data is unavailable
    if (!weakTopics.length) {
      weakTopics = profile.weakTopics || profile.weak_topics || [];
    }

    const result = await request('/study-plan', {
      method: 'POST',
      body: JSON.stringify({
        study_hours: Number(
          profile.dailyHours || profile.study_hours || 3
        ),
        weak_topics: weakTopics,
        preparation_level:
          profile.level ||
          profile.preparation_level ||
          'beginner',
      }),
    });

    return {
      ...result,
      schedule: result.sessions || [],
      totalMinutes: result.total_minutes || 0,
      preparationLevel:
        result.preparation_level || 'beginner',
      weakTopics,
    };
  }

  // Keep your existing mock implementation below this point


  await wait(500);

  return {
    schedule: clone(planState),
    planSummary: clone(planSummary),
    whyPlan: clone(whyPlan),
    planFlow: clone(planFlow),
  };
}

export async function updatePlanStatus(id, status) {
  if (!USE_MOCK) return request(`/api/study-plan/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) }); // FASTAPI
  planState = planState.map((i) => (i.id === id ? { ...i, status } : i));
  return { ok: true };
}

export async function addToPlan({ subject, topic, minutes }) {
  if (!USE_MOCK) return request('/api/study-plan', { method: 'POST', body: JSON.stringify({ subject, topic, minutes }) }); // FASTAPI
  await wait(300);
  const item = { id: `x${Date.now()}`, time: '09:00', period: 'PM', subject, topic, minutes, weak: false, extra: true, status: 'upcoming' };
  planState = [...planState, item];
  return item;
}

// ---------- Module 4: adaptive quiz (BKT mastery + difficulty adaptation) ----------
export async function getAdaptiveQuestion({
  difficulty,
  usedIds = [],
  mastery = 58,
}) {
  if (USE_BACKEND_QUIZ) {
    const topics = [
      'Percentages',
      'Number Series',
      'Grammar',
      'Indian Polity',
    ];

    for (const topic of topics) {
      try {
        const result = await request('/quiz/next', {
          method: 'POST',
          body: JSON.stringify({
            topic,
            mastery_probability: Number(mastery) / 100,
            answered_question_ids: usedIds,
          }),
        });

        return {
          question: {
            id: result.question_id,
            subject: result.topic,
            topic: result.topic,
            difficulty: result.difficulty,
            text: result.question,
            options: [
              result.options.A,
              result.options.B,
              result.options.C,
              result.options.D,
            ],
          },

          reason:
            `Your current mastery is ${Math.round(
              Number(result.mastery_probability) * 100
            )}%, so the system selected a ${result.difficulty} question.`,
        };
      } catch (error) {
        // Try the next available topic
      }
    }

    throw new Error('No more adaptive questions available.');
  }

  // Keep your existing mock implementation below this point
}
export async function submitQuizAnswer({
  questionId,
  selected,
  mastery,
}) {
  if (USE_BACKEND_QUIZ) {
    const selectedLetter = 'ABCD'[selected];

    const result = await request('/quiz/answer', {
      method: 'POST',
      body: JSON.stringify({
        question_id: Number(questionId),
        answer: selectedLetter,
        mastery_probability: Number(mastery) / 100,
      }),
    });

    return {
      correct: result.correct,

      correctIndex:
        'ABCD'.indexOf(result.correct_answer),

      masteryBefore: Math.round(
        Number(result.previous_mastery) * 100
      ),

      masteryAfter: Math.round(
        Number(result.updated_mastery) * 100
      ),

      nextDifficulty: result.next_difficulty,

      explanation: result.correct
        ? 'Correct answer. Your mastery probability has been updated using BKT.'
        : `The correct answer is option ${result.correct_answer}. Your mastery probability has been updated using BKT.`,
    };
  }

  // Keep your existing mock implementation here
}
// ---------- Module 5: performance analytics ----------
export async function getPerformanceAnalytics() {
  const result = await request('/api/analytics');

  return result;
}
// ---------- Resources, PYQs, Doubts ----------
export async function getResources() {
  if (!USE_MOCK) return request('/api/resources'); // FASTAPI
  await wait(450);
  return { items: clone(resources), categories: resourceCategories };
}

export async function getPYQs() {
  if (!USE_MOCK) return request('/api/pyqs'); // FASTAPI
  await wait(450);
  return pyqs.map(({ answer, hint, ...rest }) => rest);
}

export async function checkPYQAnswer({ id, answer }) {
  if (!USE_MOCK) return request('/api/pyqs/check', { method: 'POST', body: JSON.stringify({ id, answer }) }); // FASTAPI
  await wait(250);
  const norm = (s) => String(s).toLowerCase().replace(/[^a-z0-9.]/g, '');
  const item = pyqs.find((p) => p.id === id);
  return { correct: norm(answer) === norm(item.answer), answer: item.answer, hint: item.hint };
}

export async function getDoubts() {
  if (!USE_MOCK) return request('/api/doubts'); // FASTAPI
  await wait(450);
  return clone(doubtState);
}

export async function postDoubt({ text, subject }) {
  if (!USE_MOCK) return request('/api/doubts', { method: 'POST', body: JSON.stringify({ text, subject }) }); // FASTAPI
  await wait(500);
  const d = { id: `q${Date.now()}`, title: text, subject, author: 'Navya (You)', time: 'Just now', replies: 0, status: 'Open', preview: '' };
  doubtState = [d, ...doubtState];
  return clone(d);
}