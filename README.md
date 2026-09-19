# Smart Student Career Planner

A TY BSc CS mini-project built with **Python Flask** and **SQLite**.
Pick the skills you already have → get career matches, a skill-gap analysis and a step-by-step roadmap.

## Features
- Student registration, login and profile (passwords hashed, CSRF-protected forms)
- Skill picker: grouped by category, live search, "select all", **live preview of your top matches**
- Career recommendation with a **skill-match percentage** and a **readiness level**
- **Skill-gap analysis**: green chips = skills you have, dashed chips = skills to learn
- **Radar chart** showing how you fit every career at a glance
- **"Learn next"** suggestions with tutorial links
- **Career roadmap**: done steps, "start here" step, starter project, related careers, print / save as PDF
- Skill-coverage bars per category, animated progress rings, count-up stats
- Search / filter / sort on the careers page
- Dark mode, mobile-friendly menu, toast messages, friendly 404 page

## Run
1. Install Python 3.10+.
2. In this folder:

       pip install -r requirements.txt
       python app.py

3. Open http://127.0.0.1:5000

`career_planner.db` is created automatically on first run. (An old database from the
previous version keeps working - the tables did not change.)

## How it works (good for the viva)
| Idea | Rule |
|------|------|
| Match % | matched skills ÷ required skills × 100 |
| Readiness level | 0-24 Just starting · 25-49 Building basics · 50-74 Getting there · 75-99 Almost there · 100 Ready to apply |
| Skill gap | required skills the student has *not* ticked |
| Learn next | look at the careers you're closest to, suggest their missing skills; ties go to the skill that helps more careers |
| Roadmap | done skills → first missing skill ("start here") → remaining gaps → project & internships |

## Project structure
```
app.py            routes + all career logic (data is at the top of the file)
templates/        HTML pages (base.html = layout, _macros.html = ring + career card)
static/style.css  design system: colours as CSS variables, light + dark theme
static/app.js     small vanilla JS: theme, radar chart, live preview, filters
```

## Add your own career
Open `app.py`, copy one block inside `CAREERS`, change the name, icon, skills and project idea.
Skills must exist in the `SKILLS` dictionary above it. Nothing else needs to change.

## Ideas for the future
- Skill levels (beginner / intermediate / advanced) with weighted scores
- Save a "goal career" and track progress over time
- Admin page to edit careers from the browser
- Import careers from a CSV / real job-postings dataset

## Note
The match percentage is a simple project rule, not a professional career assessment.
