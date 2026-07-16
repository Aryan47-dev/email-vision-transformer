# Email Vision Transformer

AI-driven platform that converts a single **email preview screenshot** + a list of **asset image URLs** into a **pixel-accurate, production-ready HTML email**.

## Overview

The system uses computer vision (Google Gemini vision API) and OCR (Google Cloud Vision) to segment an email screenshot into semantic blocks — headers, paragraphs, images, buttons, footers — extract text, colors, and font styles, and map everything onto an HTML/CSS structure built for real-world email clients. The goal is near-100% visual fidelity to the original design, validated through automated pixel-diffing and email-client testing (Litmus / Email on Acid).

## Key Features

- **Layout & element segmentation** — Gemini vision detects sections and bounding boxes (header, image, text, button, footer, etc.)
- **Text extraction (OCR)** — Google Cloud Vision `TEXT_DETECTION` for reliable multi-line text
- **Color & font inference** — dominant color extraction and font-style heuristics per block
- **Asset image matching** — matches unordered asset URLs to their correct position via OpenCV template matching / feature matching
- **Email-safe HTML assembly** — `<table>`-based layouts, inline CSS, conditional MSO/Outlook hacks, fluid-hybrid responsive design with media queries
- **Accessibility** — alt text on images, semantic headings, minimum font sizes, sufficient contrast
- **Validation** — pixel-diffing against the original screenshot plus multi-client rendering tests
- **Security** — sanitized inputs/outputs, secure temporary asset storage, HTTPS + API key auth

## Inputs & Outputs

**Input**
- Email preview image (PNG/JPEG/WEBP/HEIC, file upload or URL)
- List of asset image URLs (any order)
- Optional metadata (target clients, color theme, content text)

**Output**
- A single downloadable `.html` file with inline CSS and responsive media queries
- Optional assets ZIP (renamed/optimized images)

## Architecture

```
React UI → FastAPI backend → Gemini Vision (layout/objects)
                            → Google Vision (OCR + color analysis)
                            → OpenCV (asset image matching)
                            → Section JSON → HTML/CSS Generator (MJML/Jinja2)
                            → Email HTML + Assets ZIP → Download
```

## Tech Stack

- **Backend:** Python 3.11+, FastAPI, `google-genai` (Gemini), `google-cloud-vision`, Pillow, OpenCV
- **Templating:** MJML or Jinja2 (table-based responsive email markup)
- **Frontend:** React (+ TypeScript), Axios
- **Testing:** Pytest, Jest, pixel-diff (Resemble.js/pixelmatch), Litmus/Email on Acid
- **Infra:** Docker, GitHub Actions CI/CD, Google Cloud Run / AWS, Terraform (optional)

## Repository Structure

```
email-vision-transformer/
├── frontend/          # React app (upload UI, preview, results)
├── backend/           # FastAPI app, services, models, HTML generator, tests
├── prompts/           # Versioned Gemini prompt templates
├── docs/              # Architecture diagrams, API docs
├── .github/workflows/ # CI pipelines
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── package.json
```

## Branching Strategy

- `main` — production-ready, merges only from `release/*`
- `develop` — integration branch for the next release
- `feature/*` — one branch per module (`layout-extraction`, `ocr-extraction`, `color-style`, `html-assembly`, `frontend-upload`, `api-design`, `ci-cd`)
- `release/vX.Y` and `hotfix/*` as needed

## Status

Early planning stage — architecture and requirements defined; implementation not yet started. See the roadmap below for the current phase order.

## Roadmap

| Phase | Description |
|---|---|
| 1 | Requirements & design finalization |
| 2 | Backend setup (FastAPI, Gemini/Vision SDKs) |
| 3 | Layout extraction (Gemini segmentation) |
| 4 | OCR integration |
| 5 | Style extraction (color/font) |
| 6 | Asset image matching |
| 7 | HTML generation (MJML/Jinja2) |
| 8 | Frontend UI |
| 9 | Testing & QA (pixel-diff, client testing) |
| 10 | CI/CD pipeline |
| 11 | Integration & bugfixing |
| 12 | Documentation |
